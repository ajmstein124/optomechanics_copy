"""
build.py  (remote)  -- runs/cavity_619
Build (no solve) the 619 nm / ~10 GHz full cavity, 1/8 model, for GUI inspection: cavity_619.mph.
Mirror cell = stage-2 favored candidate (runs/nanobeam_619): w 550, a 220, hx/a 0.53, hy/w 0.77, t 120.
Taper = Oh 2026 shape measured from his Fig. 1(b) (d 0.18, M 10, eta 1, xi 6, chi 3.5, 10 mirror cells);
this is the template the (a, d) sweep re-lays out via build_cavity_model.set_layout().
Same setup as the validated Oh cavity (runs/cavity_oh2026); n = 2.41 at 619 nm.

Run via:
    python scripts/remote_runner.py --block runs/cavity_619/build.py
"""
import json
import sys
from pathlib import Path

from build_cavity_model import build

A, W = 220, 550
CFG = dict(a_m=A, w=W, t=120, hx_m=round(0.53 * A, 3), hy_m=round(0.77 * W, 3),
           M=10, n_mirror=10, d=0.18, eta=1.0, xi=6.0, chi=3.5,
           pad_x=1000, pad_y=1000, pad_z=1000, d_pml=800,
           h_beam='t/5', h_air='c_const/f_op/6',
           E_d='1050[GPa]', nu_d='0.07', rho_d='3500[kg/m^3]', n_d='2.41',
           f_mech='9[GHz]', f_op='484[THz]', N_mode='30', N_op='12')

client, model, lay = build(CFG, name='cavity_619')
m = model.java
for t in m.sol().tags():
    m.sol(str(t)).clearSolutionData()
model.save('cavity_619.mph')
out = Path('runs/cavity_619/data'); out.mkdir(parents=True, exist_ok=True)
json.dump(dict(cfg=CFG, layout={k: [float(v) for v in lay[k]] for k in ('x', 'a', 'hx', 'hy')}),
          open(out / 'build_info.json', 'w'), indent=1)
print('Saved cavity_619.mph'); sys.stdout.flush()
client.clear()
