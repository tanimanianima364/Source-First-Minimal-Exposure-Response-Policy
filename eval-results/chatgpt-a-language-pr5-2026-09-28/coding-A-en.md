以下が実装とテストです。Python 3.12以降の標準ライブラリのみを使用しています。

### `inventory.py`

```python
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
```

### `test_inventory.py`

```python
from __future__ import annotations

import multiprocessing
import os
import tempfile
import unittest

import inventory


def _process_apply(path, barrier, command, out_queue):
    try:
        barrier.wait(timeout=10)
        result = inventory.apply_batch(path, [command])
        out_queue.put(("ok", result))
    except BaseException as exc:
        out_queue.put(("error", type(exc).__name__, repr(exc)))


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.db_path = os.path.join(
            self.tempdir.name,
            "inventory.sqlite3",
        )

    def init(self, stocks=None):
        if stocks is None:
            stocks = {"A": 10}
        inventory.init_db(self.db_path, stocks)

    def assert_processes_finish(self, processes):
        for process in processes:
            process.join(timeout=15)

        hung = [
            process
            for process in processes
            if process.is_alive()
        ]

        for process in hung:
            process.terminate()
            process.join(timeout=5)

        self.assertFalse(
            hung,
            "child process did not finish",
        )

        for process in processes:
            self.assertEqual(process.exitcode, 0)

    def test_normal_reserve_cancel_ship_and_conflict_priority(self):
        self.init({"A": 10})

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "q1",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 3,
                    }
                ],
            ),
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "q2",
                        "op": "cancel",
                        "reservation_id": "r1",
                    }
                ],
            ),
            [
                {
                    "request_id": "q2",
                    "status": "CANCELLED",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "q3",
                        "op": "cancel",
                        "reservation_id": "r1",
                    }
                ],
            ),
            [
                {
                    "request_id": "q3",
                    "status": "CONFLICT",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "q4",
                        "op": "reserve",
                        "reservation_id": "r2",
                        "sku": "A",
                        "qty": 10,
                    }
                ],
            ),
            [
                {
                    "request_id": "q4",
                    "status": "RESERVED",
                }
            ],
        )

        # No stock remains, but reservation-id conflict has
        # priority over stock.
        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "q5",
                        "op": "reserve",
                        "reservation_id": "r2",
                        "sku": "A",
                        "qty": 1,
                    }
                ],
            ),
            [
                {
                    "request_id": "q5",
                    "status": "CONFLICT",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "q6",
                        "op": "ship",
                        "reservation_id": "r2",
                    }
                ],
            ),
            [
                {
                    "request_id": "q6",
                    "status": "SHIPPED",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "q7",
                        "op": "cancel",
                        "reservation_id": "r2",
                    }
                ],
            ),
            [
                {
                    "request_id": "q7",
                    "status": "CONFLICT",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "q8",
                        "op": "ship",
                        "reservation_id": "missing",
                    }
                ],
            ),
            [
                {
                    "request_id": "q8",
                    "status": "NOT_FOUND",
                }
            ],
        )

        self.assertEqual(
            inventory.snapshot(self.db_path),
            {
                "available": {"A": 0},
                "reservations": {
                    "r1": {
                        "sku": "A",
                        "qty": 3,
                        "state": "CANCELLED",
                    },
                    "r2": {
                        "sku": "A",
                        "qty": 10,
                        "state": "SHIPPED",
                    },
                },
            },
        )

    def test_failed_results_are_replayed_without_reapplying(self):
        self.init({"A": 2})

        oos = {
            "request_id": "oos",
            "op": "reserve",
            "reservation_id": "r-oos",
            "sku": "A",
            "qty": 3,
        }

        self.assertEqual(
            inventory.apply_batch(self.db_path, [oos]),
            [
                {
                    "request_id": "oos",
                    "status": "OUT_OF_STOCK",
                }
            ],
        )

        reordered_oos = dict(
            [
                ("qty", 3),
                ("sku", "A"),
                ("reservation_id", "r-oos"),
                ("op", "reserve"),
                ("request_id", "oos"),
            ]
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [reordered_oos],
            ),
            [
                {
                    "request_id": "oos",
                    "status": "OUT_OF_STOCK",
                }
            ],
        )

        missing = {
            "request_id": "nf",
            "op": "cancel",
            "reservation_id": "future",
        }

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [missing],
            ),
            [
                {
                    "request_id": "nf",
                    "status": "NOT_FOUND",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "mk",
                        "op": "reserve",
                        "reservation_id": "future",
                        "sku": "A",
                        "qty": 1,
                    }
                ],
            ),
            [
                {
                    "request_id": "mk",
                    "status": "RESERVED",
                }
            ],
        )

        # The stored NOT_FOUND result must be returned even though
        # the reservation exists now.
        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [missing],
            ),
            [
                {
                    "request_id": "nf",
                    "status": "NOT_FOUND",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "ship",
                        "op": "ship",
                        "reservation_id": "future",
                    }
                ],
            ),
            [
                {
                    "request_id": "ship",
                    "status": "SHIPPED",
                }
            ],
        )

        conflict = {
            "request_id": "conf",
            "op": "cancel",
            "reservation_id": "future",
        }

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [conflict],
            ),
            [
                {
                    "request_id": "conf",
                    "status": "CONFLICT",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [conflict],
            ),
            [
                {
                    "request_id": "conf",
                    "status": "CONFLICT",
                }
            ],
        )

    def test_same_request_different_dict_key_order_is_same_request(self):
        self.init({"A": 10})

        first = {
            "request_id": "q1",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 3,
        }

        second = dict(
            [
                ("qty", 3),
                ("request_id", "q1"),
                ("sku", "A"),
                ("op", "reserve"),
                ("reservation_id", "r1"),
            ]
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [first],
            ),
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                }
            ],
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [second],
            ),
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                }
            ],
        )

        self.assertEqual(
            inventory.snapshot(
                self.db_path
            )["available"],
            {"A": 7},
        )

    def test_duplicate_request_inside_batch_applies_once(self):
        self.init({"A": 10})

        command = {
            "request_id": "q1",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 4,
        }

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    command,
                    dict(command),
                ],
            ),
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                },
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                },
            ],
        )

        state = inventory.snapshot(self.db_path)

        self.assertEqual(
            state["available"],
            {"A": 6},
        )
        self.assertEqual(
            len(state["reservations"]),
            1,
        )

    def test_request_content_conflict_rolls_back_whole_batch(self):
        self.init({"A": 10})

        inventory.apply_batch(
            self.db_path,
            [
                {
                    "request_id": "old",
                    "op": "reserve",
                    "reservation_id": "r-old",
                    "sku": "A",
                    "qty": 2,
                }
            ],
        )

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "new",
                        "op": "reserve",
                        "reservation_id": "r-new",
                        "sku": "A",
                        "qty": 3,
                    },
                    {
                        "request_id": "old",
                        "op": "reserve",
                        "reservation_id": "different",
                        "sku": "A",
                        "qty": 1,
                    },
                ],
            )

        self.assertEqual(
            inventory.snapshot(self.db_path),
            {
                "available": {"A": 8},
                "reservations": {
                    "r-old": {
                        "sku": "A",
                        "qty": 2,
                        "state": "RESERVED",
                    },
                },
            },
        )

        # "new" was rolled back from the request log too.
        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "new",
                        "op": "reserve",
                        "reservation_id": "r-new-2",
                        "sku": "A",
                        "qty": 1,
                    }
                ],
            ),
            [
                {
                    "request_id": "new",
                    "status": "RESERVED",
                }
            ],
        )

    def test_before_commit_exception_rolls_back_everything(self):
        self.init({"A": 10})

        calls = []

        def fail_before_commit():
            calls.append("called")
            raise RuntimeError("injected failure")

        command = {
            "request_id": "q1",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 4,
        }

        with self.assertRaisesRegex(
            RuntimeError,
            "injected failure",
        ):
            inventory.apply_batch(
                self.db_path,
                [command],
                before_commit=fail_before_commit,
            )

        self.assertEqual(
            calls,
            ["called"],
        )

        self.assertEqual(
            inventory.snapshot(self.db_path),
            {
                "available": {"A": 10},
                "reservations": {},
            },
        )

        # The request log was rolled back too.
        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [command],
            ),
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                }
            ],
        )

    def test_batch_order_is_visible_to_later_commands(self):
        self.init({"A": 5})

        results = inventory.apply_batch(
            self.db_path,
            [
                {
                    "request_id": "q1",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 5,
                },
                {
                    "request_id": "q2",
                    "op": "reserve",
                    "reservation_id": "r2",
                    "sku": "A",
                    "qty": 1,
                },
                {
                    "request_id": "q3",
                    "op": "cancel",
                    "reservation_id": "r1",
                },
                {
                    "request_id": "q4",
                    "op": "reserve",
                    "reservation_id": "r2",
                    "sku": "A",
                    "qty": 1,
                },
            ],
        )

        self.assertEqual(
            results,
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                },
                {
                    "request_id": "q2",
                    "status": "OUT_OF_STOCK",
                },
                {
                    "request_id": "q3",
                    "status": "CANCELLED",
                },
                {
                    "request_id": "q4",
                    "status": "RESERVED",
                },
            ],
        )

        self.assertEqual(
            inventory.snapshot(
                self.db_path
            )["available"],
            {"A": 4},
        )

    def test_validation_and_unknown_sku(self):
        with self.assertRaises(ValueError):
            inventory.init_db(
                self.db_path,
                {},
            )

        with self.assertRaises(ValueError):
            inventory.init_db(
                self.db_path,
                {"A": True},
            )

        self.init({"A": 1})

        invalid_batches = [
            [],
            [
                {
                    "request_id": "q",
                    "op": "reserve",
                    "reservation_id": "r",
                    "sku": "A",
                    "qty": True,
                }
            ],
            [
                {
                    "request_id": "q",
                    "op": "reserve",
                    "reservation_id": "r",
                    "sku": "A",
                    "qty": 0,
                }
            ],
            [
                {
                    "request_id": "q",
                    "op": "cancel",
                    "reservation_id": "r",
                    "extra": 1,
                }
            ],
            [
                {
                    "request_id": "",
                    "op": "cancel",
                    "reservation_id": "r",
                }
            ],
            [
                {
                    "request_id": "q",
                    "op": "bad",
                    "reservation_id": "r",
                }
            ],
        ]

        for batch in invalid_batches:
            with self.subTest(batch=batch):
                with self.assertRaises(ValueError):
                    inventory.apply_batch(
                        self.db_path,
                        batch,
                    )

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "u",
                        "op": "reserve",
                        "reservation_id": "r",
                        "sku": "UNKNOWN",
                        "qty": 1,
                    }
                ],
            )

        self.assertEqual(
            inventory.snapshot(self.db_path),
            {
                "available": {"A": 1},
                "reservations": {},
            },
        )

    def test_validation_is_not_hidden_by_saved_request(self):
        self.init({"A": 2})

        inventory.apply_batch(
            self.db_path,
            [
                {
                    "request_id": "q1",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 1,
                }
            ],
        )

        malformed = {
            "request_id": "q1",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 1,
            "extra": "not allowed",
        }

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db_path,
                [malformed],
            )

    def test_reopen_persists_state(self):
        self.init({"A": 7})

        inventory.apply_batch(
            self.db_path,
            [
                {
                    "request_id": "q1",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 2,
                }
            ],
        )

        # Each API call opens a new sqlite3 connection.
        self.assertEqual(
            inventory.snapshot(self.db_path),
            {
                "available": {"A": 5},
                "reservations": {
                    "r1": {
                        "sku": "A",
                        "qty": 2,
                        "state": "RESERVED",
                    }
                },
            },
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db_path,
                [
                    {
                        "request_id": "q1",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 2,
                    }
                ],
            ),
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                }
            ],
        )

        self.assertEqual(
            inventory.snapshot(
                self.db_path
            )["available"],
            {"A": 5},
        )

    def test_process_race_cannot_oversell(self):
        self.init({"A": 10})

        ctx = multiprocessing.get_context("spawn")
        barrier = ctx.Barrier(2)
        out_queue = ctx.Queue()

        commands = [
            {
                "request_id": "p1",
                "op": "reserve",
                "reservation_id": "r1",
                "sku": "A",
                "qty": 7,
            },
            {
                "request_id": "p2",
                "op": "reserve",
                "reservation_id": "r2",
                "sku": "A",
                "qty": 7,
            },
        ]

        processes = [
            ctx.Process(
                target=_process_apply,
                args=(
                    self.db_path,
                    barrier,
                    command,
                    out_queue,
                ),
            )
            for command in commands
        ]

        for process in processes:
            process.start()

        self.assert_processes_finish(processes)

        messages = [
            out_queue.get(timeout=5)
            for _ in processes
        ]

        self.assertTrue(
            all(
                message[0] == "ok"
                for message in messages
            ),
            messages,
        )

        statuses = sorted(
            message[1][0]["status"]
            for message in messages
        )

        self.assertEqual(
            statuses,
            [
                "OUT_OF_STOCK",
                "RESERVED",
            ],
        )

        state = inventory.snapshot(self.db_path)

        self.assertEqual(
            state["available"],
            {"A": 3},
        )
        self.assertEqual(
            len(state["reservations"]),
            1,
        )

    def test_process_race_same_request_is_applied_once(self):
        self.init({"A": 10})

        ctx = multiprocessing.get_context("spawn")
        barrier = ctx.Barrier(2)
        out_queue = ctx.Queue()

        command = {
            "request_id": "same",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 7,
        }

        processes = [
            ctx.Process(
                target=_process_apply,
                args=(
                    self.db_path,
                    barrier,
                    command,
                    out_queue,
                ),
            )
            for _ in range(2)
        ]

        for process in processes:
            process.start()

        self.assert_processes_finish(processes)

        messages = [
            out_queue.get(timeout=5)
            for _ in processes
        ]

        self.assertTrue(
            all(
                message[0] == "ok"
                for message in messages
            ),
            messages,
        )

        self.assertEqual(
            [
                message[1]
                for message in messages
            ],
            [
                [
                    {
                        "request_id": "same",
                        "status": "RESERVED",
                    }
                ],
                [
                    {
                        "request_id": "same",
                        "status": "RESERVED",
                    }
                ],
            ],
        )

        self.assertEqual(
            inventory.snapshot(self.db_path),
            {
                "available": {"A": 3},
                "reservations": {
                    "r1": {
                        "sku": "A",
                        "qty": 7,
                        "state": "RESERVED",
                    }
                },
            },
        )

    def test_process_race_cancel_vs_ship_only_one_succeeds(self):
        self.init({"A": 10})

        inventory.apply_batch(
            self.db_path,
            [
                {
                    "request_id": "make",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 4,
                }
            ],
        )

        ctx = multiprocessing.get_context("spawn")
        barrier = ctx.Barrier(2)
        out_queue = ctx.Queue()

        commands = [
            {
                "request_id": "cancel",
                "op": "cancel",
                "reservation_id": "r1",
            },
            {
                "request_id": "ship",
                "op": "ship",
                "reservation_id": "r1",
            },
        ]

        processes = [
            ctx.Process(
                target=_process_apply,
                args=(
                    self.db_path,
                    barrier,
                    command,
                    out_queue,
                ),
            )
            for command in commands
        ]

        for process in processes:
            process.start()

        self.assert_processes_finish(processes)

        messages = [
            out_queue.get(timeout=5)
            for _ in processes
        ]

        self.assertTrue(
            all(
                message[0] == "ok"
                for message in messages
            ),
            messages,
        )

        statuses = sorted(
            message[1][0]["status"]
            for message in messages
        )

        self.assertIn(
            statuses,
            [
                [
                    "CANCELLED",
                    "CONFLICT",
                ],
                [
                    "CONFLICT",
                    "SHIPPED",
                ],
            ],
        )

        state = inventory.snapshot(self.db_path)
        reservation = state["reservations"]["r1"]

        if reservation["state"] == "CANCELLED":
            self.assertEqual(
                state["available"],
                {"A": 10},
            )
        else:
            self.assertEqual(
                reservation["state"],
                "SHIPPED",
            )
            self.assertEqual(
                state["available"],
                {"A": 6},
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

実行コマンドは、2ファイルを同じディレクトリに置いて次のとおりです。

```bash
python3 -m unittest -v test_inventory.py
```

原子性とプロセス間直列化は、`apply_batch` 全体を SQLite の `BEGIN IMMEDIATE`～`COMMIT` で囲むことで保証しています。複数プロセスの書き込みはSQLiteのDBロックによって直列化され、在庫更新も `available >= qty` を条件にした `UPDATE` なので負数化しません。5秒の `busy_timeout` を設定しているため、ロックが解放されなければ有限時間で `sqlite3.OperationalError` になり得ます。

再送については `requests` テーブルに `request_id`、キー順に依存しない正規化済みコマンド、最初の結果を同一トランザクションで保存します。同一内容なら保存結果だけを返し、異なる内容なら `ValueError` となってbatch全体がロールバックされます。`OUT_OF_STOCK`、`NOT_FOUND`、`CONFLICT` も同様に永続化します。入力形式と未登録SKUの検査はこの再送検索より前です。

状態遷移は `RESERVED → CANCELLED` または `RESERVED → SHIPPED` だけを許可し、SQLiteの書き込みトランザクション内で判定・更新します。`snapshot` は明示的な読み取りトランザクション内で複数の `SELECT` を行うため、一貫した同一SQLiteスナップショットを返します。

この環境では **Python 3.13.5** で実際に実行し、**13テストすべて成功**しました。

```text
Ran 13 tests in 2.202s

OK
```

実行したファイルもそのまま取得できます: :chatgpt-content-reference{index="0"}[inventory.py](sandbox:/mnt/data/inventory.py) / :chatgpt-content-reference{index="1"}[test_inventory.py](sandbox:/mnt/data/test_inventory.py)