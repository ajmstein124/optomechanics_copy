"""
phononic_sweep.py

Sweep phononic bandgap over a parameter grid of (a, d/a, r/a).
Reads sweep definition from configs/sweep_config.json (in the script directory).
Saves incremental results to sweep_results.csv after each combo, plus a per-combo
.npz with the full band structure.

Usage
-----
  py -3.12 phononic_sweep.py

Setup
-----
  Write sweep config from app.py -> 'Write sweep config' button.
  Then run: python scripts/remote_runner.py scripts/phononic_sweep.py
  remote_runner.py copies configs/ alongside the script automatically.
"""

import csv
import itertools
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import mph

# =============================================================================
# LOAD SWEEP CONFIG
# =============================================================================

script_dir  = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'configs', 'sweep_config.json')

if not os.path.exists(config_path):
    print('ERROR: sweep_config.json not found: ' + config_path)
    print('Write the sweep config from app.py and re-run remote_runner.py.')
    sys.exit(1)

with open(config_path) as f:
    cfg = json.load(f)

a_nm_vals = cfg['sweep']['a_nm']
ra_vals   = cfg['sweep']['ra']
da_vals   = cfg['sweep']['da']
sim       = cfg.get('simulation', {})
n_seg         = sim.get('n_seg',         8)
n_modes       = sim.get('n_modes',      20)
eig_shift_GHz = sim.get('eig_shift_GHz', 3.0)
save_dir      = cfg.get('save_dir', script_dir)

mat   = cfg.get('material', {})
E_d   = mat.get('E_GPa',    1050) * 1e9   # Pa
nu_d  = mat.get('nu',       0.07)
rho_d = mat.get('rho_kgm3', 3500.0)

param_combos = list(itertools.product(a_nm_vals, da_vals, ra_vals))
print(f'Sweep: {len(a_nm_vals)} a x {len(da_vals)} d/a x {len(ra_vals)} r/a = {len(param_combos)} combos')
print(f'Solver: n_seg={n_seg}, n_modes={n_modes}, eig_shift={eig_shift_GHz} GHz')

# =============================================================================
# HELPERS
# =============================================================================

def make_k_path(a, n_seg):
    # IBZ boundary of the rectangular 2-atom supercell BZ (analog of
    # Gamma->X->M->Gamma for a square lattice, per COMSOL blog).
    # S = M point of the hexagonal BZ folded into the rectangular supercell.
    # A complete phononic bandgap must span this entire path.
    kx_max = np.pi / a
    ky_max = np.pi / (a * np.sqrt(3))
    kG = np.array([0, 0])
    kX = np.array([kx_max, 0])
    kS = np.array([kx_max, ky_max])
    kY = np.array([0, ky_max])
    def seg(k1, k2, n, end=False):
        t = np.linspace(0, 1, n + (1 if end else 0), endpoint=end)
        return k1 + t[:, None] * (k2 - k1)
    k_path = np.vstack([seg(kG, kX, n_seg), seg(kX, kS, n_seg),
                        seg(kS, kY, n_seg), seg(kY, kG, n_seg, end=True)])
    dk     = np.linalg.norm(np.diff(k_path, axis=0), axis=1)
    k_dist = np.r_[0, np.cumsum(dk)]
    return k_path, k_dist


def find_bandgaps(freqs, tol=0.02):
    gaps = []
    for b in range(freqs.shape[1] - 1):
        f_top = np.nanmax(freqs[:, b])
        f_bot = np.nanmin(freqs[:, b + 1])
        if f_bot > f_top:
            fc = 0.5 * (f_top + f_bot)
            gf = (f_bot - f_top) / fc
            if gf > tol:
                gaps.append((f_top, f_bot, gf))
    return gaps

# =============================================================================
# BUILD COMSOL MODEL (once; params updated in-place each combo)
# =============================================================================

a0_nm, da0, ra0 = param_combos[0]
a0 = a0_nm * 1e-9

print('Starting COMSOL server...')
client = mph.start(cores=4)
model  = client.create('phononic_sweep')
m      = model.java

print('Building model...')

