"""
cavity_designs.py  (Mac + Windows; numpy only)
Reduce a 619 nm cavity pipeline folder (<run_dir>/data/{ad_,sh_}*.npz) to designs ON the 619.4 nm line,
and the selection rule. Shared by scripts/plot_cavity_sweeps.py (figures) and
runs/cavity_619_final/refinalize.py (confirmation solves).

Breathing mode of a solved point = in-phase sidewall motion (B > 0.5), localized (loc > 0.5), and, where
stored (files from 2026-10-15 on), sidewall amplitude ratio S >= S_MIN; most localized such mode.
Design = linear interpolation in a between the two solved points that bracket 619.4 nm.
A design whose breathing mode was checked on its field map (fields_*.npz in the same data folder, matched
by d / xi / chi / a) carries that S; S < S_MIN there marks it as not a breathing mode ('hybrid').
"""
import glob
import json
from pathlib import Path

import numpy as np

from cavity_taper import layout, min_features

LAM0, S_MIN, LOC_MIN, F_TARGET = 619.4, 0.7, 0.8, 10.0


def opt_mode(z):
    io = int(z['i_opt'])
    if 'Q' not in z:                                   # older sweep files: most localized mode with Q > 1e3
        ok = z['Q_opt'] > 1e3
        if not ok.any():
            return np.nan, np.nan
        io = int(np.where(ok)[0][np.argmax(z['loc_opt'][ok])]) + 1
    return 299792.458 / (z['f_opt'][io - 1] / 1e12), float(z['Q_opt'][io - 1])


def breathing(z):
    ok = (z['B'] > 0.5) & (z['loc_mech'] > 0.5) & (z['f_mech'] > 5e9)
    if 'S' in z:
        ok &= np.nan_to_num(z['S']) >= S_MIN
    if not ok.any():
        return np.nan, np.nan
    i = np.where(ok)[0][np.argmax(z['loc_mech'][ok])]
    return z['f_mech'][i] / 1e9, float(z['loc_mech'][i])


def points(run_dir):
    """All solved points: dict(kind 'ad'/'sh', cfg, lam, Q, fb, lb)."""
    out = []
    for fn in sorted(glob.glob(str(Path(run_dir) / 'data' / '*.npz'))):
        name = Path(fn).name
        if not (name.startswith('ad_') or name.startswith('sh_')):
            continue
        z = np.load(fn)
        if 'skipped' in z and bool(z['skipped']):
            continue
        lam, Q = opt_mode(z)
        fb, lb = breathing(z)
        out.append(dict(kind=name[:2], cfg=json.loads(str(z['cfg'])), lam=lam, Q=Q, fb=fb, lb=lb))
    return out


def field_checks(run_dir):
    """Sidewall ratio S measured on exported breathing-mode field maps: [(cfg, S)]."""
    out = []
    for fn in glob.glob(str(Path(run_dir) / 'data' / 'fields_*.npz')):
        z = np.load(fn); c = json.loads(str(z['cfg']))
        x, y = z['mech_xyz'][:, 0], z['mech_xyz'][:, 1]
        u, v, w = z['mech_val'].T
        core = x < 1500; side = core & (y > c['w'] / 2 - 8)
        out.append((c, float(np.sqrt(np.max(v[side] ** 2) / np.max((u ** 2 + v ** 2 + w ** 2)[core])))))
    return out


def designs(run_dir):
    """(d, xi, chi) designs interpolated onto the 619.4 nm line."""
    groups = {}
    for p in points(run_dir):
        c = p['cfg']
        groups.setdefault((c['d'], c['xi'], c['chi']), []).append(p)
    checks = field_checks(run_dir)
    out = []
    for (d, xi, chi), P in groups.items():
        P = sorted([p for p in P if np.isfinite(p['lam'])], key=lambda p: p['cfg']['a_m'])
        lo = [p for p in P if p['lam'] < LAM0]; hi = [p for p in P if p['lam'] >= LAM0]
        if not lo or not hi:
            continue
        p1 = max(lo, key=lambda p: p['lam']); p2 = min(hi, key=lambda p: p['lam'])
        t = (LAM0 - p1['lam']) / (p2['lam'] - p1['lam'])
        a = p1['cfg']['a_m'] + t * (p2['cfg']['a_m'] - p1['cfg']['a_m'])
        c = dict(p1['cfg'], a_m=a, hx_m=p1['cfg']['hx_m'] / p1['cfg']['a_m'] * a)
        mf = min(min_features(layout(c['a_m'], c['hx_m'], c['hy_m'], c['M'], c['n_mirror'], d, c['eta'], xi, chi, c.get('lock_x', False), c.get('profile')), c['w']).values())
        near = p1 if t < 0.5 else p2                     # breathing: nearer point if one side lacks it
        both = np.isfinite(p1['fb']) and np.isfinite(p2['fb'])
        fb = p1['fb'] + t * (p2['fb'] - p1['fb']) if both else near['fb']
        lb = p1['lb'] + t * (p2['lb'] - p1['lb']) if both else near['lb']
        S = [s for cc, s in checks if (cc['d'], cc['xi'], cc['chi']) == (d, xi, chi) and abs(cc['a_m'] - a) < 2.0]
        out.append(dict(d=d, xi=xi, chi=chi, a=a, Q=float(10 ** (np.log10(p1['Q']) + t * (np.log10(p2['Q']) - np.log10(p1['Q'])))),
                        fb=fb, lb=lb, S=S[0] if S else np.nan, min_feature=mf, base=(p1['kind'] == 'ad'), w=c['w'], cfg=c))
    return out


def line_619(run_dir):
    """a(d) on the 619 nm line from the (a, d) points."""
    P = [p for p in points(run_dir) if p['kind'] == 'ad' and np.isfinite(p['lam'])]
    out = {}
    for d in sorted({p['cfg']['d'] for p in P}):
        R = sorted((p['cfg']['a_m'], p['lam']) for p in P if p['cfg']['d'] == d)
        if len(R) >= 2:
            A, L = np.array(R).T
            if L.min() < LAM0 < L.max():
                o = np.argsort(L); out[d] = float(np.interp(LAM0, L[o], A[o]))
    return out


def rank(D, min_feature):
    """Candidates in selection order: fabricable, localized breathing mode, not a field-checked hybrid;
    first those with breathing <= 10 GHz by highest Q_o, then the rest by lowest breathing frequency."""
    ok = [x for x in D if x['min_feature'] >= min_feature - 0.5 and np.isfinite(x['fb']) and x['lb'] >= LOC_MIN
          and not (np.isfinite(x['S']) and x['S'] < S_MIN)]
    good = sorted([x for x in ok if x['fb'] <= F_TARGET], key=lambda x: -x['Q'])
    rest = sorted([x for x in ok if x['fb'] > F_TARGET], key=lambda x: x['fb'])
    return good + rest


def select(D, min_feature):
    R = rank(D, min_feature)
    return (R[0], R[0]['fb'] <= F_TARGET) if R else (None, False)
