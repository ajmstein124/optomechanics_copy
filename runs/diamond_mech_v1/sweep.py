"""
sweep_diamond_mech.py
======================
Python-driven diamond Mech Study band structure sweep.
Generates k-points programmatically (no GUI CSV dependency).

Parameters (fresh start, 2026-10-13):
    a     = 300 nm    -- lattice constant (chosen so t/a ~ 0.467, close to Si 0.460)
    d     = 104 nm    -- arm length  (d/a = 0.347, same ratio as Si)
    w     = 107 nm    -- arm width   (w/a = 0.356, same ratio as Si)
    f_r   = 16 nm     -- fillet radius (f_r/a = 0.053, scaled from Si)
    t     = 140 nm    -- slab thickness (fixed)
    Material: isotropic diamond (E=1050 GPa, nu=0.07, rho=3500 kg/m^3)
    f_mech = 10 GHz   -- eigensolver shift (below expected gap ~23 GHz)
    N_mode = 10

Expected phononic bandgap: ~23 GHz
    f ~ 0.582 * v_TA / a = 0.582 * 11840 / 300e-9 ~ 23 GHz
    (0.582 = normalised gap position from validated Si model;
     v_TA = sqrt(G/rho) = sqrt(E/(2(1+nu))/rho) = sqrt(491e9/3500) = 11840 m/s)

Produces:
    runs/diamond_mech_v1/data/Python_diamond_Gamma_sym.csv
    runs/diamond_mech_v1/data/Python_diamond_Gamma_antisym.csv

Note: on Windows the script runs from C:/Users/abby/comsol/ and writes to
simu_data/Python_diamond_Gamma_*.csv there. After pulling, move those files
into runs/diamond_mech_v1/data/ locally.

Run via:
    python scripts/remote_runner.py runs/diamond_mech_v1/sweep.py
"""

import sys
import csv
import numpy as np
from pathlib import Path
from comsol_utils import start_client, mphglobal

DATA        = Path('runs/diamond_mech_v1/data')
OUT_SYM     = DATA / 'Python_diamond_Gamma_sym.csv'
OUT_ANTISYM = DATA / 'Python_diamond_Gamma_antisym.csv'

# ── Geometry and material ──────────────────────────────────────────────────────

a     = 300e-9    # lattice constant [m]
d     = 104e-9    # arm length [m]
w     = 107e-9    # arm width [m]
f_r   = 16e-9     # fillet radius [m]
t     = 140e-9    # slab thickness [m]
N_mode = 20
f_mech = 10e9     # eigensolver shift [Hz]

# Isotropic diamond material (overrides Si in .mph)
E_diamond   = 1050e9   # Young's modulus [Pa]
nu_diamond  = 0.07     # Poisson's ratio
rho_diamond = 3500.0   # density [kg/m^3]

# ── k-point path Gamma -> M -> K -> Gamma ─────────────────────────────────────
# Rectangular 2-atom supercell: Lx=a, Ly=a*sqrt(3)
# BZ high-symmetry points:
#   Gamma = (0, 0)
#   M     = (pi/a, pi/(a*sqrt(3)))
#   K     = (4*pi/(3*a), 0)

n_seg = 9    # steps per segment (27 unique k-points total)

G = np.array([0.0, 0.0])
M = np.array([np.pi / a, np.pi / (a * np.sqrt(3))])
K = np.array([4 * np.pi / (3 * a), 0.0])

def _seg(start, end, n):
    """n+1 points from start to end inclusive."""
    return [start + (end - start) * i / n for i in range(n + 1)]

seg_GM = _seg(G, M, n_seg)
seg_MK = _seg(M, K, n_seg)
seg_KG = _seg(K, G, n_seg)

# Deduplicate junction points (M and K appear at end of one segment and start of next)
raw = seg_GM + seg_MK[1:] + seg_KG[1:]
seen = set()
kpoints = []
for kv in raw:
    key = (round(kv[0]), round(kv[1]))
    if key not in seen:
        seen.add(key)
        kpoints.append((float(kv[0]), float(kv[1])))

print(f'Generated {len(kpoints)} unique k-points along Gamma->M->K->Gamma')
sys.stdout.flush()


def init_csv(out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    open(str(out_path), 'w').close()  # truncate / create

def append_csv(out_path, rows):
    with open(str(out_path), 'a', newline='') as fh:
        csv.writer(fh).writerows(rows)


# ── Connect and configure model ───────────────────────────────────────────────

client, model = start_client('unit_cell_3.mph')
m = model.java

# Geometry parameters
for name, val in [('a', a), ('d', d), ('w', w), ('f_r', f_r),
                  ('t', t), ('N_mode', N_mode), ('f_mech', f_mech),
                  ('scaling', 1.0), ('kFx', 0.0), ('kFy', 0.0)]:
    m.param().set(name, str(val))

# Override Si material with isotropic diamond.
# E and nu: set in Enu group -> appear as Output Properties (confirmed working).
# rho: setting in def group only creates a Local Property (not Output Property);
#   also set in Enu group where it becomes an Output Property too.
#   Both locations are set for safety; Enu group is the reliable path.
m.material('mat1').propertyGroup('def').set('rho', str(rho_diamond))
m.material('mat1').propertyGroup('Enu').set('E',   str(E_diamond))
m.material('mat1').propertyGroup('Enu').set('nu',  str(nu_diamond))
m.material('mat1').propertyGroup('Enu').set('rho', str(rho_diamond))
m.material('mat1').label('Diamond')

print(f'Diamond material set: E={E_diamond/1e9:.0f} GPa, nu={nu_diamond}, rho={rho_diamond} kg/m^3')
print(f'v_TA = {np.sqrt(E_diamond/(2*(1+nu_diamond))/rho_diamond):.0f} m/s')
print(f'Expected gap center ~ {0.582 * np.sqrt(E_diamond/(2*(1+nu_diamond))/rho_diamond) / a / 1e9:.1f} GHz')
sys.stdout.flush()

# ── Mech Study sweeps ─────────────────────────────────────────────────────────

solid = m.component('comp1').physics('solid')

for sym_label, active_feat, inactive_feat, out_path in [
    ('sym',     'sym1', 'as1',  OUT_SYM),
    ('antisym', 'as1',  'sym1', OUT_ANTISYM),
]:
    print(f'\n=== Mech {sym_label} sweep ({len(kpoints)} k-points) ===')
    sys.stdout.flush()
    init_csv(out_path)

    for ii, (kx, ky) in enumerate(kpoints):
        print(f'  [{ii+1}/{len(kpoints)}]  kx={kx:.4e}  ky={ky:.4e}')
        sys.stdout.flush()

        m.param().set('kFx', str(kx))
        m.param().set('kFy', str(ky))
        solid.feature(inactive_feat).active(False)
        solid.feature(active_feat).active(True)
        m.sol('sol1').runAll()

        freqs = mphglobal(m, 'solid.freq', 'dset1')
        freqs_hz = np.real(freqs[:N_mode])

        rows = [[f'{kx}', f'{ky}', f'{f}', f'{f}', ''] for f in freqs_hz]
        append_csv(out_path, rows)
        print(f'  -> saved {len(rows)} freqs to {out_path.name}')
        sys.stdout.flush()

client.clear()
print('Done.')
