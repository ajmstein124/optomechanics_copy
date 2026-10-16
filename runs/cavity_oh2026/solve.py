"""
solve.py  (remote)  -- runs/cavity_oh2026
Solve the Oh 2026 cavity (cavity_oh2026.mph, built by build.py, user-inspected 2026-10-14):
  OP Study: TE-like class (x0 PEC, y0 PEC, z0 PMC), N_op modes around 192 THz. Q_o = Re f / (2 Im f).
  Mech Study: breathing class (Sym on x0, y0, z0), N_mode modes around 6.3 GHz.
Each mode gets a localization number = fraction of |field|^2 within |x| < X_LOC of the beam center
(cavity modes ~1, beam/waveguide/PML modes small) and, for mechanics, the y-displacement fraction
(breathing mode = mostly v). Field values on the z=0 plane are saved for the most localized modes.

Output: runs/cavity_oh2026/data/solve_op.npz, solve_mech.npz; cavity_oh2026_solved.mph (remote).

Run via:
    python scripts/remote_runner.py runs/cavity_oh2026/solve.py
"""
import sys
import time
from pathlib import Path

import mph
import numpy as np
from comsol_utils import mphglobal
from build_cavity_model import op_class, mech_class

X_LOC = '4000[nm]'
N_OP, N_MODE = 12, 30
OUT = Path('runs/cavity_oh2026/data'); OUT.mkdir(parents=True, exist_ok=True)


def p(*a):
    print(*a); sys.stdout.flush()


client = mph.start()
model = client.load('cavity_oh2026.mph')
m = model.java
comp = m.component('comp1')
for tag, sel in (('int_beam', 'sel_beam'), ('int_inner', 'sel_inner')):
    op = comp.cpl().create(tag, 'Integration'); op.selection().named(sel)
m.param().set('N_op', str(N_OP)); m.param().set('N_mode', str(N_MODE))
op_class(model, x='PEC', y='PEC', z='PMC')
mech_class(model, '+', '+', '+')
sols = [str(t) for t in m.sol().tags()]
dsets = [str(t) for t in m.result().dataset().tags()]
p(f'solvers {sols}, datasets {dsets}')


def plane_fields(dset, exprs, n):
    """Node values of exprs on the z=0 plane for solution numbers 1..n."""
    lab = m.result().dataset(dset).label()
    xs, ys, zs = (np.asarray(model.evaluate(e, dataset=lab, inner=[1])).ravel() for e in ('x', 'y', 'z'))
    on = zs < 1e-9 * 1e9 * 0.5            # geometry unit nm -> z < 0.5 nm
    out = {'x': xs[on], 'y': ys[on]}
    for e in exprs:
        out[e] = np.stack([np.asarray(model.evaluate(e, dataset=lab, inner=[i])).ravel()[on] for i in range(1, n + 1)])
    return out


# ---- optics
t0 = time.time()
m.sol('sol2').runAll()
f = mphglobal(m, 'ewfd.freq', 'dset2')
loc = np.real(mphglobal(m, f'int_inner(ewfd.normE^2*(x<{X_LOC}))/int_inner(ewfd.normE^2)', 'dset2'))
Q = np.real(f) / (2 * np.abs(np.imag(f)))
p(f'OP solved ({time.time()-t0:.0f} s): f [THz] / Q / localization')
for i, (fi, qi, li) in enumerate(zip(f, Q, loc), 1):
    p(f'  {i:2d}  {np.real(fi)/1e12:8.3f}  Q={qi:10.3g}  loc={li:.3f}')
try:
    fo = plane_fields('dset2', ['real(ewfd.Ey)'], len(f))
except Exception as e:
    p(f'field export failed: {str(e)[:200]}'); fo = {}
np.savez(str(OUT / 'solve_op.npz'), f=f, Q=Q, loc=loc, **{k.replace('(', '_').replace(')', '').replace('.', '_'): v for k, v in fo.items()})

# ---- mechanics
t0 = time.time()
m.sol('sol1').runAll()
fm = mphglobal(m, 'solid.freq', 'dset1')
locm = np.real(mphglobal(m, f'int_beam(solid.disp^2*(x<{X_LOC}))/int_beam(solid.disp^2)', 'dset1'))
vfr = np.real(mphglobal(m, 'int_beam(abs(v)^2)/int_beam(solid.disp^2)', 'dset1'))
p(f'Mech solved ({time.time()-t0:.0f} s): f [GHz] / localization / v-fraction')
for i, (fi, li, vi) in enumerate(zip(fm, locm, vfr), 1):
    p(f'  {i:2d}  {np.real(fi)/1e9:8.4f}  loc={li:.3f}  v={vi:.2f}')
try:
    fmf = plane_fields('dset1', ['solid.disp'], len(fm))
except Exception as e:
    p(f'field export failed: {str(e)[:200]}'); fmf = {}
np.savez(str(OUT / 'solve_mech.npz'), f=fm, loc=locm, vfrac=vfr, **{k.replace('.', '_'): v for k, v in fmf.items()})

model.save('cavity_oh2026_solved.mph')
p('Saved cavity_oh2026_solved.mph. Done.')
client.clear()
