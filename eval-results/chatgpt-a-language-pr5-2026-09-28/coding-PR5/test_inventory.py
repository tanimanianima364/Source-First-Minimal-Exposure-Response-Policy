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
