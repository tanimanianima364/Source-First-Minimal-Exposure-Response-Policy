以下の2ファイルで要件を満たします。標準ライブラリのみを使用しています。

### `inventory.py`

```python
from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from typing import Any

_MAX_LEN = 128
_MAX_QTY = 1_000_000_000
_BUSY_TIMEOUT_MS = 5_000

_RESERVE_KEYS = {"request_id", "op", "reservation_id", "sku", "qty"}
_TERMINAL_KEYS = {"request_id", "op", "reservation_id"}


def _connect(path) -> sqlite3.Connection:
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


def _key(value: str) -> bytes:
    # sqlite3 の TEXT バインドは孤立サロゲートを拒否する。
    # 公開APIで許容している任意の Python str を保持できるよう、
    # 識別子は surrogatepass UTF-8 の BLOB として保存する。
    return str.encode(value, "utf-8", "surrogatepass")


def _from_key(value: bytes) -> str:
    return bytes.decode(value, "utf-8", "surrogatepass")


def _valid_id(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= _MAX_LEN


def _valid_int(value: Any, *, minimum: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= _MAX_QTY
    )


def _validate_stocks(stocks: Any) -> list[tuple[str, int]]:
    if not isinstance(stocks, dict) or not stocks:
        raise ValueError("stocks must be a non-empty dict")

    rows: list[tuple[str, int]] = []
    for sku, qty in stocks.items():
        if not _valid_id(sku):
            raise ValueError("each SKU must be a str of length 1..128")
        if not _valid_int(qty, minimum=0):
            raise ValueError(
                "each stock count must be an int in 0..10^9 "
                "(bool is invalid)"
            )
        rows.append((sku, qty))
    return rows


def _validate_command(command: Any) -> dict[str, Any]:
    if not isinstance(command, dict):
        raise ValueError("each command must be a dict")

    op = command.get("op")
    if not isinstance(op, str) or op not in {"reserve", "cancel", "ship"}:
        raise ValueError("invalid op")

    expected = _RESERVE_KEYS if op == "reserve" else _TERMINAL_KEYS
    if set(command) != expected:
        raise ValueError("command has missing or unexpected keys")

    request_id = command["request_id"]
    reservation_id = command["reservation_id"]

    if not _valid_id(request_id):
        raise ValueError(
            "request_id must be a str of length 1..128"
        )
    if not _valid_id(reservation_id):
        raise ValueError(
            "reservation_id must be a str of length 1..128"
        )

    if op == "reserve":
        sku = command["sku"]
        qty = command["qty"]

        if not _valid_id(sku):
            raise ValueError("sku must be a str of length 1..128")
        if not _valid_int(qty, minimum=1):
            raise ValueError(
                "qty must be an int in 1..10^9 "
                "(bool is invalid)"
            )

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
    return json.dumps(
        command,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def init_db(path, stocks) -> None:
    rows = _validate_stocks(stocks)

    conn = _connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")

        conn.execute(
            """
            CREATE TABLE stock (
                sku BLOB PRIMARY KEY,
                total INTEGER NOT NULL
                    CHECK (
                        typeof(total) = 'integer'
                        AND total BETWEEN 0 AND 1000000000
                    ),
                available INTEGER NOT NULL
                    CHECK (
                        typeof(available) = 'integer'
                        AND available BETWEEN 0 AND total
                    )
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE reservations (
                reservation_id BLOB PRIMARY KEY,
                sku BLOB NOT NULL,
                qty INTEGER NOT NULL
                    CHECK (
                        typeof(qty) = 'integer'
                        AND qty BETWEEN 1 AND 1000000000
                    ),
                state TEXT NOT NULL
                    CHECK (
                        state IN (
                            'RESERVED',
                            'CANCELLED',
                            'SHIPPED'
                        )
                    ),
                FOREIGN KEY (sku) REFERENCES stock(sku)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE request_log (
                request_id BLOB PRIMARY KEY,
                command TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (
                        status IN (
                            'RESERVED',
                            'CANCELLED',
                            'SHIPPED',
                            'OUT_OF_STOCK',
                            'NOT_FOUND',
                            'CONFLICT'
                        )
                    )
            )
            """
        )

        conn.executemany(
            """
            INSERT INTO stock(sku, total, available)
            VALUES (?, ?, ?)
            """,
            (
                (_key(sku), qty, qty)
                for sku, qty in rows
            ),
        )

        conn.commit()

    except BaseException:
        if conn.in_transaction:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()


def apply_batch(
    path,
    commands,
    *,
    before_commit: Callable[[], Any] | None = None,
) -> list[dict]:
    if not isinstance(commands, list) or not commands:
        raise ValueError("commands must be a non-empty list")

    # 構文・型検査はDBの再送判定より前に全要素へ行う。
    # 値をコピーするため、以降は呼出し側dictのキー順等にも依存しない。
    normalized = [
        _validate_command(command)
        for command in commands
    ]

    conn = _connect(path)
    try:
        # SQLite自身の書込みロックをbatch全体に保持する。
        # 同一DBに対する独立プロセスのwrite batchもここで直列化される。
        conn.execute("BEGIN IMMEDIATE")

        results: list[dict] = []

        for command in normalized:
            request_id = command["request_id"]
            request_key = _key(request_id)

            op = command["op"]

            reservation_id = command["reservation_id"]
            reservation_key = _key(reservation_id)

            # 未登録SKU検査は request_id 再送判定より先。
            if op == "reserve":
                sku = command["sku"]
                sku_key = _key(sku)

                row = conn.execute(
                    "SELECT 1 FROM stock WHERE sku = ?",
                    (sku_key,),
                ).fetchone()

                if row is None:
                    raise ValueError(
                        f"unknown SKU: {sku!r}"
                    )

            canonical = _canonical_command(command)

            prior = conn.execute(
                """
                SELECT command, status
                FROM request_log
                WHERE request_id = ?
                """,
                (request_key,),
            ).fetchone()

            if prior is not None:
                prior_command, prior_status = prior

                if prior_command != canonical:
                    raise ValueError(
                        f"request_id {request_id!r} "
                        "was already used for different content"
                    )

                # 現在の在庫・予約状態は見ず、最初にコミットした結果を返す。
                results.append(
                    {
                        "request_id": request_id,
                        "status": prior_status,
                    }
                )
                continue

            if op == "reserve":
                sku = command["sku"]
                sku_key = _key(sku)
                qty = command["qty"]

                # 予約ID衝突を在庫不足判定より優先。
                existing = conn.execute(
                    """
                    SELECT 1
                    FROM reservations
                    WHERE reservation_id = ?
                    """,
                    (reservation_key,),
                ).fetchone()

                if existing is not None:
                    status = "CONFLICT"

                else:
                    # 条件付きUPDATEなので、DBレベルでも
                    # availableを負数にできない。
                    updated = conn.execute(
                        """
                        UPDATE stock
                           SET available = available - ?
                         WHERE sku = ?
                           AND available >= ?
                        """,
                        (qty, sku_key, qty),
                    )

                    if updated.rowcount == 0:
                        status = "OUT_OF_STOCK"

                    else:
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

            elif op == "cancel":
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

                    else:
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
                            UPDATE stock
                               SET available = available + ?
                             WHERE sku = ?
                            """,
                            (qty, sku_key),
                        )

                        status = "CANCELLED"

            else:  # ship
                row = conn.execute(
                    """
                    SELECT state
                    FROM reservations
                    WHERE reservation_id = ?
                    """,
                    (reservation_key,),
                ).fetchone()

                if row is None:
                    status = "NOT_FOUND"

                elif row[0] != "RESERVED":
                    status = "CONFLICT"

                else:
                    conn.execute(
                        """
                        UPDATE reservations
                           SET state = 'SHIPPED'
                         WHERE reservation_id = ?
                        """,
                        (reservation_key,),
                    )

                    status = "SHIPPED"

            # 成功だけでなく業務失敗も再送結果として保存する。
            conn.execute(
                """
                INSERT INTO request_log(
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

        # 全コマンド処理済み、まだCOMMIT前。
        if before_commit is not None:
            before_commit()

        conn.commit()

        # COMMIT成功後のみ結果を呼出し側へ返す。
        return results

    except BaseException:
        if conn.in_transaction:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        raise

    finally:
        conn.close()


def snapshot(path) -> dict:
    conn = _connect(path)

    try:
        # 最初のSELECTで確立されたread snapshotをCOMMITまで維持する。
        # したがって複数SELECTでも同一時点を観測する。
        conn.execute("BEGIN")

        available_rows = conn.execute(
            """
            SELECT sku, available
            FROM stock
            ORDER BY sku
            """
        ).fetchall()

        reservation_rows = conn.execute(
            """
            SELECT
                reservation_id,
                sku,
                qty,
                state
            FROM reservations
            ORDER BY reservation_id
            """
        ).fetchall()

        result = {
            "available": {
                _from_key(sku): available
                for sku, available in available_rows
            },
            "reservations": {
                _from_key(reservation_id): {
                    "sku": _from_key(sku),
                    "qty": qty,
                    "state": state,
                }
                for (
                    reservation_id,
                    sku,
                    qty,
                    state,
                ) in reservation_rows
            },
        }

        conn.commit()
        return result

    except BaseException:
        if conn.in_transaction:
            try:
                conn.rollback()
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


def _batch_worker(
    path,
    commands,
    ready,
    start,
    out,
):
    try:
        ready.set()

        if not start.wait(10):
            out.put(
                ("err", "worker start timeout")
            )
            return

        out.put(
            (
                "ok",
                inventory.apply_batch(
                    path,
                    commands,
                ),
            )
        )

    except BaseException as exc:
        out.put(
            (
                "err",
                f"{type(exc).__name__}: {exc}",
            )
        )


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db = str(
            Path(self._tmp.name)
            / "inventory.sqlite3"
        )

    def tearDown(self):
        self._tmp.cleanup()

    def _finish(self, processes):
        for process in processes:
            process.join(15)

        alive = [
            process
            for process in processes
            if process.is_alive()
        ]

        for process in alive:
            process.terminate()
            process.join(5)

        self.assertFalse(
            alive,
            "worker process did not finish",
        )

        self.assertTrue(
            all(
                process.exitcode == 0
                for process in processes
            )
        )

    def test_normal_reserve_cancel_ship_and_terminal_conflicts(
        self,
    ):
        inventory.init_db(
            self.db,
            {"A": 10},
        )

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
                    "op": "reserve",
                    "reservation_id": "r2",
                    "sku": "A",
                    "qty": 4,
                },
                {
                    "request_id": "q3",
                    "op": "cancel",
                    "reservation_id": "r1",
                },
                {
                    "request_id": "q4",
                    "op": "ship",
                    "reservation_id": "r2",
                },
                {
                    "request_id": "q5",
                    "op": "ship",
                    "reservation_id": "r1",
                },
                {
                    "request_id": "q6",
                    "op": "cancel",
                    "reservation_id": "r2",
                },
            ],
        )

        self.assertEqual(
            [
                item["status"]
                for item in result
            ],
            [
                "RESERVED",
                "RESERVED",
                "CANCELLED",
                "SHIPPED",
                "CONFLICT",
                "CONFLICT",
            ],
        )

        self.assertEqual(
            inventory.snapshot(self.db),
            {
                "available": {
                    "A": 6,
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

        # q1 の予約は既にCANCELLEDだが、
        # 同一request_id・同一内容の再送は元の結果を返す。
        before_replay = inventory.snapshot(
            self.db
        )

        self.assertEqual(
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
            ),
            [
                {
                    "request_id": "q1",
                    "status": "RESERVED",
                }
            ],
        )

        self.assertEqual(
            inventory.snapshot(self.db),
            before_replay,
        )

    def test_failed_results_are_replayed(
        self,
    ):
        inventory.init_db(
            self.db,
            {"A": 2},
        )

        oos = {
            "request_id": "oos",
            "op": "reserve",
            "reservation_id": "r-oos",
            "sku": "A",
            "qty": 3,
        }

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [oos],
            )[0]["status"],
            "OUT_OF_STOCK",
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "fill",
                    "op": "reserve",
                    "reservation_id": "rf",
                    "sku": "A",
                    "qty": 2,
                }
            ],
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "undo",
                    "op": "cancel",
                    "reservation_id": "rf",
                }
            ],
        )

        # 現在は在庫が復元済みでも、
        # oosの再送結果は最初のOUT_OF_STOCK。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [oos],
            )[0]["status"],
            "OUT_OF_STOCK",
        )

        self.assertNotIn(
            "r-oos",
            inventory.snapshot(
                self.db
            )["reservations"],
        )

        not_found = {
            "request_id": "nf",
            "op": "cancel",
            "reservation_id": "future",
        }

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [not_found],
            )[0]["status"],
            "NOT_FOUND",
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "make",
                    "op": "reserve",
                    "reservation_id": "future",
                    "sku": "A",
                    "qty": 1,
                }
            ],
        )

        # 対象予約が後から作成されても、
        # 元のNOT_FOUNDを返し、取消はしない。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [not_found],
            )[0]["status"],
            "NOT_FOUND",
        )

        self.assertEqual(
            inventory.snapshot(
                self.db
            )["reservations"]["future"]["state"],
            "RESERVED",
        )

        conflict = {
            "request_id": "conf",
            "op": "reserve",
            "reservation_id": "future",
            "sku": "A",
            "qty": 1,
        }

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [conflict],
            )[0]["status"],
            "CONFLICT",
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [conflict],
            )[0]["status"],
            "CONFLICT",
        )

    def test_dict_order_and_batch_duplicate(
        self,
    ):
        inventory.init_db(
            self.db,
            {"A": 5},
        )

        command = {
            "request_id": "q",
            "op": "reserve",
            "reservation_id": "r",
            "sku": "A",
            "qty": 3,
        }

        reordered = {
            "qty": 3,
            "sku": "A",
            "reservation_id": "r",
            "op": "reserve",
            "request_id": "q",
        }

        result = inventory.apply_batch(
            self.db,
            [
                command,
                reordered,
            ],
        )

        self.assertEqual(
            result,
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

        # 同じbatch内で二重減算されていない。
        self.assertEqual(
            inventory.snapshot(
                self.db
            )["available"],
            {"A": 2},
        )

        # 接続をまたいだキー順違いの再送も同一。
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
            )["available"],
            {"A": 2},
        )

    def test_same_batch_conflicting_duplicate_request_rolls_back(
        self,
    ):
        inventory.init_db(
            self.db,
            {"A": 5},
        )

        first = {
            "request_id": "dup",
            "op": "reserve",
            "reservation_id": "r1",
            "sku": "A",
            "qty": 2,
        }

        second = {
            "request_id": "dup",
            "op": "reserve",
            "reservation_id": "r2",
            "sku": "A",
            "qty": 1,
        }

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    first,
                    second,
                ],
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

        # request_logへのfirstの記録もrollback済み。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [first],
            )[0]["status"],
            "RESERVED",
        )

    def test_validation_and_unknown_sku_precede_replay(
        self,
    ):
        with self.assertRaises(ValueError):
            inventory.init_db(
                self.db,
                {},
            )

        inventory.init_db(
            self.db,
            {"A": 3},
        )

        # bool はintとして認めない。
        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "bad",
                        "op": "reserve",
                        "reservation_id": "r",
                        "sku": "A",
                        "qty": True,
                    }
                ],
            )

        # 未定義キーは禁止。
        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "bad2",
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
                    "request_id": "q",
                    "op": "reserve",
                    "reservation_id": "r1",
                    "sku": "A",
                    "qty": 1,
                }
            ],
        )

        before = inventory.snapshot(
            self.db
        )

        # qは既存request_idだが、未登録SKU検査が
        # request_id内容衝突より先。
        with self.assertRaisesRegex(
            ValueError,
            "unknown SKU",
        ):
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "q",
                        "op": "reserve",
                        "reservation_id": "r2",
                        "sku": "missing",
                        "qty": 1,
                    }
                ],
            )

        self.assertEqual(
            inventory.snapshot(self.db),
            before,
        )

    def test_request_id_content_conflict_rolls_back_whole_batch(
        self,
    ):
        inventory.init_db(
            self.db,
            {"A": 10},
        )

        inventory.apply_batch(
            self.db,
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

        before = inventory.snapshot(
            self.db
        )

        with self.assertRaises(ValueError):
            inventory.apply_batch(
                self.db,
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
                        "op": "cancel",
                        "reservation_id": "r-old",
                    },
                ],
            )

        self.assertEqual(
            inventory.snapshot(self.db),
            before,
        )

        # newの在庫更新・予約・request_logも全てrollback。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "new",
                        "op": "reserve",
                        "reservation_id": "r-new",
                        "sku": "A",
                        "qty": 3,
                    }
                ],
            )[0]["status"],
            "RESERVED",
        )

    def test_unknown_sku_rolls_back_whole_batch(
        self,
    ):
        inventory.init_db(
            self.db,
            {"A": 5},
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
                        "qty": 2,
                    },
                    {
                        "request_id": "q2",
                        "op": "reserve",
                        "reservation_id": "r2",
                        "sku": "missing",
                        "qty": 1,
                    },
                ],
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

        # q1のrequest_logも残っていない。
        self.assertEqual(
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
            )[0]["status"],
            "RESERVED",
        )

    def test_before_commit_exception_rolls_back(
        self,
    ):
        inventory.init_db(
            self.db,
            {"A": 5},
        )

        calls = []

        class HookError(RuntimeError):
            pass

        def hook():
            calls.append(1)
            raise HookError("stop")

        command = {
            "request_id": "q",
            "op": "reserve",
            "reservation_id": "r",
            "sku": "A",
            "qty": 2,
        }

        with self.assertRaises(HookError):
            inventory.apply_batch(
                self.db,
                [command],
                before_commit=hook,
            )

        self.assertEqual(
            calls,
            [1],
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

        # request_idもrollback済み。
        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [command],
            )[0]["status"],
            "RESERVED",
        )

    def test_reopen_persists_state(
        self,
    ):
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

        # snapshot/apply_batchは毎回新しいsqlite3接続。
        self.assertEqual(
            inventory.snapshot(
                self.db
            )["available"],
            {"A": 1},
        )

        self.assertEqual(
            inventory.apply_batch(
                self.db,
                [
                    {
                        "request_id": "q2",
                        "op": "cancel",
                        "reservation_id": "r1",
                    }
                ],
            )[0]["status"],
            "CANCELLED",
        )

        self.assertEqual(
            inventory.snapshot(
                self.db
            )["available"],
            {"A": 4},
        )

    def test_two_processes_cannot_overreserve(
        self,
    ):
        inventory.init_db(
            self.db,
            {"A": 5},
        )

        ctx = mp.get_context("spawn")

        start = ctx.Event()
        ready1 = ctx.Event()
        ready2 = ctx.Event()
        out = ctx.Queue()

        process1 = ctx.Process(
            target=_batch_worker,
            args=(
                self.db,
                [
                    {
                        "request_id": "q1",
                        "op": "reserve",
                        "reservation_id": "r1",
                        "sku": "A",
                        "qty": 4,
                    }
                ],
                ready1,
                start,
                out,
            ),
        )

        process2 = ctx.Process(
            target=_batch_worker,
            args=(
                self.db,
                [
                    {
                        "request_id": "q2",
                        "op": "reserve",
                        "reservation_id": "r2",
                        "sku": "A",
                        "qty": 4,
                    }
                ],
                ready2,
                start,
                out,
            ),
        )

        process1.start()
        process2.start()

        # sleepではなく、両workerが開始待ちに到達したことを確認して解放。
        self.assertTrue(
            ready1.wait(10)
        )
        self.assertTrue(
            ready2.wait(10)
        )

        start.set()

        self._finish(
            [
                process1,
                process2,
            ]
        )

        messages = [
            out.get(timeout=5),
            out.get(timeout=5),
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

        snap = inventory.snapshot(
            self.db
        )

        self.assertEqual(
            snap["available"],
            {"A": 1},
        )

        self.assertEqual(
            len(snap["reservations"]),
            1,
        )

    def test_two_processes_cannot_both_cancel_and_ship(
        self,
    ):
        inventory.init_db(
            self.db,
            {"A": 1},
        )

        inventory.apply_batch(
            self.db,
            [
                {
                    "request_id": "make",
                    "op": "reserve",
                    "reservation_id": "r",
                    "sku": "A",
                    "qty": 1,
                }
            ],
        )

        ctx = mp.get_context("spawn")

        start = ctx.Event()
        ready1 = ctx.Event()
        ready2 = ctx.Event()
        out = ctx.Queue()

        process1 = ctx.Process(
            target=_batch_worker,
            args=(
                self.db,
                [
                    {
                        "request_id": "cancel",
                        "op": "cancel",
                        "reservation_id": "r",
                    }
                ],
                ready1,
                start,
                out,
            ),
        )

        process2 = ctx.Process(
            target=_batch_worker,
            args=(
                self.db,
                [
                    {
                        "request_id": "ship",
                        "op": "ship",
                        "reservation_id": "r",
                    }
                ],
                ready2,
                start,
                out,
            ),
        )

        process1.start()
        process2.start()

        self.assertTrue(
            ready1.wait(10)
        )
        self.assertTrue(
            ready2.wait(10)
        )

        start.set()

        self._finish(
            [
                process1,
                process2,
            ]
        )

        messages = [
            out.get(timeout=5),
            out.get(timeout=5),
        ]

        self.assertTrue(
            all(
                message[0] == "ok"
                for message in messages
            ),
            messages,
        )

        statuses = {
            message[1][0]["status"]
            for message in messages
        }

        self.assertIn(
            "CONFLICT",
            statuses,
        )

        self.assertEqual(
            len(statuses),
            2,
        )

        self.assertTrue(
            statuses
            & {
                "CANCELLED",
                "SHIPPED",
            }
        )

        snap = inventory.snapshot(
            self.db
        )

        state = snap[
            "reservations"
        ]["r"]["state"]

        if state == "CANCELLED":
            self.assertEqual(
                snap["available"],
                {"A": 1},
            )
        else:
            self.assertEqual(
                state,
                "SHIPPED",
            )

            self.assertEqual(
                snap["available"],
                {"A": 0},
            )


if __name__ == "__main__":
    unittest.main()
```

実行コマンドは次です。

```bash
python3 -m unittest -v test_inventory.py
```

この実装では、`apply_batch()` 全体を `BEGIN IMMEDIATE` から `COMMIT` まで1トランザクションにするため、SQLiteのファイルロックによって独立プロセス間の書込みbatchも直列化されます。在庫減算は `available >= qty` を条件にした単一 `UPDATE` で行うため負数化しません。`cancel` / `ship` も同じwrite transaction内で `RESERVED` から一度だけ遷移します。

再送は `request_log` に「キー順を正規化したJSONコマンド」と最初の結果を保存して保証しています。同じ `request_id`・同じ内容なら状態を再評価せず保存済み結果を返し、異なる内容なら `ValueError` です。このログ自体も在庫・予約変更と同じトランザクション内なので、例外や `before_commit` の例外ではまとめてロールバックされます。`snapshot()` は明示的なread transaction内で全SELECTを実行するため同一SQLiteスナップショットを返します。ロック待ちは5秒の有限値です。

実行確認済みです。**Python 3.13.5** で上記テストを実行し、**11 tests / OK** でした。独立プロセス競合テストは `multiprocessing` の `Event` で開始を同期しており、`sleep` に正しさを依存していません。