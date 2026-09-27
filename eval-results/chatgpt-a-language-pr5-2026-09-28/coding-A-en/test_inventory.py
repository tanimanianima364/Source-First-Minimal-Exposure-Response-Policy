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
