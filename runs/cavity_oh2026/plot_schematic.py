"""
plot_schematic.py  (Mac)
Schematic of the full-cavity 1/8 model, drawn to scale from data/build_info.json (the exact numbers
the .mph was built with). Panels: (a) full beam, holes colored by region; (b) the simulated 1/8
domain, top view, with air / PML and boundary conditions; (c) cross-section; (d) taper profile vs
Oh 2026 Fig. 1(b) measurements.

Usage (from project root):
    python runs/cavity_oh2026/plot_schematic.py [run_dir]
"""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle

RD = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('runs/cavity_oh2026')
info = json.load(open(RD / 'data' / 'build_info.json'))
c, L = info['cfg'], {k: np.array(v) for k, v in info['layout'].items()}
um = 1e-3
M, nm_ = c['M'], c['n_mirror']
x, a, hx, hy = L['x'], L['a'], L['hx'], L['hy']
X_in = x[-1] + a[-1] / 2 + c['pad_x']
W2, T2 = c['w'] / 2, c['t'] / 2
COL = {'defect': '#C0392B', 'taper': '#E67E22', 'mirror': '#2E86C1'}
region = lambda j: 'defect' if j == 0 else ('taper' if j < M else 'mirror')
BEAM, AIR, PML = '#AED6F1', '#FDFEFE', '#D5D8DC'

fig = plt.figure(figsize=(15, 11))
gs = fig.add_gridspec(3, 2, height_ratios=[0.45, 1.0, 1.1], width_ratios=[2.3, 1], hspace=0.32, wspace=0.18)

# (a) full beam
ax = fig.add_subplot(gs[0, :])
ax.add_patch(Rectangle((-X_in * um, -W2 * um), 2 * X_in * um, 2 * W2 * um, fc=BEAM, ec='k', lw=0.8))
for j in range(len(x)):
    for s in ((1, -1) if j else (1,)):
        ax.add_patch(Ellipse((s * x[j] * um, 0), hx[j] * um, hy[j] * um, fc='white', ec=COL[region(j)], lw=1.3))
ax.axvline(0, color='k', ls=':', lw=0.8)
for r_, col in COL.items():
    ax.plot([], [], 's', mfc='white', mec=col, mew=1.5, ms=9, label=r_)
ax.legend(loc='upper right', ncol=3, fontsize=9, frameon=False, bbox_to_anchor=(1, 1.45))
ax.set_xlim(-X_in * um * 1.02, X_in * um * 1.02); ax.set_ylim(-0.7, 0.7); ax.set_aspect('equal')
ax.set_xlabel('x (µm)'); ax.set_yticks([])
ax.set_title(f'(a) full beam: {2 * len(x) - 1} holes = 1 defect + 2×{M - 1} taper + 2×{nm_ + 1} mirror',
             loc='left', fontweight='bold')

# (b) 1/8 domain top view
ax = fig.add_subplot(gs[1, :])
Xo, Yi, Yo = X_in + c['d_pml'], W2 + c['pad_y'], W2 + c['pad_y'] + c['d_pml']
ax.add_patch(Rectangle((0, 0), Xo * um, Yo * um, fc=PML, ec='k', lw=0.8, hatch='//'))
ax.add_patch(Rectangle((0, 0), X_in * um, Yi * um, fc=AIR, ec='k', lw=0.8))
ax.add_patch(Rectangle((0, 0), Xo * um, W2 * um, fc=BEAM, ec='k', lw=0.8))
ax.add_patch(Rectangle((X_in * um, 0), c['d_pml'] * um, W2 * um, fc=BEAM, ec='k', lw=0.8, hatch='//'))
clip = Rectangle((0, 0), Xo * um, Yo * um, transform=ax.transData)
for j in range(len(x)):
    e = ax.add_patch(Ellipse((x[j] * um, 0), hx[j] * um, hy[j] * um, fc='white', ec=COL[region(j)], lw=1.2))
    e.set_clip_path(clip)
