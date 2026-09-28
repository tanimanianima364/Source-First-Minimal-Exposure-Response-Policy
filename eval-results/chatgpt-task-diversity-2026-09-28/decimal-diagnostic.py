import inventory as m
from pathlib import Path
from decimal import Decimal
p=Path('/tmp/large.csv')
p.write_text('department,amount\nA,123456789012345678901234567890.01\nA,0.01\n')
actual=m.sum_csv(p)['A']; expected=Decimal('123456789012345678901234567890.02')
print('expected:',expected,'actual:',actual,'equal:',actual==expected)
assert actual==expected
