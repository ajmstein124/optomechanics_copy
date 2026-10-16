"""
analyze_optical.py  (Mac)
Stage-1 results of the 619 nm nanobeam screen: TE-like gap at X for every (w, a, hx/a, hy/w).
Grid of panels: rows = w, columns = a; inside each panel rows = hy/w, cols = hx/a.
Shown in WAVELENGTH (lambda = c/f, nm). Color = DETUNING = gap-center wavelength - 619 nm
(gap center = midpoint of the two wavelength edges); 0 = gap centered on 619 nm, symmetric scale.
Hatched = 619 nm lies outside the gap. Grey = pending / incomplete. Cell text = gap at X in nm
(short-lambda edge = upper-frequency band). Works on partial data.

Usage (from project root):
    python runs/nanobeam_619/analyze_optical.py
"""
import glob
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RD = Path('runs/nanobeam_619')
F0 = 484.0
C_NM_THZ = 299792.458            # lambda[nm] = C_NM_THZ / f[THz]
L0 = C_NM_THZ / F0               # 619.4 nm


def nm(f_thz):
    return C_NM_THZ / f_thz
W = [650, 550, 450, 350]; A = [220, 245, 270, 295]; HXA = [0.45, 0.53, 0.60]; HYW = [0.60, 0.70, 0.77]

rows = {}
for fn in glob.glob(str(RD / 'data' / 'optX_*.npz')):
    d = np.load(fn)
    g = d['guided_THz']
    lo, hi = (g[0], g[1]) if g.size >= 2 else (np.nan, np.nan)
    inside = bool(g.size >= 2 and lo < F0 < hi)
    det = 0.5 * (C_NM_THZ / lo + C_NM_THZ / hi) - L0 if g.size >= 2 else np.nan
    rows[(int(d['w']), int(d['a']), float(d['hx_a']), float(d['hy_w']))] = dict(
        lo=lo, hi=hi, detuning=det, inside=inside, bridge=float(d['bridge_nm']), rail=float(d['rail_nm']))

print(f'{len(rows)}/144 combos done')
hits = sorted(((abs(v['detuning']), k, v) for k, v in rows.items() if v['inside']))
print(f'{len(hits)} contain 619 nm. Smallest |detuning|:')
for c, k, v in hits[:12]:
    print(f'  w={k[0]} a={k[1]} hx/a={k[2]} hy/w={k[3]}: gap {nm(v["hi"]):.0f}-{nm(v["lo"]):.0f} nm, '
          f'detuning {v["detuning"]:+.0f} nm, bridge {v["bridge"]:.0f} nm, rail {v["rail"]:.0f} nm')
with open(RD / 'stage1_summary.csv', 'w', newline='') as fh:
    wr = csv.writer(fh); wr.writerow(['w', 'a', 'hx_a', 'hy_w', 'gap_lo_THz', 'gap_hi_THz', 'gap_short_nm',
                                      'gap_long_nm', 'detuning_nm', 'contains_619', 'bridge_nm', 'rail_nm'])
    for k, v in sorted(rows.items()):
        wr.writerow(list(k) + [v['lo'], v['hi'], nm(v['hi']), nm(v['lo']), v['detuning'], v['inside'],
                               v['bridge'], v['rail']])

fig, axes = plt.subplots(len(W), len(A), figsize=(3.3 * len(A) + 1, 2.9 * len(W)), squeeze=False)
cm = plt.get_cmap('RdBu_r').copy(); cm.set_bad('0.85')
DMAX = 120.0          # color scale +/- nm
for i, w in enumerate(W):
    for j, a in enumerate(A):
        ax = axes[i, j]
        grid = np.full((3, 3), np.nan)
        for r, hyw in enumerate(HYW):
            for c, hxa in enumerate(HXA):
                v = rows.get((w, a, hxa, hyw))
                if v is None:
                    ax.text(c, r, '--', ha='center', va='center', fontsize=8, color='0.4'); continue
                grid[r, c] = v['detuning']
                txt = f'{nm(v["hi"]):.0f}-{nm(v["lo"]):.0f}' if np.isfinite(v['lo']) else 'incomplete'
                if np.isfinite(v['lo']) and not v['inside']:
                    ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1, fc='none', ec='0.35', hatch='///', lw=0))
                ax.text(c, r, txt, ha='center', va='center', fontsize=7.5,
                        color='white' if np.isfinite(v['detuning']) and abs(v['detuning']) > 0.65 * DMAX else 'k',
                        fontweight='bold' if v['inside'] else 'normal')
        im = ax.imshow(grid, origin='lower', cmap=cm, vmin=-DMAX, vmax=DMAX, aspect='auto')
        ax.set_xticks(range(3), HXA, fontsize=7); ax.set_yticks(range(3), HYW, fontsize=7)
        if i == 0:
            ax.set_title(f'a = {a} nm', fontsize=10, fontweight='bold')
        if j == 0:
            ax.set_ylabel(f'w = {w} nm\n\nhy/w', fontsize=9)
        if i == len(W) - 1:
            ax.set_xlabel('hx/a', fontsize=8)
fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.02, pad=0.01, label='detuning: gap center - 619 nm (nm)')
fig.suptitle('619 nm screen (t = 120 nm): TE gap at X (nm); white = centered on 619 nm; hatched = 619 nm outside gap', fontsize=12, fontweight='bold')
fig.savefig(RD / 'stage1_optical.png', dpi=140, facecolor='white', bbox_inches='tight')
print(f'Saved {RD}/stage1_optical.png')
