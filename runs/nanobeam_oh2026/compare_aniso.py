"""
compare_aniso.py  (Mac)
Which elastic model did Oh use? Mirror-cell bands for isotropic (E 1050, nu 0.07), anisotropic x || [100],
and anisotropic x || [110] vs every digitized point of Oh Fig. 1(e). Error per point = distance to the
nearest band of the same group (red = Y+Z+; blue = other three classes) at that k.
Usage: python runs/nanobeam_oh2026/compare_aniso.py
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RD = Path('runs/nanobeam_oh2026')
dig = np.genfromtxt(RD / 'reference/oh2026_fig1e_digitized.csv', delimiter=',', skip_header=2, dtype=None,
                    encoding=None, names=['k', 'f', 'c'])
cases = {'isotropic': 'bands_t5.npz', 'aniso [100]': 'bands_aniso100.npz', 'aniso [110]': 'bands_aniso110.npz'}
fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), sharey=True)
for ax, (name, fn) in zip(axes, cases.items()):
    if not (RD / 'data' / fn).exists():
        ax.set_title(f'{name}: pending'); continue
    d = np.load(RD / 'data' / fn); kf = d['k_frac']; F = d['freqs'] / 1e9      # (k, class, mode)
    errs = {'red': [], 'blue': []}
    for kk, ff, cc in zip(dig['k'], dig['f'], dig['c']):
        cls = [0] if cc == 'red' else [1, 2, 3]
        cand = np.concatenate([[np.interp(kk, kf, F[:, c, b]) for b in range(F.shape[2]) if np.all(np.isfinite(F[:, c, b]))] for c in cls])
        errs[cc].append(np.min(np.abs(cand - ff)))
    r, b = np.array(errs['red']), np.array(errs['blue'])
    for c in range(4):
        for bnd in range(F.shape[2]):
            ax.plot(kf, F[:, c, bnd], color='#C0392B' if c == 0 else '#2E86C1', lw=1.6 if c == 0 else 0.8)
    for cc, col in (('red', 'k'), ('blue', '0.45')):
        s = dig['c'] == cc
        ax.plot(dig['k'][s], dig['f'][s], '.', color=col, ms=2.5)
    ax.set_title(f'{name}\nred err median {1e3*np.median(r):.0f} MHz, blue {1e3*np.median(b):.0f} MHz', fontsize=11,
                 fontweight='bold')
    print(f'{name:12s}: red median {1e3*np.median(r):5.0f} MHz (90% {1e3*np.percentile(r,90):5.0f}), '
          f'blue median {1e3*np.median(b):5.0f} MHz (90% {1e3*np.percentile(b,90):5.0f})')
    ax.set_xlim(0, 1); ax.set_ylim(0, 12); ax.set_xticks([0, 1], [r'$\Gamma$', 'X'])
axes[0].set_ylabel('frequency (GHz)')
fig.suptitle('Oh 2026 mirror cell: me (lines) vs Oh Fig. 1(e) (dots)', fontsize=13, fontweight='bold')
fig.tight_layout(); fig.savefig(RD / 'figures_compare_aniso.png', dpi=140, facecolor='white')
print(f'Saved {RD}/figures_compare_aniso.png')
