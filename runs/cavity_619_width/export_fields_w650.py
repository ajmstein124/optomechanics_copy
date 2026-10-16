"""
export_fields_w650.py  (remote)  -- runs/cavity_619_width
Field maps of the two w650 / 60 nm finalists (user slides, 2026-10-15):
  ad    : d 0.13, a 194.0, xi 4 / chi 3.5 (base shape; 619.5 nm, Q 3.0e7, breathing 9.82 GHz) -- re-solved here,
          saved as pick_w650_mf60_ad_d13.mph
  shape : best1_w650_mf60.mph (d 0.10, xi 6, chi 4.0, a 190.3; 619.5 nm, Q 1.8e7, 9.67 GHz) -- stored solution
Output: runs/cavity_619_width/w650_mf60/data/fields_{ad,shape}.npz
Run via:  python scripts/remote_runner.py runs/cavity_619_width/export_fields_w650.py
"""
from pathlib import Path

import mph
import numpy as np
from cavity_fields import export, p
from cavity_pipeline import Pipeline

D = Path('runs/cavity_619_width/w650_mf60/data')

client = mph.start()
model = client.load('best1_w650_mf60.mph')
export(model.java, np.load(D / 'best1_w650_mf60.npz'), 'shape', D)
client.clear()

P = Pipeline('runs/cavity_619_width/w650_mf60', dict(w=650, t=120, hx_a=0.53, hy_w=0.77), 60, 'w650_mf60')
try:
    fn = D / 'pick_ad_d13.npz'
    P.solve(P.cfg(194.0, 0.13, 4.0, 3.5), fn, dict(a=194.0, d=0.13, xi=4.0, chi=3.5))
    P.model.save('pick_w650_mf60_ad_d13.mph')
    export(P.model.java, np.load(fn), 'ad', D)
finally:
    P.close()
p('Field export done.')
