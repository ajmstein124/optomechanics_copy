"""
compare_optical.py  (Mac)
Compare our TE-like optical bands of the Oh 2026 mirror cell (optical_<case>.npz) with the
digitized Fig. 1(d). Guided modes = below the air light line f = c k / (2 pi).
Reports TE band edges at X (Oh: 175.2 / 213.8 THz) for each case and mesh convergence.

Usage (from project root):
    python runs/nanobeam_oh2026/compare_optical.py
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RD = Path('runs/nanobeam_oh2026')
C0 = 299792458.0
ref = json.load(open(RD / 'reference/oh2026_reference.json'))
OH_X = ref['optical']['band_edges_at_X_THz']
dig = np.genfromtxt(RD / 'reference/oh2026_fig1d_digitized.csv', delimiter=',', skip_header=2, dtype=None,
                    encoding=None, names=['k', 'f', 'c'])

cases = {c: np.load(RD / 'data' / f'optical_{c}.npz') for c in ('n241', 'n239', 'n239_fine')
         if (RD / 'data' / f'optical_{c}.npz').exists()}
colors = {'n241': '#2E86C1', 'n239': '#C0392B', 'n239_fine': '#1E8449'}

fig, ax = plt.subplots(figsize=(7.5, 6))
any_d = next(iter(cases.values()))
kf = any_d['k_frac']; k = any_d['k']
ll = C0 * k / (2 * np.pi) / 1e12
ax.fill_between(kf, ll, 260, color='0.8', label='light cone (air)')
for case, d in cases.items():
    F = np.sort(d['freqs'], axis=1) / 1e12
    guided = F < ll[:, None]
    Fg = np.where(guided, F, np.nan)
    for b in range(F.shape[1]):
        ax.plot(kf, Fg[:, b], '-', color=colors[case], lw=2 if case == 'n239' else 1.2,
                label=f'me n={float(d["n"]):.2f}' + (' (fine mesh)' if 'fine' in case else '') if b == 0 else None)
    at_X = F[-1][F[-1] < ll[-1]]
    print(f'{case:10s} ({int(d["n_elem"])} el): guided TE modes at X = ' + ', '.join(f'{v:.1f}' for v in at_X[:3]) +
          f' THz | Oh {OH_X[0]} / {OH_X[1]} -> errors ' +
          ' / '.join(f'{100*(v-o)/o:+.1f}%' for v, o in zip(at_X[:2], OH_X)))
sel = dig['c'] == 'red'
ax.plot(dig['k'][sel], dig['f'][sel], 'k.', ms=2.5, label='Oh 2026 Fig. 1(d), digitized')
ax.axhspan(OH_X[0], OH_X[1], color='#F5B7B1', alpha=0.4, label=f'Oh TE quasi-gap at X {OH_X[0]}-{OH_X[1]}')
ax.axhline(192, color='k', ls='--', lw=1, label='Oh cavity 192 THz')
ax.set_xlim(0, 1); ax.set_ylim(0, 250); ax.set_xticks([0, 1], [r'$\Gamma$', 'X'])
ax.set_ylabel('Frequency (THz)'); ax.legend(fontsize=8, loc='upper left')
ax.set_title('Oh 2026 mirror cell, TE-like optical bands: me vs paper', fontweight='bold')
fig.tight_layout(); fig.savefig(RD / 'figures_compare_optical.png', dpi=140, facecolor='white')

if 'n239' in cases and 'n239_fine' in cases:
    a, b = np.sort(cases['n239']['freqs'], 1), np.sort(cases['n239_fine']['freqs'], 1)
    g = (b / 1e12) < ll[:, None]
    rel = np.abs(a[g] - b[g]) / b[g]
    print(f'OP mesh convergence (guided modes): median {np.median(rel):.1e}, max {rel.max():.1e}')
print(f'Saved {RD}/figures_compare_optical.png')
