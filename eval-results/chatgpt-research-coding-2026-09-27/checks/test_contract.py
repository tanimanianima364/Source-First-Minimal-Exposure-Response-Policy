"""Schema-independent, pre-collection acceptance checks; code review complements C6."""
import multiprocessing as mp
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import traceback
import unittest

import inventory as api

CTX = mp.get_context('spawn')


def reserve(q='q', r='r', qty=1, sku='A'):
    return dict(request_id=q, op='reserve', reservation_id=r, sku=sku, qty=qty)


def change(op, q, r='r'):
    return dict(request_id=q, op=op, reservation_id=r)


def worker(path, commands, ready, start, pipe, mode='apply'):
    try:
        ready.set()
        if not start.wait(10):
            raise TimeoutError('start gate')
        if mode == 'before_crash':
            def pause():
                pipe.send(('paused', None))
                threading.Event().wait(60)
            api.apply_batch(path, commands, before_commit=pause)
        elif mode == 'after_crash':
            api.apply_batch(path, commands)
            # Signal completion, but deliberately never deliver the returned result.
            pipe.send(('committed', None))
            threading.Event().wait(60)
        elif mode == 'stress':
            for i in range(150):
                api.apply_batch(path, [reserve(f'r{i}', f'r{i}')])
                api.apply_batch(path, [change('cancel', f'c{i}', f'r{i}')])
            pipe.send(('ok', None))
        else:
            pipe.send(('ok', api.apply_batch(path, commands)))
    except BaseException:
        pipe.send(('error', traceback.format_exc()))
    finally:
        pipe.close()


