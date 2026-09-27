## 結論

Python 3.12以降の標準ライブラリのみで実装しています。`BEGIN IMMEDIATE` によりプロセス間でbatch全体を直列化し、在庫・予約状態・`request_id` の結果記録を同一SQLiteトランザクションでコミットします。

### `inventory.py`

```python
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
```

### `test_inventory.py`

```python
from __future__ import annotations

import multiprocessing as mp
import tempfile
import unittest
from pathlib import Path
from typing import Any

import inventory


def _apply_worker(
    index: int,
    path: str,
    command: dict[str, Any],
    ready_queue: Any,
    start_event: Any,
    result_queue: Any,
) -> None:
    ready_queue.put(index)
    if not start_event.wait(timeout=15):
        result_queue.put((index, "error", "start event timeout"))
        return
    try:
        result = inventory.apply_batch(path, [command])
    except BaseException as exc:
        result_queue.put((index, "exception", type(exc).__name__, str(exc)))
    else:
        result_queue.put((index, "ok", result))


def _snapshot_worker(path: str, result_queue: Any) -> None:
    try:
        result_queue.put(("ok", inventory.snapshot(path)))
    except BaseException as exc:
        result_queue.put(("exception", type(exc).__name__, str(exc)))


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "inventory.sqlite3"

    def init(self, stocks: dict[str, int] | None = None) -> None:
        inventory.init_db(self.db, stocks or {"A": 10, "B": 5})

    def run_concurrent(
        self, commands: list[dict[str, Any]]
    ) -> list[list[dict[str, str]]]:
        ctx = mp.get_context("spawn")
        ready_queue = ctx.Queue()
        result_queue = ctx.Queue()
        start_event = ctx.Event()

        processes = [
            ctx.Process(
                target=_apply_worker,
                args=(
                    i,
                    str(self.db),
                    command,
                    ready_queue,
                    start_event,
                    result_queue,
                ),
            )
            for i, command in enumerate(commands)
        ]

        for process in processes:
            process.start()

        # 全プロセスが起動して共通Event待ちになった後で一斉に解放する。
        # sleepのタイミングには依存しない。
        ready = {ready_queue.get(timeout=15) for _ in processes}
        self.assertEqual(ready, set(range(len(processes))))
        start_event.set()

        raw_results = [result_queue.get(timeout=20) for _ in processes]

        for process in processes:
            process.join(timeout=20)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                self.fail("worker process did not terminate")
            self.assertEqual(process.exitcode, 0)

        by_index: dict[int, list[dict[str, str]]] = {}
        for item in raw_results:
            index = item[0]
            if item[1] != "ok":
                self.fail(f"child {index} failed: {item[2:]}")
            by_index[index] = item[2]

        return [by_index[i] for i in range(len(processes))]

    def test_normal_ordered_state_transitions(self) -> None:
        self.init()

        commands = [
            {
                "request_id": "q1",
                "op": "reserve",
                "reservation_id": "r1",
                "sku": "A",
                "qty": 3,
            },
            {
                "request_id": "q2",
                "op": "reserve",
                "reservation_id": "r2",
                "sku": "A",
                "qty": 4,
            },
            {
                "request_id": "q3",
                "op": "ship",
                "reservation_id": "r1",
            },
            {
                "request_id": "q4",
                "op": "cancel",
                "reservation_id": "r2",
            },
            {
                "request_id": "q5",
                "op": "cancel",
                "reservation_id": "r1",
            },
            {
                "request_id": "q6",
                "op": "ship",
                "reservation_id": "r2",
            },
        ]

        self.assertEqual(
            inventory.apply_batch(self.db, commands),
            [
                {"request_id": "q1", "status": "RESERVED"},
                {"request_id": "q2", "status": "RESERVED"},
                {"request_id": "q3", "status": "SHIPPED"},
                {"request_id": "q4", "status": "CANCELLED"},
                {"request_id": "q5", "status": "CONFLICT"},
                {"request_id": "q6", "status": "CONFLICT"},
            ],
        )

        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {"A": 7, "B": 5},
                "reservations": {
                    "r1": {
                        "sku": "A",
                        "qty": 3,
                        "state": "SHIPPED",
                    },
                    "r2": {
                        "sku": "A",
                        "qty": 4,
                        "state": "CANCELLED",
                    },
                },
            },
        )

    def test_reservation_id_conflict_precedes_stock_check(self) -> None:
        self.init({"A": 1})

        inventory.apply_batch(
            self.db,
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

        # available=0でも、既存reservation_idの衝突が優先される。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "q2",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 1,
                    }
                ],
            ),
            [{"request_id": "q2", "status": "CONFLICT"}],
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "q3",
                    "op": "ship",
                    "reservation_id": "r1",
                }
            ],
        )

        # SHIPPED後もreservation_idは再利用不可。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "q4",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 1,
                    }
                ],
            ),
            [{"request_id": "q4", "status": "CONFLICT"}],
        )

    def test_failed_results_are_replayed_verbatim(self) -> None:
        self.init({"A": 1})

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "q1",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 1,
                    }
                ],
            )[0]["status"],
            "RESERVED",
        )

        out_of_stock = {
            "request_id": "q2",
            "op": "reserve",
            "reservation_id": "r2",
            "sku": "A",
            "qty": 1,
        }

        self.assertEqual(
            inventory.apply_batch(self.db, [out_of_stock]),
            [{"request_id": "q2", "status": "OUT_OF_STOCK"}],
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "q3",
                    "op": "cancel",
                    "reservation_id": "r1",
                }
            ],
        )

        # 在庫が復活してもq2の再送結果は最初のOUT_OF_STOCKのまま。
        self.assertEqual(
            inventory.apply_batch(self.db, [out_of_stock]),
            [{"request_id": "q2", "status": "OUT_OF_STOCK"}],
        )
        self.assertNotIn("r2", inventory.snapshot(self.db)["reservations"])
        self.assertEqual(inventory.snapshot(self.db)["available"]["A"], 1)

        not_found = {
            "request_id": "q4",
            "op": "cancel",
            "reservation_id": "r3",
        }

        self.assertEqual(
            inventory.apply_batch(self.db, [not_found]),
            [{"request_id": "q4", "status": "NOT_FOUND"}],
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "q5",
                    "op": "reserve",
                    "reservation_id": "r3",
                    "sku": "A",
                    "qty": 1,
                }
            ],
        )

        # r3が後から存在しても、q4の再送でキャンセルしてはいけない。
        self.assertEqual(
            inventory.apply_batch(self.db, [not_found]),
            [{"request_id": "q4", "status": "NOT_FOUND"}],
        )
        self.assertEqual(
            inventory.snapshot(self.db)["reservations"]["r3"]["state"],
            "RESERVED",
        )

    def test_replay_ignores_dict_key_order_and_batch_duplicate(self) -> None:
        self.init({"A": 10})

        first = {
            "request_id": "q1",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 3,
        }

        reordered = dict(
            [
                ("qty", 3),
                ("sku", "A"),
                ("reservation_id", "r1"),
                ("op", "reserve"),
                ("request_id", "q1"),
            ]
        )

        self.assertEqual(
            inventory.apply_batch(self.db, [first, reordered]),
            [
                {"request_id": "q1", "status": "RESERVED"},
                {"request_id": "q1", "status": "RESERVED"},
            ],
        )
        self.assertEqual(
            inventory.snapshot(self.db)["available"]["A"],
            7,
        )

        self.assertEqual(
            inventory.apply_batch(self.db, [reordered]),
            [{"request_id": "q1", "status": "RESERVED"}],
        )
        self.assertEqual(
            inventory.snapshot(self.db)["available"]["A"],
            7,
        )

    def test_same_batch_request_id_content_conflict_rolls_back(self) -> None:
        self.init({"A": 10})

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "same",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 2,
                    },
                    {
                        "request_id": "same",
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
                "available": {"A": 10},
                "reservations": {},
            },
        )

    def test_existing_request_content_conflict_rolls_back_only_current_batch(
        self,
    ) -> None:
        self.init({"A": 10})

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "old",
                    "op": "reserve",
                    "reservation_id": "r-old",
                    "sku": "A",
                    "qty": 1,
                }
            ],
        )

        new_command = {
            "request_id": "new",
            "op": "reserve",
            "reservation_id": "r-new",
            "sku": "A",
            "qty": 2,
        }

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    new_command,
                    {
                        "request_id": "old",
                        "op": "ship",
                        "reservation_id": "r-old",
                    },
                ],
            )

        # oldは以前のコミットなので残り、current batchのnewだけ消える。
        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {"A": 9},
                "reservations": {
                    "r-old": {
                        "sku": "A",
                        "qty": 1,
                        "state": "RESERVED",
                    }
                },
            },
        )

        # newのrequest_id記録もrollbackされている。
        self.assertEqual(
            inventory.apply_batch(self.db, [new_command]),
            [{"request_id": "new", "status": "RESERVED"}],
        )

    def test_before_commit_exception_rolls_back_everything(self) -> None:
        self.init({"A": 10})

        calls = 0

        def fail_before_commit() -> None:
            nonlocal calls
            calls += 1
            raise RuntimeError("injected failure")

        command = {
            "request_id": "q1",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 4,
        }

        with self.assertRaisesRegex(RuntimeError, "injected failure"):
            inventory.apply_batch(
                self.db,
                [command],
                before_commit=fail_before_commit,
            )

        self.assertEqual(calls, 1)
        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {"A": 10},
                "reservations": {},
            },
        )

        # request_id記録もrollbackされているため、同じq1を正常適用できる。
        self.assertEqual(
            inventory.apply_batch(self.db, [command]),
            [{"request_id": "q1", "status": "RESERVED"}],
        )

    def test_validation_errors_leave_no_changes(self) -> None:
        self.init({"A": 10})

        invalid_batches: list[Any] = [
            [],
            (
                {
                    "request_id": "q",
                    "op": "cancel",
                    "reservation_id": "r",
                },
            ),
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
                    "sku": "UNKNOWN",
                    "qty": 1,
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
                    inventory.apply_batch(self.db, batch)

                self.assertEqual(
                    inventory.snapshot(self.db),
                    {
                        "available": {"A": 10},
                        "reservations": {},
                    },
                )

    def test_invalid_replay_shape_is_not_hidden_by_saved_request(self) -> None:
        self.init({"A": 10})

        inventory.apply_batch(
            self.db,
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

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "q1",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 1,
                        "extra": "not allowed",
                    }
                ],
            )

        self.assertEqual(
            inventory.snapshot(self.db)["available"]["A"],
            9,
        )

    def test_reopen_from_independent_process(self) -> None:
        self.init({"A": 10})

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
        result_queue = ctx.Queue()

        process = ctx.Process(
            target=_snapshot_worker,
            args=(str(self.db), result_queue),
        )
        process.start()

        result = result_queue.get(timeout=15)
        process.join(timeout=15)

        self.assertFalse(process.is_alive())
        self.assertEqual(process.exitcode, 0)
        self.assertEqual(result[0], "ok", msg=result[1:])

        self.assertEqual(
            result[1],
            {
                "available": {"A": 8},
                "reservations": {
                    "r1": {
                        "sku": "A",
                        "qty": 2,
                        "state": "RESERVED",
                    }
                },
            },
        )

    def test_processes_compete_for_stock_without_overselling(self) -> None:
        self.init({"A": 10})

        commands = [
            {
                "request_id": "q1",
                "op": "reserve",
                "reservation_id": "r1",
                "sku": "A",
                "qty": 7,
            },
            {
                "request_id": "q2",
                "op": "reserve",
                "reservation_id": "r2",
                "sku": "A",
                "qty": 7,
            },
        ]

        results = self.run_concurrent(commands)
        statuses = [result[0]["status"] for result in results]

        self.assertCountEqual(
            statuses,
            ["RESERVED", "OUT_OF_STOCK"],
        )

        snap = inventory.snapshot(self.db)
        self.assertEqual(snap["available"]["A"], 3)
        self.assertEqual(len(snap["reservations"]), 1)

        only_reservation = next(iter(snap["reservations"].values()))
        self.assertEqual(only_reservation["qty"], 7)
        self.assertEqual(
            only_reservation["state"],
            "RESERVED",
        )

    def test_processes_same_request_id_apply_once(self) -> None:
        self.init({"A": 10})

        command = {
            "request_id": "shared",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 7,
        }

        reordered = dict(reversed(list(command.items())))

        results = self.run_concurrent(
            [command, reordered]
        )

        self.assertEqual(
            [result[0]["status"] for result in results],
            ["RESERVED", "RESERVED"],
        )

        self.assertEqual(
            inventory.snapshot(self.db),
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

    def test_process_cancel_and_ship_race_allows_only_one_transition(
        self,
    ) -> None:
        self.init({"A": 10})

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

        results = self.run_concurrent(commands)
        statuses = [result[0]["status"] for result in results]

        self.assertEqual(statuses.count("CONFLICT"), 1)

        successful = [
            status
            for status in statuses
            if status != "CONFLICT"
        ]
        self.assertEqual(len(successful), 1)
        self.assertIn(
            successful[0],
            {"CANCELLED", "SHIPPED"},
        )

        snap = inventory.snapshot(self.db)
        state = snap["reservations"]["r1"]["state"]

        self.assertEqual(state, successful[0])

        if state == "CANCELLED":
            self.assertEqual(
                snap["available"]["A"],
                10,
            )
        else:
            self.assertEqual(
                snap["available"]["A"],
                6,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

### 実行

同じディレクトリに2ファイルを置いて実行します。

```bash
python3 -m unittest -v test_inventory.py
```

こちらでは **Python 3.13.5** で実行し、**13テストすべて成功**しました。

```text
Ran 13 tests in 7.650s

OK
```

実ファイルもあります: :chatgpt-content-reference{index="0"}[inventory.py](sandbox:/mnt/data/inventory.py) / :chatgpt-content-reference{index="1"}[test_inventory.py](sandbox:/mnt/data/test_inventory.py)

### 保証の仕組み

- **原子性・プロセス間競合:** `apply_batch` 冒頭の `BEGIN IMMEDIATE` でSQLiteのDBロックを取得し、batch全体を1トランザクションで処理します。途中の `ValueError`、内部例外、`before_commit` 例外はすべて `ROLLBACK` します。ロック待ちは5秒で有限です。
- **再送:** `requests` に `request_id`、キー順を無視して正規化したコマンド、最初の結果を同時コミットします。`OUT_OF_STOCK` / `NOT_FOUND` / `CONFLICT` も保存するため、その後の状態に左右されません。同じIDで内容が異なれば `ValueError` となりbatch全体がrollbackされます。
- **状態遷移:** 予約行を削除せず `RESERVED → CANCELLED/SHIPPED` と更新するため、予約IDは永久に再利用されません。取消だけ在庫を戻し、出荷は在庫を変更しません。`snapshot` は明示的なread transaction内で複数SELECTを行うため、単一時点の整合した状態を返します。