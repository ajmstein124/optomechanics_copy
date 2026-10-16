"""
build.py  (remote)  -- runs/cavity_oh2026
Build (no solve) the full Oh 2026 cavity, 1/8 model, for GUI inspection: saves cavity_oh2026.mph
in C:\\Users\\abby\\comsol. Start values: mirror cell from Oh Fig. 1(a); taper measured from Fig. 1(b)
(runs/nanobeam_oh2026/reference/oh2026_cavity_profile.json). n = 2.39 (best match in the mirror-cell
optical reproduction).

Run via:
    python scripts/remote_runner.py --block runs/cavity_oh2026/build.py
"""
import json
import sys
from pathlib import Path

from build_cavity_model import build

CFG = dict(a_m=650, w=800, t=250, hx_m=343, hy_m=617,
           M=10, n_mirror=10, d=0.18, eta=1.0, xi=6.0, chi=3.5,
           pad_x=1000, pad_y=1000, pad_z=1000, d_pml=800,
           h_beam='t/5', h_air='c_const/f_op/6',
           E_d='1050[GPa]', nu_d='0.07', rho_d='3500[kg/m^3]', n_d='2.39',
           f_mech='6.3[GHz]', f_op='192[THz]', N_mode='10', N_op='10')

client, model, lay = build(CFG, name='cavity_oh2026')
m = model.java
for t in m.sol().tags():
    m.sol(str(t)).clearSolutionData()
model.save('cavity_oh2026.mph')
out = Path('runs/cavity_oh2026/data'); out.mkdir(parents=True, exist_ok=True)
json.dump(dict(cfg=CFG, layout={k: [float(v) for v in lay[k]] for k in ('x', 'a', 'hx', 'hy')}),
          open(out / 'build_info.json', 'w'), indent=1)
print('Saved cavity_oh2026.mph'); sys.stdout.flush()
client.clear()
