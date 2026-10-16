"""
plot_verification.py  (Mac)
Oh 2026 cavity reproduction figure: fields at the resonances on the z = 0 midplane (unfolded from the
1/8 model with the model's symmetries: Ey odd in x, even in y; |u| even in both), and me vs Oh.

Usage (from project root):
    python runs/cavity_oh2026/plot_verification.py
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.patches import Ellipse

RD = Path('runs/cavity_oh2026')
d = np.load(RD / 'data' / 'post.npz', allow_pickle=True)
info = json.load(open(RD / 'data' / 'build_info.json'))
c, L = info['cfg'], {k: np.array(v) for k, v in info['layout'].items()}
W2, um = c['w'] / 2, 1e-3
XMAX = 9000.0        # nm shown on each side (cavity + taper + a few mirror cells)
R = d['g_rows']      # k, f, loc, meff, xzpf, gMB, gPE, g0, imfrac
io = int(d['i_opt'])
f_o, Q_o = d['f_opt'][io - 1], d['Q_opt'][io - 1]
# cavity breathing mode = lowest-frequency localized mode with |g0| > 50 kHz (user, 2026-10-14: the first
# breathing mode, single central bulge like Oh Fig. 1c)
ib = int(min(np.where(np.abs(R[:, 7]) > 50e3)[0], key=lambda i: R[i, 1]))


def in_hole(x, y):
    h = np.zeros_like(x, bool)
    for xj, hx, hy in zip(L['x'], L['hx'], L['hy']):
        h |= ((np.abs(x) - xj) / (hx / 2)) ** 2 + (y / (hy / 2)) ** 2 < 1
    return h


def unfold(x, y, f, sx, sy):
    X = np.concatenate([x, -x, x, -x]); Y = np.concatenate([y, y, -y, -y])
    F = np.concatenate([f, sx * f, sy * f, sx * sy * f])
    return X, Y, F


def field_panel(ax, x, y, f, sx, sy, cmap, vmin, vmax, beam_only):
    keep = (np.abs(y) <= (W2 + 0.5) if beam_only else np.abs(y) <= W2 + 600) & (x <= XMAX + 700)
    X, Y, F = unfold(x[keep], y[keep], f[keep], sx, sy)
    tri = mtri.Triangulation(X * um, Y * um)
    cx, cy = X[tri.triangles].mean(1), Y[tri.triangles].mean(1)
    mask = np.abs(cy) > (W2 if beam_only else W2 + 600)
    if beam_only:
        mask |= in_hole(cx, cy)
    tri.set_mask(mask)
    im = ax.tripcolor(tri, F, cmap=cmap, vmin=vmin, vmax=vmax, shading='gouraud', rasterized=True)
    ax.plot([-XMAX * um, XMAX * um, XMAX * um, -XMAX * um, -XMAX * um], [-W2 * um, -W2 * um, W2 * um, W2 * um, -W2 * um],
            color='k', lw=0.6)
    for xj, hx, hy in zip(L['x'], L['hx'], L['hy']):
        for s in ((1, -1) if xj > 0 else (1,)):
            if abs(xj) < XMAX:
                ax.add_patch(Ellipse((s * xj * um, 0), hx * um, hy * um, fc='none', ec='k', lw=0.4))
    ax.set_xlim(-XMAX * um, XMAX * um); ax.set_ylim(-(W2 + 600) * um, (W2 + 600) * um); ax.set_aspect('equal')
    ax.set_yticks([]); ax.set_xlabel('x (µm)')
    return im


fig = plt.figure(figsize=(14, 10.5))
gs = fig.add_gridspec(4, 2, height_ratios=[1, 1, 1, 1.25], width_ratios=[1, 0.02], hspace=0.55, wspace=0.03)

ax = fig.add_subplot(gs[0, 0])
E = d['Ey_opt'][0].astype(float); E = E / np.abs(E).max()
im = field_panel(ax, d['Ey_opt_x'], d['Ey_opt_y'], E, -1, 1, 'RdBu_r', -1, 1, beam_only=False)
ax.set_title(f'(a) optical cavity mode: {f_o/1e12:.1f} THz ({299792.458/(f_o/1e12):.0f} nm), Q$_o$ = {Q_o:.2g}   —   E$_y$',
             loc='left', fontweight='bold')
fig.colorbar(im, cax=fig.add_subplot(gs[0, 1]), ticks=[-1, 0, 1])

MF = np.load(RD / 'data' / 'mech_fields.npz')
MQ = np.load(RD / 'data' / 'mechq_ideal.npz')
Qm = lambda fr: MQ['Q'][np.argmin(np.abs(MQ['f'] - fr))]
order = sorted([ib] + [i for i in np.argsort(-np.abs(R[:, 7])) if i != ib][:1], key=lambda i: R[i, 1])
TAG = {ib: 'cavity breathing mode'}
for row, i in zip((1, 2), order):
    k = int(R[i, 0])
    ax = fig.add_subplot(gs[row, 0])
    x, y = MF[f'top_x_{k}'], MF[f'top_y_{k}']
    s_ = x <= XMAX + 600
    x, y, u, v, w = x[s_], y[s_], MF[f'top_u_{k}'][s_], MF[f'top_v_{k}'][s_], MF[f'top_w_{k}'][s_]
    X = np.concatenate([x, -x, x, -x]); Y = np.concatenate([y, y, -y, -y])
    U = np.concatenate([u, -u, u, -u]); V = np.concatenate([v, v, -v, -v]); Wz = np.tile(w, 4)
    mag = np.sqrt(U ** 2 + V ** 2 + Wz ** 2); n = mag.max()
    tri = mtri.Triangulation(X, Y)
    cx, cy = X[tri.triangles].mean(1), Y[tri.triangles].mean(1)
    td = mtri.Triangulation((X + 220 * U / n) * um, (Y + 220 * V / n) * um, tri.triangles,
                            mask=in_hole(cx, cy) | (np.abs(cy) > W2))
    im = ax.tripcolor(td, mag / n, cmap='jet', vmin=0, vmax=1, shading='gouraud', rasterized=True)
    ax.set_xlim(-XMAX * um, XMAX * um); ax.set_ylim(-(W2 + 600) * um, (W2 + 600) * um); ax.set_aspect('equal')
    ax.set_yticks([]); ax.set_xlabel('x (µm)')
    ax.set_title(f"({'bc'[row-1]}) {TAG.get(i, '2nd breathing mode')}: {R[i,1]/1e9:.3f} GHz,"
                 f"  Q$_m$ = {Qm(R[i,1]):.1e} (ideal)   —   deformed, |u|", loc='left', fontweight='bold')
    fig.colorbar(im, cax=fig.add_subplot(gs[row, 1]), ticks=[0, 1])

# (d) comparison table (g0 omitted from figures for now, user 2026-10-14; still computed in post.npz)
gs2 = gs[3, 0].subgridspec(1, 3, width_ratios=[0.5, 1, 0.5])
ax = fig.add_subplot(gs2[1]); ax.axis('off')
rows = [['', 'me', 'Oh sim', 'Oh meas'],
        ['optical (THz)', f'{f_o/1e12:.1f}', '192', '190.1'],
        ['mech. (GHz)', f'{R[ib,1]/1e9:.2f}', '6.34', '6.23'],
        ['Q$_o$', f'{Q_o:.1e}', '—', '3.8e4'],
        ['Q$_m$', f'{Qm(R[ib,1]):.0e}*', 'not sim.', '1.9e6']]
tb = ax.table(cellText=rows, loc='center', cellLoc='center', colWidths=[0.4, 0.2, 0.2, 0.2])
tb.auto_set_font_size(False); tb.set_fontsize(11); tb.scale(1, 1.6)
for j in range(4):
    tb[0, j].set_text_props(fontweight='bold')
ax.set_title('(d) vs Oh 2026', loc='left', fontweight='bold')
ax.text(0.5, -0.12, '* ideal geometry, no disorder, no shield', transform=ax.transAxes, ha='center', fontsize=8)

fig.suptitle('Oh 2026 cavity reproduction, me (|x| < 9 µm of the 25 µm beam)', fontsize=13, fontweight='bold')
fig.savefig(RD / 'verification.png', dpi=150, facecolor='white', bbox_inches='tight')
print(f'Saved {RD}/verification.png')
