"""
run_w700_lockx_shapes.py  (remote)  -- runs/cavity_619_width
Taper shapes for the lock_x pipeline (w700, hx/a 0.50, hy/w 0.77, 80 nm). run_w700_lockx.py ran 0 shapes because
Pipeline.shapes brackets at (a0, a0 - 8) and with lock_x the center holes drop below 80 nm at a0 - 8. Bracket UPWARD
instead (da = -6 -> points a0 and a0 + 6). d 0.10 / 0.13 only (d 0.16 base: Q ~1.3e6, loc < 0.8).
With lock_x, xi / chi only change the center hole HEIGHT (hy = hy_m sqrt(s r)); hx follows the period.
Run via:  python scripts/remote_runner.py runs/cavity_619_width/run_w700_lockx_shapes.py
"""
import json
from pathlib import Path

from cavity_pipeline import Pipeline, p

CELL = dict(w=700, t=120, hx_a=0.50, hy_w=0.77, lock_x=True)
rd = 'runs/cavity_619_width/w700_mf80_LX'
line = {float(k): v for k, v in json.load(open(Path(rd) / 'data' / 'line_619.json')).items() if float(k) in (0.10, 0.13)}
P = Pipeline(rd, CELL, 80, 'w700_mf80_LX')
try:
    SH = [(2.0, 4.0), (4.0, 4.5), (6.0, 4.0), (6.0, 5.0), (8.0, 5.0)]
    P.shapes(line, [2.0, 4.0, 6.0, 8.0], [4.0, 4.5, 5.0], da=-6.0, max_shapes=10, only=SH)
    P.finalize()
finally:
    P.close()
p('lock_x shapes done.')
