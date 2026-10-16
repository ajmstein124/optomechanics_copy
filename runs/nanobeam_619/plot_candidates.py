"""
plot_candidates.py  (Mac)
Band structures of the strongest stage-2 candidates. Top row: TE-like optical bands (guided only,
below the light line; grey = light cone), shaded = TE gap at X, dashed = 619 nm (484 THz).
Bottom row: mechanical Y+Z+ (breathing-class) bands, shaded = band 1-2 quasi-gap, dashed = 10 GHz.

Usage (from project root):
    python runs/nanobeam_619/plot_candidates.py
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RD = Path('runs/nanobeam_619'); D = RD / 'data'
C0 = 299792458.0
CANDS = [(550, 220, 0.53, 0.77), (450, 245, 0.60, 0.77), (450, 220, 0.53, 0.77)]

fig, axes = plt.subplots(2, len(CANDS), figsize=(4.2 * len(CANDS), 8.5), squeeze=False)
for j, (w, a, hxa, hyw) in enumerate(CANDS):
    tag = f'w{w}_a{a}_hx{int(round(hxa*100))}_hy{int(round(hyw*100))}'
    ax = axes[0, j]
    fo = D / f'optbands_{tag}.npz'
    gX = np.load(D / f'optX_{tag}.npz')['guided_THz']
    if fo.exists():
        d = np.load(fo)
        kf = d['k_frac']; ll = C0 * d['k'] / (2 * np.pi) / 1e12
        F = np.sort(d['freqs'], axis=1) / 1e12
        Fg = np.where(F < ll[:, None], F, np.nan)
        ax.fill_between(kf, ll, 800, color='0.85')
        ax.plot(kf, Fg, '.-', color='#2E86C1', ms=3, lw=1)
    else:
        ax.text(0.5, 0.5, 'pending', transform=ax.transAxes, ha='center', color='0.5')
    ax.axhspan(gX[0], gX[1], color='#F5B7B1', alpha=0.5)
    ax.axhline(484, color='k', ls='--', lw=1)
    ax.set_ylim(250, 650); ax.set_xlim(0, 1); ax.set_xticks([0, 1], [r'$\Gamma$', 'X'])
    sec = ax.secondary_yaxis('right', functions=(lambda f: C0 / 1e3 / np.maximum(f, 1),
                                                 lambda l: C0 / 1e3 / np.maximum(l, 1)))
    sec.set_ticks([500, 550, 619, 700, 800, 1000])
    if j == len(CANDS) - 1:
        sec.set_ylabel('wavelength (nm)')
    ax.set_title(f'w {w}, a {a}, hx/a {hxa}, hy/w {hyw}', fontsize=10, fontweight='bold')
    if j == 0:
        ax.set_ylabel('optical TE (THz)')

    ax = axes[1, j]
    d = np.load(D / f'mech_{tag}.npz')
    F = np.sort(d['freqs'], axis=1) / 1e9
    ax.plot(d['k_frac'], F, '.-', color='#C0392B', ms=3, lw=1)
    g1 = d['gaps'][d['gaps'][:, 0] == 1][0]
    ax.axhspan(g1[1], g1[2], color='#AED6F1', alpha=0.6)
    ax.axhline(10, color='k', ls='--', lw=1)
    ax.set_ylim(0, 25); ax.set_xlim(0, 1); ax.set_xticks([0, 1], [r'$\Gamma$', 'X'])
    ax.text(0.5, g1[2] - 0.3, f'{g1[1]:.1f}-{g1[2]:.1f} GHz', ha='center', va='top', fontsize=9,
            transform=ax.get_yaxis_transform())
    if j == 0:
        ax.set_ylabel('mechanical Y+Z+ (GHz)')
fig.suptitle('Candidate mirror cells, t = 120 nm', fontsize=12, fontweight='bold')
fig.tight_layout()
fig.savefig(RD / 'candidates_bands.png', dpi=140, facecolor='white')
print(f'Saved {RD}/candidates_bands.png')
