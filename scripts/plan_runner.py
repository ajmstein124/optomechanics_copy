"""
plan_runner.py  (runs on the Windows COMSOL machine)
Executes a plan.json produced by scripts/sweep_plan.py: for every combo with "run": true,
set a, d, w, f_mech, the cell shift (mov1 in BOTH wp1 slab and wp2 air), check the
geometry topology (2 domains / 30 boundaries), then solve the sym1 + as1 band structure
along Gamma-M-K-Gamma and save runs/<name>/data/sweep_<tag>.npz.

Resumable (existing .npz skipped); one failed combo is logged and skipped.
Uploaded automatically by remote_runner.py alongside comsol_utils.py.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
from comsol_utils import start_client, mphglobal


def _p(*a):
    print(*a)
    sys.stdout.flush()


def _kpath(a, n_seg):
    G = np.array([0.0, 0.0])
    M = np.array([np.pi / a, np.pi / (a * np.sqrt(3))])
    K = np.array([4 * np.pi / (3 * a), 0.0])

    def seg(s, e, n):
        return [s + (e - s) * i / n for i in range(n + 1)]

    raw = seg(G, M, n_seg) + seg(M, K, n_seg)[1:] + seg(K, G, n_seg)[1:]
    seen, out = set(), []
    for kv in raw:
        key = (round(kv[0]), round(kv[1]))
        if key not in seen:
            seen.add(key)
            out.append((float(kv[0]), float(kv[1])))
    return out


def _complete_gaps(freqs, n_mode):
    """Complete gaps below the complete-spectrum ceiling (see analyze scripts)."""
    f = np.abs(np.real(freqs)) * 1e-9
    ceiling = min(f[:, :n_mode].max(axis=1).min(), f[:, n_mode:].max(axis=1).min())
    sb = np.sort(f, axis=1)
    gaps = []
    for b in range(sb.shape[1] - 1):
        top, bot = sb[:, b].max(), sb[:, b + 1].min()
        if bot > top and top > 1.0 and bot <= ceiling:
            gaps.append((b + 1, top, bot))
    return gaps, ceiling


def run_plan(plan_file, run_name):
    plan = json.load(open(plan_file))
    data = Path('runs') / run_name / 'data'
    data.mkdir(parents=True, exist_ok=True)
    g, mat, sol = plan['geometry'], plan['material'], plan['solver']
    n_mode, n_seg = int(sol['N_mode']), int(sol['n_seg'])

    client, model = start_client(g.get('model', 'unit_cell_3.mph'))
    m = model.java
    geom = m.component('comp1').geom('geom1')
    movs = [geom.feature('wp1').geom().feature('mov1'), geom.feature('wp2').geom().feature('mov1')]
    solid = m.component('comp1').physics('solid')

    for name, val in [('t', g['t_nm'] * 1e-9), ('f_r', g['f_r_nm'] * 1e-9), ('N_mode', n_mode),
                      ('scaling', 1.0), ('kFx', 0.0), ('kFy', 0.0)]:
        m.param().set(name, str(val))
    m.material('mat1').propertyGroup('def').set('rho', str(mat['rho']))
    m.material('mat1').propertyGroup('Enu').set('E', str(mat['E']))
    m.material('mat1').propertyGroup('Enu').set('nu', str(mat['nu']))
    m.material('mat1').propertyGroup('Enu').set('rho', str(mat['rho']))
    m.material('mat1').label(mat.get('label', 'Diamond'))
    mh = plan.get('mesh', {})
    mesh1 = m.component('comp1').mesh('mesh1')
    if mh.get('tet_hmax'):
        mesh1.feature('ftet1').feature('size1').set('hmax', mh['tet_hmax'])
    if mh.get('tri_hmax'):
        mesh1.feature('ftri1').feature('size1').set('hmax', mh['tri_hmax'])
    _p(f"Mech mesh: ftet1 hmax={mesh1.feature('ftet1').feature('size1').getString('hmax')}, "
       f"ftri1 hmax={mesh1.feature('ftri1').feature('size1').getString('hmax')}")
    fc = plan['fab_check']
    _p(f"Material {mat.get('label')}: E={mat['E']/1e9:.0f} GPa nu={mat['nu']} rho={mat['rho']}")
    _p(f"N_mode={n_mode} n_seg={n_seg}; min-feature check "
       f"{'ON' if fc['enforce'] else 'OFF'} ({fc['min_feature_nm']} nm)")

    todo = plan['combos']
    t0 = time.time()
    for i, c in enumerate(todo, 1):
        fname = data / f"sweep_{c['tag']}.npz"
        head = f"=== {i}/{len(todo)} {c['tag']}"
        if not c['run']:
            _p(f"\n{head}: skipped ({c['status']}; bridge {c['bridge_nm']} nm, w {c['w_nm']} nm) ===")
            continue
        if fname.exists():
            _p(f'\n{head}: exists, skipping ===')
            continue
        _p(f"\n{head}  bridge={c['bridge_nm']} nm  w={c['w_nm']} nm  clearance={c['clearance_nm']} nm  "
           f"[{c['status']}]  (elapsed {(time.time()-t0)/3600:.2f} h) ===")
        a = c['a_nm'] * 1e-9
        f_mech = sol['f_mech_ref_Hz'] * sol['f_mech_ref_a_m'] / a
        m.param().set('a', str(a))
        m.param().set('d', str(c['d_nm'] * 1e-9))
        m.param().set('w', str(c['w_nm'] * 1e-9))
        m.param().set('f_mech', str(f_mech))
        for mv in movs:
            mv.set('displx', str(c['shift_x']))
            mv.set('disply', str(c['shift_y']))
        try:
            geom.run()
        except Exception as e:
            _p(f'  !! GEOMETRY FAILED: {e}')
            continue
        nd, nb = int(geom.getNDomains()), int(geom.getNBoundaries())
        try:
            mesh1.run()
            ne = int(mesh1.getNumElem())
        except Exception as e:
            _p(f'  !! MESH FAILED: {str(e)[:500]}')
            continue
        _p(f'  geometry: domains={nd} boundaries={nb}; mech mesh {ne} elements')
        if (nd, nb) != (2, 30):
            _p('  !! SKIP: topology differs from every valid combo (expected 2 domains, 30 boundaries)')
            continue

        kpts = _kpath(a, n_seg)
        freqs = np.zeros((len(kpts), 2 * n_mode))
        try:
            for ii, (kx, ky) in enumerate(kpts):
                _p(f'  k {ii+1}/{len(kpts)}')
                m.param().set('kFx', str(kx))
                m.param().set('kFy', str(ky))
                solid.feature('as1').active(False)
                solid.feature('sym1').active(True)
                m.sol('sol1').runAll()
                freqs[ii, :n_mode] = np.real(mphglobal(m, 'solid.freq', 'dset1')[:n_mode])
                solid.feature('sym1').active(False)
                solid.feature('as1').active(True)
                m.sol('sol1').runAll()
                freqs[ii, n_mode:] = np.real(mphglobal(m, 'solid.freq', 'dset1')[:n_mode])
        except Exception as e:
            _p(f'  !! FAILED: {str(e)[:1500]}')
            continue

        gaps, ceiling = _complete_gaps(freqs, n_mode)
        for b, lo, hi in gaps:
            _p(f'  --> complete gap above band {b}: {lo:.2f}-{hi:.2f} GHz')
        if not gaps:
            _p(f'  --> no complete gap below {ceiling:.1f} GHz')
        np.savez(str(fname), freqs=freqs, kpoints=np.array(kpts), N_mode=n_mode,
                 a=a, d=c['d_nm'] * 1e-9, w=c['w_nm'] * 1e-9, t=g['t_nm'] * 1e-9, f_r=g['f_r_nm'] * 1e-9,
                 da=c['da'], wa=c['wa'], f_mech=f_mech, cell_shift=np.array([c['shift_x'], c['shift_y']]),
                 clearance_nm=c['clearance_nm'], bridge_nm=c['bridge_nm'], status=c['status'],
                 all_gaps=np.array(gaps) if gaps else np.zeros((0, 3)), f_valid_GHz=ceiling)
        _p(f'  Saved: {fname}')

    client.clear()
    _p(f'\nPlan done. Total {(time.time()-t0)/3600:.2f} h')
