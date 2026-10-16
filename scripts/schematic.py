"""
schematic.py  (runs locally on Mac; needs shapely)
Shared, geometry-exact schematic for unit_cell_3.mph runs.

Every shape is drawn from the definitions read out of the .mph
(runs/diamond_a_sweep/diag_geometry.py, 2026-10-14):
  hole : r1 (lx=w, ly=d, base=center, pos=(0,d/2)) rotated +/-120 deg about the origin,
         union, fillet f_r  -> arms of length d (from hole center) at 90/210/330 deg
  cell : pol1 rhombus (a/2,-a/(2sqrt3)), (-a/2,-a/(2sqrt3)), (-a,a/sqrt3), (0,a/sqrt3)
         + mov1 shift (default (50 nm, -50/sqrt3 nm); the a-sweep fill overrides it)
         a1=(a,0), a2=(-a/2, a*sqrt3/2)   (rhombus leans LEFT)
  BCs  : Floquet pc1 on the faces parallel to a1 (bottom/top),
         pc2 on the faces parallel to a2 (slanted); z=0 sym1/as1; top face free
  BZ   : hexagon with K=(4pi/3a, 0) a vertex, M=(pi/a, pi/(sqrt3 a)) an edge midpoint

Usage from a run's plot_schematic.py:
    import sys; sys.path.insert(0, 'scripts')
    from schematic import make_schematic
    make_schematic(a_nm=300, d_nm=104, w_nm=107, fr_nm=16, t_nm=140, ..., out_stem=...)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, FancyArrowPatch
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import affinity

SQ3 = np.sqrt(3.0)
DEFAULT_SHIFT_NM = (50.0, -50.0 / SQ3)

SLAB, GHOST, HOLE_EC = '#B8D4E8', '#DCEAF5', '#2C5F8A'
RED, GREEN, PURPLE, BLUE, GREY = '#C0392B', '#117A65', '#7D3C98', '#2E86C1', '#7F8C8D'
BZ_FC = '#E8F4D4'


# --- geometry (nm) ---------------------------------------------------------------

def hole_poly(d, w, fr):
    base = Polygon([(-w / 2, 0), (w / 2, 0), (w / 2, d), (-w / 2, d)])
    arms = [affinity.rotate(base, ang, origin=(0, 0)) for ang in (0, 120, -120)]
    u = unary_union(arms)
    # fillet: round convex corners (opening) and concave corners (closing) by fr
    return (u.buffer(-fr, join_style=1).buffer(fr, join_style=1)
             .buffer(fr, join_style=1).buffer(-fr, join_style=1))


def cell_verts(a, shift):
    v = np.array([[a / 2, -a / (2 * SQ3)], [-a / 2, -a / (2 * SQ3)],
                  [-a, a / SQ3], [0.0, a / SQ3]])
    return v + np.asarray(shift)


def lattice(a):
    return np.array([a, 0.0]), np.array([-a / 2, a * SQ3 / 2])


def _add_poly(ax, shp, **kw):
    geoms = getattr(shp, 'geoms', [shp])
    for g in geoms:
        ax.add_patch(MplPolygon(np.asarray(g.exterior.coords), closed=True, **kw))


def _arrow(ax, p0, p1, color, lw=1.4, style='<->', ms=10, z=6):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, color=color, lw=lw,
                                 mutation_scale=ms, zorder=z, shrinkA=0, shrinkB=0))


# --- panels -----------------------------------------------------------------------

def panel_tiling(ax, a, d, w, fr, shift):
    a1, a2 = lattice(a)
    h = hole_poly(d, w, fr)
    cv = cell_verts(a, shift)
    span = 2.6 * a
    ax.add_patch(plt.Rectangle((-span, -span), 2 * span, 2 * span, fc=SLAB, ec='none', zorder=0))
    for n1 in range(-4, 5):
        for n2 in range(-4, 5):
            L = n1 * a1 + n2 * a2
            if np.abs(L).max() > 2.6 * a:
                continue
            _add_poly(ax, affinity.translate(h, *L), fc='white', ec=HOLE_EC, lw=0.8, zorder=2)
    ax.add_patch(MplPolygon(cv, closed=True, fc='none', ec=RED, lw=2.4, zorder=4))
    o = cv[1]   # (-a/2, -a/(2sqrt3)) + shift : cell corner the lattice vectors start from
    _arrow(ax, o, o + a1, RED, lw=1.8, style='-|>', ms=14)
    _arrow(ax, o, o + a2, RED, lw=1.8, style='-|>', ms=14)
    ax.text(*(o + a1 / 2 + np.array([0, -0.13 * a])), r'$\mathbf{a}_1=(a,0)$', color=RED,
            ha='center', va='top', fontsize=10)
    ax.text(*(o + a2 / 2 + np.array([-0.08 * a, 0])), r'$\mathbf{a}_2=(-a/2,\ a\sqrt{3}/2)$',
            color=RED, ha='right', va='center', fontsize=10)
    ax.set_xlim(-1.9 * a, 1.6 * a)
    ax.set_ylim(-1.5 * a, 1.6 * a)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('(A)  Triangular lattice -- rhombus primitive cell (as in pol1)',
                 fontsize=11, fontweight='bold')


def panel_cell(ax, a, d, w, fr, t, shift, shift_label='mov1 shift'):
    cv = cell_verts(a, shift)
    h = hole_poly(d, w, fr)
    ax.add_patch(MplPolygon(cv, closed=True, fc=SLAB, ec=HOLE_EC, lw=2.2, zorder=1))
    _add_poly(ax, h, fc='white', ec=HOLE_EC, lw=1.4, zorder=2)
    # unshifted pol1 (dashed) + shift vector
    cv0 = cell_verts(a, (0, 0))
    ax.add_patch(MplPolygon(cv0, closed=True, fc='none', ec=GREY, lw=0.9, ls='--', zorder=1))
    ax.plot(0, 0, '+', color='k', ms=9, mew=1.2, zorder=5)
    ax.text(-0.04 * a, -0.04 * a, 'hole center\n(origin)', fontsize=7.5, ha='right', va='top', color='k')
    _arrow(ax, (cv0[1][0], cv0[1][1]), (cv[1][0], cv[1][1]), GREY, lw=1.2, style='-|>', ms=9)
    ax.text(cv[1][0] - 0.03 * a, cv[1][1] - 0.05 * a,
            f'{shift_label}\n({shift[0]:.1f}, {shift[1]:.1f}) nm', fontsize=7.5, color=GREY,
            ha='right', va='top')
    # d along the up arm (from hole center)
    xd = w / 2 + 0.06 * a
    _arrow(ax, (xd, 0), (xd, d), BLUE)
    ax.plot([0, xd + 0.02 * a], [0, 0], color=BLUE, lw=0.6, ls=':')
    ax.plot([w / 2, xd + 0.02 * a], [d, d], color=BLUE, lw=0.6, ls=':')
    ax.text(xd + 0.03 * a, d / 2, f'$d$ = {d:.0f} nm\n(from center)', color=BLUE,
            fontsize=9, va='center')
    # w across the up arm, near its tip
    yw = d - max(fr, 0.06 * a) - 0.03 * a
    _arrow(ax, (-w / 2, yw), (w / 2, yw), GREEN)
    ax.text(-w / 2 - 0.03 * a, yw, f'$w$ = {w:.0f} nm', color=GREEN, fontsize=9,
            ha='right', va='center')
    ax.text(-w / 2 - 0.03 * a, d + 0.02 * a, f'fillet $f_r$ = {fr:.0f} nm', color=GREY,
            fontsize=8, ha='right', va='bottom')
    # a along the bottom edge (a1)
    yb = cv[1][1] - 0.12 * a
    _arrow(ax, (cv[1][0], yb), (cv[0][0], yb), PURPLE)
    ax.text((cv[0][0] + cv[1][0]) / 2, yb - 0.03 * a, f'$a$ = {a:.0f} nm', color=PURPLE,
            fontsize=10, ha='center', va='top')
    # side view inset: slab thickness
    x0, y0 = cv[0][0] + 0.12 * a, cv[0][1]
    sw, sh = 0.42 * a, 0.42 * a * min(t / a, 1.2)
    ax.add_patch(plt.Rectangle((x0, y0), sw, sh, fc=SLAB, ec=HOLE_EC, lw=1.4))
    ax.add_patch(plt.Rectangle((x0 + 0.17 * sw, y0), 0.25 * sw, sh, fc='white', ec=HOLE_EC, lw=1.0))
    _arrow(ax, (x0 + sw + 0.04 * a, y0), (x0 + sw + 0.04 * a, y0 + sh), PURPLE, lw=1.2, ms=8)
    ax.text(x0 + sw + 0.07 * a, y0 + sh / 2, f'$t$ = {t:.0f} nm', color=PURPLE, fontsize=9, va='center')
    ax.text(x0 + sw / 2, y0 - 0.03 * a, 'side view', color=GREY, fontsize=7.5, ha='center', va='top')
    allx = np.r_[cv[:, 0], cv0[:, 0], x0 + sw + 0.35 * a]
    ally = np.r_[cv[:, 1], cv0[:, 1]]
    ax.set_xlim(allx.min() - 0.45 * a, allx.max())
    ax.set_ylim(ally.min() - 0.3 * a, ally.max() + 0.12 * a)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('(B)  Unit cell (top view): hole at lower-triangle centroid,\n'
                 '3 arms of length d from the center at 90/210/330 deg', fontsize=11, fontweight='bold')


def panel_floquet(ax, a, d, w, fr, shift):
    a1, a2 = lattice(a)
    cv = cell_verts(a, shift)
    h = hole_poly(d, w, fr)
    span = 2.2 * a
    ax.add_patch(plt.Rectangle((-span, -span), 2 * span, 2 * span, fc=GHOST, ec='none', zorder=0))
    for n1 in range(-3, 4):
        for n2 in range(-3, 4):
            L = n1 * a1 + n2 * a2
            if np.abs(L).max() > 2.2 * a:
                continue
            ax.add_patch(MplPolygon(cv + L, closed=True, fc='none', ec='#A6ACAF', lw=0.7, zorder=1))
            _add_poly(ax, affinity.translate(h, *L), fc='white', ec=HOLE_EC, lw=0.6, zorder=2, alpha=0.9)
    ax.add_patch(MplPolygon(cv, closed=True, fc=SLAB, ec='#1B4F72', lw=2.6, zorder=3))
    _add_poly(ax, h, fc='white', ec=HOLE_EC, lw=1.3, zorder=4)
    # pc1: faces parallel to a1 (bottom cv[1]->cv[0], top cv[2]->cv[3])
    for p0, p1, sgn in [(cv[1], cv[0], -1), (cv[2], cv[3], +1)]:
        for f in (0.3, 0.7):
            q = p0 + f * (p1 - p0)
            _arrow(ax, q, q + np.array([0, sgn * 0.17 * a]), RED, lw=1.6, style='-|>', ms=10)
    # pc2: faces parallel to a2 (left cv[1]->cv[2], right cv[0]->cv[3]); outward normal of a2-edge
    n2 = np.array([a2[1], -a2[0]]); n2 /= np.linalg.norm(n2)          # points +x side
    for p0, p1, sgn in [(cv[1], cv[2], -1), (cv[0], cv[3], +1)]:
        for f in (0.3, 0.7):
            q = p0 + f * (p1 - p0)
            _arrow(ax, q, q + sgn * 0.17 * a * n2, GREEN, lw=1.6, style='-|>', ms=10)
    ax.text(*(cv[1] + (cv[0] - cv[1]) / 2 + np.array([0, -0.3 * a])),
            r'Floquet pc1: faces $\parallel\mathbf{a}_1$', color=RED, ha='center', va='top', fontsize=9.5,
            bbox=dict(fc='white', ec='none', alpha=0.85))
    ax.text(*(cv[0] + (cv[3] - cv[0]) / 2 + np.array([0.22 * a, 0])),
            r'Floquet pc2:' + '\n' + r'faces $\parallel\mathbf{a}_2$', color=GREEN, ha='left', va='center',
            fontsize=9.5, bbox=dict(fc='white', ec='none', alpha=0.85))
    c = cv.mean(axis=0)
    ax.set_xlim(c[0] - 1.45 * a, c[0] + 1.45 * a)
    ax.set_ylim(c[1] - 0.95 * a, c[1] + 0.8 * a)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('(C)  COMSOL cell + Floquet BCs (pc1, pc2)\n'
                 r'$\mathbf{k}=(k_{Fx},k_{Fy},0)$ Cartesian;  z=0 midplane: sym1 / as1;  top face free',
                 fontsize=11, fontweight='bold')


def panel_bz(ax, a=1.0):
    r = 4 * np.pi / (3 * a)
    ang = np.linspace(0, 2 * np.pi, 7)                 # vertices at 0, 60, ... deg
    ax.fill(r * np.cos(ang), r * np.sin(ang), fc=BZ_FC, ec=HOLE_EC, lw=1.8, zorder=1)
    G = np.array([0, 0]); M = np.array([np.pi / a, np.pi / (SQ3 * a)]); K = np.array([r, 0])
    pts = [G, M, K, G]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=RED, lw=2.4, zorder=3)
    for pt, lbl, off in [(G, r'$\Gamma$', (-0.1, -0.08)), (M, r'$M$', (0.07, 0.07)), (K, r'$K$', (0.1, -0.06))]:
        ax.plot(*pt, 'o', ms=7, color=HOLE_EC, zorder=4)
        ax.text(pt[0] + off[0] * r, pt[1] + off[1] * r, lbl, fontsize=13, ha='center', va='center', color=HOLE_EC)
    ax.text(0, -1.12 * r, r'$K=(4\pi/3a,\ 0)$ vertex;  $M=(\pi/a,\ \pi/\sqrt{3}a)$ edge midpoint'
            '\nband path  $\\Gamma \\to M \\to K \\to \\Gamma$', ha='center', va='top', fontsize=9, color='#333')
    ax.set_xlim(-1.3 * r, 1.4 * r); ax.set_ylim(-1.45 * r, 1.2 * r)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('(D)  First Brillouin zone + k-path', fontsize=11, fontweight='bold')


def make_schematic(a_nm, d_nm, w_nm, fr_nm, t_nm, title, out_stem,
                   shift_nm=DEFAULT_SHIFT_NM, shift_label='mov1 shift (default)', panel_d=None):
    """panel_d: optional callable(ax) replacing the BZ panel."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 13))
    panel_tiling(axes[0, 0], a_nm, d_nm, w_nm, fr_nm, shift_nm)
    panel_cell(axes[0, 1], a_nm, d_nm, w_nm, fr_nm, t_nm, shift_nm, shift_label)
    panel_floquet(axes[1, 0], a_nm, d_nm, w_nm, fr_nm, shift_nm)
    (panel_d or panel_bz)(axes[1, 1])
    fig.suptitle(title, fontsize=12.5, fontweight='bold')
    fig.text(0.5, 0.005, 'Geometry drawn from unit_cell_3.mph feature definitions (r1, rot1/2, fil1, pol1, mov1 in wp1+wp2), '
             'read via mph on 2026-10-14.', ha='center', fontsize=8, color=GREY)
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    for ext in ('png', 'pdf'):
        fig.savefig(f'{out_stem}.{ext}', dpi=150, facecolor='white')
    plt.close(fig)
    print(f'Saved: {out_stem}.png / .pdf')


