# Post-hoc diagnostic: the task accepts any Python str of length 1..128.
# Discovered while reading A-en; separate from the frozen nine-test harness.
import tempfile
from pathlib import Path
import inventory

with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / 'db.sqlite')
    sku, request_id, reservation_id = '\ud800', '\ud801', '\ud802'
    assert all(isinstance(s, str) and len(s) == 1 for s in (sku, request_id, reservation_id))
    inventory.init_db(path, {sku: 1})
    command = dict(request_id=request_id, op='reserve', reservation_id=reservation_id, sku=sku, qty=1)
    expected = [{'request_id': request_id, 'status': 'RESERVED'}]
    assert inventory.apply_batch(path, [command]) == expected
    assert inventory.apply_batch(path, [command]) == expected
    assert inventory.snapshot(path) == {'available': {sku: 0}, 'reservations': {reservation_id: {'sku': sku, 'qty': 1, 'state': 'RESERVED'}}}
print('LONE_SURROGATE_DIAGNOSTIC=PASS')
