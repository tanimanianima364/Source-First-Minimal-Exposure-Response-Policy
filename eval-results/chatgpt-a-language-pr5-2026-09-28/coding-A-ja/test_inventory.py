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
