"""
sweep_fill.py
=============
Fill in diamond_a_sweep combos that failed in sweep.py because the snowflake hole
crossed the (fixed 50 nm, -50/sqrt3 nm shifted) rhombus cell boundary.

Root cause (diag_geometry.py, 2026-10-14): unit_cell_3.mph subtracts ONE hole from a
rhombus whose position is set by Move 1 (mov1) with a FIXED absolute offset tuned for
Si a=478 nm. At small a / long arms the up-pointing arm crosses the cell's top edge ->
non-periodic geometry -> mesh 'Copy Face 1' "Disconnected source not allowed".

Fix: per-combo cell shift (mov1 displx/disply in BOTH wp1 slab and wp2 air) chosen by scripts/cell_placement.py +
shapely (filleted hole) to maximise hole-to-boundary clearance. For an infinite
crystal the cell placement does not change the physics; validated below.

Plan comes from fill_plan.json (computed on the Mac). Infeasible combos
(d/a=0.48, w/a=0.43: hole cannot fit any placement of the rhombus cell; bridges to
neighbouring holes 0-5 nm) are skipped and logged.

Order:
  1. VALIDATION: a200_da35_wa28 (ran OK last night, right after a failed combo)
       a) default shift  -> must reproduce saved .npz (tests no state corruption)
       b) optimal shift  -> should match to mesh tolerance (tests placement invariance)
     saved to runs/diamond_a_sweep/data/validation/
  2. The 15 feasible missing combos -> runs/diamond_a_sweep/data/ (resumable)

Before solving each combo the geometry topology is checked (2 domains, 30 boundaries,
same as every passing combo); anything else is skipped and logged.

Run via:
    python scripts/remote_runner.py runs/diamond_a_sweep/sweep_fill.py
"""

import sys
import json
import time
import numpy as np
from pathlib import Path
from comsol_utils import start_client, mphglobal

DATA = Path('runs/diamond_a_sweep/data')
VAL  = DATA / 'validation'
VAL.mkdir(parents=True, exist_ok=True)

PLAN = json.load(open('diamond_a_sweep__fill_plan.json' if Path('diamond_a_sweep__fill_plan.json').exists() else 'fill_plan.json'))

t      = 140e-9
f_r    = 16e-9
N_mode = 10
E_diamond, nu_diamond, rho_diamond = 1050e9, 0.07, 3500.0
DEFAULT_SHIFT = (50e-9, -50e-9 / np.sqrt(3))
GAP_BAND = 6
n_seg = 7


def p(*a):
    print(*a)
    sys.stdout.flush()


def kpath(a):
    G = np.array([0.0, 0.0])
    M = np.array([np.pi / a, np.pi / (a * np.sqrt(3))])
    K = np.array([4 * np.pi / (3 * a), 0.0])

    def _seg(s, e, n):
        return [s + (e - s) * i / n for i in range(n + 1)]

    raw = _seg(G, M, n_seg) + _seg(M, K, n_seg)[1:] + _seg(K, G, n_seg)[1:]
    seen, kpts = set(), []
    for kv in raw:
        key = (round(kv[0]), round(kv[1]))
        if key not in seen:
            seen.add(key)
            kpts.append((float(kv[0]), float(kv[1])))
    return kpts


def all_complete_gaps(freqs_arr):
    sb = np.sort(np.abs(np.real(freqs_arr)), axis=1) * 1e-9
    gaps = []
    for b in range(sb.shape[1] - 1):
        top, bot = sb[:, b].max(), sb[:, b + 1].min()
        if bot > top and top > 1.0:
            gaps.append((b + 1, top, bot))
    return gaps


client, model = start_client('unit_cell_3.mph')
m     = model.java
geom  = m.component('comp1').geom('geom1')
# wp1 = slab cell (pol1 minus hole), wp2 = air cell (same pol1 + same mov1). Both must move together.
movs  = [geom.feature('wp1').geom().feature('mov1'), geom.feature('wp2').geom().feature('mov1')]
solid = m.component('comp1').physics('solid')

for name, val in [('t', t), ('f_r', f_r), ('N_mode', N_mode),
                  ('scaling', 1.0), ('kFx', 0.0), ('kFy', 0.0)]:
    m.param().set(name, str(val))
m.material('mat1').propertyGroup('def').set('rho', str(rho_diamond))
m.material('mat1').propertyGroup('Enu').set('E',   str(E_diamond))
m.material('mat1').propertyGroup('Enu').set('nu',  str(nu_diamond))
m.material('mat1').propertyGroup('Enu').set('rho', str(rho_diamond))
m.material('mat1').label('Diamond')
p(f'Diamond: E={E_diamond/1e9:.0f} GPa, nu={nu_diamond}, rho={rho_diamond} kg/m^3')
for tag, mv in zip(('wp1', 'wp2'), movs):
    p(f'Original {tag}/mov1: displx={mv.getString("displx")}  disply={mv.getString("disply")}')


