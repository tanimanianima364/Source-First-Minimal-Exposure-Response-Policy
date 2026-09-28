"""Frozen checks: run in the existing isolated runner, never import answers on host.
Candidate source is /candidate/inventory.py; cases are selected by CASE below.
"""
from decimal import Decimal
from pathlib import Path
import sqlite3
import inventory as m

CASE = 'duration'  # evaluator substitutes only this task selector in a staging copy

def raises(kind, fn, *args):
    try:
        fn(*args)
    except kind:
        return
    raise AssertionError(f'expected {kind.__name__}: {args!r}')

if CASE == 'duration':
    for text, want in [('1h30m45s',5445),('0s',0),('90m',5400),('2h3s',7203),('1h',3600)]:
        assert m.parse_duration(text) == want
        assert type(m.parse_duration(text)) is int
    for text in ['', '1s1h','1h1h','1sX','１s','1s\n',' 1s','-1s','1.5h']:
        raises(ValueError,m.parse_duration,text)
    for value in [None,1,[],True]: raises(TypeError,m.parse_duration,value)
elif CASE == 'csv':
    p=Path('/tmp/sales.csv')
    p.write_text('department,amount\n"A,B",0.10\n"A,B",0.20\nC,-2.50\n',encoding='utf8')
    out=m.sum_csv(p)
    assert out == {'A,B':Decimal('0.30'),'C':Decimal('-2.50')}
    assert all(isinstance(v,Decimal) for v in out.values())
    p.write_text('department,amount\n',encoding='utf8'); assert m.sum_csv(p)=={}
    for data in ['', 'amount,department\n1,A\n', 'department,amount\nA,\n', 'department,amount\nA,NaN\n', 'department,amount\nA,Infinity\n','department,amount\nA,1.234\n','department,amount\nA,1,2\n','department,amount\nA\n','department,amount\n,1\n']:
        p.write_text(data,encoding='utf8'); raises(ValueError,m.sum_csv,p)
elif CASE == 'sql':
    c=sqlite3.connect(':memory:'); c.execute('CREATE TABLE users(id INTEGER,username TEXT UNIQUE,email TEXT)')
    c.executemany('INSERT INTO users VALUES(?,?,?)',[(1,'alice','a'),(2,"O'Reilly",'o')])
    assert m.get_user(c,'alice')==(1,'alice','a')
    assert m.get_user(c,"O'Reilly")== (2,"O'Reilly",'o')
    assert m.get_user(c,"' OR 1=1 --") is None
    assert m.get_user(c,'nobody') is None
    assert c.in_transaction
    c.rollback(); assert c.execute('SELECT COUNT(*) FROM users').fetchone()==(0,)
elif CASE == 'rootcause':
    assert m.invoice_total(['1,200.50','-20.25'])==Decimal('1180.25')
    assert m.refund_amount('1,200.50')==Decimal('-1200.50')
    assert m.invoice_total([])==Decimal(0)
    for s in ['  +1,234.5  ','1234.50','0','-0.25']:
        assert m.parse_amount(s)==Decimal(s.strip().replace(',',''))
    for s in ['12,34','1,,000','1,23,456','NaN','Infinity','1.234','', '1e3']:
        raises(ValueError,m.invoice_total,[s]); raises(ValueError,m.refund_amount,s)
    for v in [None,1,[],True]:
        raises(TypeError,m.invoice_total,[v]); raises(TypeError,m.refund_amount,v)
else:
    raise AssertionError('Unknown task')
print('FROZEN_CHECKS_PASS',CASE)
