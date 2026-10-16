"""
plot_model_contents.py  (runs locally on Mac)
Second review sheet for the 1D nanobeam: exactly what nanobeam_1d.mph will contain,
BEFORE it is built. 3D views of the quarter cell (BC-colored faces) and of the beam in its
air box (to scale), plus the planned model tree.

Confirmed: w=400, t=140 nm, pad 1.5 um, quarter cell, 4 classes, diamond, mech on beam only.
Placeholders (drawing only): a, hx/a, hy/w -- same as plot_schematic.py.
Proposed (not yet agreed): mech-mesh size t/5 (from the 2D convergence test), N_mode, shift.

Usage (from project root):
    python runs/nanobeam_1d/plot_model_contents.py
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path

OUT = Path('runs/nanobeam_1d/figures')
W, T, PAD = 400.0, 140.0, 1500.0
PH = dict(a_nm=500.0, hx_a=0.50, hy_w=0.60)          # placeholders, as in plot_schematic.py
a = PH['a_nm']; hx = PH['hx_a'] * a; hy = PH['hy_w'] * W
Y2, Z2 = W / 2, T / 2

C = dict(floq='#C0392B', ysym='#117A65', zsym='#2E86C1', free='#BFC9CA', hole='#F2F3F4', air='#F9E79F')


def arc(n=40):
    th = np.linspace(np.pi, 0, n)          # from x=a/2-hx/2 to a/2+hx/2 along the half-ellipse (y>=0)
    return a / 2 + hx / 2 * np.cos(th), hy / 2 * np.sin(th)


def add(ax, verts, color, alpha=0.95, ec='k', lw=0.4):
    ax.add_collection3d(Poly3DCollection([verts], facecolors=color, edgecolors=ec, linewidths=lw, alpha=alpha))


def beam_faces(ax, alpha=0.95, faces=('hole', 'bottom', 'top', 'x0', 'xa', 'y0', 'yw')):
    """Draw only the requested faces, in the given order (back-to-front for the chosen view)."""
    ax_, ay_ = arc()

    def zface(z, col):
        poly = [(0, 0, z), (a / 2 - hx / 2, 0, z)] + [(x, y, z) for x, y in zip(ax_, ay_)] + \
               [(a / 2 + hx / 2, 0, z), (a, 0, z), (a, Y2, z), (0, Y2, z)]
        add(ax, poly, col, alpha)

    for f in faces:
        if f == 'bottom':
            zface(0.0, C['zsym'])
        elif f == 'top':
            zface(Z2, C['free'])
        elif f in ('x0', 'xa'):
            x = 0.0 if f == 'x0' else a
            add(ax, [(x, 0, 0), (x, Y2, 0), (x, Y2, Z2), (x, 0, Z2)], C['floq'], alpha)
        elif f == 'yw':
            add(ax, [(0, Y2, 0), (a, Y2, 0), (a, Y2, Z2), (0, Y2, Z2)], C['free'], alpha)
        elif f == 'y0':
            for x0, x1 in ((0, a / 2 - hx / 2), (a / 2 + hx / 2, a)):
                add(ax, [(x0, 0, 0), (x1, 0, 0), (x1, 0, Z2), (x0, 0, Z2)], C['ysym'], alpha)
        elif f == 'hole':
            for k in range(len(ax_) - 1):
                add(ax, [(ax_[k], ay_[k], 0), (ax_[k + 1], ay_[k + 1], 0), (ax_[k + 1], ay_[k + 1], Z2),
                         (ax_[k], ay_[k], Z2)], C['hole'], alpha, ec='#7F8C8D', lw=0.2)


fig = plt.figure(figsize=(17, 13))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], wspace=0.05, hspace=0.12)

# --- (A1/A2) quarter cell, BC-colored, seen from above and from below -------------------
from matplotlib.patches import Patch
views = [
    ('(A1) from ABOVE: top z=t/2 (free), x=a (Floquet dst), y=w/2 (free), hole wall',
     dict(elev=30, azim=55), ('hole', 'yw', 'xa', 'top')),
    ('(A2) from BELOW: z=0 plane (sym/antisym), y=0 plane (sym/antisym), x=0 (Floquet src)',
     dict(elev=-30, azim=-125), ('hole', 'x0', 'y0', 'bottom')),
]
sub = gs[0, 0].subgridspec(2, 1, hspace=0.05)
for k, (title, view, faces) in enumerate(views):
    ax = fig.add_subplot(sub[k], projection='3d', computed_zorder=False)
    beam_faces(ax, alpha=1.0, faces=faces)
    ax.set_xlim(0, a); ax.set_ylim(0, Y2); ax.set_zlim(0, Z2)
    ax.set_box_aspect((a, Y2, Z2 * 1.6))          # z stretched 1.6x for visibility (labelled)
    ax.view_init(**view)
    ax.set_xlabel('x (nm)', fontsize=8); ax.set_ylabel('y (nm)', fontsize=8); ax.set_zlabel('z', fontsize=8)
    ax.tick_params(labelsize=7)
    ax.set_title(title, fontsize=9.5, fontweight='bold')
ax.legend(handles=[Patch(fc=C['floq'], label='x=0 / x=a: Floquet periodic (k_x)'),
                   Patch(fc=C['ysym'], label='y=0: Symmetry (Y+) or Antisymmetry (Y-)'),
                   Patch(fc=C['zsym'], label='z=0: Symmetry (Z+) or Antisymmetry (Z-)'),
                   Patch(fc=C['free'], label='y=w/2, z=t/2: free (traction-free)'),
                   Patch(fc=C['hole'], ec='#7F8C8D', label='hole wall: free')],
          loc='center left', fontsize=8, bbox_to_anchor=(1.0, 1.0))
fig.text(0.27, 0.905, 'Beam quarter cell 0<x<a, 0<y<w/2, 0<z<t/2 (placeholder a, hx, hy; z drawn 1.6x stretched)',
         ha='center', fontsize=10.5, fontweight='bold')

# --- (B) beam inside air box, to scale ----------------------------------------------------
ax = fig.add_subplot(gs[0, 1], projection='3d', computed_zorder=False)
beam_faces(ax, alpha=1.0, faces=('hole', 'yw', 'xa', 'top'))
YA, ZA = Y2 + PAD, PAD
box = [[(0, 0, 0), (a, 0, 0), (a, YA, 0), (0, YA, 0)], [(0, 0, ZA), (a, 0, ZA), (a, YA, ZA), (0, YA, ZA)],
       [(0, YA, 0), (a, YA, 0), (a, YA, ZA), (0, YA, ZA)], [(0, 0, 0), (0, YA, 0), (0, YA, ZA), (0, 0, ZA)],
       [(a, 0, 0), (a, YA, 0), (a, YA, ZA), (a, 0, ZA)]]
ax.add_collection3d(Poly3DCollection(box, facecolors=C['air'], edgecolors='#B7950B', linewidths=0.8, alpha=0.12))
ax.set_xlim(0, a); ax.set_ylim(0, YA); ax.set_zlim(0, ZA)
ax.set_box_aspect((a, YA, ZA))
ax.view_init(elev=22, azim=-62)
ax.set_xlabel('x (nm)'); ax.set_ylabel('y (nm)'); ax.set_zlabel('z (nm)')
ax.text(a / 2, YA * 0.6, ZA * 0.7, f'AIR\n(to y = w/2 + {PAD/1000:g} um,\n z = {PAD/1000:g} um)\n'
        'optics only', color='#7D6608', fontsize=9, ha='center')
ax.set_title('(B)  Same quarter cell inside its air box, TO SCALE\n'
             '(beam = small colored block at the corner; air has no mechanics)',
             fontsize=10.5, fontweight='bold')

# --- (C) model tree ---------------------------------------------------------------------------
ax = fig.add_subplot(gs[1, :]); ax.axis('off')
tree = [
    ('Parameters', 'a [TBD], w = 400 nm, t = 140 nm, hx = (hx/a)*a, hy = (hy/w)*w [ratios TBD], '
                   'pad_y = pad_z = 1.5 um, kx (Floquet), f_mech (shift), N_mode'),
    ('Geometry', '1) Block "beam": [0,a] x [0,w/2] x [0,t/2]   2) Work plane z=0: Ellipse center (a/2, 0), '
                 'semi-axes hx/2, hy/2 -> Extrude to t/2 = "hole"\n'
                 '3) Difference beam - hole   4) Block "air": [0,a] x [0,w/2+pad_y] x [0,pad_z]   '
                 '5) Form Union -> 2 domains (beam, air)'),
    ('Materials', 'Diamond (isotropic): E = 1050 GPa, nu = 0.07, rho = 3500 kg/m^3, n = 2.41 -> beam domain;   '
                  'Air (n = 1) -> air domain'),
    ('Solid Mechanics', 'domain = beam ONLY.  Linear Elastic (isotropic) | Free (default, all other beam faces) | '
                        'Periodic Condition: Floquet, k = (kx, 0, 0),\nsource x=0 -> destination x=a | '
                        'Symmetry + Antisymmetry on y=0 (one active per class) | '
                        'Symmetry + Antisymmetry on z=0 (one active per class)'),
    ('Meshes', 'Mech Mesh (beam only): Free Triangular on x=0 face -> Copy Face to x=a -> Free Tetrahedral; '
               'size PROPOSED hmax = t/5 (validated in 2D at a=1000)\n'
               'OP Mesh (beam + air): same periodic-face approach; sizes TBD with the optical study'),
    ('Study "Mech"', 'Eigenfrequency (ARPACK, around shift f_mech), N_mode per class; Python loops kx = 0 .. pi/a '
                     '(Gamma -> X) and the 4 classes\n(Y+Z+, Y-Z+, Y+Z-, Y-Z-) by activating the Symmetry / '
                     'Antisymmetry features; extracts solid.freq'),
    ('Not included yet', 'optical (ewfd) physics and study, outer-air optical BC, PML / Q calculations, '
                         'cavity (tapered) geometry'),
    ('Validation', 'first model run: hole disabled (hx = hy = 0) -> compare lowest bands with analytic beam '
                   'dispersion (longitudinal sqrt(E/rho), flexural, torsion)'),
]
y = 0.97
for head, body in tree:
    ax.text(0.0, y, head, fontsize=10.5, fontweight='bold', color='#1B4F72', va='top', transform=ax.transAxes)
    ax.text(0.14, y, body, fontsize=9.5, va='top', transform=ax.transAxes, wrap=True)
    y -= 0.125 if '\n' in body else 0.085
ax.set_title('(C)  Planned contents of nanobeam_1d.mph (built from scratch in Python; nothing created yet)',
             fontsize=11, fontweight='bold', loc='left')

fig.suptitle('1D diamond nanobeam -- planned COMSOL model, for review before building\n'
             f'confirmed: w = {W:.0f} nm, t = {T:.0f} nm, air pad {PAD/1000:g} um, quarter cell, 4 classes, '
             f'mech on beam only | PLACEHOLDER a = {a:.0f} nm, hx/a = {PH["hx_a"]}, hy/w = {PH["hy_w"]} '
             '(drawing only)', fontsize=12, fontweight='bold')
for ext in ('png', 'pdf'):
    fig.savefig(OUT / f'model_contents_proposed.{ext}', dpi=140, facecolor='white', bbox_inches='tight')
print(f'Saved {OUT}/model_contents_proposed.png')
