"""
run.py  (remote)  -- runs/cavity_619_mf80
Overnight chain (user 2026-10-14): after the 60 nm shape sweep, (1) finalize the 60 nm designs
(runs/cavity_619), then (2) the full pipeline at an 80 nm minimum feature for two mirror cells:
  A: w 550, hx/a 0.53, hy/w 0.70 (rail 82.5, bridge ~100; best-scoring 80 nm cell from stage 2)
  B: w 550, hx/a 0.45, hy/w 0.70 (narrower holes -> more taper freedom at 80 nm: xi up to 8)
(a, d) grid: a 185..225 step 10 x d 0.07..0.16 (d >= 0.19 has no shape fabricable at 80 nm),
baseline shapes fabricable over the grid (A: xi 2 / chi 3.5, B: xi 4 / chi 3.5); then (xi, chi)
shapes on the 619 nm line (<= 12 per cell, strongest pull first); then best designs.
Run via:  python scripts/remote_runner.py runs/cavity_619_mf80/run.py
"""
import sys
import time
from pathlib import Path
from cavity_pipeline import Pipeline, p

LOG60 = Path(r'C:\Users\abby\comsol\job_log_cavity_619__sweep_shape_d10.txt')   # d = 0.10 shapes run first
t0 = time.time()
while (not LOG60.exists()) or 'd10 shape sweep done.' not in LOG60.read_text(errors='ignore'):
    if time.time() - t0 > 6 * 3600:
        p('waited 6 h for the 60 nm shape sweep; starting anyway'); break
    time.sleep(60)
p(f'chain start ({time.time()-t0:.0f} s wait)')

P60 = Pipeline('runs/cavity_619', dict(w=550, t=120, hx_a=0.53, hy_w=0.77), 60, 'mf60')
try:
    P60.finalize()
finally:
    P60.close()

D80 = [0.07, 0.10, 0.13, 0.16]
for label, cell, base in (('mf80A', dict(w=550, t=120, hx_a=0.53, hy_w=0.70), (2.0, 3.5)),
                          ('mf80B', dict(w=550, t=120, hx_a=0.45, hy_w=0.70), (4.0, 3.5))):
    P = Pipeline(f'runs/cavity_619_mf80/{label}', cell, 80, label)
    try:
        P.ad([185, 195, 205, 215, 225], D80, base)
        line = P.line(D80)
        P.shapes(line, [2, 4, 6, 8, 10], [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0])
        P.finalize()
    finally:
        P.close()
p('80 nm chain done.')
