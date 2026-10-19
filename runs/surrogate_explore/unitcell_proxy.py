"""
unitcell_proxy.py  (remote)  -- runs/surrogate_explore
Cheap low-fidelity proxy for the full cavity (multi-fidelity idea, 2026-10-16): for each unit cell in
surrogate_explore__cells.json (center cell j = 0 and mirror cell of every solved cavity point), solve
  mech: breathing class Y+Z+ at Gamma, 15 modes around 8 GHz
  optics: cavity family (y0 PEC, z0 PMC) at X, 20 modes from a 300 THz shift
-> runs/surrogate_explore/data/uc_<tag>.npz. Resumable. One model, parameters updated per cell.
Run via:  python scripts/remote_runner.py runs/surrogate_explore/unitcell_proxy.py
"""
import json
import time
from pathlib import Path

import numpy as np
from build_nanobeam_model import build as build_cell, class_on, op_class
from comsol_utils import mphglobal
from cavity_pipeline import p

D = Path('runs/surrogate_explore/data'); D.mkdir(parents=True, exist_ok=True)
cells = json.load(open('surrogate_explore__cells.json'))
todo = [(t, g) for t, g in cells.items() if not (D / f'uc_{t}.npz').exists()]
p(f'{len(todo)} / {len(cells)} unit cells to solve')
g0 = todo[0][1] if todo else None
if g0:
    par = {'a': f"{g0['a']}[nm]", 'w': f"{g0['w']}[nm]", 't': '120[nm]', 'hx': f"{g0['hx']}[nm]", 'hy': f"{g0['hy']}[nm]",
           'pad_y': '1.5[um]', 'pad_z': '1.5[um]', 'E_d': '1050[GPa]', 'nu_d': '0.07', 'rho_d': '3500[kg/m^3]', 'n_d': '2.41',
           'kx': '0[1/m]', 'f_mech': '8[GHz]', 'N_mode': '15', 'f_op': '300[THz]', 'N_op': '20'}
    client, model = build_cell(par, hole=True, name='uc_proxy')
    m = model.java
    sol_op = [str(t) for t in m.sol().tags()][-1]
    class_on(model, '+', '+'); op_class(model, y='PEC', z='PMC')
    t0 = time.time()
    for i, (tag, g) in enumerate(todo, 1):
        try:
            for k_ in ('a', 'w', 'hx', 'hy'):
                m.param().set(k_, f'{g[k_]}[nm]')
            m.param().set('kx', '0[1/m]')
            m.sol('sol1').runAll()
            fm = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1')))[:15]
            kX = np.pi / (g['a'] * 1e-9)
            m.param().set('kx', f'{kX}[1/m]')
            m.sol(sol_op).runAll()
            fo = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2'))); fo = fo[fo > 1e12][:20]
            ll = 299792458.0 * kX / (2 * np.pi)
            np.savez(str(D / f'uc_{tag}.npz'), f_mech_G=fm, f_opt_X=fo, light_line_X=ll, **g)
            if i % 10 == 0 or i == 1:
                gd = fo[fo < ll]
                p(f'{i}/{len(todo)} {tag}: Gamma ' + ', '.join(f'{f/1e9:.2f}' for f in fm[:4]) +
                  ' GHz | X guided ' + ', '.join(f'{f/1e12:.0f}' for f in gd[:3]) + f' THz ({time.time()-t0:.0f} s)')
        except Exception as e:
            p(f'{i} {tag}: FAILED {str(e)[:200]}')
    client.clear()
p('unit-cell proxy done.')
