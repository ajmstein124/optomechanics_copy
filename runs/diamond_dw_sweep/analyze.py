"""
analyze.py  (runs locally on Mac)
Diamond 3x3 d/w sweep -- heatmaps of fundamental bandgap center and width.

Usage (from project root):
    python runs/diamond_dw_sweep/analyze.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

RESULTS = Path('runs/diamond_dw_sweep/data')
OUT     = Path('runs/diamond_dw_sweep/figures')
OUT.mkdir(exist_ok=True, parents=True)

d_nm = np.array([85, 104, 124])
w_nm = np.array([85, 107, 128])
GAP_BAND = 6   # fundamental gap lies between bands 6 and 7 in all 9 combos (checked 2026-10-13)

# ── Load ──────────────────────────────────────────────────────────────────────

gap_cen = np.full((3, 3), np.nan)
gap_wid = np.full((3, 3), np.nan)

for i, d in enumerate(d_nm):
    for j, w in enumerate(w_nm):
        p = RESULTS / f'sweep_d{d}_w{w}.npz'
        if p.exists():
            dat = np.load(str(p))
            # Track the SAME gap in every combo: between sorted bands GAP_BAND and GAP_BAND+1
            # (sym + antisym combined). The 'first gap > 0.5 GHz' stored in the .npz jumps to a
            # higher-order gap when this one narrows (d=85, w=128 -> 51 GHz), so don't use it.
            sb  = np.sort(np.abs(np.real(dat['freqs'])), axis=1) * 1e-9
            top = sb[:, GAP_BAND - 1].max()
            bot = sb[:, GAP_BAND].min()
            if bot > top:
                gap_cen[i, j] = 0.5 * (top + bot)
                gap_wid[i, j] = bot - top
        else:
            print(f'Missing: {p.name}')

print('Fundamental gap center (GHz):'); print(np.round(gap_cen, 2))
print('Fundamental gap width  (GHz):'); print(np.round(gap_wid, 2))

# ── Heatmaps ──────────────────────────────────────────────────────────────────

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
fig.patch.set_facecolor('white')

panels = [
    (axes[0], gap_cen, 'Bandgap center (GHz)', 'GHz', '{:.1f}', 'Blues'),
    (axes[1], gap_wid, 'Bandgap width (GHz)',   'GHz', '{:.1f}', 'Greens'),
]

for ax, data, title, unit, fmt, cmap_name in panels:
    cmap = plt.get_cmap(cmap_name).copy()
    cmap.set_bad('0.88')
    valid = data[~np.isnan(data)]
    vmin  = valid.min() * 0.95 if len(valid) else 0
    vmax  = valid.max() * 1.05 if len(valid) else 1
    im = ax.imshow(data, origin='lower', cmap=cmap,
                   vmin=vmin, vmax=vmax, aspect='auto')
    ax.set_xticks(range(3)); ax.set_xticklabels([f'{v}' for v in w_nm])
    ax.set_yticks(range(3)); ax.set_yticklabels([f'{v}' for v in d_nm])
    ax.set_xlabel('arm width  w (nm)', fontsize=11)
    ax.set_ylabel('arm length  d (nm)', fontsize=11)
    ax.set_title(title, fontsize=12)
    plt.colorbar(im, ax=ax, shrink=0.85, label=unit)
    for i in range(3):
        for j in range(3):
            v = data[i, j]
            txt = fmt.format(v) if not np.isnan(v) else 'no gap'
            if not np.isnan(v) and gap_wid[i, j] < 0.5:
                txt += '*'
            dark = (not np.isnan(v)) and (v - vmin) / (vmax - vmin) > 0.55
            ax.text(j, i, txt, ha='center', va='center',
                    fontsize=12, fontweight='bold',
                    color='white' if dark else '0.15')

plt.suptitle('Diamond snowflake phononic sweep  (a=300nm, t=140nm, f_r=16nm)\n'
             'gap between bands 6 and 7 (sym+antisym) tracked in every combo;  * = width < 0.5 GHz, at k-sampling resolution (21 k-pts)',
             fontsize=11)
plt.tight_layout()
out = OUT / 'diamond_dw_heatmap.png'
plt.savefig(str(out), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f'\nSaved: {out}')
print('Done.')
