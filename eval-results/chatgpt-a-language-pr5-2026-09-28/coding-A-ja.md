実装とテストを以下に示します。Python **3.13.5**（要件の3.12以降を満たす環境）で `python3 -m unittest -v` を実行し、**10テストすべて成功**しています。

### `inventory.py`

```python
from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from os import PathLike
from typing import Any

_MAX_QTY = 10**9
_MAX_TEXT = 128
_BUSY_TIMEOUT_MS = 5_000

_RESERVE_KEYS = {"request_id", "op", "reservation_id", "sku", "qty"}
_TERMINAL_KEYS = {"request_id", "op", "reservation_id"}


def _is_text(value: object) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= _MAX_TEXT


def _is_int_in_range(value: object, low: int, high: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def _connect(path: str | bytes | PathLike[str] | PathLike[bytes]) -> sqlite3.Connection:
    conn = sqlite3.connect(
        path,
        timeout=_BUSY_TIMEOUT_MS / 1000,
        isolation_level=None,
    )
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        return conn
    except BaseException:
        conn.close()
        raise


def _validate_stocks(stocks: object) -> list[tuple[str, int]]:
    if not isinstance(stocks, dict) or not stocks:
        raise ValueError("stocks must be a non-empty dict")

    rows: list[tuple[str, int]] = []
    for sku, qty in stocks.items():
        if not _is_text(sku):
            raise ValueError("each SKU must be a str of length 1..128")
        if not _is_int_in_range(qty, 0, _MAX_QTY):
            raise ValueError(
                "each initial stock must be an int in 0..10^9 "
                "(bool is not allowed)"
            )
        rows.append((sku, qty))
    return rows


def _validate_commands(commands: object) -> list[tuple[dict[str, Any], str, int]]:
    if not isinstance(commands, list) or not commands:
        raise ValueError("commands must be a non-empty list")

    validated: list[tuple[dict[str, Any], str, int]] = []

    for index, raw in enumerate(commands):
        if not isinstance(raw, dict):
            raise ValueError(f"commands[{index}] must be a dict")

        op = raw.get("op")
        if op not in ("reserve", "cancel", "ship"):
            raise ValueError(f"commands[{index}] has an invalid op")

        expected_keys = _RESERVE_KEYS if op == "reserve" else _TERMINAL_KEYS
        if set(raw) != expected_keys:
            raise ValueError(f"commands[{index}] has invalid keys")

        request_id = raw["request_id"]
        reservation_id = raw["reservation_id"]

        if not _is_text(request_id):
            raise ValueError(
                f"commands[{index}].request_id must be a str of length 1..128"
            )
        if not _is_text(reservation_id):
            raise ValueError(
                f"commands[{index}].reservation_id must be a str of length 1..128"
            )

        if op == "reserve":
            sku = raw["sku"]
            qty = raw["qty"]

            if not _is_text(sku):
                raise ValueError(
                    f"commands[{index}].sku must be a str of length 1..128"
                )
            if not _is_int_in_range(qty, 1, _MAX_QTY):
                raise ValueError(
                    f"commands[{index}].qty must be an int in 1..10^9 "
                    "(bool is not allowed)"
                )

            command = {
                "request_id": request_id,
                "op": op,
                "reservation_id": reservation_id,
                "sku": sku,
                "qty": qty,
            }
        else:
            command = {
                "request_id": request_id,
                "op": op,
                "reservation_id": reservation_id,
            }

        canonical = json.dumps(
            command,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        validated.append((command, canonical, index))

    return validated


def init_db(path, stocks) -> None:
    rows = _validate_stocks(stocks)

    conn = _connect(path)
    in_transaction = False

    try:
        # init_db は新規DBに対して一度だけ、非並行で呼ばれる前提。
        # WAL は永続設定であり、snapshot の読み取りと writer の共存にも適する。
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = FULL")

        conn.execute("BEGIN IMMEDIATE")
        in_transaction = True

        conn.execute(
            """
            CREATE TABLE stocks (
                sku TEXT COLLATE BINARY NOT NULL PRIMARY KEY,
                available INTEGER NOT NULL
                    CHECK (
                        typeof(available) = 'integer'
                        AND available BETWEEN 0 AND 1000000000
                    )
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE reservations (
                reservation_id TEXT COLLATE BINARY NOT NULL PRIMARY KEY,
                sku TEXT COLLATE BINARY NOT NULL,
                qty INTEGER NOT NULL
                    CHECK (
                        typeof(qty) = 'integer'
                        AND qty BETWEEN 1 AND 1000000000
                    ),
                state TEXT NOT NULL
                    CHECK (state IN ('RESERVED', 'CANCELLED', 'SHIPPED')),
                FOREIGN KEY (sku) REFERENCES stocks(sku)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE requests (
                request_id TEXT COLLATE BINARY NOT NULL PRIMARY KEY,
                canonical_command TEXT NOT NULL,
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
            "INSERT INTO stocks(sku, available) VALUES (?, ?)",
            rows,
        )

        conn.execute("COMMIT")
        in_transaction = False

    except BaseException:
        if in_transaction:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()


def _apply_new_command(
    conn: sqlite3.Connection,
    command: dict[str, Any],
) -> str:
    op = command["op"]
    reservation_id = command["reservation_id"]

    if op == "reserve":
        # 在庫判定より予約ID衝突を優先する。
        exists = conn.execute(
            """
            SELECT 1
              FROM reservations
             WHERE reservation_id = ?
            """,
            (reservation_id,),
        ).fetchone()

        if exists is not None:
            return "CONFLICT"

        sku = command["sku"]
        qty = command["qty"]

        # 在庫確認と減算を1 UPDATEで行う。
        cursor = conn.execute(
            """
            UPDATE stocks
               SET available = available - ?
             WHERE sku = ?
               AND available >= ?
            """,
            (qty, sku, qty),
        )

        if cursor.rowcount != 1:
            return "OUT_OF_STOCK"

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
            (reservation_id, sku, qty),
        )

        return "RESERVED"

    row = conn.execute(
        """
        SELECT sku, qty, state
          FROM reservations
         WHERE reservation_id = ?
        """,
        (reservation_id,),
    ).fetchone()

    if row is None:
        return "NOT_FOUND"

    sku, qty, state = row

    if state != "RESERVED":
        return "CONFLICT"

    if op == "cancel":
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
            raise sqlite3.DatabaseError(
                "reservation state changed unexpectedly"
            )

        cursor = conn.execute(
            """
            UPDATE stocks
               SET available = available + ?
             WHERE sku = ?
            """,
            (qty, sku),
        )

        if cursor.rowcount != 1:
            raise sqlite3.DatabaseError(
                "reservation refers to a missing SKU"
            )

        return "CANCELLED"

    if op == "ship":
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
            raise sqlite3.DatabaseError(
                "reservation state changed unexpectedly"
            )

        return "SHIPPED"

    raise sqlite3.DatabaseError(
        "invalid operation reached execution"
    )


def apply_batch(
    path,
    commands,
    *,
    before_commit: Callable[[], object] | None = None,
) -> list[dict]:
    # 型・キー・op・範囲はDB操作や再送判定より先に検査する。
    validated = _validate_commands(commands)

    conn = _connect(path)
    in_transaction = False

    try:
        # SQLiteのプロセス間write lockを最初に取得する。
        # 成功するwriter batchはこれにより直列化される。
        conn.execute("BEGIN IMMEDIATE")
        in_transaction = True

        # 未登録SKU検査も request_id の再送判定より先に行う。
        checked_skus: set[str] = set()

        for command, _canonical, index in validated:
            if command["op"] != "reserve":
                continue

            sku = command["sku"]

            if sku in checked_skus:
                continue

            checked_skus.add(sku)

            row = conn.execute(
                """
                SELECT 1
                  FROM stocks
                 WHERE sku = ?
                """,
                (sku,),
            ).fetchone()

            if row is None:
                raise ValueError(
                    f"commands[{index}] refers to an unknown SKU"
                )

        results: list[dict] = []

        # 入力順に処理するので、後続commandは先行commandの更新を見る。
        for command, canonical, _index in validated:
            request_id = command["request_id"]

            previous = conn.execute(
                """
                SELECT canonical_command, status
                  FROM requests
                 WHERE request_id = ?
                """,
                (request_id,),
            ).fetchone()

            if previous is not None:
                previous_command, previous_status = previous

                if previous_command != canonical:
                    raise ValueError(
                        f"request_id {request_id!r} "
                        "was already used for different content"
                    )

                # 成功・失敗を問わず最初にcommitされた結果をそのまま返す。
                status = previous_status

            else:
                status = _apply_new_command(conn, command)

                # 業務失敗も含め、結果と正規化済みcommandを同じtransactionに保存。
                conn.execute(
                    """
                    INSERT INTO requests(
                        request_id,
                        canonical_command,
                        status
                    )
                    VALUES (?, ?, ?)
                    """,
                    (request_id, canonical, status),
                )

            results.append(
                {
                    "request_id": request_id,
                    "status": status,
                }
            )

        # 全command処理後、COMMIT直前にちょうど1回。
        if before_commit is not None:
            before_commit()

        conn.execute("COMMIT")
        in_transaction = False

        # commit完了後にのみ成功結果を呼出し側へ返す。
        return results

    except BaseException:
        if in_transaction:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()


def snapshot(path) -> dict:
    conn = _connect(path)
    in_transaction = False

    try:
        # 複数SELECTを同じread transactionに置く。
        # 最初のSELECTで確立したSQLite snapshotを最後まで保持する。
        conn.execute("BEGIN")
        in_transaction = True

        stock_rows = conn.execute(
            """
            SELECT sku, available
              FROM stocks
             ORDER BY sku COLLATE BINARY
            """
        ).fetchall()

        reservation_rows = conn.execute(
            """
            SELECT reservation_id, sku, qty, state
              FROM reservations
             ORDER BY reservation_id COLLATE BINARY
            """
        ).fetchall()

        result = {
            "available": {
                sku: available
                for sku, available in stock_rows
            },
            "reservations": {
                reservation_id: {
                    "sku": sku,
                    "qty": qty,
                    "state": state,
                }
                for reservation_id, sku, qty, state
                in reservation_rows
            },
        }

        conn.execute("COMMIT")
        in_transaction = False

        return result

    except BaseException:
        if in_transaction:
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

import multiprocessing as mp
import tempfile
import unittest
from pathlib import Path

import inventory


def _apply_worker(
    path: str,
    commands: list[dict],
    barrier,
    queue,
) -> None:
    try:
        # sleepではなくBarrierで独立プロセスの開始を揃える。
        barrier.wait(timeout=15)

        result = inventory.apply_batch(
            path,
            commands,
        )

        queue.put(("ok", result))

    except BaseException as exc:
        queue.put(
            (
                "error",
                type(exc).__name__,
                str(exc),
            )
        )


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db = str(
            Path(self._tmp.name) / "inventory.sqlite3"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_basic_reserve_cancel_ship_and_business_failures(self) -> None:
        inventory.init_db(
            self.db,
            {
                "A": 5,
                "B": 0,
            },
        )

        results = inventory.apply_batch(
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
                    "op": "cancel",
                    "reservation_id": "r1",
                },
                {
                    "request_id": "q3",
                    "op": "reserve",
                    "reservation_id": "r2",
                    "sku": "A",
                    "qty": 4,
                },
                {
                    "request_id": "q4",
                    "op": "ship",
                    "reservation_id": "r2",
                },
                {
                    "request_id": "q5",
                    "op": "cancel",
                    "reservation_id": "r2",
                },
                {
                    "request_id": "q6",
                    "op": "ship",
                    "reservation_id": "missing",
                },
                {
                    "request_id": "q7",
                    "op": "reserve",
                    "reservation_id": "r3",
                    "sku": "B",
                    "qty": 1,
                },
                # 在庫不足より既存reservation_id衝突を優先する。
                {
                    "request_id": "q8",
                    "op": "reserve",
                    "reservation_id": "r2",
                    "sku": "B",
                    "qty": 1,
                },
            ],
        )

        self.assertEqual(
            [r["status"] for r in results],
            [
                "RESERVED",
                "CANCELLED",
                "RESERVED",
                "SHIPPED",
                "CONFLICT",
                "NOT_FOUND",
                "OUT_OF_STOCK",
                "CONFLICT",
            ],
        )

        self.assertTrue(
            all(
                set(r) == {"request_id", "status"}
                for r in results
            )
        )

        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {
                    "A": 1,
                    "B": 0,
                },
                "reservations": {
                    "r1": {
                        "sku": "A",
                        "qty": 3,
                        "state": "CANCELLED",
                    },
                    "r2": {
                        "sku": "A",
                        "qty": 4,
                        "state": "SHIPPED",
                    },
                },
            },
        )

    def test_failed_result_replay_is_sticky_even_after_state_changes(
        self,
    ) -> None:
        inventory.init_db(
            self.db,
            {"A": 1},
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "hold",
                        "op": "reserve",
                        "reservation_id": "held",
                        "sku": "A",
                        "qty": 1,
                    }
                ],
            )[0]["status"],
            "RESERVED",
        )

        out = {
            "request_id": "oos",
            "op": "reserve",
            "reservation_id": "later",
            "sku": "A",
            "qty": 1,
        }

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [out],
            )[0]["status"],
            "OUT_OF_STOCK",
        )

        # OUT_OF_STOCK後に在庫を戻し、現在なら成功可能な状態にする。
        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "release",
                    "op": "cancel",
                    "reservation_id": "held",
                }
            ],
        )

        # それでも同一request_id・同一内容の再送は最初の結果を返す。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [out],
            )[0]["status"],
            "OUT_OF_STOCK",
        )

        snap = inventory.snapshot(self.db)

        self.assertNotIn(
            "later",
            snap["reservations"],
        )

        self.assertEqual(
            snap["available"]["A"],
            1,
        )

        # NOT_FOUNDも同様に保存される。
        missing_cancel = {
            "request_id": "missing-cancel",
            "op": "cancel",
            "reservation_id": "x",
        }

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [missing_cancel],
            )[0]["status"],
            "NOT_FOUND",
        )

        # 後からxという予約を作る。
        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "make-x",
                    "op": "reserve",
                    "reservation_id": "x",
                    "sku": "A",
                    "qty": 1,
                }
            ],
        )

        # 再送された古いcancelは現在の予約を取り消さない。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [missing_cancel],
            )[0]["status"],
            "NOT_FOUND",
        )

        self.assertEqual(
            inventory.snapshot(
                self.db
            )["reservations"]["x"]["state"],
            "RESERVED",
        )

    def test_dict_key_order_and_identical_duplicate_within_batch(
        self,
    ) -> None:
        inventory.init_db(
            self.db,
            {"A": 5},
        )

        first = {
            "request_id": "q",
            "op": "reserve",
            "reservation_id": "r",
            "sku": "A",
            "qty": 2,
        }

        reordered = {
            "qty": 2,
            "sku": "A",
            "reservation_id": "r",
            "op": "reserve",
            "request_id": "q",
        }

        results = inventory.apply_batch(
            self.db,
            [
                first,
                reordered,
            ],
        )

        self.assertEqual(
            results,
            [
                {
                    "request_id": "q",
                    "status": "RESERVED",
                },
                {
                    "request_id": "q",
                    "status": "RESERVED",
                },
            ],
        )

        # 同一batchで2回現れても減算は1回だけ。
        self.assertEqual(
            inventory.snapshot(
                self.db
            )["available"]["A"],
            3,
        )

        # 後続呼出しでもdictのキー順に依存しない。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [reordered],
            ),
            [
                {
                    "request_id": "q",
                    "status": "RESERVED",
                }
            ],
        )

        self.assertEqual(
            inventory.snapshot(
                self.db
            )["available"]["A"],
            3,
        )

    def test_request_id_content_conflict_rolls_back_entire_batch(
        self,
    ) -> None:
        inventory.init_db(
            self.db,
            {"A": 10},
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "committed",
                    "op": "reserve",
                    "reservation_id": "r0",
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
                        "request_id": "new",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 3,
                    },
                    # 既存request_idを異なる内容で再利用。
                    {
                        "request_id": "committed",
                        "op": "cancel",
                        "reservation_id": "r0",
                    },
                ],
            )

        snap = inventory.snapshot(self.db)

        # batch先頭のr1更新もrollback済み。
        self.assertEqual(
            snap["available"]["A"],
            9,
        )

        self.assertEqual(
            snap["reservations"],
            {
                "r0": {
                    "sku": "A",
                    "qty": 1,
                    "state": "RESERVED",
                }
            },
        )

        # 同一batch内のrequest_id内容衝突も全体rollback。
        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "dup",
                        "op": "reserve",
                        "reservation_id": "r2",
                        "sku": "A",
                        "qty": 2,
                    },
                    {
                        "request_id": "dup",
                        "op": "reserve",
                        "reservation_id": "r3",
                        "sku": "A",
                        "qty": 2,
                    },
                ],
            )

        self.assertEqual(
            inventory.snapshot(self.db),
            snap,
        )

    def test_before_commit_exception_rolls_back_and_request_can_be_retried(
        self,
    ) -> None:
        inventory.init_db(
            self.db,
            {"A": 5},
        )

        calls: list[str] = []

        def fail_before_commit() -> None:
            calls.append("called")
            raise RuntimeError("injected failure")

        command = {
            "request_id": "q1",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 2,
        }

        with self.assertRaisesRegex(
            RuntimeError,
            "injected failure",
        ):
            inventory.apply_batch(
                self.db,
                [command],
                before_commit=fail_before_commit,
            )

        self.assertEqual(
            calls,
            ["called"],
        )

        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {
                    "A": 5,
                },
                "reservations": {},
            },
        )

        # request記録もrollbackされているので、同じrequest_idを再試行可能。
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

        self.assertEqual(
            inventory.snapshot(
                self.db
            )["available"]["A"],
            3,
        )

    def test_reopen_persists_state(self) -> None:
        inventory.init_db(
            self.db,
            {"A": 4},
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "q1",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 3,
                }
            ],
        )

        # 公開APIは呼出しごとに新しいSQLite接続を開いて閉じる。
        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {
                    "A": 1,
                },
                "reservations": {
                    "r1": {
                        "sku": "A",
                        "qty": 3,
                        "state": "RESERVED",
                    }
                },
            },
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "q2",
                        "op": "ship",
                        "reservation_id": "r1",
                    }
                ],
            ),
            [
                {
                    "request_id": "q2",
                    "status": "SHIPPED",
                }
            ],
        )

        self.assertEqual(
            inventory.snapshot(
                self.db
            )["reservations"]["r1"]["state"],
            "SHIPPED",
        )

    def test_validation_and_unknown_sku_precedes_replay_lookup(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            inventory.init_db(
                self.db,
                {"A": True},
            )

        inventory.init_db(
            self.db,
            {"A": 5},
        )

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "x",
                        "op": "reserve",
                        "reservation_id": "r",
                        "sku": "A",
                        "qty": True,
                    }
                ],
            )

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "x",
                        "op": "cancel",
                        "reservation_id": "r",
                        "extra": 1,
                    }
                ],
            )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "same",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 1,
                }
            ],
        )

        # request_idは既存だが、UNKNOWN SKU検査が再送判定より先。
        with self.assertRaisesRegex(
            ValueError,
            "unknown SKU",
        ):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "same",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "UNKNOWN",
                        "qty": 1,
                    }
                ],
            )

    def _run_two_processes(
        self,
        commands1: list[dict],
        commands2: list[dict],
    ):
        ctx = mp.get_context("spawn")

        # 子2プロセス+親の3者Barrier。
        # 両子プロセスが準備できるまで開始させない。
        barrier = ctx.Barrier(3)
        queue = ctx.Queue()

        p1 = ctx.Process(
            target=_apply_worker,
            args=(
                self.db,
                commands1,
                barrier,
                queue,
            ),
        )

        p2 = ctx.Process(
            target=_apply_worker,
            args=(
                self.db,
                commands2,
                barrier,
                queue,
            ),
        )

        p1.start()
        p2.start()

        # 両workerがBarrierに到達後、同時に解放。
        barrier.wait(timeout=15)

        outputs = [
            queue.get(timeout=20),
            queue.get(timeout=20),
        ]

        p1.join(timeout=20)
        p2.join(timeout=20)

        self.assertFalse(p1.is_alive())
        self.assertFalse(p2.is_alive())

        self.assertEqual(
            p1.exitcode,
            0,
        )
        self.assertEqual(
            p2.exitcode,
            0,
        )

        self.assertTrue(
            all(
                item[0] == "ok"
                for item in outputs
            ),
            outputs,
        )

        return [
            item[1]
            for item in outputs
        ]

    def test_multiprocess_competing_reservations_do_not_oversell(
        self,
    ) -> None:
        inventory.init_db(
            self.db,
            {"A": 5},
        )

        outputs = self._run_two_processes(
            [
                {
                    "request_id": "q1",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 4,
                }
            ],
            [
                {
                    "request_id": "q2",
                    "op": "reserve",
                    "reservation_id": "r2",
                    "sku": "A",
                    "qty": 4,
                }
            ],
        )

        statuses = sorted(
            output[0]["status"]
            for output in outputs
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
            1,
        )

        self.assertEqual(
            len(snap["reservations"]),
            1,
        )

    def test_multiprocess_same_request_id_is_applied_once(
        self,
    ) -> None:
        inventory.init_db(
            self.db,
            {"A": 5},
        )

        command = {
            "request_id": "same",
            "op": "reserve",
            "reservation_id": "r",
            "sku": "A",
            "qty": 3,
        }

        # 2プロセス目はキー順だけ逆転。
        reordered = dict(
            reversed(
                list(command.items())
            )
        )

        outputs = self._run_two_processes(
            [command],
            [reordered],
        )

        self.assertEqual(
            [
                output[0]["status"]
                for output in outputs
            ],
            [
                "RESERVED",
                "RESERVED",
            ],
        )

        snap = inventory.snapshot(self.db)

        # 在庫減算は1回だけ。
        self.assertEqual(
            snap["available"]["A"],
            2,
        )

        self.assertEqual(
            snap["reservations"],
            {
                "r": {
                    "sku": "A",
                    "qty": 3,
                    "state": "RESERVED",
                }
            },
        )

    def test_multiprocess_cancel_ship_race_has_only_one_success(
        self,
    ) -> None:
        inventory.init_db(
            self.db,
            {"A": 5},
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "reserve",
                    "op": "reserve",
                    "reservation_id": "r",
                    "sku": "A",
                    "qty": 3,
                }
            ],
        )

        outputs = self._run_two_processes(
            [
                {
                    "request_id": "cancel",
                    "op": "cancel",
                    "reservation_id": "r",
                }
            ],
            [
                {
                    "request_id": "ship",
                    "op": "ship",
                    "reservation_id": "r",
                }
            ],
        )

        statuses = [
            output[0]["status"]
            for output in outputs
        ]

        # 一方だけ成功し、もう一方はterminal stateを見てCONFLICT。
        self.assertEqual(
            statuses.count("CONFLICT"),
            1,
        )

        terminal = next(
            status
            for status in statuses
            if status != "CONFLICT"
        )

        self.assertIn(
            terminal,
            {
                "CANCELLED",
                "SHIPPED",
            },
        )

        snap = inventory.snapshot(self.db)

        self.assertEqual(
            snap["reservations"]["r"]["state"],
            terminal,
        )

        self.assertEqual(
            snap["available"]["A"],
            5 if terminal == "CANCELLED" else 2,
        )


if __name__ == "__main__":
    unittest.main()
```

