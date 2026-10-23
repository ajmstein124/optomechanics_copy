"""
gap_cells.py  (remote)  -- runs/surrogate_explore
Mechanical-gap study (user 2026-10-19: the breathing mode must sit INSIDE the mirror cell's breathing-class (Y+Z+) gap).
For each unit cell in surrogate_explore__gapcells.json (mirror-type and center-type cells, incl. different widths for a
width taper), solve
  mech  Y+Z+ at k = 0, 0.25, 0.5, 1 (pi/a), 12 modes around 8 GHz   -> gap top = lowest band-2+ value over k
  optics cavity family (y0 PEC, z0 PMC) at X, 20 modes from 300 THz
-> runs/surrogate_explore/data/ucg_<tag>.npz. Resumable. One model; parameters updated per cell.
Run via:  python scripts/remote_runner.py runs/surrogate_explore/gap_cells.py
"""
import json
import time
from pathlib import Path

import numpy as np
from build_nanobeam_model import build as build_cell, class_on, op_class
from comsol_utils import mphglobal
from cavity_pipeline import p

D = Path('runs/surrogate_explore/data'); D.mkdir(parents=True, exist_ok=True)
cells = json.load(open('surrogate_explore__gapcells.json'))
todo = [(t, g) for t, g in cells.items() if not (D / f'ucg_{t}.npz').exists()]
p(f'{len(todo)} / {len(cells)} gap cells to solve')
KF = [0.0, 0.25, 0.5, 1.0]
if todo:
    g0 = todo[0][1]
    par = {'a': f"{g0['a']}[nm]", 'w': f"{g0['w']}[nm]", 't': '120[nm]', 'hx': f"{g0['hx']}[nm]", 'hy': f"{g0['hy']}[nm]",
           'pad_y': '1.5[um]', 'pad_z': '1.5[um]', 'E_d': '1050[GPa]', 'nu_d': '0.07', 'rho_d': '3500[kg/m^3]', 'n_d': '2.41',
           'kx': '0[1/m]', 'f_mech': '8[GHz]', 'N_mode': '12', 'f_op': '300[THz]', 'N_op': '20'}
    client, model = build_cell(par, hole=True, name='uc_gap')
    m = model.java
    sol_op = [str(t) for t in m.sol().tags()][-1]
    class_on(model, '+', '+'); op_class(model, y='PEC', z='PMC')
    t0 = time.time()
    for i, (tag, g) in enumerate(todo, 1):
        try:
            for k_ in ('a', 'w', 'hx', 'hy'):
                m.param().set(k_, f'{g[k_]}[nm]')
            kX = np.pi / (g['a'] * 1e-9)
            fm = np.full((len(KF), 12), np.nan)
            for ik, kf in enumerate(KF):
                m.param().set('kx', f'{kf * kX}[1/m]')
                m.sol('sol1').runAll()
                f = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1')))[:12]
                fm[ik, :len(f)] = f
            m.param().set('kx', f'{kX}[1/m]')
            m.sol(sol_op).runAll()
            fo = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2'))); fo = fo[fo > 1e12][:20]
            ll = 299792458.0 * kX / (2 * np.pi)
            np.savez(str(D / f'ucg_{tag}.npz'), k_frac=np.array(KF), f_mech=fm, f_opt_X=fo, light_line_X=ll, **g)
            if i % 10 == 0 or i == 1:
                p(f'{i}/{len(todo)} {tag}: Gamma ' + ', '.join(f'{f/1e9:.2f}' for f in fm[0, :3]) + f' GHz ({time.time()-t0:.0f} s)')
        except Exception as e:
            p(f'{i} {tag}: FAILED {str(e)[:200]}')
    client.clear()
p('gap cells done.')
