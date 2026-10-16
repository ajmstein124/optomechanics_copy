"""
diamond_dw_sweep.py
====================
3x3 sweep of snowflake arm length d and arm width w for diamond.

Fixed:  a=300nm, t=140nm, f_r=16nm
        Material: isotropic diamond (E=1050 GPa, nu=0.07, rho=3500 kg/m^3)
        N_mode=10, f_mech=10 GHz, n_seg=7 (23 unique k-points)
Sweep:  d in [85, 104, 124] nm  x  w in [85, 107, 128] nm  (9 combos)

Saves one .npz per combo to runs/diamond_dw_sweep/data/ (relative to C:/Users/abby/comsol/).

Run via:
    python scripts/remote_runner.py runs/diamond_dw_sweep/sweep.py
"""

import sys
import numpy as np
from pathlib import Path
from comsol_utils import start_client, mphglobal

DATA = Path('runs/diamond_dw_sweep/data')
DATA.mkdir(parents=True, exist_ok=True)

# ── Fixed geometry and material ───────────────────────────────────────────────

a      = 300e-9
t      = 140e-9
f_r    = 16e-9
N_mode = 10
f_mech = 10e9

E_diamond   = 1050e9
nu_diamond  = 0.07
rho_diamond = 3500.0

# ── Sweep axes ────────────────────────────────────────────────────────────────

d_vals = np.array([85, 104, 124]) * 1e-9   # arm length [m]
w_vals = np.array([85, 107, 128]) * 1e-9   # arm width  [m]

# ── k-point path Gamma -> M -> K -> Gamma ─────────────────────────────────────

n_seg = 7    # 23 unique k-points -- sufficient for gap detection in a parameter sweep

G = np.array([0.0, 0.0])
M = np.array([np.pi / a, np.pi / (a * np.sqrt(3))])
K = np.array([4 * np.pi / (3 * a), 0.0])

def _seg(start, end, n):
    return [start + (end - start) * i / n for i in range(n + 1)]

raw = _seg(G, M, n_seg) + _seg(M, K, n_seg)[1:] + _seg(K, G, n_seg)[1:]
seen = set()
kpoints = []
for kv in raw:
    key = (round(kv[0]), round(kv[1]))
    if key not in seen:
        seen.add(key)
        kpoints.append((float(kv[0]), float(kv[1])))

n_kpts = len(kpoints)
print(f'Generated {n_kpts} unique k-points along Gamma->M->K->Gamma')
sys.stdout.flush()

# ── Gap detection (fundamental = lowest-frequency complete gap) ───────────────

def find_fundamental_gap(freqs_arr):
    """Return (center_GHz, width_GHz) of the lowest-frequency complete bandgap > 0.5 GHz."""
    sb = np.sort(np.abs(np.real(freqs_arr)), axis=1) * 1e-9  # GHz, sorted per k-point
    for b in range(sb.shape[1] - 1):
        top = sb[:, b].max()
        bot = sb[:, b + 1].min()
        if bot > top and (bot - top) > 0.5 and top > 1.0:
            return 0.5 * (top + bot), bot - top
    return 0.0, 0.0

# ── Connect ───────────────────────────────────────────────────────────────────

client, model = start_client('unit_cell_3.mph')
m     = model.java
solid = m.component('comp1').physics('solid')

# Set fixed parameters and diamond material once
for name, val in [('a', a), ('t', t), ('f_r', f_r),
                  ('N_mode', N_mode), ('f_mech', f_mech),
                  ('scaling', 1.0), ('kFx', 0.0), ('kFy', 0.0)]:
    m.param().set(name, str(val))

m.material('mat1').propertyGroup('def').set('rho', str(rho_diamond))
m.material('mat1').propertyGroup('Enu').set('E',   str(E_diamond))
m.material('mat1').propertyGroup('Enu').set('nu',  str(nu_diamond))
m.material('mat1').propertyGroup('Enu').set('rho', str(rho_diamond))
m.material('mat1').label('Diamond')

print(f'Diamond: E={E_diamond/1e9:.0f} GPa, nu={nu_diamond}, rho={rho_diamond} kg/m^3')
sys.stdout.flush()

# ── Sweep ─────────────────────────────────────────────────────────────────────

n_combos = len(d_vals) * len(w_vals)
combo    = 0

for i_d, d in enumerate(d_vals):
    for i_w, w in enumerate(w_vals):
        combo += 1
        d_nm = int(round(d * 1e9))
        w_nm = int(round(w * 1e9))
        print(f'\n=== Combo {combo}/{n_combos}: d={d_nm}nm  w={w_nm}nm ===')
        sys.stdout.flush()

        m.param().set('d', str(d))
        m.param().set('w', str(w))

        freqs = np.zeros((n_kpts, 2 * N_mode))

        for ii, (kx, ky) in enumerate(kpoints):
            print(f'  k {ii+1}/{n_kpts}  kx={kx:.3e}  ky={ky:.3e}')
            sys.stdout.flush()
            m.param().set('kFx', str(kx))
            m.param().set('kFy', str(ky))

            solid.feature('as1').active(False)
            solid.feature('sym1').active(True)
            m.sol('sol1').runAll()
            sym_f = mphglobal(m, 'solid.freq', 'dset1')
            freqs[ii, :N_mode] = np.real(sym_f[:N_mode])

            solid.feature('sym1').active(False)
            solid.feature('as1').active(True)
            m.sol('sol1').runAll()
            asym_f = mphglobal(m, 'solid.freq', 'dset1')
            freqs[ii, N_mode:] = np.real(asym_f[:N_mode])

        gc, gw = find_fundamental_gap(freqs)
        print(f'  --> Fundamental gap: center={gc:.2f} GHz  width={gw:.2f} GHz')
        sys.stdout.flush()

        fname = DATA / f'sweep_d{d_nm}_w{w_nm}.npz'
        np.savez(str(fname), freqs=freqs, kpoints=np.array(kpoints),
                 a=a, d=d, w=w, t=t, f_r=f_r,
                 gap_cen=gc, gap_wid=gw)
        print(f'  Saved: {fname.name}')
        sys.stdout.flush()

client.clear()
print('\nAll combos done.')