def run_combo(a_nm, da, wa, shift, fname, extra):
    a = a_nm * 1e-9
    d, w = da * a, wa * a
    f_mech = 10e9 * (300e-9 / a)
    m.param().set('a', str(a))
    m.param().set('f_mech', str(f_mech))
    m.param().set('d', str(d))
    m.param().set('w', str(w))
    for mv in movs:
        mv.set('displx', str(shift[0]))
        mv.set('disply', str(shift[1]))
    try:
        geom.run()
    except Exception as e:
        p(f'  !! GEOMETRY FAILED: {e}')
        return
    nd, nb = int(geom.getNDomains()), int(geom.getNBoundaries())
    p(f'  geometry: domains={nd} boundaries={nb}  shift=({shift[0]*1e9:.2f}, {shift[1]*1e9:.2f}) nm')
    if (nd, nb) != (2, 30):
        p('  !! SKIP: topology differs from every passing combo (expected 2 domains, 30 boundaries)')
        return

    kpoints = kpath(a)
    n_kpts = len(kpoints)
    freqs = np.zeros((n_kpts, 2 * N_mode))
    try:
        for ii, (kx, ky) in enumerate(kpoints):
            p(f'  k {ii+1}/{n_kpts}  kx={kx:.3e}  ky={ky:.3e}')
            m.param().set('kFx', str(kx))
            m.param().set('kFy', str(ky))
            solid.feature('as1').active(False)
            solid.feature('sym1').active(True)
            m.sol('sol1').runAll()
            freqs[ii, :N_mode] = np.real(mphglobal(m, 'solid.freq', 'dset1')[:N_mode])
            solid.feature('sym1').active(False)
            solid.feature('as1').active(True)
            m.sol('sol1').runAll()
            freqs[ii, N_mode:] = np.real(mphglobal(m, 'solid.freq', 'dset1')[:N_mode])
    except Exception as e:
        p(f'  !! FAILED: {str(e)[:1500]}')
        return

    gaps = all_complete_gaps(freqs)
    fund = [g for g in gaps if g[0] == GAP_BAND]
    gc, gw = ((fund[0][1] + fund[0][2]) / 2, fund[0][2] - fund[0][1]) if fund else (0.0, 0.0)
    p(f'  --> Band {GAP_BAND}-{GAP_BAND+1} gap: center={gc:.2f} GHz  width={gw:.2f} GHz')
    for b, lo, hi in gaps:
        p(f'      complete gap above band {b}: {lo:.2f}-{hi:.2f} GHz')
    np.savez(str(fname), freqs=freqs, kpoints=np.array(kpoints),
             a=a, d=d, w=w, t=t, f_r=f_r, da=da, wa=wa, f_mech=f_mech,
             gap_cen=gc, gap_wid=gw,
             all_gaps=np.array(gaps) if gaps else np.zeros((0, 3)),
             cell_shift=np.array(shift), **extra)
    p(f'  Saved: {fname}')


t0 = time.time()

# --- 1. Validation ------------------------------------------------------------
v = PLAN['a200_da35_wa28']
for label, shift in [('defaultshift', DEFAULT_SHIFT), ('optshift', (v['shift_x'], v['shift_y']))]:
    fname = VAL / f'sweep_a200_da35_wa28_{label}.npz'
    if fname.exists():
        p(f'\n=== VALIDATION {label}: exists, skipping ===')
        continue
    p(f'\n=== VALIDATION a200_da35_wa28 {label} ===')
    run_combo(200, 0.35, 0.28, shift, fname, dict(clearance_nm=v['clearance_nm'], bridge_nm=v['bridge_nm']))

# --- 2. Fill missing feasible combos ---------------------------------------------
todo = [(k, e) for k, e in PLAN.items() if k != 'a200_da35_wa28']
for i, (tag, e) in enumerate(todo, 1):
    fname = DATA / f'sweep_{tag}.npz'
    if not e['feasible']:
        p(f'\n=== {i}/{len(todo)} {tag}: INFEASIBLE in rhombus cell (bridge {e["bridge_nm"]} nm) -- skipped ===')
        continue
    if fname.exists():
        p(f'\n=== {i}/{len(todo)} {tag}: exists, skipping ===')
        continue
    p(f'\n=== {i}/{len(todo)} {tag}  clearance={e["clearance_nm"]} nm  bridge={e["bridge_nm"]} nm  '
      f'(elapsed {(time.time()-t0)/3600:.2f} h) ===')
    run_combo(e['a_nm'], e['da'], e['wa'], (e['shift_x'], e['shift_y']), fname,
              dict(clearance_nm=e['clearance_nm'], bridge_nm=e['bridge_nm']))

client.clear()
p(f'\nFill done. Total {(time.time()-t0)/3600:.2f} h')
