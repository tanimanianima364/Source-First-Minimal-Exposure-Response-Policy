from __future__ import annotations

import sqlite3
from typing import Any, Callable

__all__ = ["init_db", "apply_batch", "snapshot"]

_MAX_VALUE = 1_000_000_000
_MAX_TEXT_LEN = 128
_BUSY_TIMEOUT_SECONDS = 5.0

_EXPECTED_KEYS = {
    "reserve": {"request_id", "op", "reservation_id", "sku", "qty"},
    "cancel": {"request_id", "op", "reservation_id"},
    "ship": {"request_id", "op", "reservation_id"},
}


def _connect(path: Any) -> sqlite3.Connection:
    conn = sqlite3.connect(
        path,
        timeout=_BUSY_TIMEOUT_SECONDS,
        isolation_level=None,
    )
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {int(_BUSY_TIMEOUT_SECONDS * 1000)}")
    return conn


def _valid_text(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= _MAX_TEXT_LEN


def _valid_int(value: Any, minimum: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= _MAX_VALUE
    )


def _encode_text(value: str) -> bytes:
    # surrogatepass preserves every Python str value, including lone surrogates.
    return value.encode("utf-8", "surrogatepass")


def _decode_text(value: bytes) -> str:
    return value.decode("utf-8", "surrogatepass")


def _pack_text(value: str) -> bytes:
    encoded = _encode_text(value)
    return len(encoded).to_bytes(4, "big") + encoded


def _validate_stocks(stocks: Any) -> list[tuple[bytes, int]]:
    if not isinstance(stocks, dict) or not stocks:
        raise ValueError("stocks must be a non-empty dict")

    rows: list[tuple[bytes, int]] = []
    for sku, available in stocks.items():
        if not _valid_text(sku):
            raise ValueError("each SKU must be a str of length 1..128")
        if not _valid_int(available, 0):
            raise ValueError(
                "each stock value must be an int in 0..10^9, excluding bool"
            )
        rows.append((_encode_text(sku), int(available)))
    return rows


def _validate_commands(commands: Any) -> list[dict[str, Any]]:
    if not isinstance(commands, list) or not commands:
        raise ValueError("commands must be a non-empty list")

    validated: list[dict[str, Any]] = []
    for command in commands:
        if not isinstance(command, dict):
            raise ValueError("each command must be a dict")

        op = command.get("op")
        if not isinstance(op, str) or op not in _EXPECTED_KEYS:
            raise ValueError("invalid op")
        if set(command.keys()) != _EXPECTED_KEYS[op]:
            raise ValueError("command has missing or unexpected keys")

        if not _valid_text(command["request_id"]):
            raise ValueError("request_id must be a str of length 1..128")
        if not _valid_text(command["reservation_id"]):
            raise ValueError("reservation_id must be a str of length 1..128")

        if op == "reserve":
            if not _valid_text(command["sku"]):
                raise ValueError("sku must be a str of length 1..128")
            if not _valid_int(command["qty"], 1):
                raise ValueError(
                    "qty must be an int in 1..10^9, excluding bool"
                )

        validated.append(command)
    return validated


def _canonical_command(command: dict[str, Any]) -> bytes:
    op = command["op"]
    prefix = {"reserve": b"R", "cancel": b"C", "ship": b"S"}[op]
    data = (
        prefix
        + _pack_text(command["request_id"])
        + _pack_text(command["reservation_id"])
    )
    if op == "reserve":
        data += _pack_text(command["sku"])
        data += int(command["qty"]).to_bytes(8, "big", signed=False)
    return data


def init_db(path: Any, stocks: dict[str, int]) -> None:
    stock_rows = _validate_stocks(stocks)
    conn = _connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            CREATE TABLE stock (
                sku BLOB PRIMARY KEY NOT NULL CHECK (typeof(sku) = 'blob'),
                available INTEGER NOT NULL
                    CHECK (typeof(available) = 'integer'
                           AND available BETWEEN 0 AND 1000000000)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE reservations (
                reservation_id BLOB PRIMARY KEY NOT NULL
                    CHECK (typeof(reservation_id) = 'blob'),
                sku BLOB NOT NULL CHECK (typeof(sku) = 'blob'),
                qty INTEGER NOT NULL
                    CHECK (typeof(qty) = 'integer'
                           AND qty BETWEEN 1 AND 1000000000),
                state TEXT NOT NULL
                    CHECK (state IN ('RESERVED', 'CANCELLED', 'SHIPPED')),
                FOREIGN KEY (sku) REFERENCES stock(sku)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE requests (
                request_id BLOB PRIMARY KEY NOT NULL
                    CHECK (typeof(request_id) = 'blob'),
                command BLOB NOT NULL CHECK (typeof(command) = 'blob'),
                status TEXT NOT NULL
                    CHECK (status IN ('RESERVED', 'OUT_OF_STOCK', 'CANCELLED',
                                      'SHIPPED', 'NOT_FOUND', 'CONFLICT'))
            )
            """
        )
        conn.executemany(
            "INSERT INTO stock(sku, available) VALUES (?, ?)",
            stock_rows,
        )
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        raise
    finally:
        conn.close()


def _preflight_registered_skus(
    conn: sqlite3.Connection,
    commands: list[dict[str, Any]],
) -> None:
    # The SKU set is immutable after init_db, so this can be checked before the
    # writer transaction. This guarantees an unknown SKU is rejected before any
    # request-id replay lookup or mutation.
    seen: set[bytes] = set()
    for command in commands:
        if command["op"] != "reserve":
            continue
        sku = _encode_text(command["sku"])
        if sku in seen:
            continue
        seen.add(sku)
        row = conn.execute(
            "SELECT 1 FROM stock WHERE sku = ?",
            (sku,),
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown SKU: {command['sku']!r}")


def apply_batch(
    path: Any,
    commands: list[dict[str, Any]],
    *,
    before_commit: Callable[[], Any] | None = None,
) -> list[dict[str, str]]:
    validated = _validate_commands(commands)
    conn = _connect(path)
    try:
        _preflight_registered_skus(conn, validated)
        conn.execute("BEGIN IMMEDIATE")

        results: list[dict[str, str]] = []

        for command in validated:
            request_id = _encode_text(command["request_id"])
            canonical = _canonical_command(command)

            previous = conn.execute(
                """
                SELECT command, status
                  FROM requests
                 WHERE request_id = ?
                """,
                (request_id,),
            ).fetchone()

            if previous is not None:
                previous_command, previous_status = previous
                if previous_command != canonical:
                    raise ValueError(
                        "request_id was already used with different content"
                    )

                results.append(
                    {
                        "request_id": command["request_id"],
                        "status": previous_status,
                    }
                )
                continue

            op = command["op"]
            reservation_id = _encode_text(command["reservation_id"])

            if op == "reserve":
                existing = conn.execute(
                    """
                    SELECT 1
                      FROM reservations
                     WHERE reservation_id = ?
                    """,
                    (reservation_id,),
                ).fetchone()

                # Reservation-id conflict deliberately has priority over
                # checking available stock.
                if existing is not None:
                    status = "CONFLICT"
                else:
                    sku = _encode_text(command["sku"])
                    qty = int(command["qty"])

                    # Guarding the UPDATE with available >= qty provides a
                    # database-level non-negative-stock invariant as well.
                    cursor = conn.execute(
                        """
                        UPDATE stock
                           SET available = available - ?
                         WHERE sku = ?
                           AND available >= ?
                        """,
                        (qty, sku, qty),
                    )

                    if cursor.rowcount == 0:
                        status = "OUT_OF_STOCK"
                    else:
                        conn.execute(
                            """
                            INSERT INTO reservations(
                                reservation_id, sku, qty, state
                            )
                            VALUES (?, ?, ?, 'RESERVED')
                            """,
                            (reservation_id, sku, qty),
                        )
                        status = "RESERVED"

            else:
                reservation = conn.execute(
                    """
                    SELECT sku, qty, state
                      FROM reservations
                     WHERE reservation_id = ?
                    """,
                    (reservation_id,),
                ).fetchone()

                if reservation is None:
                    status = "NOT_FOUND"
                else:
                    sku, qty, state = reservation

                    if state != "RESERVED":
                        status = "CONFLICT"

                    elif op == "cancel":
                        cursor = conn.execute(
                            """
                            UPDATE reservations
                               SET state = 'CANCELLED'
                             WHERE reservation_id = ?
                               AND state = 'RESERVED'
                            """,
                            (reservation_id,),
                        )
                        if cursor.rowcount != 1:
                            raise sqlite3.IntegrityError(
                                "reservation state changed unexpectedly"
                            )

                        conn.execute(
                            """
                            UPDATE stock
                               SET available = available + ?
                             WHERE sku = ?
                            """,
                            (qty, sku),
                        )
                        status = "CANCELLED"

                    else:  # ship
                        cursor = conn.execute(
                            """
                            UPDATE reservations
                               SET state = 'SHIPPED'
                             WHERE reservation_id = ?
                               AND state = 'RESERVED'
                            """,
                            (reservation_id,),
                        )
                        if cursor.rowcount != 1:
                            raise sqlite3.IntegrityError(
                                "reservation state changed unexpectedly"
                            )
                        status = "SHIPPED"

            conn.execute(
                """
                INSERT INTO requests(request_id, command, status)
                VALUES (?, ?, ?)
                """,
                (request_id, canonical, status),
            )
            results.append(
                {
                    "request_id": command["request_id"],
                    "status": status,
                }
            )

        if before_commit is not None:
            before_commit()

        conn.execute("COMMIT")
        return results

    except BaseException:
        if conn.in_transaction:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()


def snapshot(path: Any) -> dict[str, dict[str, Any]]:
    conn = _connect(path)
    try:
        # A read transaction pins a single SQLite snapshot for both SELECTs.
        conn.execute("BEGIN")

        stock_rows = conn.execute(
            """
            SELECT sku, available
              FROM stock
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

        result = {
            "available": {
                _decode_text(sku): available
                for sku, available in stock_rows
            },
            "reservations": {
                _decode_text(reservation_id): {
                    "sku": _decode_text(sku),
                    "qty": qty,
                    "state": state,
                }
                for reservation_id, sku, qty, state in reservation_rows
            },
        }

        conn.execute("COMMIT")
        return result

    except BaseException:
        if conn.in_transaction:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()