### 実行

2ファイルを同じディレクトリに置いて実行します。

```bash
python3 -m unittest -v
```

今回の実行結果は Python 3.13.5 で次のとおりです。

```text
Ran 10 tests in 5.538s

OK
```

原子性は `apply_batch()` 全体を明示的な `BEGIN IMMEDIATE` ～ `COMMIT` に入れ、例外時は在庫・予約・request記録をまとめて `ROLLBACK` することで保証しています。`BEGIN IMMEDIATE` はSQLite自身のプロセス間write lockを取得するため、Pythonプロセス内ロックには依存せず、成功したwriter batch同士が直列化されます。

再送は `requests` テーブルに **request_id・キー順非依存のcanonical JSON・最初のstatus** を同じトランザクションで保存します。したがって `OUT_OF_STOCK`、`NOT_FOUND`、`CONFLICT` も再計算されません。同じIDでcanonical内容が違えば `ValueError` になり、そのbatch全体がrollbackされます。

状態遷移は予約行を削除せず `RESERVED → CANCELLED` または `RESERVED → SHIPPED` のみに限定しています。取消時だけ在庫を戻し、出荷時は在庫を変更しません。`snapshot()` は明示的read transaction内で両SELECTを実行するため、在庫と予約を同一SQLite snapshotから取得します。