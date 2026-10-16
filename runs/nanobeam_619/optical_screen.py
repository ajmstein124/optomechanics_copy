"""
optical_screen.py  (remote)
Stage 1 of the 619 nm / 10 GHz nanobeam design: TE-like optical modes at the X point only
(y=0 PEC, z=0 PMC -- the class validated against Oh 2026 Fig 1d) for a grid of
(w, a, hx/a, hy/w) at t = 120 nm, n_diamond = 2.41 (619 nm), air pad 1.5 um.
Widest w first. Guided = below the air light line at X, f < c/(2a).

Eigen-solver shift: F_SHIFT = 300 THz (BELOW the guided TE bands). A shift near the target (480 THz)
let the many air-box modes above the light line crowd guided band 1 out of the N_op closest
modes at large a (first launch, 2026-10-14) -> wrong gaps. Shift only selects WHICH modes are
returned, never their frequencies; shift_check() verifies that on the first combo.
Combos with < 2 guided bands found are flagged 'incomplete'.
Spurious ~0 Hz modes (static gradient solutions of the curl-curl EM eigenproblem; six of them appear
with a low shift) are dropped (f < 1 THz); N_op = 20 so the guided bands still fit.

Output: runs/nanobeam_619/data/optX_<tag>.npz (freqs at X, light line, params). Resumable.

Run via:
    python scripts/remote_runner.py runs/nanobeam_619/optical_screen.py
"""
import itertools
import sys
import time
from pathlib import Path

import numpy as np
from build_nanobeam_model import build
from comsol_utils import mphglobal

T_NM = 120.0
W = [650, 550, 450, 350]
A = [220, 245, 270, 295]
HXA = [0.45, 0.53, 0.60]
HYW = [0.60, 0.70, 0.77]
OUT = Path('runs/nanobeam_619/data'); OUT.mkdir(parents=True, exist_ok=True)
C0 = 299792458.0
import os
N_OP = os.environ.get('N_OP', '20')   # 40 for the rerun of combos that came back incomplete
RERUN_INCOMPLETE = os.environ.get('RERUN_INCOMPLETE') == '1'


def p(*a):
    print(*a); sys.stdout.flush()


P = {'a': '245[nm]', 'w': '450[nm]', 't': f'{T_NM}[nm]', 'hx': '130[nm]', 'hy': '315[nm]',
     'pad_y': '1.5[um]', 'pad_z': '1.5[um]',
     'E_d': '1050[GPa]', 'nu_d': '0.07', 'rho_d': '3500[kg/m^3]', 'n_d': '2.41',
     'kx': '0[1/m]', 'f_mech': '8[GHz]', 'N_mode': '12', 'f_op': '300[THz]', 'N_op': N_OP}
F_SHIFT = '300[THz]'
client, model = build(P, hole=True, name='nanobeam_619')
m = model.java
for t in m.sol().tags():
    m.sol(str(t)).clearSolutionData()
model.save('nanobeam_619.mph')
p('Saved nanobeam_619.mph (template, t=120 nm)')
sol_op = [str(t) for t in m.sol().tags()][-1]

combos = list(itertools.product(W, A, HXA, HYW))


def shift_check(w, a, hxa, hyw):
    """Same combo at shift 300 vs 480 THz: modes found in both must coincide."""
    for k_, v in (('a', a), ('w', w), ('hx', hxa * a), ('hy', hyw * w)):
        m.param().set(k_, f'{v}[nm]')
    m.param().set('kx', f'{np.pi / (a * 1e-9)}[1/m]')
    res = {}
    for sh in ('300[THz]', '480[THz]'):
        m.param().set('f_op', sh)
        m.sol(sol_op).runAll()
        r = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2'))) / 1e12
        res[sh] = r[r > 1.0]
    m.param().set('f_op', F_SHIFT)
    lo, hi = res['300[THz]'], res['480[THz]']
    common = [(x, hi[np.argmin(np.abs(hi - x))]) for x in lo if np.min(np.abs(hi - x)) < 1.0]
    dev = max(abs(x - y) / x for x, y in common) if common else float('nan')
    p(f'SHIFT CHECK {w}/{a}/{hxa}/{hyw}: shift 300 -> ' + ', '.join(f'{x:.2f}' for x in lo[:8]))
    p(f'                              shift 480 -> ' + ', '.join(f'{x:.2f}' for x in hi[:8]))
    p(f'  {len(common)} modes found by both; max relative difference {dev:.1e}')


if not RERUN_INCOMPLETE:
    shift_check(650, 295, 0.45, 0.60)      # the combo that exposed the problem
t0 = time.time()
for i, (w, a, hxa, hyw) in enumerate(combos, 1):
    tag = f'w{w}_a{a}_hx{int(round(hxa*100))}_hy{int(round(hyw*100))}'
    fn = OUT / f'optX_{tag}.npz'
    if fn.exists():
        if RERUN_INCOMPLETE and np.load(fn)['guided_THz'].size < 2:
            pass                      # redo with more modes
        else:
            continue
    hx, hy = hxa * a, hyw * w
    bridge, rail = a - hx, (w - hy) / 2
    for k_, v in (('a', a), ('w', w), ('hx', hx), ('hy', hy)):
        m.param().set(k_, f'{v}[nm]')
    kX = np.pi / (a * 1e-9)
    m.param().set('kx', f'{kX}[1/m]')
    try:
        m.sol(sol_op).runAll()
        f = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2')))
        n_spurious = int((f < 1e12).sum())
        f = f[f >= 1e12]
    except Exception as e:
        p(f'{i}/{len(combos)} {tag}: FAILED {str(e)[:200]}')
        continue
    ll = C0 / (2 * a * 1e-9)
    g = f[f < ll] / 1e12
    np.savez(str(fn), N_op=int(N_OP), freqs_X=f, light_line_X=ll, guided_THz=g, shift_THz=300.0, n_spurious=n_spurious, w=w, a=a, hx=hx, hy=hy, t=T_NM,
             hx_a=hxa, hy_w=hyw, bridge_nm=bridge, rail_nm=rail)
    gap = f'{g[0]:.0f}-{g[1]:.0f}' if g.size >= 2 else ('INCOMPLETE: ' + ', '.join(f'{x:.0f}' for x in g) if g.size else 'INCOMPLETE: none')
    hit = g.size >= 2 and g[0] < 484 < g[1]
    p(f'{i}/{len(combos)} {tag}: guided at X {gap} THz (light line {ll/1e12:.0f}) '
      f'{"<-- contains 484" if hit else ""}  ({time.time()-t0:.0f} s)')
client.clear()
p('Optical screen done.')
