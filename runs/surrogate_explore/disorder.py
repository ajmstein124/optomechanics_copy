"""
disorder.py  (remote)  -- runs/surrogate_explore
Fabrication-disorder robustness (2026-10-17): per-hole Gaussian disorder s_hx = s_hy = 2 nm, hole position s_x = 1 nm
(build_cavity_model.perturb; symmetric about the 1/8-model symmetry planes), 8 seeds per design, for
  final60 : current 60 nm final (w650, .53/.77, d .10, xi 6, chi 4, a 190.3)
  final80 : current 80 nm final (w700, .45/.70, d .10, xi 4, chi 3.5, a 182.8)
  bo2_0   : best BO 80 nm design (gentle taper, w713)
Question: are the gentle-taper high-Q designs fragile? Output data/dis_<design>_s<seed>.npz. Waits for confirm_fields.
"""
import json
import time
from pathlib import Path

import numpy as np
from cavity_pipeline import Pipeline, p

ROOT = Path(r'C:\Users\abby\comsol')
D = Path('runs/surrogate_explore/data')
t0 = time.time()
LOGF = ROOT / 'job_log_surrogate_explore__confirm_fields.txt'
while (not LOGF.exists()) or 'confirm fields done' not in LOGF.read_text(errors='ignore'):
    if time.time() - t0 > 6 * 3600:
        break
    time.sleep(60)
base = dict(t=120, M=10, n_mirror=10, eta=1.0, pad_x=1000)
DES = {
    'final60': dict(base, a_m=190.3, w=650, hx_m=round(0.53 * 190.3, 3), hy_m=round(0.77 * 650, 3), d=0.10, xi=6.0, chi=4.0),
    'final80': dict(base, a_m=182.8, w=700, hx_m=82.278, hy_m=490.0, d=0.10, xi=4.0, chi=3.5),
    'bo2_0': json.loads(str(np.load(D / 'bo2_0.npz', allow_pickle=True)['cfg'])),
}
DIS = dict(s_hx=2.0, s_hy=2.0, s_x=1.0)
c0 = DES['final80']
P = Pipeline('runs/surrogate_explore', dict(w=c0['w'], t=120, hx_a=0.45, hy_w=0.70), 0.0, 'disorder')
try:
    for seed in range(8):
        for name, cfg in DES.items():
            fn = D / f'dis_{name}_s{seed}.npz'
            c = dict(cfg, dis=dict(DIS, seed=1000 + seed))
            r = P.point(c, fn, dict(design=name, seed=seed))
            p(f'[dis] {name} seed {seed}: {r} ({time.time()-t0:.0f} s)')
finally:
    P.close()
p('disorder done.')
