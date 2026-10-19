"""plot_progress.py (Mac): 80 nm designs, optical Q vs breathing frequency (all pipelines + BO batches), and BO predicted vs
observed. -> runs/surrogate_explore/figures/progress.png"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
(HERE / 'figures').mkdir(exist_ok=True)
pts = pd.read_csv(HERE / 'data' / 'points.csv')
bo = pd.read_csv(HERE / 'data' / 'bo_results.csv')
near = lambda d: d[(d.lam - 619.4).abs() < 1.5]
fig, ax = plt.subplots(1, 3, figsize=(17, 4.8))
for df, lab, mk, col in ((near(pts[pts.min_feature >= 79.5]), 'grid/taper sweeps (80 nm)', 'o', '0.6'),
                         (near(pts[pts.min_feature < 79.5]), 'sweeps (60 nm only)', '.', '0.85')):
    ax[0].scatter(df.fb, np.log10(df.Q), s=18, marker=mk, c=col, label=lab)
for b, mk in zip(sorted(bo.kind.str.extract(r'bo(\d+)_')[0].astype(int).unique()), 'sDv^<>'):
    d = bo[bo.kind.str.startswith(f'bo{b}_')]
    sc = ax[0].scatter(d.fb, np.log10(d.Q), s=50, marker=mk, c=d['loc'], cmap='viridis', vmin=0.6, vmax=1.0, edgecolor='k', label=f'BO batch {b}')
ax[0].axvline(10, color='C3', ls='--', lw=1); ax[0].axhline(np.log10(3.4e6), color='C2', ls=':', lw=1)
ax[0].text(10.02, np.log10(3.4e6) + 0.05, 'current 80 nm final', color='C2', fontsize=8)
ax[0].set_xlabel('breathing (GHz)'); ax[0].set_ylabel('log10 optical Q'); ax[0].set_xlim(9.4, 11.8)
ax[0].legend(fontsize=7, loc='lower left'); fig.colorbar(sc, ax=ax[0], label='localization (x < 1.5 µm)')
ax[0].set_title('80 nm: Q vs breathing (within 1.5 nm of 619.4)')
for k, (o, p_, lab) in enumerate((('lam', 'pred_lam', 'resonance (nm)'), ('logQ', 'pred_logQ', 'log10 Q'))):
    bo['logQ'] = np.log10(bo.Q)
    d = bo.dropna(subset=[p_])
    ax[k + 1].scatter(d[p_], d[o], c=d.lock_x, cmap='coolwarm', s=40, edgecolor='k')
    lo, hi = min(d[p_].min(), d[o].min()), max(d[p_].max(), d[o].max())
    ax[k + 1].plot([lo, hi], [lo, hi], 'k-', lw=0.7)
    ax[k + 1].set_xlabel(f'predicted {lab}'); ax[k + 1].set_ylabel(f'COMSOL {lab}')
    ax[k + 1].set_title(f'BO: predicted vs observed {lab} (red = lock_x)')
fig.tight_layout(); fig.savefig(HERE / 'figures' / 'progress.png', dpi=140)
print('saved')
