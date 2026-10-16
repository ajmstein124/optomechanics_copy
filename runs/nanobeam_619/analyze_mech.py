"""
analyze_mech.py  (Mac)
Stage-2 results of the 619 nm / 10 GHz nanobeam design: lowest Y+Z+ (breathing-class) quasi-gap
(band 1-2, the analog of Oh 2026's 3.6-7.2 GHz mirror gap) for every stage-1 cell containing 619 nm.
Same panel layout as stage1_optical.png: rows = w, columns = a; inside each panel rows = hy/w, cols = hx/a.
Color = gap center - 10 GHz (0 = gap centered on 10 GHz, symmetric scale). Hatched = 10 GHz outside
the gap. Grey = not run (619 nm outside the optical gap). Cell text = gap in GHz.
Also writes stage2_summary.csv and prints a ranking of cells holding both targets.

Usage (from project root):
    python runs/nanobeam_619/analyze_mech.py
"""
import csv
import glob
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RD = Path('runs/nanobeam_619')
F_M = 10.0                       # GHz target
F0 = 484.0                       # THz (619 nm)
C_NM_THZ = 299792.458
W = [650, 550, 450, 350]; A = [220, 245, 270, 295]; HXA = [0.45, 0.53, 0.60]; HYW = [0.60, 0.70, 0.77]

rows = {}
for fn in glob.glob(str(RD / 'data' / 'mech_*.npz')):
    d = np.load(fn)
    g = d['gaps']
    g1 = g[g[:, 0] == 1]
    lo, hi = (g1[0, 1], g1[0, 2]) if len(g1) else (np.nan, np.nan)
    tag = Path(fn).stem.replace('mech_', '')
    o = np.load(RD / 'data' / f'optX_{tag}.npz')['guided_THz']
    olo, ohi = o[0], o[1]
    # optical: position of 484 THz in the TE gap (0 = lower edge, 1 = upper edge)
    opos = (F0 - olo) / (ohi - olo)
    rows[(int(d['w']), int(d['a']), float(d['hx_a']), float(d['hy_w']))] = dict(
        lo=lo, hi=hi, center=0.5 * (lo + hi), inside=bool(lo < F_M < hi),
        mpos=(F_M - lo) / (hi - lo), mgap=(hi - lo) / (0.5 * (lo + hi)),
        olo=olo, ohi=ohi, opos=opos, ogap=(ohi - olo) / (0.5 * (ohi + olo)),
        det_nm=float(d['detuning_nm']), bridge=float(d['bridge_nm']), rail=float(d['rail_nm']))

print(f'{len(rows)} cells with mechanics')
both = [(k, v) for k, v in rows.items() if v['inside']]
print(f'{len(both)} hold both 619 nm (optical) and 10 GHz (Y+Z+ band 1-2 quasi-gap)')


def score(v):
    """Both targets as close to their gap centers as possible, weighted by relative gap widths."""
    return v['mgap'] * v['ogap'] * (1 - abs(2 * v['mpos'] - 1)) * (1 - abs(2 * v['opos'] - 1))


print('Top cells by combined score (mech pos / opt pos: 0 = lower edge, 1 = upper edge):')
for k, v in sorted(both, key=lambda kv: -score(kv[1]))[:12]:
    print(f'  w={k[0]} a={k[1]} hx/a={k[2]} hy/w={k[3]}: mech {v["lo"]:.1f}-{v["hi"]:.1f} GHz '
          f'({100*v["mgap"]:.0f}%, 10 GHz at {v["mpos"]:.2f}) | opt {C_NM_THZ/v["ohi"]:.0f}-{C_NM_THZ/v["olo"]:.0f} nm '
          f'({100*v["ogap"]:.0f}%, 619 at {v["opos"]:.2f}) | bridge {v["bridge"]:.0f}, rail {v["rail"]:.0f} nm')

with open(RD / 'stage2_summary.csv', 'w', newline='') as fh:
    wr = csv.writer(fh)
    wr.writerow(['w', 'a', 'hx_a', 'hy_w', 'mech_lo_GHz', 'mech_hi_GHz', 'contains_10GHz', 'pos_10GHz',
                 'opt_short_nm', 'opt_long_nm', 'pos_619nm', 'score', 'bridge_nm', 'rail_nm'])
    for k, v in sorted(rows.items()):
        wr.writerow(list(k) + [v['lo'], v['hi'], v['inside'], v['mpos'], C_NM_THZ / v['ohi'], C_NM_THZ / v['olo'],
                               v['opos'], score(v) if v['inside'] else 0.0, v['bridge'], v['rail']])

fig, axes = plt.subplots(len(W), len(A), figsize=(3.3 * len(A) + 1, 2.9 * len(W)), squeeze=False)
cm = plt.get_cmap('RdBu_r').copy(); cm.set_bad('0.85')
DMAX = 4.0                        # GHz
for i, w in enumerate(W):
    for j, a in enumerate(A):
        ax = axes[i, j]
        grid = np.full((3, 3), np.nan)
        for r, hyw in enumerate(HYW):
            for c, hxa in enumerate(HXA):
                v = rows.get((w, a, hxa, hyw))
                if v is None:
                    continue
                grid[r, c] = v['center'] - F_M
                if not v['inside']:
                    ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1, fc='none', ec='0.35', hatch='///', lw=0))
                ax.text(c, r, f'{v["lo"]:.1f}-{v["hi"]:.1f}', ha='center', va='center', fontsize=7.5,
                        color='white' if abs(grid[r, c]) > 0.65 * DMAX else 'k',
                        fontweight='bold' if v['inside'] else 'normal')
        im = ax.imshow(grid, origin='lower', cmap=cm, vmin=-DMAX, vmax=DMAX, aspect='auto')
        ax.set_xticks(range(3), HXA, fontsize=7); ax.set_yticks(range(3), HYW, fontsize=7)
        if i == 0:
            ax.set_title(f'a = {a} nm', fontsize=10, fontweight='bold')
        if j == 0:
            ax.set_ylabel(f'w = {w} nm\n\nhy/w', fontsize=9)
        if i == len(W) - 1:
            ax.set_xlabel('hx/a', fontsize=8)
fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.02, pad=0.01, label='gap center - 10 GHz (GHz)')
fig.suptitle('Y+Z+ quasi-gap, bands 1-2 (GHz); hatched = 10 GHz outside; grey = 619 nm outside optical gap',
             fontsize=12, fontweight='bold')
fig.savefig(RD / 'stage2_mech.png', dpi=140, facecolor='white', bbox_inches='tight')
print(f'Saved {RD}/stage2_mech.png')
