"""
run.py  (remote)  -- runs/cavity_619_width
Beam-width study (user 2026-10-15): the 60 nm shape sweep at w = 550 put the breathing mode at >= 11.4 GHz
for every fabricable taper, so widen the beam (breathing ~ 1/w) to reach <= 10 GHz. Watch the optical Q
(user concern: wider beam -> more optical modes). w = 650 first (target-relevant), then 600.
Per (w, min feature):
  60 nm: cell hx/a 0.53, hy/w 0.77 (same ratios as the w550 mf60 cell), base shape xi 4 / chi 3.5
  80 nm: cell B hx/a 0.45, hy/w 0.70 (cell A has no taper freedom at 80 nm), base shape xi 4 / chi 3.5
Steps: per d, bracket 619.4 nm adaptively in a (slope ~2.3 nm of wavelength per nm of a), then the
619 nm line, (xi, chi) shapes on it (<= 8, strongest pull first), finalize (best1/best2).
Data: runs/cavity_619_width/<label>/data, label = w<w>_mf<mf>.
Run via:  python scripts/remote_runner.py runs/cavity_619_width/run.py
"""
import numpy as np
from cavity_pipeline import Pipeline, p, LAM0

SLOPE = 2.3
D_LIST = [0.10, 0.13, 0.16]
CELLS = {60: dict(hx_a=0.53, hy_w=0.77), 80: dict(hx_a=0.45, hy_w=0.70)}
A_GUESS = {650: 185.0, 600: 190.0}
BASE = (4.0, 3.5)


def bracket(P, d, a0):
    """Solve ad_ points along a at this d until 619.4 nm is bracketed (<= 5 solves)."""
    xi, chi = BASE
    R = {}
    a = round(a0)
    for _ in range(5):
        while not P.feasible(P.cfg(a, d, xi, chi))[0] and a < 240:
            a += 5                                         # bridges grow with a
        fn = P.dd / f'ad_a{a}_d{int(round(d*100)):02d}.npz'
        r = P.point(P.cfg(a, d, xi, chi), fn, dict(a=a, d=d, xi=xi, chi=chi))
        if r is None:
            break
        R[a] = r['lam']
        L = list(R.values())
        if min(L) < LAM0 < max(L):
            break
        step = (LAM0 - r['lam']) / SLOPE
        step = np.sign(step) * max(3.0, min(abs(step) * 1.3, 25.0))   # overshoot a little to bracket
        a_new = int(round(a + step))
        if a_new in R:
            a_new += int(np.sign(step)) * 3
        a = a_new
    p(f'[{P.label}] d {d}: ' + ', '.join(f'a {k}: {v:.1f} nm' for k, v in sorted(R.items())))
    ok = [k for k, v in R.items()]
    return float(np.interp(LAM0, *zip(*sorted((v, k) for k, v in R.items())))) if len(ok) >= 2 else a0


for w in (650, 600):
    for mf in (60, 80):
        label = f'w{w}_mf{mf}'
        P = Pipeline(f'runs/cavity_619_width/{label}', dict(w=w, t=120, **CELLS[mf]), mf, label)
        try:
            a_next = A_GUESS[w]
            for d in D_LIST:
                a_next = bracket(P, d, a_next) + 4.0       # 619 a grows ~5 nm per 0.03 in d
            line = P.line(D_LIST)
            P.shapes(line, [2, 4, 6, 8], [3.0, 3.5, 4.0, 4.5, 5.0], max_shapes=8)
            P.finalize()
        finally:
            P.close()
p('Width study done.')
