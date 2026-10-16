"""
plot_mech_modes.py  (Mac)
All localized mechanical modes of the Oh 2026 cavity, drawn like Oh Fig. 1(c): top face, deformed
geometry (exaggerated), color = |u| normalized. Unfolded with the model symmetries
(x=0 Sym: u odd in x; y=0 Sym: v odd in y). Right column: sidewall y-displacement v(x, y=w/2) --
a breathing mode pushes both sidewalls out together (v > 0 at y = +w/2) under one smooth envelope.

Usage (from project root):
    python runs/cavity_oh2026/plot_mech_modes.py
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

RD = Path('runs/cavity_oh2026')
F = np.load(RD / 'data' / 'mech_fields.npz')
P = np.load(RD / 'data' / 'post.npz', allow_pickle=True)
info = json.load(open(RD / 'data' / 'build_info.json'))
L = {k: np.array(v) for k, v in info['layout'].items()}
W2 = info['cfg']['w'] / 2
g0 = {int(r[0]): abs(r[7]) / 1e3 for r in P['g_rows']}
XMAX, SCALE = 6000.0, 220.0       # nm shown per side; displacement exaggeration (nm per unit max)


def in_hole(x, y):
    h = np.zeros_like(x, bool)
    for xj, hx, hy in zip(L['x'], L['hx'], L['hy']):
        h |= ((np.abs(x) - xj) / (hx / 2)) ** 2 + (y / (hy / 2)) ** 2 < 1
    return h


ks = [int(k) for k in F['k']]
fig, axes = plt.subplots(len(ks), 2, figsize=(15, 1.55 * len(ks)), gridspec_kw=dict(width_ratios=[3, 1]))
for row, k in enumerate(ks):
    x, y = F[f'top_x_{k}'], F[f'top_y_{k}']
    u, v, w = F[f'top_u_{k}'], F[f'top_v_{k}'], F[f'top_w_{k}']
    s = (x <= XMAX + 600)
    x, y, u, v, w = x[s], y[s], u[s], v[s], w[s]
    X = np.concatenate([x, -x, x, -x]); Y = np.concatenate([y, y, -y, -y])
    U = np.concatenate([u, -u, u, -u]); V = np.concatenate([v, v, -v, -v]); Wz = np.concatenate([w, w, w, w])
    mag = np.sqrt(U ** 2 + V ** 2 + Wz ** 2); n = mag.max()
    tri = mtri.Triangulation(X, Y)
    cx, cy = X[tri.triangles].mean(1), Y[tri.triangles].mean(1)
    tri.set_mask(in_hole(cx, cy) | (np.abs(cy) > W2))
    td = mtri.Triangulation(X + SCALE * U / n, Y + SCALE * V / n, tri.triangles, mask=tri.mask)
    ax = axes[row, 0]
    ax.tripcolor(td, mag / n, cmap='jet', vmin=0, vmax=1, shading='gouraud', rasterized=True)
    ax.plot([-XMAX, XMAX, XMAX, -XMAX, -XMAX], [-W2, -W2, W2, W2, -W2], color='0.6', lw=0.5, ls=':')
    ax.set_xlim(-XMAX, XMAX); ax.set_ylim(-W2 - 300, W2 + 300); ax.set_aspect('equal'); ax.axis('off')
    f = F['f'][list(F['k']).index(k)] / 1e9
    ax.text(-XMAX, W2 + 320, f'mode {k}:  {f:.3f} GHz', fontsize=10,
            fontweight='bold', va='bottom')
    # sidewall v(x)
    ax = axes[row, 1]
    sw = (y > W2 - 3)
    o = np.argsort(x[sw])
    xs, vs = x[sw][o], v[sw][o] / n
    ax.plot(np.concatenate([-xs[::-1], xs]) / 1e3, np.concatenate([vs[::-1], vs]), 'k-', lw=1)
    ax.axhline(0, color='0.7', lw=0.6); ax.set_xlim(-XMAX / 1e3, XMAX / 1e3); ax.set_ylim(-1.05, 1.05)
    ax.set_yticks([-1, 0, 1]); ax.tick_params(labelsize=8)
    if row == 0:
        ax.set_title('sidewall v (y = w/2)', fontsize=10, fontweight='bold')
    if row < len(ks) - 1:
        ax.set_xticklabels([])
    else:
        ax.set_xlabel('x (µm)')
fig.suptitle('Oh 2026 cavity, me: localized mechanical modes (top face, deformed, color = |u|)', fontsize=12,
             fontweight='bold')
fig.tight_layout()
fig.savefig(RD / 'mech_modes.png', dpi=140, facecolor='white')
print(f'Saved {RD}/mech_modes.png')
