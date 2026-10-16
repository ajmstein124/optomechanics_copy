"""
plot_bands_grid.py  (runs locally on Mac)
Diamond 3x3 d/w sweep -- band structure for every combo on a 3x3 grid,
fundamental complete gap shaded. Rows: d (top = largest), cols: w.

Usage (from project root):
    python runs/diamond_dw_sweep/plot_bands_grid.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS = Path('runs/diamond_dw_sweep/data')
OUT     = Path('runs/diamond_dw_sweep/figures')
OUT.mkdir(exist_ok=True, parents=True)

d_nm = [124, 104, 85]   # top row = largest d
w_nm = [85, 107, 128]
N_mode = 10
F_MAX  = 60.0           # GHz, y-axis limit

fig, axes = plt.subplots(3, 3, figsize=(13, 12), sharex=True, sharey=True)

for i, d in enumerate(d_nm):
    for j, w in enumerate(w_nm):
        ax  = axes[i, j]
        dat = np.load(str(RESULTS / f'sweep_d{d}_w{w}.npz'))
        freqs = np.abs(np.real(dat['freqs'])) * 1e-9          # (n_k, 2*N_mode) GHz
        kpts  = dat['kpoints']
        a     = float(dat['a'])

        # Cumulative path length along Gamma->M->K->Gamma
        dk  = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(kpts, axis=0), axis=1))]
        tail = np.linalg.norm(kpts[-1])                        # last point -> Gamma
        kx  = np.r_[dk, dk[-1] + tail]
        freqs = np.vstack([freqs, freqs[0]])                   # close path at Gamma

        for b in range(N_mode):
            ax.plot(kx, np.sort(freqs[:, :N_mode], axis=1)[:, b], '-', color='#2C5F8A', lw=1.0)
            ax.plot(kx, np.sort(freqs[:, N_mode:], axis=1)[:, b], '--', color='#C0392B', lw=1.0)

        # Same gap in every panel: between sorted bands 6 and 7 (see analyze.py GAP_BAND)
        sb = np.sort(freqs[:-1], axis=1)
        top, bot = sb[:, 5].max(), sb[:, 6].min()
        gc, gw = (0.5 * (top + bot), bot - top) if bot > top else (0.0, 0.0)
        if gw > 0:
            ax.axhspan(gc - gw/2, gc + gw/2, color='#F4D03F', alpha=0.35, zorder=0)
            ax.text(0.97, 0.03, f'gap {gc:.1f} GHz\nwidth {gw:.2f} GHz ({100*gw/gc:.0f}%)',
                    transform=ax.transAxes, ha='right', va='bottom', fontsize=8.5,
                    bbox=dict(fc='white', ec='#999', lw=0.6))

        # High-symmetry ticks: M and K by matching kpoints
        M = np.array([np.pi/a, np.pi/(a*np.sqrt(3))])
        K = np.array([4*np.pi/(3*a), 0.0])
        iM = np.argmin(np.linalg.norm(kpts - M, axis=1))
        iK = np.argmin(np.linalg.norm(kpts - K, axis=1))
        ticks = [0, kx[iM], kx[iK], kx[-1]]
        for t in ticks:
            ax.axvline(t, color='#bbb', lw=0.6, zorder=0)
        ax.set_xticks(ticks, [r'$\Gamma$', r'$M$', r'$K$', r'$\Gamma$'])
        ax.set_xlim(0, kx[-1]); ax.set_ylim(0, F_MAX)
        ax.set_title(f'd={d} nm, w={w} nm' + ('  (nominal)' if (d, w) == (104, 107) else ''),
                     fontsize=10, fontweight='bold' if (d, w) == (104, 107) else 'normal')
        if j == 0:
            ax.set_ylabel('Frequency (GHz)')

axes[0, 0].plot([], [], '-',  color='#2C5F8A', label='symmetric (sym1)')
axes[0, 0].plot([], [], '--', color='#C0392B', label='antisymmetric (as1)')
axes[0, 0].legend(loc='upper left', fontsize=8)

fig.suptitle('Diamond snowflake d x w sweep -- mechanical band structures\n'
             'a=300 nm, t=140 nm, f_r=16 nm | E=1050 GPa, nu=0.07, rho=3500 | '
             'N_mode=10/symmetry, shaded = complete gap between bands 6 and 7',
             fontsize=11, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.95])
for ext in ('png', 'pdf'):
    fig.savefig(str(OUT / f'diamond_dw_bands_grid.{ext}'), dpi=150, facecolor='white')
print('Saved:', OUT / 'diamond_dw_bands_grid.png')