p = m.param()
p.set('a_lat',  str(a0),         'Lattice constant [m]')
p.set('d_slab', str(da0 * a0),   'Slab thickness [m]')
p.set('r_hole', str(ra0 * a0),   'Hole radius [m]')
p.set('kx',     '0',             'Bloch kx [rad/m]')
p.set('ky',     '0',             'Bloch ky [rad/m]')

comp = m.component().create('comp1', True)
geom = comp.geom().create('geom1', 3)
geom.lengthUnit('m')

slab = geom.create('slab', 'Block')
slab.set('size', ['a_lat', 'a_lat*sqrt(3)', 'd_slab'])
slab.set('base', 'corner')
slab.set('pos',  ['0', '0', '-d_slab/2'])

hole_specs = [
    ('h_int', 'a_lat/2', 'a_lat*sqrt(3)/2'),
    ('h_c0',  '0',       '0'              ),
    ('h_c1',  'a_lat',   '0'              ),
    ('h_c2',  '0',       'a_lat*sqrt(3)'  ),
    ('h_c3',  'a_lat',   'a_lat*sqrt(3)'  ),
]
hole_names = []
for name, x0, y0 in hole_specs:
    cyl = geom.create(name, 'Cylinder')
    cyl.set('r', 'r_hole')
    cyl.set('h', '1.1*d_slab')
    cyl.set('pos', [x0, y0, '-0.55*d_slab'])
    hole_names.append(name)

uni = geom.create('uni_holes', 'Union')
uni.selection('input').set(hole_names)
uni.set('keepSubdomains', 'off')

dif = geom.create('dif1', 'Difference')
dif.selection('input').set(['slab'])
dif.selection('input2').set(['uni_holes'])
geom.run('fin')


def box_face_sel(name, axis, coord_expr, tol='a_lat*1e-4'):
    s = comp.selection().create(name, 'Box')
    s.set('entitydim', 2)
    s.set('condition', 'allvertices')
    spans = {'x': ('-a_lat*0.1', 'a_lat*1.1'),
             'y': ('-a_lat*0.1', 'a_lat*2.0'),
             'z': ('-d_slab',    'd_slab'   )}
    for ax in ('x', 'y', 'z'):
        if ax == axis:
            s.set(f'{ax}min', f'({coord_expr})-{tol}')
            s.set(f'{ax}max', f'({coord_expr})+{tol}')
        else:
            s.set(f'{ax}min', spans[ax][0])
            s.set(f'{ax}max', spans[ax][1])

box_face_sel('sel_x0', 'x', '0'            )
box_face_sel('sel_xa', 'x', 'a_lat'        )
box_face_sel('sel_y0', 'y', '0'            )
box_face_sel('sel_ya', 'y', 'a_lat*sqrt(3)')

mat = comp.material().create('mat1', 'Common')
mat.label('Diamond')
mat.propertyGroup('def').set('density',       str(rho_d))
mat.propertyGroup('def').set('youngsmodulus', str(E_d))
mat.propertyGroup('def').set('poissonsratio', str(nu_d))

solid = comp.physics().create('solid', 'SolidMechanics', 'geom1')

# Floquet (Bloch) BCs: u_dest = exp(-i * k_F . (r_dest - r_src)) * u_src
# k_F = (kx, ky, 0).  COMSOL uses a complex eigensolver for k != 0 because
# the phase factor is complex; eigenvalues (omega^2) remain real.
# At k=Gamma (kx=ky=0): real matrices, zero-frequency rigid-body modes appear
# -- hence eig_shift > 0.  Top/bottom faces: free (traction-free, default).
# Ref: COMSOL blog "Modeling Phononic Band Gap Materials and Structures";
#      Chan thesis App. F.
for bc_name, src, dst in [('pc_x', 'comp1_sel_x0', 'comp1_sel_xa'),
                           ('pc_y', 'comp1_sel_y0', 'comp1_sel_ya')]:
    pc = solid.create(bc_name, 'PeriodicCondition', 2)
    pc.set('PeriodicType', 'Floquet')
    pc.set('kFloquet', ['kx', 'ky', '0'])
    pc.selection().named(src)
    dest = pc.create('dest', 'Destination', 2)
    dest.selection().named(dst)

