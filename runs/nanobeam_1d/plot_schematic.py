"""
plot_schematic.py  (runs locally on Mac)
Proposed simulation setup for the 1D diamond nanobeam phononic crystal -- for review
BEFORE any model is built.

Confirmed (user, 2026-10-13/14): t = 140 nm, w = 400 nm (first runs), elliptical holes
parameterized by hx/a and hy/w, isotropic diamond, quarter cell with symmetry planes at
y=0 and z=0 (4 mode classes), Floquet BC along x, Gamma->X.
NOT chosen yet: a, hx/a, hy/w ranges -> drawn with PLACEHOLDER proportions, labelled
symbolically. Change PLACEHOLDER below to redraw.

Usage (from project root):
    python runs/nanobeam_1d/plot_schematic.py
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, FancyArrowPatch, Polygon
from pathlib import Path

OUT = Path('runs/nanobeam_1d/figures')
OUT.mkdir(parents=True, exist_ok=True)

W_NM, T_NM = 400.0, 140.0                      # confirmed
PAD_NM = 1500.0                                # air padding (user, 2026-10-14; matches 2D t_air)
PLACEHOLDER = dict(a_nm=500.0, hx_a=0.50, hy_w=0.60)   # drawing only -- NOT chosen values
a = PLACEHOLDER['a_nm']; hx = PLACEHOLDER['hx_a'] * a; hy = PLACEHOLDER['hy_w'] * W_NM
w, t = W_NM, T_NM

SLAB, HOLE_EC, QUAD, AIR = '#B8D4E8', '#2C5F8A', '#F5B041', '#FDF6E3'
RED, GREEN, BLUE, PURPLE, GREY = '#C0392B', '#117A65', '#2E86C1', '#7D3C98', '#7F8C8D'


def arrow(ax, p0, p1, c, style='<->', lw=1.3, ms=9):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, color=c, lw=lw, mutation_scale=ms,
                                 shrinkA=0, shrinkB=0, zorder=6))


fig = plt.figure(figsize=(16, 13))
gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.15, 1.0], hspace=0.38, wspace=0.18)

# --- (A) top view of the beam -------------------------------------------------------
ax = fig.add_subplot(gs[0, :])
N = 5
ax.add_patch(Rectangle((-0.6 * a, -w / 2), (N + 0.2) * a, w, fc=SLAB, ec=HOLE_EC, lw=1.5))
for n in range(N):
    ax.add_patch(Ellipse(((n - 0.0) * a, 0), hx, hy, fc='white', ec=HOLE_EC, lw=1.3))
x0 = 2 * a - a / 2
ax.add_patch(Rectangle((x0, -w / 2), a, w, fc='none', ec=RED, lw=2.4, zorder=5))
ax.text(x0 + a / 2, w / 2 + 25, 'unit cell', color=RED, ha='center', va='bottom', fontsize=10)
arrow(ax, (x0, -w / 2 - 45), (x0 + a, -w / 2 - 45), PURPLE)
ax.text(x0 + a / 2, -w / 2 - 60, 'a', color=PURPLE, ha='center', va='top', fontsize=10)
arrow(ax, (-0.6 * a - 40, -w / 2), (-0.6 * a - 40, w / 2), PURPLE)
ax.text(-0.6 * a - 55, 0, f'w = {w:.0f} nm', color=PURPLE, ha='right', va='center', fontsize=10)
cx = 3 * a
arrow(ax, (cx - hx / 2, 0), (cx + hx / 2, 0), BLUE)
ax.text(cx, 12, r'$h_x$', color=BLUE, ha='center', va='bottom', fontsize=11)
arrow(ax, (cx + hx / 2 + 15, -hy / 2), (cx + hx / 2 + 15, hy / 2), GREEN)
ax.text(cx + hx / 2 + 25, -hy / 4, r'$h_y$', color=GREEN, ha='left', va='top', fontsize=11)
# bridge and rail
arrow(ax, (cx + hx / 2, -hy / 2 - 10), (cx + a - hx / 2, -hy / 2 - 10), '#D35400', lw=1.2, ms=7)
ax.text(cx + a / 2, -hy / 2 - 22, r'bridge $a-h_x$', color='#D35400', ha='center', va='top', fontsize=9)
arrow(ax, (cx, hy / 2), (cx, w / 2), '#D35400', lw=1.2, ms=7)
ax.text(cx, w / 2 + 12, r'rail $(w-h_y)/2$', color='#D35400', ha='center', va='bottom', fontsize=9)
ax.annotate('', xy=(N * a - 0.2 * a, -w / 2 - 110), xytext=(N * a - 0.9 * a, -w / 2 - 110),
            arrowprops=dict(arrowstyle='-|>', color='k'))
ax.text(N * a - 0.2 * a, -w / 2 - 110, '  x', va='center', fontsize=10)
ax.set_xlim(-1.05 * a, (N + 0.15) * a); ax.set_ylim(-w / 2 - 150, w / 2 + 70)
ax.set_aspect('equal'); ax.axis('off')
ax.set_title('(A)  Top view',
             fontsize=11, fontweight='bold', loc='left')

# --- (B) simulated quarter cell, top view (x-y) -----------------------------------------
ax = fig.add_subplot(gs[1, 0])
ax.add_patch(Rectangle((0, -w / 2), a, w, fc='#EAF2F8', ec=GREY, lw=1, ls='--'))
ax.add_patch(Ellipse((a / 2, 0), hx, hy, fc='white', ec=GREY, lw=1, ls='--'))
qx = np.r_[np.linspace(0, a, 2)]
ax.add_patch(Rectangle((0, w / 2), a, 0.55 * w, fc=AIR, ec='#B7950B', lw=1.2, zorder=1))
ax.text(a / 2, w / 2 + 0.28 * w, 'air', color='#7D6608', ha='center', va='center', fontsize=11, zorder=5)
quad = Rectangle((0, 0), a, w / 2, fc=SLAB, ec='#1B4F72', lw=2.4, zorder=2)
ax.add_patch(quad)
th = np.linspace(0, np.pi, 100)
ax.add_patch(Polygon(np.c_[a / 2 + hx / 2 * np.cos(th), hy / 2 * np.sin(th)], closed=True,
                     fc='white', ec=HOLE_EC, lw=1.6, zorder=3))
# BCs
for xf, lbl in ((0, 'x = 0'), (a, 'x = a')):
    ax.plot([xf, xf], [0, w / 2], color=RED, lw=4, zorder=4, solid_capstyle='butt')
ax.text(-10, w / 4, 'Floquet', color=RED, ha='right', va='center', fontsize=9.5)
ax.text(a + 10, w / 4, 'Floquet', color=RED, ha='left', va='center', fontsize=9.5)
arrow(ax, (0.05 * a, w / 2 + 0.6 * w), (0.95 * a, w / 2 + 0.6 * w), RED, style='<|-|>')
ax.text(a / 2, w / 2 + 0.62 * w, r'$u(x{=}a) = e^{-ik_x a}\,u(x{=}0)$', color=RED, ha='center', va='bottom', fontsize=10)
ax.plot([0, a / 2 - hx / 2], [0, 0], color=GREEN, lw=4, zorder=4, solid_capstyle='butt')
ax.plot([a / 2 + hx / 2, a], [0, 0], color=GREEN, lw=4, zorder=4, solid_capstyle='butt')
ax.text(a / 2, -w / 2 - 12, 'green = y = 0 plane', color=GREEN, ha='center', va='top', fontsize=9.5)
ax.plot([0, a], [w / 2, w / 2], color=GREY, lw=2.5, zorder=4)
ax.text(a * 0.85, w / 2 - 12, 'free', color=GREY, ha='center', va='top', fontsize=9)
ax.text(a / 2, hy / 4, 'hole', color=GREY, ha='center', va='center', fontsize=9)
ax.text(a / 2, -w / 2 + 12, 'mirror (not simulated)', color=GREY, ha='center', fontsize=8.5)
ax.set_xlim(-0.35 * a, 1.35 * a); ax.set_ylim(-w / 2 - 75, w / 2 + 0.95 * w)
ax.set_aspect('equal'); ax.axis('off')
ax.set_title('(B)  Simulated cell, top view (x-y)',
             fontsize=11, fontweight='bold', loc='left')

# --- (C) cross-section (y-z), to scale, with zoom of the beam ------------------------------
ax = fig.add_subplot(gs[1, 1])
Ya, Za = w / 2 + PAD_NM, PAD_NM
ax.add_patch(Rectangle((0, 0), Ya, Za, fc=AIR, ec='#B7950B', lw=1.5))
ax.add_patch(Rectangle((0, 0), w / 2, t / 2, fc=SLAB, ec='#1B4F72', lw=1.5, zorder=2))
ax.plot([0, 0], [0, Za], color=GREEN, lw=3, zorder=3)
ax.plot([0, Ya], [0, 0], color=BLUE, lw=3, zorder=3)
ax.text(Ya * 0.55, Za * 0.55, 'air', ha='center', va='center', fontsize=14, color='#7D6608')
arrow(ax, (w / 2, Za + 80), (Ya, Za + 80), PURPLE)
ax.text((w / 2 + Ya) / 2, Za + 100, '1.5 um', color=PURPLE, ha='center', va='bottom', fontsize=10)
arrow(ax, (-90, 0), (-90, Za), PURPLE)
ax.text(-110, Za / 2, '1.5 um', color=PURPLE, ha='right', va='center', fontsize=10)
ax.set_xlim(-450, Ya + 1300); ax.set_ylim(-250, Za + 300)
ax.set_aspect('equal'); ax.axis('off')
ax.set_title('(C)  Cross-section (y-z), to scale', fontsize=11, fontweight='bold', loc='left')
# zoom of the beam, placed OUTSIDE the air box
ins = ax.inset_axes([0.67, 0.30, 0.31, 0.32])
ins.add_patch(Rectangle((0, 0), w / 2 + 40, t / 2 + 30, fc=AIR, ec='none'))
ins.add_patch(Rectangle((0, 0), w / 2, t / 2, fc=SLAB, ec='#1B4F72', lw=2))
ins.plot([0, 0], [0, t / 2 + 30], color=GREEN, lw=4, solid_capstyle='butt')
ins.plot([0, w / 2 + 40], [0, 0], color=BLUE, lw=4, solid_capstyle='butt')
ins.text(w / 4, t / 4, 'beam', ha='center', va='center', fontsize=10)
ins.text(w / 4, -12, '200 nm', ha='center', va='top', fontsize=8.5, color=PURPLE)
ins.text(w / 2 + 6, t / 4, '70 nm', ha='left', va='center', fontsize=8.5, color=PURPLE)
ins.set_xlim(-5, w / 2 + 40); ins.set_ylim(-35, t / 2 + 30)
ins.set_aspect('equal'); ins.set_xticks([]); ins.set_yticks([])
for sp in ins.spines.values():
    sp.set_edgecolor('#1B4F72')
ax.indicate_inset_zoom(ins, edgecolor='#1B4F72', alpha=0.8)
ax.text(Ya * 0.5, -120, 'green = y = 0 plane     blue = z = 0 plane', ha='center', va='top', fontsize=9.5)

# --- (D) symmetry classes ---------------------------------------------------------------
ax = fig.add_subplot(gs[2, 0]); ax.axis('off')
rows = [['class', 'y = 0', 'z = 0', 'mode family'],
        ['Y+ Z+', 'sym', 'sym', 'longitudinal / breathing'],
        ['Y- Z+', 'antisym', 'sym', 'in-plane bending'],
        ['Y+ Z-', 'sym', 'antisym', 'out-of-plane bending'],
        ['Y- Z-', 'antisym', 'antisym', 'torsion']]
tb = ax.table(cellText=rows[1:], colLabels=rows[0], cellLoc='center',
              colWidths=[0.15, 0.17, 0.17, 0.51], bbox=[0.05, 0.15, 0.9, 0.8])
tb.auto_set_font_size(False); tb.set_fontsize(11)
for (r_, c_), cell in tb.get_celld().items():
    if r_ == 0:
        cell.set_facecolor('#D6EAF8'); cell.set_text_props(fontweight='bold')
ax.set_title('(D)  Four mode-symmetry classes',
             fontsize=11, fontweight='bold', loc='left')

# --- (E) 1D BZ ------------------------------------------------------------------------------
ax = fig.add_subplot(gs[2, 1])
ax.plot([-1, 1], [0, 0], color=HOLE_EC, lw=2)
for xv, lbl in ((-1, r'$-X$'), (0, r'$\Gamma$'), (1, r'$X$')):
    ax.plot(xv, 0, 'o', color=HOLE_EC, ms=8)
    ax.text(xv, -0.12, lbl, ha='center', va='top', fontsize=13, color=HOLE_EC)
ax.plot([0, 1], [0, 0], color=RED, lw=4)
ax.text(0.5, 0.08, r'$k_x = 0 \ldots \pi/a$', color=RED, ha='center', fontsize=12)
ax.set_xlim(-1.3, 1.3); ax.set_ylim(-0.5, 0.3); ax.axis('off')
ax.set_title('(E)  1D Brillouin zone + k-path', fontsize=11, fontweight='bold', loc='left')

fig.suptitle('1D diamond nanobeam -- proposed simulation setup\n'
             f'w = {w:.0f} nm, t = {t:.0f} nm, air 1.5 um  |  a, hx, hy = placeholders', fontsize=13, fontweight='bold')
for ext in ('png', 'pdf'):
    fig.savefig(OUT / f'schematic_proposed.{ext}', dpi=150, facecolor='white', bbox_inches='tight')
print(f'Saved {OUT}/schematic_proposed.png')
