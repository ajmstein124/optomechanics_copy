"""
sweep_shape_d10.py  (remote)  -- runs/cavity_619
Taper-shape sweep at d = 0.10 for the 60 nm design (user 2026-10-14): the (a, d) map showed the d = 0.10
row is fabricable at 60 nm with Q ~ 4e7 at 619 nm (a = 195.2 nm) but breathing at 11.1 GHz. 8 of the 16
fabricable (xi, chi) shapes, spread over xi = 4..10. Same pipeline/identification as everything else.
Waits for sweep_shape.py ('Shape sweep done.'); the 80 nm chain waits for this ('d10 shape sweep done.').
"""
import time
from pathlib import Path
from cavity_pipeline import Pipeline, p

LOG = Path(r'C:\Users\abby\comsol\job_log_cavity_619__sweep_shape.txt')
t0 = time.time()
while LOG.exists() and 'Shape sweep done.' not in LOG.read_text(errors='ignore'):
    if time.time() - t0 > 6 * 3600:
        break
    time.sleep(60)
p(f'd10 start ({time.time()-t0:.0f} s wait)')
P = Pipeline('runs/cavity_619', dict(w=550, t=120, hx_a=0.53, hy_w=0.77), 60, 'mf60')
try:
    P.shapes({0.10: 195.2}, [4, 6, 8, 10], [3.5, 4.0, 5.0, 6.0], only=[(10, 6.0), (8, 6.0), (8, 5.0), (6, 6.0),
                                                                      (6, 5.0), (6, 4.0), (4, 5.0), (4, 3.5)])
finally:
    P.close()
p('d10 shape sweep done.')
