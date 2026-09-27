以下の実装で、batch 単位の原子性、`request_id` の永続的な冪等性、独立プロセス間の直列化、`snapshot` の一貫性をSQLiteトランザクションだけで保証します。

### `inventory.py`

```python
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
```

### `test_inventory.py`

```python
from __future__ import annotations

import multiprocessing as mp
import tempfile
import unittest
from pathlib import Path

import inventory


def _apply_worker(path, barrier, queue, commands):
    try:
        barrier.wait(timeout=10)
        result = inventory.apply_batch(path, commands)
        queue.put(("ok", result))
    except BaseException as exc:
        queue.put(
            (
                "error",
                type(exc).__name__,
                repr(exc),
            )
        )


def _snapshot_worker(path, queue):
    try:
        queue.put(
            (
                "ok",
                inventory.snapshot(path),
            )
        )
    except BaseException as exc:
        queue.put(
            (
                "error",
                type(exc).__name__,
                repr(exc),
            )
        )


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(
            Path(self.tmp.name) / "inventory.sqlite3"
        )
        inventory.init_db(
            self.db,
            {
                "A": 10,
                "B": 3,
            },
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_reserve_cancel_ship_and_snapshot(self):
        result = inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "q1",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 3,
                },
                {
                    "request_id": "q2",
                    "op": "ship",
                    "reservation_id": "r1",
                },
                {
                    "request_id": "q3",
                    "op": "cancel",
                    "reservation_id": "r1",
                },
                {
                    "request_id": "q4",
                    "op": "cancel",
                    "reservation_id": "missing",
                },
                {
                    "request_id": "q5",
                    "op": "reserve",
                    "reservation_id": "r2",
                    "sku": "A",
                    "qty": 2,
                },
                {
                    "request_id": "q6",
                    "op": "cancel",
                    "reservation_id": "r2",
                },
            ],
        )

        self.assertEqual(
            result,
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                },
                {
                    "request_id": "q2",
                    "status": "SHIPPED",
                },
                {
                    "request_id": "q3",
                    "status": "CONFLICT",
                },
                {
                    "request_id": "q4",
                    "status": "NOT_FOUND",
                },
                {
                    "request_id": "q5",
                    "status": "RESERVED",
                },
                {
                    "request_id": "q6",
                    "status": "CANCELLED",
                },
            ],
        )

        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {
                    "A": 7,
                    "B": 3,
                },
                "reservations": {
                    "r1": {
                        "sku": "A",
                        "qty": 3,
                        "state": "SHIPPED",
                    },
                    "r2": {
                        "sku": "A",
                        "qty": 2,
                        "state": "CANCELLED",
                    },
                },
            },
        )

        # Existing reservation_id wins over stock sufficiency.
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "q7",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "B",
                        "qty": 999,
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

    def test_failed_results_are_replayed_and_dict_order_is_ignored(
        self,
    ):
        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "hold",
                    "op": "reserve",
                    "reservation_id": "r-hold",
                    "sku": "A",
                    "qty": 6,
                }
            ],
        )

        failures = inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "oos",
                    "op": "reserve",
                    "reservation_id": "r-oos",
                    "sku": "A",
                    "qty": 5,
                },
                {
                    "request_id": "conflict",
                    "op": "reserve",
                    "reservation_id": "r-hold",
                    "sku": "B",
                    "qty": 1,
                },
                {
                    "request_id": "missing",
                    "op": "cancel",
                    "reservation_id": "r-future",
                },
            ],
        )

        self.assertEqual(
            failures,
            [
                {
                    "request_id": "oos",
                    "status": "OUT_OF_STOCK",
                },
                {
                    "request_id": "conflict",
                    "status": "CONFLICT",
                },
                {
                    "request_id": "missing",
                    "status": "NOT_FOUND",
                },
            ],
        )

        # Make the live state different from the state at which
        # those failed results were first produced.
        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "release",
                    "op": "cancel",
                    "reservation_id": "r-hold",
                },
                {
                    "request_id": "create",
                    "op": "reserve",
                    "reservation_id": "r-future",
                    "sku": "A",
                    "qty": 1,
                },
            ],
        )

        replays = inventory.apply_batch(
            self.db,
            [
                # Same content as "oos", different dict key order.
                {
                    "qty": 5,
                    "sku": "A",
                    "reservation_id": "r-oos",
                    "op": "reserve",
                    "request_id": "oos",
                },
                {
                    "reservation_id": "r-hold",
                    "request_id": "conflict",
                    "qty": 1,
                    "sku": "B",
                    "op": "reserve",
                },
                {
                    "reservation_id": "r-future",
                    "op": "cancel",
                    "request_id": "missing",
                },
            ],
        )

        self.assertEqual(
            replays,
            failures,
        )

        snap = inventory.snapshot(self.db)

        self.assertNotIn(
            "r-oos",
            snap["reservations"],
        )

        self.assertEqual(
            snap["reservations"]["r-future"]["state"],
            "RESERVED",
        )

        self.assertEqual(
            snap["available"]["A"],
            9,
        )

    def test_duplicate_request_within_batch_is_applied_once(
        self,
    ):
        one = {
            "request_id": "q1",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 4,
        }

        same_reordered = {
            "qty": 4,
            "sku": "A",
            "reservation_id": "r1",
            "op": "reserve",
            "request_id": "q1",
        }

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    one,
                    same_reordered,
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

        snap = inventory.snapshot(self.db)

        self.assertEqual(
            snap["available"]["A"],
            6,
        )

        self.assertEqual(
            set(snap["reservations"]),
            {"r1"},
        )

    def test_request_id_content_conflict_rolls_back_entire_batch(
        self,
    ):
        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "old",
                    "op": "reserve",
                    "reservation_id": "old-r",
                    "sku": "A",
                    "qty": 2,
                }
            ],
        )

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "new",
                        "op": "reserve",
                        "reservation_id": "new-r",
                        "sku": "A",
                        "qty": 3,
                    },
                    {
                        "request_id": "old",
                        "op": "cancel",
                        "reservation_id": "old-r",
                    },
                ],
            )

        snap = inventory.snapshot(self.db)

        self.assertEqual(
            snap["available"]["A"],
            8,
        )

        self.assertNotIn(
            "new-r",
            snap["reservations"],
        )

        self.assertEqual(
            snap["reservations"]["old-r"]["state"],
            "RESERVED",
        )

        # The request-log row for "new" must have been rolled back too.
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "new",
                        "op": "reserve",
                        "reservation_id": "new-r",
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

    def test_different_content_duplicate_inside_batch_rolls_back(
        self,
    ):
        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "q1",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 2,
                    },
                    {
                        "request_id": "q1",
                        "op": "reserve",
                        "reservation_id": "r2",
                        "sku": "A",
                        "qty": 2,
                    },
                ],
            )

        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {
                    "A": 10,
                    "B": 3,
                },
                "reservations": {},
            },
        )

    def test_before_commit_exception_rolls_back_everything(
        self,
    ):
        calls = []

        def fail():
            calls.append("called")
            raise RuntimeError("injected failure")

        command = {
            "request_id": "q1",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 5,
        }

        with self.assertRaisesRegex(
            RuntimeError,
            "injected failure",
        ):
            inventory.apply_batch(
                self.db,
                [command],
                before_commit=fail,
            )

        self.assertEqual(
            calls,
            ["called"],
        )

        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {
                    "A": 10,
                    "B": 3,
                },
                "reservations": {},
            },
        )

        # request_id was rolled back, so retry must execute normally.
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [command],
            ),
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                }
            ],
        )

    def test_validation_and_unknown_sku_are_value_errors(
        self,
    ):
        bad_commands = [
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
                    "qty": 1,
                    "extra": 1,
                }
            ],
            [
                {
                    "request_id": "q",
                    "op": "bogus",
                    "reservation_id": "r",
                }
            ],
            [
                {
                    "request_id": "q",
                    "op": "reserve",
                    "reservation_id": "r",
                    "sku": "NOPE",
                    "qty": 1,
                }
            ],
        ]

        for commands in bad_commands:
            with self.subTest(commands=commands):
                with self.assertRaises(ValueError):
                    inventory.apply_batch(
                        self.db,
                        commands,
                    )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "saved",
                    "op": "cancel",
                    "reservation_id": "r",
                }
            ],
        )

        # Invalid syntax must not be hidden by an existing request_id.
        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "saved",
                        "op": "cancel",
                        "reservation_id": "r",
                        "extra": 1,
                    }
                ],
            )

    def test_reopen_from_fresh_process(self):
        inventory.apply_batch(
            self.db,
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

        ctx = mp.get_context("spawn")
        queue = ctx.Queue()

        process = ctx.Process(
            target=_snapshot_worker,
            args=(
                self.db,
                queue,
            ),
        )

        process.start()
        process.join(10)

        self.assertFalse(
            process.is_alive(),
        )

        self.assertEqual(
            process.exitcode,
            0,
        )

        kind, payload = queue.get(timeout=2)

        self.assertEqual(
            kind,
            "ok",
            payload,
        )

        self.assertEqual(
            payload["available"]["A"],
            8,
        )

        self.assertEqual(
            payload["reservations"]["r1"]["state"],
            "RESERVED",
        )

    def _race(
        self,
        command1,
        command2,
    ):
        ctx = mp.get_context("spawn")
        barrier = ctx.Barrier(3)
        queue = ctx.Queue()

        processes = [
            ctx.Process(
                target=_apply_worker,
                args=(
                    self.db,
                    barrier,
                    queue,
                    command1,
                ),
            ),
            ctx.Process(
                target=_apply_worker,
                args=(
                    self.db,
                    barrier,
                    queue,
                    command2,
                ),
            ),
        ]

        for process in processes:
            process.start()

        # Simultaneous release is controlled by the Barrier,
        # not by sleep timing.
        barrier.wait(timeout=10)

        for process in processes:
            process.join(10)

            self.assertFalse(
                process.is_alive(),
            )

            self.assertEqual(
                process.exitcode,
                0,
            )

        replies = [
            queue.get(timeout=2),
            queue.get(timeout=2),
        ]

        for reply in replies:
            self.assertEqual(
                reply[0],
                "ok",
                reply,
            )

        return [
            reply[1]
            for reply in replies
        ]

    def test_process_race_cannot_oversell(self):
        replies = self._race(
            [
                {
                    "request_id": "q1",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 6,
                }
            ],
            [
                {
                    "request_id": "q2",
                    "op": "reserve",
                    "reservation_id": "r2",
                    "sku": "A",
                    "qty": 6,
                }
            ],
        )

        statuses = sorted(
            reply[0]["status"]
            for reply in replies
        )

        self.assertEqual(
            statuses,
            [
                "OUT_OF_STOCK",
                "RESERVED",
            ],
        )

        snap = inventory.snapshot(self.db)

        self.assertEqual(
            snap["available"]["A"],
            4,
        )

        self.assertEqual(
            len(snap["reservations"]),
            1,
        )

    def test_process_race_same_request_id_applies_once(
        self,
    ):
        command = [
            {
                "request_id": "same",
                "op": "reserve",
                "reservation_id": "r1",
                "sku": "A",
                "qty": 4,
            }
        ]

        replies = self._race(
            command,
            command,
        )

        self.assertEqual(
            [
                reply[0]["status"]
                for reply in replies
            ],
            [
                "RESERVED",
                "RESERVED",
            ],
        )

        snap = inventory.snapshot(self.db)

        self.assertEqual(
            snap["available"]["A"],
            6,
        )

        self.assertEqual(
            set(snap["reservations"]),
            {"r1"},
        )

    def test_process_race_cancel_vs_ship_has_only_one_success(
        self,
    ):
        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "reserve",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 4,
                }
            ],
        )

        replies = self._race(
            [
                {
                    "request_id": "cancel",
                    "op": "cancel",
                    "reservation_id": "r1",
                }
            ],
            [
                {
                    "request_id": "ship",
                    "op": "ship",
                    "reservation_id": "r1",
                }
            ],
        )

        statuses = [
            reply[0]["status"]
            for reply in replies
        ]

        self.assertEqual(
            statuses.count("CONFLICT"),
            1,
        )

        self.assertEqual(
            statuses.count("CANCELLED")
            + statuses.count("SHIPPED"),
            1,
        )

        snap = inventory.snapshot(self.db)
        state = snap["reservations"]["r1"]["state"]

        self.assertIn(
            state,
            {
                "CANCELLED",
                "SHIPPED",
            },
        )

        self.assertEqual(
            snap["available"]["A"],
            10 if state == "CANCELLED" else 6,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

実行は2ファイルを同じディレクトリに置いて次のコマンドです。

```bash
python3 -m unittest -v
```

主要な保証は次の通りです。

- **原子性・プロセス間競合**: `apply_batch()` 冒頭で `BEGIN IMMEDIATE` を取得します。SQLiteのDBロックにより独立プロセスのwriter batchが直列化されるため、在庫判定から予約状態更新、`request_id` 保存までが1つの直列化点を持ちます。5秒の `busy_timeout` 後は `sqlite3.OperationalError` になり得ますが、未コミット変更は残りません。
- **再送**: `requests` テーブルに正規化したcommandと最初のstatusを、在庫・予約更新と**同じトランザクション**で保存します。JSONを `sort_keys=True` で正規化するためdictのキー順は無関係です。`OUT_OF_STOCK`、`NOT_FOUND`、`CONFLICT` も保存されます。同一batch内の後続commandからも未コミットのrequest記録が見えるので、同一内容は再適用せず、異内容なら `ValueError` になりbatch全体がrollbackされます。
- **状態遷移**: `RESERVED` からだけ `CANCELLED` / `SHIPPED` へ遷移します。cancelは在庫を戻し、shipは戻しません。一度終端状態になれば以後は `CONFLICT` です。
- **検証順序**: 構文・型・キー検証をトランザクション開始前、未登録SKU検査をトランザクション開始後かつrequest再送判定前に実施しています。
- **`before_commit`**: 全command処理後、まだトランザクションが開いている状態で1回だけ呼びます。例外は在庫・予約・request履歴をまとめてrollbackします。
- **snapshot**: 明示的なread transaction内で両SELECTを行うので、在庫と予約は同じSQLite snapshotに対応します。

実際に **Python 3.13.5** で実行し、`spawn` による独立プロセス競合3ケースを含む **11テストすべて成功**しました。

```text
Ran 11 tests in 3.395s

OK
```