"""
setup_verify.py -- Diamond mech v1 parameter/material verification
===================================================================
Loads unit_cell_3.mph, applies all diamond geometry + material parameters,
reads them back to confirm, rebuilds geometry, and saves as
diamond_mech_v1_verify.mph.

Does NOT run any simulation.

After this runs, open  C:/Users/abby/comsol/diamond_mech_v1_verify.mph
in the COMSOL GUI and verify:

  1. Parameters 1 node:
       a     = 3E-7   (300 nm)
       d     = 1.04E-7 (104 nm)
       w     = 1.07E-7 (107 nm)
       f_r   = 1.6E-8  (16 nm)
       t     = 1.4E-7  (140 nm)
       scaling = 1
       kFx   = 0,  kFy = 0

  2. Materials -> Silicon (mat1) -> Material Contents table:
       Young's modulus (E)  = 1050[GPa]   (was 170 GPa for Si)
       Poisson's ratio (nu) = 0.07         (was 0.28)
       Density (rho)        = 3500[kg/m^3] (was 2329)

  3. Geometry 1 -> Build All:
       Snowflake hole should be smaller / more delicate than the Si version.
       Unit cell is 300 nm x 300*sqrt(3) nm.

  4. Mesh -> Mech Mesh -> Build All:
       Mesh should complete without errors.

Run via (blocking -- fast, no simulation):
    python scripts/remote_runner.py --block runs/diamond_mech_v1/setup_verify.py
"""

import sys
from pathlib import Path
from comsol_utils import start_client

# ── Parameters matching sweep.py exactly ─────────────────────────────────────

a      = 300e-9
d      = 104e-9
w      = 107e-9
f_r    = 16e-9
t      = 140e-9
N_mode = 10
f_mech = 10e9

E_diamond   = 1050e9
nu_diamond  = 0.07
rho_diamond = 3500.0

SAVE_NAME = 'diamond_mech_v1_verify.mph'

# ── Load and configure ────────────────────────────────────────────────────────

print('Loading unit_cell_3.mph ...')
sys.stdout.flush()
client, model = start_client('unit_cell_3.mph')
m = model.java

# Geometry / solver parameters
params = [
    ('a',       a),
    ('d',       d),
    ('w',       w),
    ('f_r',     f_r),
    ('t',       t),
    ('N_mode',  N_mode),
    ('f_mech',  f_mech),
    ('scaling', 1.0),
    ('kFx',     0.0),
    ('kFy',     0.0),
]
print('\nSetting parameters:')
for name, val in params:
    m.param().set(name, str(val))
    readback = m.param().get(name)
    print('  {:8s} = {:12s}   (readback: {})'.format(name, str(val), readback))
sys.stdout.flush()

# Material override -- GUI-confirmed property names (2026-10-13):
#   density   -> group 'def',  variable 'rho'
#   Young's E -> group 'Enu',  variable 'E'
#   Poisson nu-> group 'Enu',  variable 'nu'
print('\nSetting mat1 (diamond):')
m.material('mat1').propertyGroup('def').set('rho', str(rho_diamond))
m.material('mat1').propertyGroup('Enu').set('E',   str(E_diamond))
m.material('mat1').propertyGroup('Enu').set('nu',  str(nu_diamond))
m.material('mat1').propertyGroup('Enu').set('rho', str(rho_diamond))
m.material('mat1').label('Diamond')

# Read back
rho_def_rb = m.material('mat1').propertyGroup('def').getString('rho')
rho_enu_rb = m.material('mat1').propertyGroup('Enu').getString('rho')
E_rb       = m.material('mat1').propertyGroup('Enu').getString('E')
nu_rb      = m.material('mat1').propertyGroup('Enu').getString('nu')
print('  rho (def local)  readback = {}'.format(rho_def_rb))
print('  rho (Enu output) readback = {}'.format(rho_enu_rb))
print('  E   readback = {}'.format(E_rb))
print('  nu  readback = {}'.format(nu_rb))

expected = {
    'rho_def': str(rho_diamond),
    'rho_enu': str(rho_diamond),
    'E':       str(E_diamond),
    'nu':      str(nu_diamond),
}
actual = {'rho_def': rho_def_rb, 'rho_enu': rho_enu_rb, 'E': E_rb, 'nu': nu_rb}
all_ok = True
for k in expected:
    if actual[k] != expected[k]:
        print('  WARNING: {} mismatch -- set {} got {}'.format(k, expected[k], actual[k]))
        all_ok = False
    else:
        print('  {} OK ({})'.format(k, actual[k]))
if all_ok:
    print('  All material values confirmed OK.')
sys.stdout.flush()

# ── Build geometry so it renders immediately when opened ──────────────────────

print('\nBuilding geometry ...')
sys.stdout.flush()
try:
    m.component('comp1').geom('geom1').run()
    print('  Geometry built.')
except Exception as e:
    print('  Geometry build warning: {}'.format(e))
sys.stdout.flush()

# ── Save ─────────────────────────────────────────────────────────────────────

print('\nSaving {} ...'.format(SAVE_NAME))
sys.stdout.flush()
model.save(SAVE_NAME)
print('Saved.')

client.clear()
print('\nDone. Open {} in COMSOL GUI to verify.'.format(SAVE_NAME))
