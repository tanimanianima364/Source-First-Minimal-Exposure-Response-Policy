from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from os import PathLike
from typing import Any

_MAX_VALUE = 10**9
_BUSY_TIMEOUT_MS = 5_000


def _connect(path: str | bytes | PathLike[str] | PathLike[bytes]) -> sqlite3.Connection:
    conn = sqlite3.connect(
        path,
        timeout=_BUSY_TIMEOUT_MS / 1000,
        isolation_level=None,
    )
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    return conn


def _rollback(conn: sqlite3.Connection) -> None:
    if conn.in_transaction:
        try:
            conn.rollback()
        except sqlite3.Error:
            # Closing a connection with an active transaction also rolls it back.
            pass


def _is_int_not_bool(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_name(value: Any, field: str) -> str:
    if not isinstance(value, str) or not (1 <= len(value) <= 128):
        raise ValueError(f"{field} must be a str of length 1..128")
    return value


def _key(value: str) -> bytes:
    # SQLite's Python adapter cannot encode lone surrogates as TEXT.
    # BLOB + surrogatepass preserves every Python str accepted by the API.
    return value.encode("utf-8", "surrogatepass")


def _unkey(value: bytes) -> str:
    return value.decode("utf-8", "surrogatepass")


def _canonical_command(command: dict[str, Any]) -> str:
    # Key order must not affect request identity.
    return json.dumps(
        command,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _validate_commands(commands: Any) -> list[dict[str, Any]]:
    if not isinstance(commands, list) or not commands:
        raise ValueError("commands must be a non-empty list")

    validated: list[dict[str, Any]] = []

    for raw in commands:
        if not isinstance(raw, dict):
            raise ValueError("each command must be a dict")

        op = raw.get("op")

        if op == "reserve":
            expected = {
                "request_id",
                "op",
                "reservation_id",
                "sku",
                "qty",
            }
        elif op in {"cancel", "ship"}:
            expected = {
                "request_id",
                "op",
                "reservation_id",
            }
        else:
            raise ValueError("invalid op")

        if set(raw.keys()) != expected:
            raise ValueError("command has missing or extra keys")

        request_id = _validate_name(raw["request_id"], "request_id")
        reservation_id = _validate_name(
            raw["reservation_id"],
            "reservation_id",
        )

        if op == "reserve":
            sku = _validate_name(raw["sku"], "sku")
            qty = raw["qty"]

            if (
                not _is_int_not_bool(qty)
                or not (1 <= qty <= _MAX_VALUE)
            ):
                raise ValueError(
                    "qty must be an int in 1..10^9 "
                    "(bool is invalid)"
                )

            validated.append(
                {
                    "request_id": request_id,
                    "op": "reserve",
                    "reservation_id": reservation_id,
                    "sku": sku,
                    "qty": qty,
                }
            )
        else:
            validated.append(
                {
                    "request_id": request_id,
                    "op": op,
                    "reservation_id": reservation_id,
                }
            )

    return validated


def init_db(path, stocks) -> None:
    if not isinstance(stocks, dict) or not stocks:
        raise ValueError("stocks must be a non-empty dict")

    items: list[tuple[str, int]] = []

    for sku, available in stocks.items():
        sku = _validate_name(sku, "sku")

        if (
            not _is_int_not_bool(available)
            or not (0 <= available <= _MAX_VALUE)
        ):
            raise ValueError(
                "stock must be an int in 0..10^9 "
                "(bool is invalid)"
            )

        items.append((sku, available))

    conn = _connect(path)

    try:
        conn.execute("BEGIN IMMEDIATE")

        conn.execute(
            """
            CREATE TABLE inventory (
                sku BLOB PRIMARY KEY NOT NULL,
                available INTEGER NOT NULL
                    CHECK (available BETWEEN 0 AND 1000000000)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE reservations (
                reservation_id BLOB PRIMARY KEY NOT NULL,
                sku BLOB NOT NULL REFERENCES inventory(sku),
                qty INTEGER NOT NULL
                    CHECK (qty BETWEEN 1 AND 1000000000),
                state TEXT NOT NULL
                    CHECK (
                        state IN (
                            'RESERVED',
                            'CANCELLED',
                            'SHIPPED'
                        )
                    )
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE requests (
                request_id BLOB PRIMARY KEY NOT NULL,
                command TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (
                        status IN (
                            'RESERVED',
                            'OUT_OF_STOCK',
                            'CANCELLED',
                            'SHIPPED',
                            'NOT_FOUND',
                            'CONFLICT'
                        )
                    )
            )
            """
        )

        conn.executemany(
            """
            INSERT INTO inventory(sku, available)
            VALUES (?, ?)
            """,
            [
                (_key(sku), available)
                for sku, available in items
            ],
        )

        conn.commit()

    except BaseException:
        _rollback(conn)
        raise

    finally:
        conn.close()


def apply_batch(
    path,
    commands,
    *,
    before_commit: Callable[[], Any] | None = None,
) -> list[dict]:
    # Syntax/type/key validation happens before replay detection.
    validated = _validate_commands(commands)

    conn = _connect(path)

    try:
        # Serialize successful writer batches at the SQLite database level.
        # This works across independent processes, not just threads.
        conn.execute("BEGIN IMMEDIATE")

        # Unknown-SKU checking is deliberately performed before any replay
        # lookup, as required by the API contract.
        reserve_skus = {
            _key(command["sku"])
            for command in validated
            if command["op"] == "reserve"
        }

        for sku_key in reserve_skus:
            row = conn.execute(
                """
                SELECT 1
                FROM inventory
                WHERE sku = ?
                """,
                (sku_key,),
            ).fetchone()

            if row is None:
                raise ValueError(
                    "reserve refers to an unregistered SKU"
                )

        results: list[dict] = []

        for command in validated:
            request_id = command["request_id"]
            request_key = _key(request_id)
            canonical = _canonical_command(command)

            replay = conn.execute(
                """
                SELECT command, status
                FROM requests
                WHERE request_id = ?
                """,
                (request_key,),
            ).fetchone()

            if replay is not None:
                saved_command, saved_status = replay

                if saved_command != canonical:
                    raise ValueError(
                        "request_id was already used "
                        "for different content"
                    )

                results.append(
                    {
                        "request_id": request_id,
                        "status": saved_status,
                    }
                )
                continue

            op = command["op"]
            reservation_key = _key(
                command["reservation_id"]
            )

            if op == "reserve":
                # Reservation-id collision takes precedence over
                # the stock sufficiency test.
                exists = conn.execute(
                    """
                    SELECT 1
                    FROM reservations
                    WHERE reservation_id = ?
                    """,
                    (reservation_key,),
                ).fetchone()

                if exists is not None:
                    status = "CONFLICT"

                else:
                    sku_key = _key(command["sku"])
                    qty = command["qty"]

                    available = conn.execute(
                        """
                        SELECT available
                        FROM inventory
                        WHERE sku = ?
                        """,
                        (sku_key,),
                    ).fetchone()[0]

                    if available < qty:
                        status = "OUT_OF_STOCK"

                    else:
                        conn.execute(
                            """
                            UPDATE inventory
                            SET available = available - ?
                            WHERE sku = ?
                            """,
                            (qty, sku_key),
                        )

                        conn.execute(
                            """
                            INSERT INTO reservations(
                                reservation_id,
                                sku,
                                qty,
                                state
                            )
                            VALUES (?, ?, ?, 'RESERVED')
                            """,
                            (
                                reservation_key,
                                sku_key,
                                qty,
                            ),
                        )

                        status = "RESERVED"

            else:
                row = conn.execute(
                    """
                    SELECT sku, qty, state
                    FROM reservations
                    WHERE reservation_id = ?
                    """,
                    (reservation_key,),
                ).fetchone()

                if row is None:
                    status = "NOT_FOUND"

                else:
                    sku_key, qty, state = row

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
                            """
                            UPDATE inventory
                            SET available = available + ?
                            WHERE sku = ?
                            """,
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

            # Business failures are persisted too, so retransmission
            # always returns the first committed result.
            conn.execute(
                """
                INSERT INTO requests(
                    request_id,
                    command,
                    status
                )
                VALUES (?, ?, ?)
                """,
                (
                    request_key,
                    canonical,
                    status,
                ),
            )

            results.append(
                {
                    "request_id": request_id,
                    "status": status,
                }
            )

        # All state/request-log changes already exist inside the still-open
        # transaction here.
        if before_commit is not None:
            before_commit()

        # Results are not returned until commit succeeds.
        conn.commit()
        return results

    except BaseException:
        _rollback(conn)
        raise

    finally:
        conn.close()


def snapshot(path) -> dict:
    conn = _connect(path)

    try:
        # Both SELECTs belong to one explicit read transaction, so they
        # observe one consistent SQLite snapshot.
        conn.execute("BEGIN")

        stock_rows = conn.execute(
            """
            SELECT sku, available
            FROM inventory
            ORDER BY sku
            """
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
        _rollback(conn)
        raise

    finally:
        conn.close()

    available = {
        _unkey(sku): qty
        for sku, qty in stock_rows
    }

    reservations = {
        _unkey(reservation_id): {
            "sku": _unkey(sku),
            "qty": qty,
            "state": state,
        }
        for reservation_id, sku, qty, state
        in reservation_rows
    }

    return {
        "available": available,
        "reservations": reservations,
    }