ax.plot([X_in * um] * 2, [0, W2 * um], color='#7D3C98', lw=4)
ax.text(X_in * um, W2 * um + 0.08, 'fixed', color='#7D3C98', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.text((X_in + c['d_pml'] / 2) * um, (Yi + c['d_pml'] / 2) * um, 'PML', ha='center', va='center', fontsize=11, fontweight='bold')
ax.text(X_in * um * 0.5, (W2 + c['pad_y'] / 2) * um, 'air', ha='center', va='center', fontsize=11, color='0.4')
ax.text(-0.15, Yo * um / 2, 'x = 0\nmech: Sym\noptics: PEC', ha='right', va='center', fontsize=10)
ax.text(Xo * um / 2, -0.08, 'y = 0:   mech Sym   |   optics PEC', ha='center', va='top', fontsize=10)
ax.set_xlim(-1.6, Xo * um + 0.2); ax.set_ylim(-0.4, Yo * um + 0.15); ax.set_aspect('equal')
ax.set_xlabel('x (µm)'); ax.set_ylabel('y (µm)')
ax.set_title('(b) simulated 1/8 (top view, z = 0)', loc='left', fontweight='bold')

# (c) cross-section y-z
ax = fig.add_subplot(gs[2, 0])
Zi, Zo = T2 + c['pad_z'], T2 + c['pad_z'] + c['d_pml']
ax.add_patch(Rectangle((0, 0), Yo * um, Zo * um, fc=PML, ec='k', lw=0.8, hatch='//'))
ax.add_patch(Rectangle((0, 0), Yi * um, Zi * um, fc=AIR, ec='k', lw=0.8))
ax.add_patch(Rectangle((0, 0), W2 * um, T2 * um, fc=BEAM, ec='k', lw=0.8))
ax.text(Yo * um / 2, -0.08, 'z = 0:   mech Sym   |   optics PMC', ha='center', va='top', fontsize=10)
ax.text((Yi + c['d_pml'] / 2) * um, Zo * um / 2, 'PML', ha='center', va='center', fontsize=11, fontweight='bold')
ax.text(W2 * um / 2, T2 * um + 0.05, 'beam', ha='center', va='bottom', fontsize=10)
ax.text(Yi * um / 2, Zi * um / 2, 'air', ha='center', va='center', fontsize=11, color='0.4')
ax.set_xlim(-0.1, Yo * um + 0.1); ax.set_ylim(-0.4, Zo * um + 0.1); ax.set_aspect('equal')
ax.set_xlabel('y (µm)'); ax.set_ylabel('z (µm)')
ax.set_title('(c) cross-section', loc='left', fontweight='bold')

# (d) taper profile
ax = fig.add_subplot(gs[2, 1])
j = np.arange(len(x))
ax.plot(j, a, 'k-o', ms=4, label='a')
ax.plot(j, hx, '-o', color='#27AE60', ms=4, label='hx')
ax.plot(j, hy, '-o', color='#C0392B', ms=4, label='hy')
ref = RD.parent / 'nanobeam_oh2026/reference/oh2026_cavity_profile.json'
if 'oh2026' in RD.name and ref.exists():
    r = json.load(open(ref))
    ax.plot(np.arange(11), r['pitch_nm_from_center_outward'], 'ks', mfc='none', ms=7, label='Oh Fig. 1b')
    ax.plot(np.arange(11), r['hy_nm_hole_0_to_10'], 's', color='#C0392B', mfc='none', ms=7)
ax.axvspan(-0.5, M - 0.5, color=COL['taper'], alpha=0.08)
ax.set_xlabel('hole index j (0 = center)'); ax.set_ylabel('nm')
ax.legend(fontsize=9, ncol=2, loc='lower right')
ax.set_title(f"(d) taper: d={c['d']}, M={M}, η={c['eta']}, ξ={c['xi']}, χ={c['chi']}", loc='left', fontweight='bold')

fig.suptitle(f"Full cavity model: a={c['a_m']}, w={c['w']}, t={c['t']}, hx={c['hx_m']}, hy={c['hy_m']} nm, n={c['n_d']}",
             fontsize=13, fontweight='bold')
for ext in ('png', 'pdf'):
    fig.savefig(RD / f'schematic.{ext}', dpi=150, facecolor='white', bbox_inches='tight')
print(f'Saved {RD}/schematic.png')
