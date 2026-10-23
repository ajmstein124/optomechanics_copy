"""analyze_gap_cells.py (Mac): mechanical-gap design map from data/ucg_*.npz (gap_cells.py).
Per cell: breathing-class (Y+Z+) gap = (max over k of band 1, min over k of band 2); optical cavity-family band edges at X.
Pairs a MIRROR cell (619 nm inside its optical gap, mech gap top G) with a CENTER cell of the same width (optical band-1 edge
495-520 THz, i.e. the cavity mode ~4.3% below it lands near 619 nm; Gamma breathing f_c) such that the cavity breathing mode
(~ f_c - 0.23 GHz, unit-cell proxy) sits inside the mirror gap with margin. Translates each pair to taper params (d, chi, xi):
  1 - d = a_c/a_m,  s = hx_c hy_c / (hx_m hy_m),  chi = (1 - s)/d,  r = (hy_c/hx_c)/(hy_m/hx_m),  xi = ln r / ln(1 - d).
Usage: python analyze_gap_cells.py [--pull] [--mf 60|80] [--margin 0.4]"""
import argparse
import glob
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--pull', action='store_true'); ap.add_argument('--mf', type=float, default=60); ap.add_argument('--margin', type=float, default=0.4)
ap.add_argument('--strict', action='store_true', help='use the 2nd nonzero Gamma mode too (two near-degenerate low bands cross; either may be the breathing band)')
A = ap.parse_args()
if A.pull:
    subprocess.run(f'scp -q -i ~/.ssh/id_ed25519 "<USER>@<COMSOL_HOST>:C:/Users/abby/comsol/runs/surrogate_explore/data/ucg_*.npz" "{HERE}/data/"', shell=True)

R = []
for fn in glob.glob(str(HERE / 'data' / 'ucg_*.npz')):
    z = np.load(fn, allow_pickle=True)
    f = np.sort(z['f_mech'], axis=1) / 1e9
    f = np.where(f > 0.5, f, np.nan)                       # drop the k=0 rigid mode
    b = np.array([row[np.isfinite(row)] for row in f], dtype=object)
    band1 = np.array([r[0] if k > 0 else 0.0 for k, r in zip(z['k_frac'], b)])   # Gamma: band 1 starts at 0
    band2 = np.array([r[1] if k > 0 else r[0] for k, r in zip(z['k_frac'], b)])
    fo = np.sort(z['f_opt_X']) / 1e12; ll = float(z['light_line_X']) / 1e12; g = fo[fo < ll]
    w, a, hx, hy = (float(z[k]) for k in ('w', 'a', 'hx', 'hy'))
    R.append(dict(kind=str(z['kind']), w=w, a=a, hx=hx, hy=hy, rail=(w - hy) / 2, bridge=a - hx,
                  gap_lo=float(band1.max()), gap_hi=float(band2.min()), k_hi=float(z['k_frac'][np.argmin(band2)]),
                  fG=float(band2[0]), fG2=float(b[0][1]) if len(b[0]) > 1 else np.nan, b1=g[0] if len(g) else np.nan, b2=g[1] if len(g) > 1 else ll))
print(f'{len(R)} cells ({sum(r["kind"] == "M" for r in R)} mirror-type)')
off = [r for r in R if r['k_hi'] > 0]
print(f'gap top away from Gamma in {len(off)} cells' + (': ' + ', '.join(f"w{r['w']:.0f} a{r['a']:.0f} k{r['k_hi']}" for r in off[:8]) if off else ''))

mf = A.mf
M = [r for r in R if r['kind'] == 'M' and r['b1'] < 478 and r['b2'] > 492 and min(r['rail'], r['bridge'], r['hx']) >= mf]
C = [r for r in R if r['kind'] == 'C' and 495 <= r['b1'] <= 520]
print(f'\nmirror cells with 619 nm in the optical gap, features >= {mf:.0f}: {len(M)}')
for w in sorted({r['w'] for r in M}):
    mm = sorted([r for r in M if r['w'] == w], key=lambda r: -r['gap_hi'])[:3]
    print(f'  w {w:.0f}: ' + ' | '.join(f"a{r['a']:.0f} hx/a {r['hx']/r['a']:.2f} hy/w {r['hy']/r['w']:.2f}: gap {r['gap_lo']:.2f}-{r['gap_hi']:.2f} GHz, opt {r['b1']:.0f}-{r['b2']:.0f}" for r in mm))
pairs = []
for m in M:
    for c in C:
        if c['w'] != m['w']:
            continue
        d = 1 - c['a'] / m['a']
        if not 0.05 <= d <= 0.20:
            continue
        fb = (max(c['fG'], c['fG2']) if A.strict and c['fG2'] < 20 else c['fG']) - 0.23
        if not (m['gap_lo'] + A.margin <= fb <= m['gap_hi'] - A.margin) or fb > 10.0:
            continue
        s = c['hx'] * c['hy'] / (m['hx'] * m['hy']); r_ = (c['hy'] / c['hx']) / (m['hy'] / m['hx'])
        chi = (1 - s) / d; xi = np.log(r_) / np.log(1 - d)
        cmf = min(c['rail'], c['bridge'] * (1 - 0.0), c['hx'])   # center-cell features (bridges in the cavity also depend on neighbors)
        if cmf < mf:
            continue
        pairs.append(dict(m=m, c=c, d=d, chi=chi, xi=xi, fb=fb, margin=m['gap_hi'] - fb))
pairs.sort(key=lambda p: -p['margin'])
print(f'\npairs with breathing (center f_Gamma - 0.23) inside the mirror gap by >= {A.margin} GHz and <= 10 GHz: {len(pairs)}')
for p in pairs[:20]:
    m, c = p['m'], p['c']
    print(f"  w {m['w']:.0f} | mirror a{m['a']:.0f} hx/a {m['hx']/m['a']:.2f} hy/w {m['hy']/m['w']:.2f} gap {m['gap_lo']:.2f}-{m['gap_hi']:.2f}"
          f" | center a{c['a']:.0f} hx {c['hx']:.0f} hy {c['hy']:.0f} rail {c['rail']:.0f} bridge {c['bridge']:.0f} opt b1 {c['b1']:.0f}"
          f" | fb~{p['fb']:.2f} (margin {p['margin']:.2f}) d {p['d']:.3f} chi {p['chi']:.2f} xi {p['xi']:.2f}")
