"""
run_w700.py  (remote)  -- runs/cavity_619_width
80 nm device below 10 GHz (user 2026-10-15): w 650 gave 10.53 GHz at 80 nm (no fabricable taper beyond the
base shape), so widen to w 700, cell B (hx/a 0.45, hy/w 0.70). Runs AFTER the first deliverables + fsp builds.
  1. mirror-cell check at the expected 619 nm period (a 180): optical bands Gamma -> X in BOTH y-parities
     (y0 PEC = cavity family, y0 PMC = higher-order y-odd family; user concern: single-mode at wider w) and
     breathing-class (Y+Z+) mechanical bands -> data/mirror_check.npz
  2. pipeline w700_mf80: d 0.07 / 0.10 / 0.13 (80 nm leaves the most taper room at small d), period bracketed
     to 619.4 nm with the base shape xi 4 / chi 3.5, then up to 8 taper shapes, finalize
  3. re-run the deliverables (re-selects the 80 nm final across w 600 / 650 / 700) and the fsp builds
Run via:  python scripts/remote_runner.py runs/cavity_619_width/run_w700.py
"""
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from build_nanobeam_model import build as build_cell, class_on, op_class
from cavity_pipeline import Pipeline, p
from comsol_utils import mphglobal

PY = sys.executable
ROOT = Path(r'C:\Users\abby\comsol')
CELL = dict(w=700, t=120, hx_a=0.45, hy_w=0.70)
D = Path('runs/cavity_619_width/w700_mf80/data'); D.mkdir(parents=True, exist_ok=True)

t0 = time.time()
LOGF = ROOT / 'job_log_cavity_619_final__fsp_builds.txt'
while (not LOGF.exists()) or 'fsp builds done.' not in LOGF.read_text(errors='ignore'):
    if time.time() - t0 > 30 * 3600:
        p('waited 30 h for the fsp builds; starting anyway'); break
    time.sleep(120)
p(f'w700 start ({time.time()-t0:.0f} s wait)')

# 1. mirror-cell check
fn = D / 'mirror_check.npz'
if not fn.exists():
    a = 180.0
    par = {'a': f'{a}[nm]', 'w': f"{CELL['w']}[nm]", 't': f"{CELL['t']}[nm]", 'hx': f"{CELL['hx_a'] * a}[nm]",
           'hy': f"{CELL['hy_w'] * CELL['w']}[nm]", 'pad_y': '1.5[um]', 'pad_z': '1.5[um]', 'E_d': '1050[GPa]',
           'nu_d': '0.07', 'rho_d': '3500[kg/m^3]', 'n_d': '2.41', 'kx': '0[1/m]', 'f_mech': '8[GHz]', 'N_mode': '15',
           'f_op': '300[THz]', 'N_op': '30'}
    client, model = build_cell(par, hole=True, name='mirror_w700')
    m = model.java
    sol_op = [str(t) for t in m.sol().tags()][-1]
    ks = np.linspace(0, np.pi / (a * 1e-9), 11)
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
    np.savez(str(fn), a=a, k=ks, f_opt=fo, opt_classes=np.array(['y0 PEC (cavity)', 'y0 PMC']), f_mech_YpZp=fm, **CELL)
    client.clear()
    ll = 299792458.0 * ks / (2 * np.pi)
    for iy, name in enumerate(('y0 PEC (cavity)', 'y0 PMC (higher order)')):
        guided = [f for f in fo[-1, iy] if np.isfinite(f) and f < ll[-1]]
        p(f'mirror check {name}: guided at X ' + ', '.join(f'{f/1e12:.0f}' for f in guided[:4]) + ' THz (619 nm = 484 THz)')
    p(f'mirror check Y+Z+ at Gamma: ' + ', '.join(f'{f/1e9:.2f}' for f in fm[0, :4]) + f' GHz ({time.time()-t0:.0f} s)')

# 2. pipeline
P = Pipeline('runs/cavity_619_width/w700_mf80', CELL, 80, 'w700_mf80')
try:
    a_next = 180.0
    for d in (0.07, 0.10, 0.13):
        a_next = P.bracket(d, a_next, (4.0, 3.5)) + 3.0
    line = P.line([0.07, 0.10, 0.13])
    P.shapes(line, [2, 4, 6, 8], [3.0, 3.5, 4.0, 4.5, 5.0], max_shapes=8)
    P.finalize()
finally:
    P.close()
p('w700 pipeline done.')

# 3. deliverables (selection across widths) + fsp builds, in this process's log
for script in ('cavity_619_final__deliverables.py', 'cavity_619_final__fsp_builds.py'):
    p(f'--- {script}')
    r = subprocess.run([PY, '-u', script], cwd=str(ROOT), capture_output=True, text=True)
    p(r.stdout[-6000:]); p(r.stderr[-3000:])
p('w700 chain done.')
