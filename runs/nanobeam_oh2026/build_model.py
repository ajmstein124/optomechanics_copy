"""
build_model.py  (remote)
Build the nanobeam quarter-cell model at the Oh et al. 2026 mirror-cell dimensions
(a, w, hx, hy, t) = (650, 800, 343, 617, 250) nm, isotropic diamond (user decision), air pad 1.5 um,
then do ONE quick k=0 solve per symmetry class as a smoke test, and save
nanobeam_oh2026.mph (no solution stored) for GUI inspection.

Run via:
    python scripts/remote_runner.py --block runs/nanobeam_oh2026/build_model.py
"""
import sys
import time

import numpy as np
from build_nanobeam_model import build, class_on
from comsol_utils import mphglobal

P = {
    'a': '650[nm]', 'w': '800[nm]', 't': '250[nm]', 'hx': '343[nm]', 'hy': '617[nm]',
    'pad_y': '1.5[um]', 'pad_z': '1.5[um]',
    'E_d': '1050[GPa]', 'nu_d': '0.07', 'rho_d': '3500[kg/m^3]', 'n_d': '2.41',
    'kx': '0[1/m]', 'f_mech': '3[GHz]', 'N_mode': '12', 'f_op': '200[THz]', 'N_op': '10',
}

client, model = build(P, hole=True, name='nanobeam_oh2026')
m = model.java
for yc, zc in (('+', '+'), ('-', '+'), ('+', '-'), ('-', '-')):
    class_on(model, yc, zc)
    t0 = time.time()
    m.sol('sol1').runAll()
    f = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1'))) / 1e9
    print(f'class Y{yc} Z{zc} at Gamma ({time.time()-t0:.1f} s): ' + ', '.join(f'{x:.3f}' for x in f) + ' GHz')
    sys.stdout.flush()
class_on(model, '+', '+')
# optical smoke test at X (TE-like: y PEC, z PMC)
import numpy as _np
m.param().set('kx', f'{_np.pi/650e-9}[1/m]')
sol_op = [str(t) for t in m.sol().tags()][-1]
t0 = time.time()
m.sol(sol_op).runAll()
fo = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2'))) / 1e12
print(f'optical TE-like at X ({time.time()-t0:.1f} s, solver {sol_op}): ' + ', '.join(f'{x:.1f}' for x in fo) + ' THz')
m.param().set('kx', '0[1/m]')
for t in m.sol().tags():
    m.sol(str(t)).clearSolutionData()
model.save('nanobeam_oh2026.mph')
print('Saved C:/Users/abby/comsol/nanobeam_oh2026.mph')
client.clear()
