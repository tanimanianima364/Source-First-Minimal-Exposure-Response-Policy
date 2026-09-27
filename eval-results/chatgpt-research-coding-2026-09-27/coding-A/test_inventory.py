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
