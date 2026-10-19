"""
validate_swa.py  (remote)  -- runs/sidewall
Sidewall-angle model check (2026-10-18). Full-thickness 1/4 model (build_cavity_model: cfg['swa'] -> sloped beam sidewalls +
tapered elliptic holes, mask = top surface): bo2_0 (best BO 80 nm design) at swa 0 (must reproduce the 1/8 model: 619.32 nm,
Q 2.15e7, breathing 9.84 GHz), then the same mask at 5 and 10 deg. Output runs/sidewall/data/val_swa<deg>.npz.
"""
import json
import time
from pathlib import Path

import numpy as np
from cavity_pipeline import Pipeline, p

D = Path('runs/sidewall/data'); D.mkdir(parents=True, exist_ok=True)
c = json.loads(str(np.load('runs/surrogate_explore/data/confirm_bo2_0.npz', allow_pickle=True)['cfg']))
P = Pipeline('runs/sidewall', dict(w=c['w'], t=120, hx_a=c['hx_m'] / c['a_m'], hy_w=c['hy_m'] / c['w']), 0.0, 'swa_full', swa=0.0)
t0 = time.time()
try:
    for swa in (0.0, 5.0, 10.0):
        r = P.point(dict(c, swa=swa), D / f'val_swa{swa:g}.npz', dict(swa=swa))
        p(f'[val] swa {swa:g}: {r} ({time.time()-t0:.0f} s)')
finally:
    P.close()
p('validate_swa done.')
