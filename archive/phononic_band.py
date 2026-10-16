"""
phononic_band.py

Phononic band structure of a 2D triangular lattice of circular holes in a
diamond slab, via COMSOL 6.x (mph).

Geometry
--------
Hexagonal (triangular) lattice, period a, free-standing diamond slab, thickness d.
Simulated with a rectangular 2-atom supercell: Lx = a, Ly = a*sqrt(3), Lz = d.

  Two cylindrical holes per rectangular cell:
    - 1 interior hole at (a/2, a*sqrt(3)/2)  -- fully inside cell
    - 4 fractional corner holes at (0,0), (a,0), (0,a*sqrt(3)), (a,a*sqrt(3))
      each is 1/4 atom by periodicity; Boolean Difference clips them to the slab

Parameters (starting point):
  d/a = 0.44,  r/a = 0.35  =>  (d, r, a) = (220, 175, 500) nm

Band-structure path (rectangular BZ of the hexagonal supercell):
  Gamma (0,0) -> X (pi/a, 0) -> S (pi/a, pi/(a*sqrt(3))) -> Y (0, pi/(a*sqrt(3))) -> Gamma

Usage
-----
  py -3.12 phononic_band.py

Dependencies
------------
  pip install mph matplotlib numpy
  COMSOL 6.x must be installed and accessible.
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mph

# =============================================================================
# PARAMETERS
# =============================================================================

a  = 500e-9    # lattice constant [m]  -- main tuning knob; scale for target gap freq
d  = 220e-9    # slab thickness [m]    (d/a = 0.44)
r  = 175e-9    # hole radius [m]       (r/a = 0.35; try 0.30-0.45)

# Diamond material -- isotropic approximation
E_d   = 1050e9   # Young's modulus [Pa]
nu_d  = 0.07     # Poisson's ratio
rho_d = 3500.0   # density [kg/m^3]
# Note: c11=1076 GPa, c12=125 GPa, c44=578 GPa for cubic anisotropy (upgrade later)
# v_LA = sqrt(c11/rho) ~ 17500 m/s vs Si ~9000 m/s -> gap freq scales by ~2x for same a

# Simulation
n_seg         = 15    # k-points per BZ segment (total = 4*n_seg + 1)
n_modes       = 20    # eigenfrequencies at each k-point
eig_shift_GHz = 3.0   # eigenfrequency search center [GHz]; raise if low modes missed

# Output (must be a local Windows drive path -- fill in username to match remote_runner.py)
save_dir = r'C:\Users\USERNAME\Documents\optomechanics'
tag      = f'circles_a{int(a*1e9)}nm_d{int(d*1e9)}nm_r{int(r*1e9)}nm'

# =============================================================================
# K-PATH: Gamma -> X -> S -> Y -> Gamma  (rectangular BZ of hex supercell)
#
# The hexagonal lattice has a rhombic primitive cell, but we simulate a
# rectangular 2-atom supercell (Lx=a, Ly=a*sqrt(3)) to allow orthogonal
# Floquet BCs in COMSOL.  The reciprocal lattice of this supercell is also
# rectangular, with BZ boundaries kx_max=pi/a, ky_max=pi/(a*sqrt(3)).
#
# The irreducible BZ (IBZ) boundary of the rectangular BZ is the path:
#   Gamma -> X -> S -> Y -> Gamma
#
# This is the rectangular-supercell analog of the Gamma->X->M->Gamma path
# used for a square lattice (COMSOL blog).  The S point here corresponds to
# the M point of the hexagonal BZ.
#
# A bandgap is COMPLETE if it spans the gap for ALL k in the full IBZ (not
# just the path boundary).  Sweeping the IBZ boundary is the standard check:
# gaps found on the high-symmetry path are expected to be complete for
# geometries with the full C6v lattice symmetry.  They should be verified
# with a 2D k-space scan if the geometry breaks that symmetry.
#
# High-symmetry points:
#   Gamma = (0,       0              )
#   X     = (pi/a,    0              )
#   S     = (pi/a,    pi/(a*sqrt(3)) )   <- M point of hex BZ
#   Y     = (0,       pi/(a*sqrt(3)) )
# =============================================================================

kx_max = np.pi / a
ky_max = np.pi / (a * np.sqrt(3))

kG = np.array([0,      0     ])
kX = np.array([kx_max, 0     ])
kS = np.array([kx_max, ky_max])
kY = np.array([0,      ky_max])

def linseg(k1, k2, n, endpoint=False):
    t = np.linspace(0, 1, n + (1 if endpoint else 0), endpoint=endpoint)
    return k1[None, :] + t[:, None] * (k2 - k1)[None, :]

k_path = np.vstack([
    linseg(kG, kX, n_seg),
    linseg(kX, kS, n_seg),
    linseg(kS, kY, n_seg),
    linseg(kY, kG, n_seg, endpoint=True),
])  # shape (4*n_seg + 1, 2), units [rad/m]

dk     = np.linalg.norm(np.diff(k_path, axis=0), axis=1)
k_dist = np.r_[0, np.cumsum(dk)]

tick_idx = [0, n_seg, 2*n_seg, 3*n_seg, 4*n_seg]
tick_x   = k_dist[tick_idx]
tick_lbl = ['G', 'X', 'S', 'Y', 'G']   # ASCII only -- Windows cp1252 safe

# =============================================================================
# BUILD COMSOL MODEL
# =============================================================================

print('Starting COMSOL server...')
client = mph.start(cores=4)
model  = client.create('phononic_circles')
m      = model.java

print('Building model...')

# --- Global parameters -------------------------------------------------------
p = m.param()
p.set('a_lat',  str(a),  'Lattice constant [m]')
p.set('d_slab', str(d),  'Slab thickness [m]')
p.set('r_hole', str(r),  'Hole radius [m]')
p.set('kx',     '0',     'Bloch kx [rad/m]')
p.set('ky',     '0',     'Bloch ky [rad/m]')

# --- Component ---------------------------------------------------------------
comp = m.component().create('comp1', True)

# --- Geometry ----------------------------------------------------------------
# Rectangular supercell: x in [0, a_lat], y in [0, a_lat*sqrt(3)], z in [-d_slab/2, d_slab/2]
geom = comp.geom().create('geom1', 3)
geom.lengthUnit('m')

# Slab block
slab = geom.create('slab', 'Block')
slab.set('size', ['a_lat', 'a_lat*sqrt(3)', 'd_slab'])
slab.set('base', 'corner')
slab.set('pos',  ['0', '0', '-d_slab/2'])

def make_hole(geom, name, x0_expr, y0_expr):
    """Create a cylindrical hole (radius r_hole, height 1.1*d_slab) centered at (x0, y0, 0)."""
    cyl = geom.create(name, 'Cylinder')
    cyl.set('r', 'r_hole')
    cyl.set('h', '1.1*d_slab')
    cyl.set('pos', [x0_expr, y0_expr, '-0.55*d_slab'])
    return name

hole_names = []

# Interior hole -- fully inside the cell
hole_names.append(make_hole(geom, 'h_int', 'a_lat/2', 'a_lat*sqrt(3)/2'))

# Corner holes -- 1/4 atom at each corner; Boolean Difference clips to slab
corner_positions = [
    ('0',       '0'                 ),
    ('a_lat',   '0'                 ),
    ('0',       'a_lat*sqrt(3)'     ),
    ('a_lat',   'a_lat*sqrt(3)'     ),
]
for ci, (x0, y0) in enumerate(corner_positions):
    hole_names.append(make_hole(geom, f'h_c{ci}', x0, y0))

# Union all holes into one body, then subtract from slab
uni = geom.create('uni_holes', 'Union')
uni.selection('input').set(hole_names)
uni.set('keepSubdomains', 'off')

dif = geom.create('dif1', 'Difference')
dif.selection('input').set(['slab'])
dif.selection('input2').set(['uni_holes'])

geom.run('fin')
print('  Geometry built.')

# --- Component-level Box Selections for the 4 lateral periodic faces ---------

def box_face_sel(comp_node, name, axis, coord_expr, tol='a_lat*1e-4'):
    """Select all faces on the plane axis=coord_expr (within tolerance)."""
    s = comp_node.selection().create(name, 'Box')
    s.set('entitydim', 2)
    s.set('condition', 'allvertices')
    spans = {
        'x': ('-a_lat*0.1',  'a_lat*1.1'  ),
        'y': ('-a_lat*0.1',  'a_lat*2.0'  ),
        'z': ('-d_slab',     'd_slab'      ),
    }
    for ax in ('x', 'y', 'z'):
        if ax == axis:
            s.set(f'{ax}min', f'({coord_expr})-{tol}')
            s.set(f'{ax}max', f'({coord_expr})+{tol}')
        else:
            s.set(f'{ax}min', spans[ax][0])
            s.set(f'{ax}max', spans[ax][1])

box_face_sel(comp, 'sel_x0', 'x', '0'                )   # x = 0 face
box_face_sel(comp, 'sel_xa', 'x', 'a_lat'            )   # x = a face
box_face_sel(comp, 'sel_y0', 'y', '0'                )   # y = 0 face
box_face_sel(comp, 'sel_ya', 'y', 'a_lat*sqrt(3)'    )   # y = a*sqrt(3) face

# --- Material: diamond -------------------------------------------------------
mat = comp.material().create('mat1', 'Common')
mat.label('Diamond')
mat.propertyGroup('def').set('density',       str(rho_d))
mat.propertyGroup('def').set('youngsmodulus', str(E_d))
mat.propertyGroup('def').set('poissonsratio', str(nu_d))

# --- Physics: Solid Mechanics ------------------------------------------------
solid = comp.physics().create('solid', 'SolidMechanics', 'geom1')

# Floquet (Bloch) periodic boundary conditions.
#
# The condition on each pair of opposing faces is:
#   u_dest = exp(-i * k_F . (r_dest - r_src)) * u_src
#
# where k_F = (kx, ky, 0) is the Bloch wavevector, r is the position vector,
# and u is the displacement field.  This couples the degrees of freedom on
# the source face to those on the destination face with the Bloch phase factor.
#
# Because the phase factor is complex for k != 0, COMSOL automatically invokes
# a complex eigensolver.  The eigenvalues (omega^2) remain real for the undamped
# system; only the mode shapes are complex.  getData() still returns real
# frequencies -- this is expected and correct.
#
# At k = Gamma (kx=ky=0) the factor is 1 and the matrices are real.  The
# zero-frequency rigid-body modes appear there, hence eig_shift_GHz > 0.
#
# References: COMSOL blog "Modeling Phononic Band Gap Materials and Structures";
#             Chan thesis App. F.

def add_floquet_bc(solid_node, name, src_sel, dst_sel):
    pc = solid_node.create(name, 'PeriodicCondition', 2)
    pc.label(f'Floquet {name}')
    pc.set('PeriodicType', 'Floquet')
    pc.set('kFloquet', ['kx', 'ky', '0'])
    pc.selection().named(src_sel)
    dest = pc.create('dest', 'Destination', 2)
    dest.selection().named(dst_sel)

add_floquet_bc(solid, 'pc_x', 'comp1_sel_x0', 'comp1_sel_xa')
add_floquet_bc(solid, 'pc_y', 'comp1_sel_y0', 'comp1_sel_ya')
# Top and bottom faces: free (traction-free) boundary -- COMSOL Solid Mechanics default.

# --- Mesh --------------------------------------------------------------------
mesh = comp.mesh().create('mesh1')
mesh.create('ftet1', 'FreeTet')
sz = mesh.create('sz1', 'Size')
sz.set('hauto', 5)   # 1=finest .. 9=coarsest; 5=normal, 4=fine

# --- Study: Eigenfrequency ---------------------------------------------------
# The shift-invert Lanczos solver finds the n_modes eigenvalues (omega^2)
# nearest to omega_shift^2.  Setting shift > 0 serves two purposes:
#   1. Skips the zero-frequency rigid-body modes at k=Gamma.
#   2. Centers the search window on the frequency range of interest.
# Rule: set shift to 30-70% of the expected gap center frequency.
# If getData() returns unexpected or missing modes, adjust eig_shift_GHz.
std = m.study().create('std1')
eig = std.create('eig1', 'Eigenfrequency')
eig.set('neigsactive', 'on')
eig.set('neigs', str(n_modes))
eig.set('shift', f'{eig_shift_GHz}[GHz]')

# Global evaluation: extract all eigenfrequencies in GHz after each k-solve.
# getData() returns a list-of-lists: outer index = eigenmode, inner = expression.
# Eigenfrequencies are real even though the Floquet matrices are complex.
ev = m.result().numerical().create('ev1', 'EvalGlobal')
ev.set('data', 'dset1')
ev.setIndex('expr',  'freq', 0)
ev.setIndex('unit',  'GHz',  0)
ev.setIndex('descr', 'Eigenfrequency', 0)

print('Model ready. Starting k-sweep...')

# =============================================================================
# SOLVE LOOP
# =============================================================================

os.makedirs(save_dir, exist_ok=True)
freqs_GHz = np.full((len(k_path), n_modes), np.nan)

for i, (kxi, kyi) in enumerate(k_path):
    m.param().set('kx', repr(kxi))
    m.param().set('ky', repr(kyi))

    m.study('std1').run()

    # getData() returns a list of lists: outer = eigenmode, inner = expression.
    try:
        raw = ev.getData()
        row = np.array([float(entry[0]) for entry in raw], dtype=float)
    except Exception as e:
        print(f'  WARNING getData at k={i}: {e}')
        row = np.full(n_modes, np.nan)

    n = min(len(row), n_modes)
    freqs_GHz[i, :n] = row[:n]

    if i % 5 == 0 or i == len(k_path) - 1:
        f_lo = np.nanmin(row[:n]) if n else float('nan')
        f_hi = np.nanmax(row[:n]) if n else float('nan')
        print(f'  k={i+1:3d}/{len(k_path)}'
              f'  kx={kxi:.3e}  ky={kyi:.3e}'
              f'  f=[{f_lo:.3f}, {f_hi:.3f}] GHz')

# =============================================================================
# BANDGAP ANALYSIS
# =============================================================================

def find_bandgaps(freqs, tol_frac=0.02):
    """
    Find complete phononic bandgaps (across all k-points).
    A gap between band b and b+1 exists if max(band_b) < min(band_{b+1})
    with fractional gap > tol_frac.
    """
    n_k, n_b = freqs.shape
    gaps = []
    for b in range(n_b - 1):
        f_top    = np.nanmax(freqs[:, b])
        f_bottom = np.nanmin(freqs[:, b+1])
        if f_bottom > f_top:
            fc    = 0.5 * (f_top + f_bottom)
            gfrac = (f_bottom - f_top) / fc
            if gfrac > tol_frac:
                gaps.append((f_top, f_bottom, gfrac))
    return gaps

gaps = find_bandgaps(freqs_GHz)

print('\nBandgap summary (diamond, triangular lattice of circular holes):')
if gaps:
    for fl, fu, gf in gaps:
        fc = 0.5 * (fl + fu)
        print(f'  {fl:.3f} - {fu:.3f} GHz  center={fc:.3f} GHz  gap={gf*100:.1f}%')
    print(f'  Hint: to shift gap to target freq, scale a by f_current/f_target')
else:
    print('  No complete bandgap found.')
    print('  Suggestions:')
    print('    - Increase r/a (try 0.38-0.45) for wider gap')
    print('    - Check eig_shift_GHz covers the expected gap region')
    print('    - Increase n_modes if bands may be missing')
    print('    - Note: circular holes may give only a partial gap;')
    print('      upgrade to snowflake geometry for a complete gap')

# =============================================================================
# SAVE DATA
# =============================================================================

data_path = os.path.join(save_dir, f'phononic_band_{tag}.npz')
np.savez(data_path,
         freqs_GHz=freqs_GHz,
         k_path_radpm=k_path,
         k_dist=k_dist,
         a=a, d=d, r=r,
         tick_idx=tick_idx,
         tick_lbl=np.array(tick_lbl))
print(f'\nData saved: {data_path}')

# =============================================================================
# PLOT BAND STRUCTURE
# =============================================================================

fig, ax = plt.subplots(figsize=(5.5, 5))

for mi in range(n_modes):
    ax.plot(k_dist, freqs_GHz[:, mi], 'b-', lw=0.9, alpha=0.75)

for fl, fu, _ in gaps:
    ax.axhspan(fl, fu, color='red', alpha=0.15)

for xv in tick_x:
    ax.axvline(xv, color='gray', lw=0.5, ls='--')

ax.set_xticks(tick_x)
ax.set_xticklabels(tick_lbl, fontsize=11)
ax.set_xlabel('Wavevector')
ax.set_ylabel('Frequency (GHz)')
ax.set_title(f'Triangular lattice, circular holes -- diamond\n'
             f'a={a*1e9:.0f}nm  d={d*1e9:.0f}nm  r={r*1e9:.0f}nm'
             f'  (r/a={r/a:.2f})', fontsize=10)
ax.set_xlim([k_dist[0], k_dist[-1]])
ax.set_ylim([0, None])
ax.grid(alpha=0.3)
plt.tight_layout()

fig_path = os.path.join(save_dir, f'phononic_band_{tag}.png')
fig.savefig(fig_path, dpi=150)
print(f'Figure saved: {fig_path}')

client.clear()
print('Done.')
