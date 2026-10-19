"""
run_w700_lockx.py  (remote)  -- runs/cavity_619_width
80 nm device with the hole x fill fraction locked to the period (user 2026-10-16): taper the period and the hole height
as before, but hx_j = (hx/a)_mirror * a_j (cavity_taper.layout lock_x=True), so center bridges shrink only by (1 - d).
Feasibility (Mac): mirror hx/a 0.50, hy/w 0.77 at w 700 -> base bridge 83 nm, 40 / 48 (d, xi, chi) shapes >= 80 nm
(vs 4 with the normal taper). Starts after run_w700_cells.py reaches '80 nm improvement chain done'.
  1. mirror-cell check at a 188 (Gamma + X; lock_x does not change the mirror cell)
  2. pipeline w700_mf80_LX: d 0.10 / 0.13 / 0.16 bracketed with the base shape, up to 10 shapes, finalize
diamond_a_large is TABLED (user 2026-10-16; its launcher renamed to diamond_a_large__sweep.py.tabled).
Run via:  python scripts/remote_runner.py runs/cavity_619_width/run_w700_lockx.py
"""
import time
from pathlib import Path

import numpy as np
from build_nanobeam_model import build as build_cell, class_on, op_class
from cavity_pipeline import Pipeline, p
from comsol_utils import mphglobal

ROOT = Path(r'C:\Users\abby\comsol')
CELL = dict(w=700, t=120, hx_a=0.50, hy_w=0.77, lock_x=True)
t0 = time.time()

LOGF = ROOT / 'job_log_cavity_619_width__run_w700_cells.txt'
while (not LOGF.exists()) or '80 nm improvement chain done' not in LOGF.read_text(errors='ignore'):
    if time.time() - t0 > 12 * 3600:
        p('waited 12 h for run_w700_cells; starting anyway'); break
    time.sleep(120)
p(f'lock_x start ({time.time()-t0:.0f} s wait)')


def mirror_check(cell, D, a=186.0):
    fn = D / 'mirror_check.npz'
    if fn.exists():
        return
    par = {'a': f'{a}[nm]', 'w': f"{cell['w']}[nm]", 't': f"{cell['t']}[nm]", 'hx': f"{cell['hx_a'] * a}[nm]",
           'hy': f"{cell['hy_w'] * cell['w']}[nm]", 'pad_y': '1.5[um]', 'pad_z': '1.5[um]', 'E_d': '1050[GPa]',
           'nu_d': '0.07', 'rho_d': '3500[kg/m^3]', 'n_d': '2.41', 'kx': '0[1/m]', 'f_mech': '8[GHz]', 'N_mode': '15',
           'f_op': '300[THz]', 'N_op': '30'}
    client, model = build_cell(par, hole=True, name=f'mirror_{D.parent.name}')
    m = model.java
    sol_op = [str(t) for t in m.sol().tags()][-1]
    ks = np.array([0.0, np.pi / (a * 1e-9)])
    fo = np.full((len(ks), 2, 30), np.nan); fm = np.full((len(ks), 15), np.nan)
    class_on(model, '+', '+')
    for ik, k in enumerate(ks):
        m.param().set('kx', f'{k}[1/m]')
        for iy, yc in enumerate(('PEC', 'PMC')):
            op_class(model, y=yc, z='PMC')
            m.sol(sol_op).runAll()
            f = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2'))); f = f[f > 1e12][:30]
            fo[ik, iy, :len(f)] = f
        m.sol('sol1').runAll()
        g = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1')))[:15]
        fm[ik, :len(g)] = g
    np.savez(str(fn), a=a, k=ks, f_opt=fo, opt_classes=np.array(['y0 PEC (cavity)', 'y0 PMC']), f_mech_YpZp=fm, **{k: v for k, v in cell.items() if k != 'lock_x'})
    client.clear()
    ll = 299792458.0 * ks[-1] / (2 * np.pi)
    for iy, name in enumerate(('y0 PEC (cavity)', 'y0 PMC (higher order)')):
        guided = [f for f in fo[-1, iy] if np.isfinite(f) and f < ll]
        p(f'[{D.parent.name}] mirror {name}: guided at X ' + ', '.join(f'{f/1e12:.0f}' for f in guided[:4]) + ' THz (619 nm = 484 THz)')
    p(f'[{D.parent.name}] mirror Y+Z+ Gamma: ' + ', '.join(f'{f/1e9:.2f}' for f in fm[0, :4]) +
      ' GHz; X: ' + ', '.join(f'{f/1e9:.2f}' for f in fm[1, :4]) + f' GHz ({time.time()-t0:.0f} s)')



rd = Path('runs/cavity_619_width/w700_mf80_LX'); D = rd / 'data'; D.mkdir(parents=True, exist_ok=True)
try:
    mirror_check(CELL, D, a=188.0)
except Exception as e:
    p(f'[LX] mirror check failed: {str(e)[:300]}')
P = Pipeline(str(rd), CELL, 80, 'w700_mf80_LX')
try:
    a_next = 188.0
    for d in (0.10, 0.13, 0.16):
        a_next = P.bracket(d, a_next, (4.0, 3.5)) + 3.0
    line = P.line([0.10, 0.13, 0.16])
    P.shapes(line, [2, 4, 6, 8], [3.0, 3.5, 4.0, 4.5, 5.0], max_shapes=10)
    P.finalize()
finally:
    P.close()
p(f'lock_x pipeline done ({time.time()-t0:.0f} s).')
