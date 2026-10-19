"""
confirm_fields.py  (remote)  -- runs/surrogate_explore
Re-solve the best 80 nm BO candidates (exact cfg from their bo*.npz) and export optical Ey/|E| and breathing-mode
displacement on cut planes (user rule: look at the deformed mode before calling a design best).
Output: data/fields_<name>.npz (+ confirm_<name>.npz solve, confirm_<name>.mph). xmax 6 um (broad gentle-taper modes).
"""
import json
from pathlib import Path

import numpy as np
from cavity_fields import export, p
from cavity_pipeline import Pipeline

D = Path('runs/surrogate_explore/data')
NAMES = ['bo2_0', 'bo1_2', 'bo2_6']
cfgs = {n: json.loads(str(np.load(D / f'{n}.npz', allow_pickle=True)['cfg'])) for n in NAMES}
c0 = cfgs[NAMES[0]]
P = Pipeline('runs/surrogate_explore', dict(w=c0['w'], t=120, hx_a=c0['hx_m'] / c0['a_m'], hy_w=c0['hy_m'] / c0['w']), 79.5,
             'confirm', n_mirror=10, M=10)
try:
    for n in NAMES:
        fn = D / f'confirm_{n}.npz'
        if not fn.exists():
            P.solve(cfgs[n], fn, dict(name=n))
        P.model.save(f'confirm_{n}.mph')
        export(P.model.java, np.load(fn, allow_pickle=True), n, D, xmax=6000.0)
finally:
    P.close()
p('confirm fields done.')
