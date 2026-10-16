"""
deliverables.py  (remote)  -- runs/cavity_619_final
Last link of the COMSOL chain. Waits for runs/cavity_619_width/run.py (2026-10-15; replaced the w550
80 nm chain), then for the TWO final devices (one per minimum feature), each the best over all widths
(breathing <= 10 GHz first, then highest Q_o):
  60 nm: selected of runs/cavity_619 (w550, mf60), cavity_619_width/w650_mf60, w600_mf60
  80 nm: selected of cavity_619_width/w650_mf80, w600_mf80
first RE-FINALIZES every pipeline (refinalize(): confirmation solves of the top-ranked 619 nm designs from
scripts/cavity_designs.py, now with the sidewall amplitude ratio S; first one whose breathing mode passes
is selected, saved as final_<label>.mph and its fields exported -> <run_dir>/data/selected.json,
fields_final.npz), then picks the two final devices from the selected ones, and
produces
  1. mirror-cell band diagrams: optical, Gamma -> X, 21 k, shift 300 THz, in BOTH y classes
     (y0 PEC = cavity class TE0-like; y0 PMC = the y-odd higher-order family -> single-mode check, user
     concern about wider beams), z0 PMC; and mechanical, all 4 symmetry classes (21 k), with the
     validated quarter-cell model (build_nanobeam_model.py)
  2. defect (center) cell: optical TE frequency at X (cavity mode origin, for the band-diagram marker)
  3. device field maps: done by refinalize() (<run_dir>/data/fields_final.npz)
Output: runs/cavity_619_final/data/final_<mf>.json, bands_<mf>.npz
Run via:  python scripts/remote_runner.py runs/cavity_619_final/deliverables.py
"""
import json
import sys
import time
from pathlib import Path

import mph
import numpy as np
import cavity_designs as CD
from cavity_fields import export
from cavity_pipeline import Pipeline
from comsol_utils import mphglobal
from build_nanobeam_model import build as build_cell, class_on, op_class

OUT = Path('runs/cavity_619_final/data'); OUT.mkdir(parents=True, exist_ok=True)
LOGW = Path(r'C:\Users\abby\comsol\job_log_cavity_619_width__run.txt')
N_K = 21
CLASSES = [('+', '+'), ('-', '+'), ('+', '-'), ('-', '-')]


def p(*a):
    print(*a); sys.stdout.flush()


t0 = time.time()
while (not LOGW.exists()) or 'Width study done.' not in LOGW.read_text(errors='ignore'):
    if time.time() - t0 > 30 * 3600:
        p('waited 30 h for the width study; starting anyway'); break
    time.sleep(120)
p(f'deliverables start ({time.time()-t0:.0f} s wait)')


C60, C80 = dict(t=120, hx_a=0.53, hy_w=0.77), dict(t=120, hx_a=0.45, hy_w=0.70)
cells = {'mf60': dict(C60, w=550)}
pools = {'60nm': [('runs/cavity_619', 'mf60', 60)], '80nm': []}
for w in (650, 600):
    cells[f'w{w}_mf60'] = dict(C60, w=w); cells[f'w{w}_mf80'] = dict(C80, w=w)
    pools['60nm'].append((f'runs/cavity_619_width/w{w}_mf60', f'w{w}_mf60', 60))
    pools['80nm'].append((f'runs/cavity_619_width/w{w}_mf80', f'w{w}_mf80', 80))
cells['w700_mf80'] = dict(C80, w=700)                       # queued 2026-10-15 (runs/cavity_619_width/run_w700.py)
pools['80nm'].append(('runs/cavity_619_width/w700_mf80', 'w700_mf80', 80))


def refinalize(run_dir, label, mf, n_try=3):
    """Confirm the top-ranked designs (with S); select the first whose breathing mode passes."""
    sel_fn = Path(run_dir) / 'data' / 'selected.json'
    if sel_fn.exists():
        return json.load(open(sel_fn))
    R = CD.rank(CD.designs(run_dir), mf)
    if not R:
        p(f'[{label}] refinalize: no candidate'); return None
    P = Pipeline(run_dir, cells[label], mf, label)
    chosen = None
    try:
        for i, x in enumerate(R[:n_try], 1):
            fn = P.dd / f'confirm{i}.npz'
            r = P.point(P.cfg(x['a'], x['d'], x['xi'], x['chi']), fn,
                        dict(a=round(x['a'], 1), d=x['d'], xi=x['xi'], chi=x['chi'], rank=i))
            p(f'[{label}] confirm {i}: d {x["d"]} xi {x["xi"]} chi {x["chi"]} a {x["a"]:.1f} -> {r}')
            if r and np.isfinite(r['fb']):
                P.model.save(f'final_{label}.mph')
                export(P.model.java, np.load(fn), 'final', P.dd)
                chosen = dict(label=label, run_dir=str(run_dir), d=x['d'], xi=x['xi'], chi=x['chi'], a=round(x['a'], 1),
                              lam=r['lam'], Q=r['Q'], fb=r['fb'], rank=i, meets_target=bool(r['fb'] <= CD.F_TARGET))
                break
    finally:
        P.close()
    if chosen is None:
        p(f'[{label}] refinalize: none of the top {n_try} confirmed a breathing mode')
        return None
    json.dump(chosen, open(sel_fn, 'w'), indent=1)
    p(f'[{label}] SELECTED {chosen}')
    return chosen


