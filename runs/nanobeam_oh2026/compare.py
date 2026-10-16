"""
compare.py  (Mac)
Compare our Oh 2026 mirror-cell mechanical bands (bands_<mesh>.npz) with the digitized Fig. 1(e).

Figure: left = ours (Y+Z+ red, other classes blue, like the paper) with the paper's digitized
points overlaid (black = their red, grey = their blue) and their quasi-gap shading; right = the
Y+Z+ quasi-gap comparison.  Prints: Y+Z+ quasi-gap (ours vs 3.59-7.15 GHz), band values at
Gamma and X per class, mesh convergence (t/5 vs t/8).

Usage (from project root):
    python runs/nanobeam_oh2026/compare.py
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RD = Path('runs/nanobeam_oh2026')
ref = json.load(open(RD / 'reference/oh2026_reference.json'))
dig = np.genfromtxt(RD / 'reference/oh2026_fig1e_digitized.csv', delimiter=',', skip_header=2, dtype=None,
                    encoding=None, names=['k', 'f', 'c'])
QG = ref['mechanical']['quasi_gap_GHz_from_shading']
FMAX = 12.0

runs = {}
for mname in ('t5', 't8'):
    fn = RD / 'data' / f'bands_{mname}.npz'
    if fn.exists():
        runs[mname] = np.load(fn)
best = 't8' if 't8' in runs else 't5'
d = runs[best]
kf, F = d['k_frac'], d['freqs'] / 1e9          # [k, class, mode]


def class_gaps(F_cls):
    """All gaps between consecutive sorted bands of one class (over all k), with band index."""
    sb = np.sort(F_cls, axis=1)
    out = []
    for b in range(sb.shape[1] - 1):
        top, bot = np.nanmax(sb[:, b]), np.nanmin(sb[:, b + 1])
        if bot > top:
            out.append((top, bot, b + 1))
    return out


gaps = class_gaps(F[:, 0, :])
print('Y+Z+ gaps (all):', ', '.join(f'b{g[2]}-{g[2]+1}: {g[0]:.2f}-{g[1]:.2f}' for g in gaps))
# Oh's shaded quasi-gap is the one containing their cavity mode (6.34 GHz)
qg = next((g for g in gaps if g[0] < 6.34 < g[1]), gaps[0])
print(f'mesh used: {best} ({int(d["n_elem"])} elements)')
print(f'Y+Z+ quasi-gap: me {qg[0]:.2f}-{qg[1]:.2f} GHz (above band {qg[2]})  |  Oh 2026 {QG[0]:.2f}-{QG[1]:.2f} GHz'
      f'  ->  edge errors {100*(qg[0]-QG[0])/QG[0]:+.1f}% / {100*(qg[1]-QG[1])/QG[1]:+.1f}%')
print(f'cavity breathing mode 6.34 GHz inside our quasi-gap: {qg[0] < 6.34 < qg[1]}')
for lbl, ik in (('Gamma', 0), ('X', -1)):
    for ic, cname in enumerate(d['classes']):
        vals = F[ik, ic][F[ik, ic] < FMAX]
        print(f'  {lbl:5s} {cname}: ' + ', '.join(f'{v:.2f}' for v in vals))
print('  Oh red at X:', ref['mechanical']['red_bands_at_X_GHz'], ' red at Gamma:', ref['mechanical']['lowest_red_at_Gamma_GHz'])

if len(runs) == 2:
    a, b = np.sort(runs['t5']['freqs'], axis=2), np.sort(runs['t8']['freqs'], axis=2)
    ok = b > 0.5e9
    rel = np.abs(a[ok] - b[ok]) / b[ok]
    print(f'mesh convergence t/5 vs t/8: median {np.median(rel):.1e}, max {rel.max():.1e} '
          f'({int(runs["t5"]["n_elem"])} vs {int(runs["t8"]["n_elem"])} elements)')

fig, axes = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw=dict(width_ratios=[1.5, 1]))
ax = axes[0]
ax.axhspan(*QG, color='#F5B7B1', alpha=0.5, zorder=0, label=f'Oh quasi-gap {QG[0]:.2f}-{QG[1]:.2f}')
ax.axhline(6.34, color='k', ls='--', lw=1, label='Oh cavity 6.34 GHz')
for ic in range(4):
    for b in range(F.shape[2]):
        ax.plot(kf, np.sort(F[:, ic, :], axis=1)[:, b], '-', color='#C0392B' if ic == 0 else '#2E86C1',
                lw=2.2 if ic == 0 else 1.0, zorder=3)
for c, col, lab in (('red', 'k', 'Oh 2026 red (Y+Z+), digitized'), ('blue', '0.55', 'Oh 2026 blue, digitized')):
    sel = dig['c'] == c
    ax.plot(dig['k'][sel], dig['f'][sel], '.', ms=2.2, color=col, zorder=4, label=lab)
ax.plot([], [], '-', color='#C0392B', lw=2.2, label='me Y+Z+'); ax.plot([], [], '-', color='#2E86C1', label='me other classes')
ax.set_xlim(0, 1); ax.set_ylim(0, FMAX)
ax.set_xticks([0, 1], [r'$\Gamma$', 'X']); ax.set_ylabel('Frequency (GHz)')
ax.legend(fontsize=8, loc='upper left')
ax.set_title('Oh 2026 mirror cell: me (lines) vs paper (dots)', fontweight='bold')

ax = axes[1]
ax.barh([1], [QG[1] - QG[0]], left=[QG[0]], color='#F5B7B1', height=0.4)
ax.barh([0], [qg[1] - qg[0]], left=[qg[0]], color='#C0392B', height=0.4)
ax.set_yticks([0, 1], ['me', 'Oh 2026']); ax.set_xlim(0, FMAX); ax.set_xlabel('Y+Z+ quasi-gap (GHz)')
for y, (lo, hi) in ((0, qg[:2]), (1, QG)):
    ax.text(lo, y + 0.25, f'{lo:.2f}', ha='center', fontsize=9); ax.text(hi, y + 0.25, f'{hi:.2f}', ha='center', fontsize=9)
ax.axvline(6.34, color='k', ls='--', lw=1)
ax.set_title('Y+Z+ quasi-gap', fontweight='bold')
fig.suptitle(f'Oh 2026 reproduction (isotropic diamond, mesh {best})', fontsize=12, fontweight='bold')
fig.tight_layout()
fig.savefig(RD / 'figures_compare.png', dpi=140, facecolor='white')
print(f'Saved {RD}/figures_compare.png')