class Contract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / 'db.sqlite')
        api.init_db(self.db, {'A': 5, 'B': 0})

    def result(self, commands, statuses, **kwargs):
        expected = [dict(request_id=c['request_id'], status=s) for c, s in zip(commands, statuses)]
        self.assertEqual(api.apply_batch(self.db, commands, **kwargs), expected)

    def clean(self):
        self.assertEqual(api.snapshot(self.db), {'available': {'A': 5, 'B': 0}, 'reservations': {}})

    def spawn(self, commands, gate=None, mode='apply'):
        ready, gate = CTX.Event(), gate or CTX.Event()
        parent, child = CTX.Pipe(duplex=False)
        p = CTX.Process(target=worker, args=(self.db, commands, ready, gate, child, mode))
        p.start()
        child.close()
        def cleanup():
            if p.is_alive():
                p.terminate()
            p.join(3)
            if p.is_alive():
                p.kill()
                p.join(3)
            parent.close()
        self.addCleanup(cleanup)
        self.assertTrue(ready.wait(10), 'worker did not reach start gate')
        return p, parent, gate

    def receive(self, entry, tag='ok'):
        p, pipe, _ = entry
        self.assertTrue(pipe.poll(15), 'worker result timeout')
        state, value = pipe.recv()
        self.assertEqual(state, tag, value)
        if tag == 'ok':
            p.join(5)
            self.assertEqual(p.exitcode, 0)
        return value

    def race(self, left, right):
        gate = CTX.Event()
        a, b = self.spawn(left, gate), self.spawn(right, gate)
        gate.set()
        return self.receive(a), self.receive(b)

    def test_C1_shapes_and_input_validation(self):
        bad = [None, (), {}, [], [None], [dict(reserve(), extra=1)],
               [change('other', 'q')], [change([], 'q')], [dict(reserve(), qty='1')],
               [dict(reserve(), qty=None)], [dict(reserve(), qty=True)], [dict(reserve(), qty=1.0)],
               [dict(reserve(), qty=0)], [dict(reserve(), qty=10**9 + 1)],
               [dict(reserve(), sku='missing')], [dict(reserve(), sku=[])]]
        for key in ('request_id', 'reservation_id', 'sku'):
            for value in ('', 'x' * 129, 1, None, [], True):
                bad.append([dict(reserve(), **{key: value})])
        for key in reserve():
            command = reserve()
            del command[key]
            bad.append([command])
        for op in ('cancel', 'ship'):
            bad.extend([[dict(change(op, 'x'), qty=1)], [dict(change(op, 'x'), sku='A')]])
        for commands in bad:
            with self.subTest(commands=commands), self.assertRaises(ValueError):
                api.apply_batch(self.db, commands)
        self.clean()
        self.result([reserve(q='x' * 128, r='y' * 128, qty=10**9)], ['OUT_OF_STOCK'])
        for i, stocks in enumerate((None, {}, [], {'': 1}, {'x' * 129: 1}, {1: 1}, {'A': True},
                                    {'A': -1}, {'A': 1.0}, {'A': 10**9 + 1})):
            with self.subTest(stocks=stocks), self.assertRaises(ValueError):
                api.init_db(str(Path(self.tmp.name) / f'invalid{i}'), stocks)
        boundary = str(Path(self.tmp.name) / 'boundary')
        api.init_db(boundary, {'A': 10**9, 'a': 0})
        self.assertEqual(api.snapshot(boundary)['available'], {'A': 10**9, 'a': 0})

    def test_C2_transitions_and_precedence(self):
        commands = [reserve('q1', 'r1', 3), change('ship', 'q2', 'r1'),
                    change('cancel', 'q3', 'r1'), reserve('q4', 'r1', 10),
                    reserve('q5', 'r2', 2), change('cancel', 'q6', 'r2'),
                    reserve('q7', 'r2', 3), change('ship', 'q8', 'missing')]
        self.result(commands, ['RESERVED', 'SHIPPED', 'CONFLICT', 'CONFLICT',
                               'RESERVED', 'CANCELLED', 'CONFLICT', 'NOT_FOUND'])
        self.assertEqual(api.snapshot(self.db), {'available': {'A': 2, 'B': 0}, 'reservations': {
            'r1': {'sku': 'A', 'qty': 3, 'state': 'SHIPPED'},
            'r2': {'sku': 'A', 'qty': 2, 'state': 'CANCELLED'}}})
        self.result([commands[1], commands[5]], ['SHIPPED', 'CANCELLED'])

    def test_C3_replay_success_failures_order_duplicates(self):
        q = reserve(qty=3)
        self.result([q, dict(reversed(list(q.items())))], ['RESERVED', 'RESERVED'])
        self.result([change('cancel', 'cancel')], ['CANCELLED'])
        self.result([q], ['RESERVED'])
        self.assertEqual(api.snapshot(self.db)['available']['A'], 5)
        self.assertEqual(api.snapshot(self.db)['reservations']['r']['state'], 'CANCELLED')
        absent = change('cancel', 'absent', 'future')
        full = reserve('full', 'future', 6)
        self.result([absent, full], ['NOT_FOUND', 'OUT_OF_STOCK'])
        self.result([reserve('new', 'future', 1)], ['RESERVED'])
        self.result([absent, full], ['NOT_FOUND', 'OUT_OF_STOCK'])
        conflict = reserve('collision', 'future')
        self.result([conflict], ['CONFLICT'])
        self.result([change('cancel', 'later', 'future'), conflict], ['CANCELLED', 'CONFLICT'])
        entry = self.spawn([q, full, absent, conflict])
        entry[2].set()
        self.assertEqual([x['status'] for x in self.receive(entry)],
                         ['RESERVED', 'OUT_OF_STOCK', 'NOT_FOUND', 'CONFLICT'])
        self.result([reserve('strict', 'strict', 1)], ['RESERVED'])
        for command in (reserve('strict', 'strict', True), dict(q, sku='unknown'), dict(q, qty=1)):
            with self.assertRaises(ValueError):
                api.apply_batch(self.db, [command])

    def test_C4_rollback_all_new_records_and_hook(self):
        first = reserve('one', 'one', 2)
        for ending in ({'bad': 1}, dict(first, qty=1)):
            with self.assertRaises(ValueError):
                api.apply_batch(self.db, [first, ending])
            self.clean()
        called = []
        def fail():
            called.append(1)
            raise RuntimeError('injected')
        with self.assertRaises(RuntimeError):
            api.apply_batch(self.db, [first, change('cancel', 'missing', 'absent')], before_commit=fail)
        self.assertEqual(called, [1])
        self.clean()
        # Every rolled-back request ID, including a failure record, remains reusable.
        self.result([dict(first, qty=3), reserve('missing', 'another')], ['RESERVED', 'RESERVED'])
        saved = api.snapshot(self.db)
        with self.assertRaises(ValueError):
            api.apply_batch(self.db, [change('cancel', 'fresh', 'one'), dict(first, qty=4)])
        self.assertEqual(api.snapshot(self.db), saved)
        hooks = []
        self.result([dict(first, qty=3)], ['RESERVED'], before_commit=lambda: hooks.append(1))
        self.assertEqual(hooks, [1])

    def test_C4_kill_before_commit_and_lost_response(self):
        entry = self.spawn([reserve(qty=2)], mode='before_crash')
        entry[2].set()
        self.receive(entry, 'paused')
        entry[0].terminate()
        entry[0].join(5)
        self.assertIsNotNone(entry[0].exitcode)
        self.clean()
        entry = self.spawn([reserve(qty=3)], mode='after_crash')
        entry[2].set()
        self.receive(entry, 'committed')
        entry[0].terminate()
        entry[0].join(5)
        retry = self.spawn([reserve(qty=3)])
        retry[2].set()
        self.assertEqual(self.receive(retry), [{'request_id': 'q', 'status': 'RESERVED'}])
        self.assertEqual(api.snapshot(self.db)['available']['A'], 2)

    def test_C5_competing_reserves_and_identical_requests(self):
        a, b = self.race([reserve('a', 'a', 5)], [reserve('b', 'b', 5)])
        self.assertEqual(sorted([a[0]['status'], b[0]['status']]), ['OUT_OF_STOCK', 'RESERVED'])
        self.assertEqual(api.snapshot(self.db)['available']['A'], 0)
        winner = 'a' if a[0]['status'] == 'RESERVED' else 'b'
        self.result([change('cancel', 'reset', winner)], ['CANCELLED'])
        a, b = self.race([reserve('same', 'same', 3)], [reserve('same', 'same', 3)])
        self.assertEqual(a, b)
        self.assertEqual(a[0]['status'], 'RESERVED')
        self.assertEqual(api.snapshot(self.db)['available']['A'], 2)

    def test_C5_cancel_vs_ship(self):
        self.result([reserve(qty=3)], ['RESERVED'])
        a, b = self.race([change('cancel', 'c')], [change('ship', 's')])
        statuses = [a[0]['status'], b[0]['status']]
        self.assertEqual(statuses.count('CONFLICT'), 1)
        state = api.snapshot(self.db)
        self.assertIn(state['reservations']['r']['state'], ('CANCELLED', 'SHIPPED'))
        self.assertEqual(state['available']['A'], 5 if 'CANCELLED' in statuses else 2)

    def test_C5_external_lock_releases_without_partial_state(self):
        # No maximum timeout is specified. Release the lock after both parties are ready;
        # an early bounded OperationalError or eventual success is acceptable here.
        with sqlite3.connect(self.db) as con:
            con.execute('BEGIN IMMEDIATE')
            entry = self.spawn([reserve(qty=2)])
            entry[2].set()
            if entry[1].poll(12):
                tag, message = entry[1].recv()
                self.assertEqual(tag, 'error')
                self.assertIn('OperationalError', message)
                con.rollback()
                self.clean()
            else:
                print('LOCK_TIMEOUT_UNVERIFIED: no error within 12 s; inspect finite retry bound')
                con.rollback()
                self.assertEqual(self.receive(entry)[0]['status'], 'RESERVED')

    def test_C6_coherent_snapshot_stress(self):
        entry = self.spawn([], mode='stress')
        entry[2].set()
        observed = 0
        while not entry[1].poll(0) and observed < 1000:
            state = api.snapshot(self.db)
            self.assertEqual(set(state), {'available', 'reservations'})
            self.assertEqual(state['available']['B'], 0)
            self.assertGreaterEqual(state['available']['A'], 0)
            used = sum(r['qty'] for r in state['reservations'].values()
                       if r['sku'] == 'A' and r['state'] in ('RESERVED', 'SHIPPED'))
            self.assertEqual(state['available']['A'] + used, 5)
            observed += 1
        self.receive(entry)
        self.assertEqual(len(api.snapshot(self.db)['reservations']), 150)
        if observed == 0:
            self.skipTest('SNAPSHOT_OVERLAP_UNVERIFIED: writer finished before sampling')


if __name__ == '__main__':
    unittest.main()
