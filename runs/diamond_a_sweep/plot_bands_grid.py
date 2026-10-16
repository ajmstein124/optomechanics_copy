"""
plot_bands_grid.py  (runs locally on Mac)
One 3x3 band-structure grid (rows d/a, cols w/a) per lattice constant a.
Shades the tracked band 6-7 complete gap; outlines every other complete gap below the
complete-spectrum ceiling (grey band above it = N_mode truncation region).
Missing combos are left blank.

Output: runs/diamond_a_sweep/figures/bands_grid_a{a}.png

Usage (from project root):
    python runs/diamond_a_sweep/plot_bands_grid.py          # all a with any data
    python runs/diamond_a_sweep/plot_bands_grid.py 200 225  # selected a only
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

DATA = Path('runs/diamond_a_sweep/data')
OUT  = Path('runs/diamond_a_sweep/figures')
OUT.mkdir(parents=True, exist_ok=True)

a_all   = [150, 175, 200, 225, 250, 275]
da_vals = [0.48, 0.41, 0.35]     # top row = largest d/a
wa_vals = [0.28, 0.36, 0.43]
N_mode  = 10
GAP_BAND = 6


def tag(a, da, wa):
    return f'a{a}_da{int(round(da*100)):02d}_wa{int(round(wa*100)):02d}'


a_sel = [int(x) for x in sys.argv[1:]] or a_all

for a in a_sel:
    files = {(da, wa): DATA / f'sweep_{tag(a, da, wa)}.npz' for da in da_vals for wa in wa_vals}
    if not any(p.exists() for p in files.values()):
        continue
    f_max = 60.0 * 300.0 / a

    fig, axes = plt.subplots(3, 3, figsize=(13, 12), sharex=False, sharey=True)
    for i, da in enumerate(da_vals):
        for j, wa in enumerate(wa_vals):
            ax = axes[i, j]
            ax.set_title(f'd/a={da} (d={da*a:.0f} nm), w/a={wa} (w={wa*a:.0f} nm)', fontsize=9.5)
            p = files[(da, wa)]
            if not p.exists():
                ax.text(0.5, 0.5, 'not run yet', transform=ax.transAxes,
                        ha='center', va='center', color='0.5')
                ax.set_xticks([])
                continue
            dat   = np.load(str(p))
            freqs = np.abs(np.real(dat['freqs'])) * 1e-9
            kpts  = dat['kpoints']

            dk = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(kpts, axis=0), axis=1))]
            kx = np.r_[dk, dk[-1] + np.linalg.norm(kpts[-1])]
            fpl = np.vstack([freqs, freqs[0]])

            for b in range(N_mode):
                ax.plot(kx, np.sort(fpl[:, :N_mode], axis=1)[:, b], '-', color='#2C5F8A', lw=1.0)
                ax.plot(kx, np.sort(fpl[:, N_mode:], axis=1)[:, b], '--', color='#C0392B', lw=1.0)

            sb = np.sort(freqs, axis=1)
            # complete-spectrum ceiling: above it, N_mode truncation makes gaps meaningless
            f_valid = min(freqs[:, :N_mode].max(axis=1).min(), freqs[:, N_mode:].max(axis=1).min())
            ax.axhspan(f_valid, f_max, color='0.85', alpha=0.5, zorder=0)
            label = 'no 6-7 gap'
            for b in range(sb.shape[1] - 1):
                top, bot = sb[:, b].max(), sb[:, b + 1].min()
                if bot > top and top > 1.0 and bot <= f_valid:
                    if b + 1 == GAP_BAND:
                        ax.axhspan(top, bot, color='#F4D03F', alpha=0.4, zorder=0)
                        c, w = 0.5 * (top + bot), bot - top
                        label = f'6-7 gap {c:.1f} GHz\nwidth {w:.2f} GHz ({100*w/c:.0f}%)'
                    else:
                        ax.axhspan(top, bot, fc='none', ec='#7D3C98', ls=':', lw=1.0, zorder=0)
            ax.text(0.97, 0.03, label, transform=ax.transAxes, ha='right', va='bottom',
                    fontsize=8.5, bbox=dict(fc='white', ec='#999', lw=0.6))

            a_m = float(dat['a'])
            M = np.array([np.pi / a_m, np.pi / (a_m * np.sqrt(3))])
            K = np.array([4 * np.pi / (3 * a_m), 0.0])
            iM = np.argmin(np.linalg.norm(kpts - M, axis=1))
            iK = np.argmin(np.linalg.norm(kpts - K, axis=1))
            ticks = [0, kx[iM], kx[iK], kx[-1]]
            for t in ticks:
                ax.axvline(t, color='#bbb', lw=0.6, zorder=0)
            ax.set_xticks(ticks, [r'$\Gamma$', r'$M$', r'$K$', r'$\Gamma$'])
            ax.set_xlim(0, kx[-1])
            ax.set_ylim(0, f_max)
            if j == 0:
                ax.set_ylabel('Frequency (GHz)')

    axes[0, 0].plot([], [], '-',  color='#2C5F8A', label='symmetric (sym1)')
    axes[0, 0].plot([], [], '--', color='#C0392B', label='antisymmetric (as1)')
    axes[0, 0].legend(loc='upper left', fontsize=8)
    fig.suptitle(f'Diamond snowflake a-sweep -- a = {a} nm (a/λ = {a/619:.2f} at 619 nm)\n'
                 't=140 nm, f_r=16 nm | yellow = complete gap bands 6-7, purple dotted = other complete gaps\n'
                 'grey = above complete-spectrum ceiling (N_mode truncation, gaps there not meaningful)',
                 fontsize=11, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = OUT / f'bands_grid_a{a}.png'
    fig.savefig(str(out), dpi=130, facecolor='white')
    plt.close(fig)
    print('Saved:', out)
