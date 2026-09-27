from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from os import PathLike
from typing import Any

_MAX_NUMBER = 10**9
_ID_MAX_LEN = 128
_LOCK_TIMEOUT_SECONDS = 5.0

_RESERVE_KEYS = {"request_id", "op", "reservation_id", "sku", "qty"}
_OTHER_KEYS = {"request_id", "op", "reservation_id"}


def _connect(path: str | bytes | PathLike[str] | PathLike[bytes]) -> sqlite3.Connection:
    conn = sqlite3.connect(
        path,
        timeout=_LOCK_TIMEOUT_SECONDS,
        isolation_level=None,  # transactions are controlled explicitly below
    )
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {int(_LOCK_TIMEOUT_SECONDS * 1000)}")
    return conn


def _as_db_key(value: str) -> bytes:
    # Store identifiers as BLOBs so every Python str accepted by the API,
    # including strings containing lone surrogates, round-trips losslessly.
    return value.encode("utf-8", "surrogatepass")


def _from_db_key(value: bytes) -> str:
    return value.decode("utf-8", "surrogatepass")


def _validate_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= _ID_MAX_LEN):
        raise ValueError(f"{name} must be a str of length 1..{_ID_MAX_LEN}")
    return value


def _validate_int(value: Any, name: str, minimum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an int (bool is not allowed)")
    if not (minimum <= value <= _MAX_NUMBER):
        raise ValueError(f"{name} must be in {minimum}..{_MAX_NUMBER}")
    return int(value)


def _validate_command(command: Any) -> dict[str, Any]:
    if not isinstance(command, dict):
        raise ValueError("each command must be a dict")

    if "request_id" not in command or "op" not in command:
        raise ValueError("command is missing request_id or op")

    request_id = _validate_text(command["request_id"], "request_id")
    op = command["op"]
    if not isinstance(op, str) or op not in {"reserve", "cancel", "ship"}:
        raise ValueError("op must be 'reserve', 'cancel', or 'ship'")

    expected_keys = _RESERVE_KEYS if op == "reserve" else _OTHER_KEYS
    if set(command.keys()) != expected_keys:
        raise ValueError(f"invalid keys for {op}")

    reservation_id = _validate_text(command["reservation_id"], "reservation_id")

    if op == "reserve":
        sku = _validate_text(command["sku"], "sku")
        qty = _validate_int(command["qty"], "qty", 1)
        return {
            "request_id": request_id,
            "op": op,
            "reservation_id": reservation_id,
            "sku": sku,
            "qty": qty,
        }

    return {
        "request_id": request_id,
        "op": op,
        "reservation_id": reservation_id,
    }


def _canonical_command(command: dict[str, Any]) -> str:
    # sort_keys makes dict insertion order irrelevant. ensure_ascii=True also
    # makes the stored representation safe for every Python str value.
    return json.dumps(
        command,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _rollback_quietly(conn: sqlite3.Connection) -> None:
    if conn.in_transaction:
        try:
            conn.rollback()
        except sqlite3.Error:
            # Closing the connection is still attempted by the caller.
            pass


def init_db(
    path: str | bytes | PathLike[str] | PathLike[bytes],
    stocks: dict[str, int],
) -> None:
    if not isinstance(stocks, dict) or not stocks:
        raise ValueError("stocks must be a non-empty dict")

    initial_rows: list[tuple[bytes, int]] = []
    for sku, available in stocks.items():
        sku = _validate_text(sku, "sku")
        available = _validate_int(available, "stock", 0)
        initial_rows.append((_as_db_key(sku), available))

    conn = _connect(path)
    try:
        # Put BEGIN inside executescript: sqlite3.executescript() may otherwise
        # commit a pending transaction before running the script.
        conn.executescript(
            """
            BEGIN IMMEDIATE;

            CREATE TABLE stock (
                sku BLOB PRIMARY KEY,
                available INTEGER NOT NULL
                    CHECK (typeof(available) = 'integer' AND available BETWEEN 0 AND 1000000000)
            ) WITHOUT ROWID;

            CREATE TABLE reservations (
                reservation_id BLOB PRIMARY KEY,
                sku BLOB NOT NULL,
                qty INTEGER NOT NULL
                    CHECK (typeof(qty) = 'integer' AND qty BETWEEN 1 AND 1000000000),
                state TEXT NOT NULL
                    CHECK (state IN ('RESERVED', 'CANCELLED', 'SHIPPED')),
                FOREIGN KEY (sku) REFERENCES stock(sku)
            ) WITHOUT ROWID;

            CREATE TABLE requests (
                request_id BLOB PRIMARY KEY,
                command TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN (
                        'RESERVED', 'CANCELLED', 'SHIPPED',
                        'OUT_OF_STOCK', 'NOT_FOUND', 'CONFLICT'
                    ))
            ) WITHOUT ROWID;
            """
        )
        conn.executemany(
            "INSERT INTO stock(sku, available) VALUES (?, ?)",
            initial_rows,
        )
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
    except BaseException:
        _rollback_quietly(conn)
        raise
    finally:
        conn.close()


def apply_batch(
    path: str | bytes | PathLike[str] | PathLike[bytes],
    commands: list[dict[str, Any]],
    *,
    before_commit: Callable[[], Any] | None = None,
) -> list[dict[str, str]]:
    if not isinstance(commands, list) or not commands:
        raise ValueError("commands must be a non-empty list")

    # Validate all syntax/types before any write transaction starts.
    validated = [_validate_command(command) for command in commands]

    conn = _connect(path)
    try:
        # A RESERVED writer lock serializes complete batches across processes.
        # Other writers either wait up to the finite busy timeout or fail with
        # sqlite3.OperationalError; they never observe a partially committed batch.
        conn.execute("BEGIN IMMEDIATE")

        # SKU existence is part of input validation and must happen before any
        # request-id replay decision. Stocks are immutable after init_db.
        checked_skus: set[bytes] = set()
        for command in validated:
            if command["op"] != "reserve":
                continue
            sku_key = _as_db_key(command["sku"])
            if sku_key in checked_skus:
                continue
            checked_skus.add(sku_key)
            row = conn.execute(
                "SELECT 1 FROM stock WHERE sku = ?",
                (sku_key,),
            ).fetchone()
            if row is None:
                raise ValueError(f"unknown sku: {command['sku']!r}")

        results: list[dict[str, str]] = []

        for command in validated:
            request_id = command["request_id"]
            request_key = _as_db_key(request_id)
            canonical = _canonical_command(command)

            replay = conn.execute(
                "SELECT command, status FROM requests WHERE request_id = ?",
                (request_key,),
            ).fetchone()
            if replay is not None:
                stored_command, stored_status = replay
                if stored_command != canonical:
                    raise ValueError(
                        f"request_id {request_id!r} was already used with different content"
                    )
                results.append({"request_id": request_id, "status": stored_status})
                continue

            op = command["op"]
            reservation_key = _as_db_key(command["reservation_id"])

            if op == "reserve":
                existing = conn.execute(
                    "SELECT 1 FROM reservations WHERE reservation_id = ?",
                    (reservation_key,),
                ).fetchone()

                # Reservation-id conflict has priority over stock availability.
                if existing is not None:
                    status = "CONFLICT"
                else:
                    sku_key = _as_db_key(command["sku"])
                    available = conn.execute(
                        "SELECT available FROM stock WHERE sku = ?",
                        (sku_key,),
                    ).fetchone()[0]
                    qty = command["qty"]
                    if available < qty:
                        status = "OUT_OF_STOCK"
                    else:
                        conn.execute(
                            "UPDATE stock SET available = available - ? WHERE sku = ?",
                            (qty, sku_key),
                        )
                        conn.execute(
                            """
                            INSERT INTO reservations(reservation_id, sku, qty, state)
                            VALUES (?, ?, ?, 'RESERVED')
                            """,
                            (reservation_key, sku_key, qty),
                        )
                        status = "RESERVED"

            else:
                reservation = conn.execute(
                    """
                    SELECT sku, qty, state
                    FROM reservations
                    WHERE reservation_id = ?
                    """,
                    (reservation_key,),
                ).fetchone()

                if reservation is None:
                    status = "NOT_FOUND"
                else:
                    sku_key, qty, state = reservation
                    if state != "RESERVED":
                        status = "CONFLICT"
                    elif op == "cancel":
                        conn.execute(
                            """
                            UPDATE reservations
                            SET state = 'CANCELLED'
                            WHERE reservation_id = ?
                            """,
                            (reservation_key,),
                        )
                        conn.execute(
                            "UPDATE stock SET available = available + ? WHERE sku = ?",
                            (qty, sku_key),
                        )
                        status = "CANCELLED"
                    else:  # ship
                        conn.execute(
                            """
                            UPDATE reservations
                            SET state = 'SHIPPED'
                            WHERE reservation_id = ?
                            """,
                            (reservation_key,),
                        )
                        status = "SHIPPED"

            # Store both success and business-failure results atomically with
            # any state transition. A replay can therefore return the original
            # result without looking at today's stock/reservation state.
            conn.execute(
                "INSERT INTO requests(request_id, command, status) VALUES (?, ?, ?)",
                (request_key, canonical, status),
            )
            results.append({"request_id": request_id, "status": status})

        if before_commit is not None:
            before_commit()

        conn.commit()
        return results
    except BaseException:
        _rollback_quietly(conn)
        raise
    finally:
        conn.close()


def snapshot(
    path: str | bytes | PathLike[str] | PathLike[bytes],
) -> dict[str, dict[str, Any]]:
    conn = _connect(path)
    try:
        # Explicit read transaction pins both SELECTs to one SQLite snapshot.
        conn.execute("BEGIN")
        stock_rows = conn.execute(
            "SELECT sku, available FROM stock ORDER BY sku"
        ).fetchall()
        reservation_rows = conn.execute(
            """
            SELECT reservation_id, sku, qty, state
            FROM reservations
            ORDER BY reservation_id
            """
        ).fetchall()
        conn.commit()
    except BaseException:
        _rollback_quietly(conn)
        raise
    finally:
        conn.close()

    available = {
        _from_db_key(sku): amount
        for sku, amount in stock_rows
    }
    reservations = {
        _from_db_key(reservation_id): {
            "sku": _from_db_key(sku),
            "qty": qty,
            "state": state,
        }
        for reservation_id, sku, qty, state in reservation_rows
    }
    return {"available": available, "reservations": reservations}