mesh = comp.mesh().create('mesh1')
mesh.create('ftet1', 'FreeTet')
sz = mesh.create('sz1', 'Size')
sz.set('hauto', 5)

# Shift-invert Lanczos: finds n_modes eigenvalues nearest to eig_shift^2.
# Set shift to 30-70% of expected gap center to skip DC modes and center on
# the frequency range of interest.
std = m.study().create('std1')
eig = std.create('eig1', 'Eigenfrequency')
eig.set('neigsactive', 'on')
eig.set('neigs', str(n_modes))
eig.set('shift', f'{eig_shift_GHz}[GHz]')

ev = m.result().numerical().create('ev1', 'EvalGlobal')
ev.set('data', 'dset1')
ev.setIndex('expr',  'freq', 0)
ev.setIndex('unit',  'GHz',  0)
ev.setIndex('descr', 'Eigenfrequency', 0)

print('Model ready. Starting sweep...')

# =============================================================================
# SWEEP LOOP
# =============================================================================

os.makedirs(save_dir, exist_ok=True)

csv_path   = os.path.join(save_dir, 'sweep_results.csv')
fieldnames = ['combo', 'a_nm', 'da', 'ra', 'd_nm', 'r_nm',
              'n_gaps', 'gap1_lo_GHz', 'gap1_hi_GHz', 'gap1_center_GHz', 'gap1_frac']

with open(csv_path, 'w', newline='') as csv_f:
    writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
    writer.writeheader()

    for ci, (a_nm, da, ra) in enumerate(param_combos):
        a = a_nm * 1e-9
        d = da * a
        r = ra * a

        print(f'\n[{ci+1}/{len(param_combos)}]  a={a_nm}nm  d/a={da:.2f}  r/a={ra:.2f}')

        m.param().set('a_lat',  str(a))
        m.param().set('d_slab', str(d))
        m.param().set('r_hole', str(r))
        if ci > 0:
            m.component('comp1').geom('geom1').run('fin')
            m.component('comp1').mesh('mesh1').run()

        k_path, k_dist = make_k_path(a, n_seg)
        freqs_GHz      = np.full((len(k_path), n_modes), np.nan)

        for i, (kxi, kyi) in enumerate(k_path):
            m.param().set('kx', repr(kxi))
            m.param().set('ky', repr(kyi))
            m.study('std1').run()
            try:
                raw = ev.getData()
                row = np.array([float(entry[0]) for entry in raw])
                n   = min(len(row), n_modes)
                freqs_GHz[i, :n] = row[:n]
            except Exception as e:
                print(f'  WARNING getData k={i}: {e}')

            if i % 10 == 0:
                print(f'  k={i+1}/{len(k_path)}')

        gaps = find_bandgaps(freqs_GHz)

        row_out = {
            'combo':           ci + 1,
            'a_nm':            a_nm,
            'da':              round(da, 4),
            'ra':              round(ra, 4),
            'd_nm':            round(da * a_nm, 1),
            'r_nm':            round(ra * a_nm, 1),
            'n_gaps':          len(gaps),
            'gap1_lo_GHz':     round(gaps[0][0], 4) if gaps else 0,
            'gap1_hi_GHz':     round(gaps[0][1], 4) if gaps else 0,
            'gap1_center_GHz': round(0.5*(gaps[0][0]+gaps[0][1]), 4) if gaps else 0,
            'gap1_frac':       round(gaps[0][2], 4) if gaps else 0,
        }
        writer.writerow(row_out)
        csv_f.flush()

        gap_str = (f'{gaps[0][2]*100:.1f}%  center={0.5*(gaps[0][0]+gaps[0][1]):.2f} GHz'
                   if gaps else 'no gap')
        print(f'  -> {gap_str}')

        tag = f'a{int(a_nm)}nm_da{int(da*100):03d}_ra{int(ra*100):03d}'
        np.savez(os.path.join(save_dir, f'sweep_band_{tag}.npz'),
                 freqs_GHz=freqs_GHz, k_dist=k_dist,
                 a=a, d=d, r=r, da=da, ra=ra)

print(f'\nSweep complete. Results saved: {csv_path}')
client.clear()
print('Done.')
