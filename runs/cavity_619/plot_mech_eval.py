"""
plot_mech_eval.py  (Mac)  -- runs/cavity_619
Mechanics of the w550 / 60 nm cavities (corrected breathing identification, 2026-10-15).
  (a) best 60 nm device: every computed mechanical mode, frequency vs localization, color = sidewall
      coherence B (1 = in-phase breathing of the two sidewalls)
  (b) (a, d) sweep: breathing-like mode (B > 0.5, highest localization) frequency, text = localization
  (c) all (a, d) + shape points: breathing frequency vs localization, color = d
Breathing-like = B > 0.5 and loc > 0.5 (the pipeline's strict rule also needs loc > 0.8).
Output: runs/cavity_619/mech_eval.png
"""
import glob
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

D = Path('runs/cavity_619/data')


def breathing(z):
    f, loc, B = z['f_mech'] / 1e9, z['loc_mech'], z['B']
    ok = (B > 0.5) & (loc > 0.5) & (f > 5)
    if not ok.any():
        return np.nan, np.nan
    i = np.where(ok)[0][np.argmax(loc[ok])]
    return f[i], loc[i]


fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))

# (a) best device spectrum
z = np.load(D / 'best1_mf60.npz')
f, loc, B = z['f_mech'] / 1e9, z['loc_mech'], z['B']
sc = ax[0].scatter(f, loc, c=B, cmap='viridis', vmin=0, vmax=1, s=28, edgecolor='k', lw=0.3)
fb, lb = breathing(z)
ax[0].scatter([fb], [lb], s=160, facecolor='none', edgecolor='r', lw=1.8)
ax[0].annotate(f'breathing {fb:.2f} GHz', (fb, lb), xytext=(fb + 1.2, lb + 0.12), color='r',
               arrowprops=dict(arrowstyle='-', color='r'))
ax[0].axvline(10, color='0.5', ls='--', lw=1)
ax[0].axhline(0.8, color='0.5', ls=':', lw=1)
ax[0].set(xlabel='frequency (GHz)', ylabel='localization', xlim=(0, 24), ylim=(0, 1.05),
          title=f"best 60 nm: a {float(z['a']):.1f}, d {float(z['d'])}, ξ {float(z['xi']):.0f}, χ {float(z['chi'])}")
plt.colorbar(sc, ax=ax[0], label='sidewall coherence B')

# (b) (a, d) map
R = []
for fn in glob.glob(str(D / 'ad_*.npz')):
    z = np.load(fn)
    if 'skipped' in z and bool(z['skipped']):
        continue
    c = json.loads(str(z['cfg']))
    R.append((c['a_m'], c['d']) + breathing(z))
A = sorted({r[0] for r in R}); Ds = sorted({r[1] for r in R})
M = np.full((len(Ds), len(A)), np.nan); Lm = np.full_like(M, np.nan)
for a, d, fb, lb in R:
    M[Ds.index(d), A.index(a)] = fb; Lm[Ds.index(d), A.index(a)] = lb
im = ax[1].imshow(M, origin='lower', aspect='auto', cmap='RdBu_r', vmin=9, vmax=13,
                  extent=(A[0] - 2.5, A[-1] + 2.5, -0.5, len(Ds) - 0.5))
for i, d in enumerate(Ds):
    for j, a in enumerate(A):
        if np.isfinite(M[i, j]):
            ax[1].text(a, i, f'{M[i, j]:.1f}\n{Lm[i, j]:.2f}', ha='center', va='center', fontsize=6.5)
ax[1].set_yticks(range(len(Ds)), [f'{d:.2f}' for d in Ds])
ax[1].set(xlabel='a (nm)', ylabel='d', title='(a, d) sweep: breathing GHz / localization')
plt.colorbar(im, ax=ax[1], label='breathing (GHz)')

# (c) all points
for fn in glob.glob(str(D / 'ad_*.npz')) + glob.glob(str(D / 'sh_*.npz')):
    z = np.load(fn)
    if 'skipped' in z and bool(z['skipped']):
        continue
    d = json.loads(str(z['cfg']))['d']
    fb, lb = breathing(z)
    ax[2].scatter(fb, lb, c=[plt.cm.plasma((d - 0.10) / 0.12)], s=22,
                  marker='o' if Path(fn).name.startswith('sh') else 's', edgecolor='k', lw=0.3)
for d in (0.10, 0.13, 0.16, 0.19, 0.22):
    ax[2].scatter([], [], c=[plt.cm.plasma((d - 0.10) / 0.12)], label=f'd {d:.2f}')
ax[2].axvline(10, color='0.5', ls='--', lw=1); ax[2].axhline(0.8, color='0.5', ls=':', lw=1)
ax[2].set(xlabel='breathing (GHz)', ylabel='localization', ylim=(0.4, 1.02),
          title='all w550 points (square = (a, d), circle = shape)')
ax[2].legend(fontsize=8, loc='lower left')
fig.tight_layout()
fig.savefig('runs/cavity_619/mech_eval.png', dpi=160)
print('wrote runs/cavity_619/mech_eval.png')
