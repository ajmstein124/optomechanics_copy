"""
plot_cell_examples.py  (runs locally on Mac)
Geometry-exact drawings of chosen (d/a, w/a) unit cells at a few lattice constants:
hole + its 6 nearest periodic images, the rhombus cell (best mov1 shift if the hole fits,
otherwise the default shift, drawn dashed), and the narrowest slab bridge marked.

Usage (from project root):
    python runs/diamond_a_sweep/plot_cell_examples.py
"""
import sys
sys.path.insert(0, 'scripts')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import Polygon
from shapely import affinity
from shapely.ops import nearest_points
from schematic import hole_poly, cell_verts, lattice, _add_poly, SLAB, HOLE_EC, RED, DEFAULT_SHIFT_NM
from cell_placement import best_shift_filleted

CASES = [(0.48, 0.36), (0.43, 0.41)]      # (d/a, w/a)
A_NM  = [200, 700]
FR, T = 16, 140
OUT   = 'runs/diamond_a_sweep/figures/cell_examples'

fig, axes = plt.subplots(len(A_NM), len(CASES), figsize=(6.2 * len(CASES), 5.6 * len(A_NM)))
for i, a in enumerate(A_NM):
    a1, a2 = lattice(a)
    for j, (da, wa) in enumerate(CASES):
        ax = axes[i, j]
        d, w = da * a, wa * a
        h = hole_poly(d, w, FR)
        s, _, _ = best_shift_filleted(a * 1e-9, d * 1e-9, w * 1e-9, FR * 1e-9)
        s = (s[0] * 1e9, s[1] * 1e9)
        cell = Polygon(cell_verts(a, s))
        fits = cell.contains(h)
        if not fits:
            s = DEFAULT_SHIFT_NM
        cv = cell_verts(a, s)
        ctr = cv.mean(axis=0)
        span = 1.25 * a
        ax.add_patch(plt.Rectangle((ctr[0] - span, ctr[1] - span), 2 * span, 2 * span, fc=SLAB, ec='none', zorder=0))
        imgs = []
        for n1 in range(-2, 3):
            for n2 in range(-2, 3):
                L = n1 * a1 + n2 * a2
                hi = affinity.translate(h, *L)
                imgs.append((n1, n2, hi))
                _add_poly(ax, hi, fc='white', ec=HOLE_EC, lw=1.0, zorder=2)
        ax.add_patch(MplPolygon(cv, closed=True, fc='none', ec=RED, lw=2.2, ls='-' if fits else '--', zorder=4))
        # narrowest bridge between the central hole and its nearest images
        best = None
        for n1, n2, hi in imgs:
            if (n1, n2) == (0, 0) or max(abs(n1), abs(n2), abs(n1 + n2)) > 1:
                continue
            dist = h.distance(hi)
            if best is None or dist < best[0]:
                best = (dist, hi)
        bw, hi = best
        if bw > 0:
            p, q = nearest_points(h, hi)
            ax.annotate('', xy=(q.x, q.y), xytext=(p.x, p.y),
                        arrowprops=dict(arrowstyle='<->', color='#D35400', lw=1.8), zorder=6)
            ax.plot([p.x, q.x], [p.y, q.y], 'o', color='#D35400', ms=3, zorder=6)
        status = (f'fits rhombus cell (clearance {cell.exterior.distance(h):.1f} nm)' if fits
                  else 'does NOT fit any rhombus placement (dashed = default cell)')
        ax.set_title(f'd/a={da}, w/a={wa}  at a={a} nm   (d={d:.0f}, w={w:.0f}, f_r={FR} nm)\n'
                     f'narrowest bridge = {bw:.1f} nm;  {status}', fontsize=9,
                     color='k' if fits else '#922B21')
        ax.set_xlim(ctr[0] - 1.15 * a, ctr[0] + 1.15 * a)
        ax.set_ylim(ctr[1] - 1.0 * a, ctr[1] + 1.0 * a)
        ax.set_aspect('equal'); ax.axis('off')
        ax.plot([ctr[0] - 1.05 * a, ctr[0] - 1.05 * a + 100], [ctr[1] - 0.93 * a] * 2, 'k-', lw=3)
        ax.text(ctr[0] - 1.05 * a + 50, ctr[1] - 0.9 * a, '100 nm', ha='center', va='bottom', fontsize=8)

fig.suptitle('Diamond snowflake unit cells, drawn from the unit_cell_3.mph geometry definition\n'
             'white = hole (center + 6 periodic images), red = rhombus unit cell, orange = narrowest slab bridge',
             fontsize=12, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.95])
for ext in ('png', 'pdf'):
    fig.savefig(f'{OUT}.{ext}', dpi=150, facecolor='white')
print(f'Saved: {OUT}.png')