def panel_grid(ax, cells, row_labels, col_labels, row_title, col_title, title, note=None):
    """Grid of mini unit cells. cells: list of dict(row, col, a, d, w, fr, shift, text, status)
    status in {'nominal', 'ok', 'shifted', 'infeasible'} -> edge colour/hatching."""
    nr, nc = len(row_labels), len(col_labels)
    pitch = 1.0
    styles = {'ok': ('#2C5F8A', 1.0, None), 'nominal': (RED, 2.4, None),
              'shifted': ('#D68910', 2.0, None), 'infeasible': ('#7F8C8D', 1.0, '///')}
    for c in cells:
        a = c['a']
        sc = 0.36 / a                                    # normalise each mini-cell to the grid pitch
        cx, cy = c['col'] * pitch, (nr - 1 - c['row']) * pitch
        cv = cell_verts(a, c['shift'])
        ctr = cv.mean(axis=0)
        ec, lw, hatch = styles[c['status']]
        ax.add_patch(MplPolygon((cv - ctr) * sc + [cx, cy], closed=True, fc=SLAB, ec=ec, lw=lw, hatch=hatch))
        h = hole_poly(c['d'], c['w'], c['fr'])
        h = affinity.translate(affinity.scale(affinity.translate(h, -ctr[0], -ctr[1]), sc, sc, origin=(0, 0)), cx, cy)
        _add_poly(ax, h, fc='white', ec=HOLE_EC, lw=0.7)
        ax.text(cx, cy - 0.4, c['text'], ha='center', va='top', fontsize=7.5, color='#333')
    for i, lbl in enumerate(row_labels):
        ax.text(-0.62, (nr - 1 - i) * pitch, lbl, ha='right', va='center', fontsize=9.5, fontweight='bold', color='#1B4F72')
    for j, lbl in enumerate(col_labels):
        ax.text(j * pitch, nr - 0.42, lbl, ha='center', va='bottom', fontsize=9.5, fontweight='bold', color=GREEN)
    ax.text((nc - 1) / 2, nr - 0.12, col_title, ha='center', va='bottom', fontsize=10, color=GREEN)
    ax.text(-1.45, (nr - 1) / 2, row_title, ha='center', va='center', rotation=90, fontsize=10, color='#1B4F72')
    if note:
        ax.text((nc - 1) / 2, -0.95, note, ha='center', va='top', fontsize=8, color='#333')
    ax.set_xlim(-1.7, nc - 0.4); ax.set_ylim(-1.5 if note else -0.9, nr + 0.25)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(title, fontsize=11, fontweight='bold')
