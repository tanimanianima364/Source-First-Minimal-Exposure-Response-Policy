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
