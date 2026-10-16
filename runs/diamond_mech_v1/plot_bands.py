"""
plot_bands.py -- Diamond mech band structure (v1)
Reads sym + antisym CSVs and plots phononic bands along Gamma->M->K->Gamma.
Detects and annotates the phononic bandgap.

Inputs:  runs/diamond_mech_v1/data/Python_diamond_Gamma_{sym,antisym}.csv
Outputs: runs/diamond_mech_v1/figures/diamond_mech_bands.{png,pdf}
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import csv
from pathlib import Path

a    = 300e-9
E_d  = 1050e9
nu_d = 0.07
rho_d = 3500.0
v_TA = np.sqrt(E_d / (2 * (1 + nu_d)) / rho_d)

G = np.array([0.0, 0.0])
M = np.array([np.pi / a, np.pi / (a * np.sqrt(3))])
K = np.array([4 * np.pi / (3 * a), 0.0])

DATA = Path('runs/diamond_mech_v1/data')
OUT  = Path('runs/diamond_mech_v1/figures')
OUT.mkdir(parents=True, exist_ok=True)


def parse_csv(fpath):
    kpoints = []
    cur_k, cur_freqs = None, []
    with open(fpath, newline='') as fh:
        for row in csv.reader(fh):
            if len(row) < 3:
                continue
            try:
                kx, ky, f = float(row[0]), float(row[1]), abs(float(row[2]))
            except ValueError:
                continue
            if f < 1e6:
                continue
            if cur_k is None or (kx, ky) != cur_k:
                if cur_k is not None:
                    kpoints.append((cur_k[0], cur_k[1], sorted(cur_freqs)))
                cur_k = (kx, ky)
                cur_freqs = []
            cur_freqs.append(f)
    if cur_k is not None:
        kpoints.append((cur_k[0], cur_k[1], sorted(cur_freqs)))
    return kpoints


def kpath_dist(kpoints):
    kvecs = np.array([[kx, ky] for kx, ky, _ in kpoints])
    d = np.zeros(len(kvecs))
    for i in range(1, len(kvecs)):
        d[i] = d[i - 1] + np.linalg.norm(kvecs[i] - kvecs[i - 1])
    return d


sym     = parse_csv(DATA / 'Python_diamond_Gamma_sym.csv')
antisym = parse_csv(DATA / 'Python_diamond_Gamma_antisym.csv')

sym_d    = kpath_dist(sym)
antisym_d = kpath_dist(antisym)
total    = sym_d[-1] if sym_d[-1] > 0 else 1.0
sym_n    = sym_d / total
antisym_n = antisym_d / total

# High-symmetry tick positions
kvecs = np.array([[kx, ky] for kx, ky, _ in sym])
ticks = []
for ref, label in [(G, r'$\Gamma$'), (M, r'$M$'), (K, r'$K$'), (G, r'$\Gamma$')]:
    idx = np.argmin(np.linalg.norm(kvecs - ref, axis=1))
    ticks.append((sym_n[idx], label))

# Collect all frequencies to find bandgap
all_freqs = []
for _, _, fs in sym + antisym:
    all_freqs.extend(fs)
all_freqs = np.array(sorted(all_freqs)) / 1e9  # GHz

# Detect all bandgaps wider than 1 GHz
diffs = np.diff(all_freqs)
all_gaps = [(all_freqs[i], all_freqs[i+1]) for i in range(len(all_freqs)-1)
            if diffs[i] > 1.0]

print(f'v_TA = {v_TA:.0f} m/s')
print(f'Expected gap center: {0.582 * v_TA / a / 1e9:.1f} GHz')
for f_bot, f_top in all_gaps:
    f_cen = 0.5 * (f_bot + f_top)
    f_wid = f_top - f_bot
    print(f'Bandgap: {f_bot:.3f} -- {f_top:.3f} GHz  (center {f_cen:.3f}, width {f_wid:.3f} GHz)')

fig, ax = plt.subplots(figsize=(7, 5.5))
fig.patch.set_facecolor('white')

# Shade all bandgaps
for f_bot, f_top in all_gaps:
    ax.axhspan(f_bot, f_top, color='#E8F4FD', zorder=0)

# Sym (blue) and antisym (red)
for i, (kx, ky, freqs) in enumerate(sym):
    ax.plot([sym_n[i]] * len(freqs), [f / 1e9 for f in freqs],
            '.', color='#2980B9', ms=4, alpha=0.9, zorder=2)
for i, (kx, ky, freqs) in enumerate(antisym):
    ax.plot([antisym_n[i]] * len(freqs), [f / 1e9 for f in freqs],
            '.', color='#E74C3C', ms=4, alpha=0.9, zorder=2)

# Annotate each bandgap, alternating sides to avoid overlap
sides = [(0.97, 'right'), (0.03, 'left'), (0.97, 'right')]
for (f_bot, f_top), (xpos, ha) in zip(all_gaps, sides):
    f_cen = 0.5 * (f_bot + f_top)
    f_wid = f_top - f_bot
    ax.annotate(f'bandgap center {f_cen:.1f} GHz\nbandgap width {f_wid:.1f} GHz',
                xy=(xpos, f_cen),
                xycoords=('axes fraction', 'data'),
                ha=ha, va='center', fontsize=8,
                color='#1A5276',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#2980B9', alpha=0.8))

# HSP lines and labels
tick_xs = [t[0] for t in ticks]
for tx in tick_xs:
    ax.axvline(tx, color='#555', lw=0.8, zorder=1)
ax.set_xticks(tick_xs)
ax.set_xticklabels([t[1] for t in ticks], fontsize=13)

handles = [
    plt.Line2D([0], [0], marker='.', color='w', markerfacecolor='#2980B9', ms=9,
               label='Symmetric (in-plane)'),
    plt.Line2D([0], [0], marker='.', color='w', markerfacecolor='#E74C3C', ms=9,
               label='Antisymmetric (flexural)'),
]
ax.legend(handles=handles, fontsize=9, loc='upper right', framealpha=0.9)

ax.set_xlim(0, 1)
ax.set_ylim(bottom=0)
ax.set_ylabel('Frequency (GHz)', fontsize=12)
ax.set_title(
    r'Diamond snowflake phononic band structure'
    '\n'
    r'$a=300\,\mathrm{nm}$, $d=104\,\mathrm{nm}$, $w=107\,\mathrm{nm}$, '
    r'$t=140\,\mathrm{nm}$, $E=1050\,\mathrm{GPa}$',
    fontsize=10)
ax.grid(axis='y', lw=0.4, alpha=0.5)

for ext in ['png', 'pdf']:
    p = OUT / f'diamond_mech_bands.{ext}'
    fig.savefig(str(p), dpi=180 if ext == 'png' else None,
                bbox_inches='tight', facecolor='white')
    print(f'Saved: {p}')
plt.close(fig)
print('Done.')
