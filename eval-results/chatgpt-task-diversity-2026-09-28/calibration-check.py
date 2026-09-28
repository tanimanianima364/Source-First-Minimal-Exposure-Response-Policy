"""Execute the preregistered calibration criteria after extraction; not a frozen test file."""
import math
import inventory as m
f = getattr(m, 'temperature_c', None) or m.raw_to_temperature
assert math.isclose(f(310,1.02,-0.01),51.0,abs_tol=1e-10)
assert math.isclose(f(0,1.02,-0.01),-51.0,abs_tol=1e-10)
assert math.isclose(f(1023,1.02,-0.01),285.6,abs_tol=1e-10)
for args in [(True,1,0),(310.5,1,0),(-1,1,0),(1024,1,0),(310,0,0),(310,-1,0),(310,float('nan'),0),(310,float('inf'),0),(310,1,float('nan')),(310,1,float('inf'))]:
    try:
        f(*args)
    except (TypeError,ValueError):
        pass
    else:
        raise AssertionError(args)
print('CALIBRATION_CRITERIA_PASS')
