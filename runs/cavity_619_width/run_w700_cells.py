"""
run_w700_cells.py  (remote)  -- runs/cavity_619_width
Improve the 80 nm device (user 2026-10-16). At w 700 the binding 80 nm feature is the center bridges, not the rails
(cell B hy/w 0.70 leaves 105 nm rails), so enlarge the holes:
  C1: hx/a 0.45, hy/w 0.77 (rails 80.5 nm; bridges unchanged vs cell B)
  C2: hx/a 0.48, hy/w 0.77
  1. per cell: mirror-cell check at a 186, k = Gamma and X only: optics in both y-parities (y0 PEC cavity family,
     y0 PMC higher-order family) + breathing-class (Y+Z+) mechanics -> <run>/data/mirror_check.npz
  2. per cell: pipeline (d 0.10 / 0.13 bracketed to 619.4 nm with the base shape, up to 8 taper shapes, finalize)
  3. mirror-length test: the best 80 nm design (cell B final, C1, C2; breathing <= 10 GHz first, then highest Q)
     re-solved with n_mirror 15 instead of 10 -> <run>/data/n15_<label>.npz
  4. resume diamond_a_large (finished combos are skipped), log job_log_diamond_a_large__sweep.txt
Run via:  python scripts/remote_runner.py runs/cavity_619_width/run_w700_cells.py
"""
import json
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
CELLS = {'C1': dict(w=700, t=120, hx_a=0.45, hy_w=0.77),
         'C2': dict(w=700, t=120, hx_a=0.48, hy_w=0.77)}
t0 = time.time()


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
    np.savez(str(fn), a=a, k=ks, f_opt=fo, opt_classes=np.array(['y0 PEC (cavity)', 'y0 PMC']), f_mech_YpZp=fm, **cell)
    client.clear()
    ll = 299792458.0 * ks[-1] / (2 * np.pi)
    for iy, name in enumerate(('y0 PEC (cavity)', 'y0 PMC (higher order)')):
        guided = [f for f in fo[-1, iy] if np.isfinite(f) and f < ll]
        p(f'[{D.parent.name}] mirror {name}: guided at X ' + ', '.join(f'{f/1e12:.0f}' for f in guided[:4]) + ' THz (619 nm = 484 THz)')
    p(f'[{D.parent.name}] mirror Y+Z+ Gamma: ' + ', '.join(f'{f/1e9:.2f}' for f in fm[0, :4]) +
      ' GHz; X: ' + ', '.join(f'{f/1e9:.2f}' for f in fm[1, :4]) + f' GHz ({time.time()-t0:.0f} s)')


# 1 + 2. per cell: mirror check, then the pipeline
for name, cell in CELLS.items():
    rd = Path(f'runs/cavity_619_width/w700_mf80_{name}')
    D = rd / 'data'; D.mkdir(parents=True, exist_ok=True)
    try:
        mirror_check(cell, D)
    except Exception as e:
        p(f'[{name}] mirror check failed: {str(e)[:300]}')
    P = Pipeline(str(rd), cell, 80, f'w700_mf80_{name}')
    try:
        a_next = 186.0
        for d in (0.10, 0.13):
            a_next = P.bracket(d, a_next, (4.0, 3.5)) + 3.0
        line = P.line([0.10, 0.13])
        P.shapes(line, [2, 4, 6, 8], [3.0, 3.5, 4.0, 4.5, 5.0], max_shapes=8)
        P.finalize()
    except Exception as e:
        p(f'[{name}] pipeline failed: {str(e)[:300]}')
    finally:
        P.close()
p(f'cell pipelines done ({time.time()-t0:.0f} s)')

# 3. mirror-length test on the best 80 nm design
B = []
fj = Path('runs/cavity_619_final/data/final_80nm.json')
if fj.exists():
    c = json.load(open(fj)); c['cell'].update(t=120)
    B.append(dict(label='w700_mf80', rd='runs/cavity_619_width/w700_mf80', cell=dict(w=c['cell']['w'], t=120,
              hx_a=c['cell']['hx_a'], hy_w=c['cell']['hy_w']), d=c['d'], xi=c['xi'], chi=c['chi'], a=c['a'], Q=c['Q'], fb=c['fb']))
for name, cell in CELLS.items():
    fc = Path(f'runs/cavity_619_width/w700_mf80_{name}/data/candidates.json')
    if fc.exists():
        for c in json.load(open(fc)).get('all', []):
            if np.isfinite(c.get('fb', np.nan)):
                B.append(dict(label=f'w700_mf80_{name}', rd=f'runs/cavity_619_width/w700_mf80_{name}', cell=cell, **c))
if B:
    ok = [b for b in B if b['fb'] <= 10.0]
    b = max(ok, key=lambda b: b['Q']) if ok else min(B, key=lambda b: b['fb'])
    p(f"n_mirror 15 test on {b['label']} d {b['d']} xi {b['xi']} chi {b['chi']} a {b['a']:.1f} (n10: Q {b['Q']:.2g}, {b['fb']:.2f} GHz)")
    P = Pipeline(b['rd'], b['cell'], 80, b['label'] + '_n15', n_mirror=15)
    try:
        r = P.point(P.cfg(b['a'], b['d'], b['xi'], b['chi']), P.dd / f"n15_{b['label']}.npz",
                    dict(a=b['a'], d=b['d'], xi=b['xi'], chi=b['chi'], n_mirror=15))
        p(f'n_mirror 15 result: {r}')
    except Exception as e:
        p(f'n_mirror 15 test failed: {str(e)[:300]}')
    finally:
        P.close()
p(f'80 nm improvement chain done ({time.time()-t0:.0f} s).')

# 4. resume diamond_a_large (own log)
script = ROOT / 'diamond_a_large__sweep.py'
if script.exists():
    p('--- resuming diamond_a_large')
    with open(ROOT / 'job_log_diamond_a_large__sweep.txt', 'a') as lf:
        subprocess.run([PY, '-u', str(script)], cwd=str(ROOT), stdout=lf, stderr=subprocess.STDOUT)
    p('diamond_a_large finished (see job_log_diamond_a_large__sweep.txt).')
p('All done.')