finals = {}
for mf, pool in pools.items():
    B = [b for b in (refinalize(r, l, m) for r, l, m in pool if Path(r, 'data').exists()) if b]
    if B:
        ok = [b for b in B if b['meets_target']]
        finals[mf] = max(ok, key=lambda b: b['Q']) if ok else min(B, key=lambda b: b['fb'])
for mf, b in finals.items():
    b['cell'] = cells[b['label']]
    json.dump(b, open(OUT / f'final_{mf}.json', 'w'), indent=1)
    p(f'FINAL {mf}: {b}')


def cell_params(c, a, hx, hy):
    return {'a': f'{a}[nm]', 'w': f"{c['w']}[nm]", 't': f"{c['t']}[nm]", 'hx': f'{hx}[nm]', 'hy': f'{hy}[nm]',
            'pad_y': '1.5[um]', 'pad_z': '1.5[um]', 'E_d': '1050[GPa]', 'nu_d': '0.07', 'rho_d': '3500[kg/m^3]',
            'n_d': '2.41', 'kx': '0[1/m]', 'f_mech': '8[GHz]', 'N_mode': '15', 'f_op': '300[THz]', 'N_op': '30'}


for mf, b in finals.items():
    fn = OUT / f'bands_{mf}.npz'
    c = b['cell']; a = b['a']
    hx_m, hy_m = c['hx_a'] * a, c['hy_w'] * c['w']
    if not fn.exists() or str(np.load(fn).get('label', '')) != b['label']:   # recompute if the final device changed
        client, model = build_cell(cell_params(c, a, hx_m, hy_m), hole=True, name=f'mirror_{mf}')
        m = model.java
        sol_op = [str(t) for t in m.sol().tags()][-1]
        ks = np.linspace(0, np.pi / (a * 1e-9), N_K)
        fo = np.full((N_K, 2, 30), np.nan); fmech = np.full((N_K, 4, 15), np.nan)
        for ik, k in enumerate(ks):
            m.param().set('kx', f'{k}[1/m]')
            for iy, yc in enumerate(('PEC', 'PMC')):
                op_class(model, y=yc, z='PMC')
                m.sol(sol_op).runAll()
                f = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2'))); f = f[f > 1e12][:30]
                fo[ik, iy, :len(f)] = f
            for ic, (yc, zc) in enumerate(CLASSES):
                class_on(model, yc, zc)
                m.sol('sol1').runAll()
                g = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1')))[:15]
                fmech[ik, ic, :len(g)] = g
        p(f'{mf}: mirror bands done ({time.time()-t0:.0f} s)')
        # defect (center) cell optical X point, for the band-diagram marker
        from cavity_taper import layout
        lay = layout(a, hx_m, hy_m, 10, 10, b['d'], 1.0, b['xi'], b['chi'])
        a0, hx0, hy0 = lay['a'][0], lay['hx'][0], lay['hy'][0]
        for k_, v in (('a', a0), ('hx', hx0), ('hy', hy0)):
            m.param().set(k_, f'{v}[nm]')
        m.param().set('kx', f'{np.pi / (a0 * 1e-9)}[1/m]')
        op_class(model, y='PEC', z='PMC')
        m.sol(sol_op).runAll()
        fd = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2'))); fd = fd[fd > 1e12]
        np.savez(str(fn), label=b['label'], k=ks, k_frac=ks / ks[-1], f_opt=fo, opt_classes=np.array(['y0 PEC (cavity)', 'y0 PMC']), f_mech=fmech, classes=np.array(['Y+Z+', 'Y-Z+', 'Y+Z-', 'Y-Z-']),
                 a=a, hx=hx_m, hy=hy_m, defect_a=a0, defect_hx=hx0, defect_hy=hy0, defect_fX=fd)
        client.clear()

p('Deliverables done.')
