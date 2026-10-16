"""
diamond_a_sweep.py
==================
Exploratory lattice-constant sweep for diamond, toward photonic-compatible periods
(a/lambda ~ 0.24-0.44 at the 619 nm SnV ZPL). Mechanical band structure only.

Sweep (54 combos, a = outer loop):
    a   in [150, 175, 200, 225, 250, 275] nm
    d/a in [0.35, 0.41, 0.48]       (0.41 = 124/300, best from diamond_dw_sweep)
    w/a in [0.28, 0.36, 0.43]       (0.36 = 107/300)
Fixed:  t=140 nm, f_r=16 nm
        Material: isotropic diamond (E=1050 GPa, nu=0.07, rho=3500 kg/m^3)
        N_mode=10, n_seg=7 (21 unique k-points)
        f_mech = 10 GHz * (300 nm / a)  -- gap moves up as 1/a

Resumable: combos whose .npz already exists are skipped. No time limit -- runs
until done or killed manually.

Saves one .npz per combo to runs/diamond_a_sweep/data/ (relative to C:/Users/abby/comsol/).

Run via:
    python scripts/remote_runner.py runs/diamond_a_sweep/sweep.py
"""

import sys
import time
import numpy as np
from pathlib import Path
from comsol_utils import start_client, mphglobal

DATA = Path('runs/diamond_a_sweep/data')
DATA.mkdir(parents=True, exist_ok=True)

# --- Fixed geometry and material ---------------------------------------------

t      = 140e-9
f_r    = 16e-9
N_mode = 10

E_diamond   = 1050e9
nu_diamond  = 0.07
rho_diamond = 3500.0

# --- Sweep axes ----------------------------------------------------------------

a_vals  = np.array([150, 175, 200, 225, 250, 275]) * 1e-9
da_vals = [0.35, 0.41, 0.48]
wa_vals = [0.28, 0.36, 0.43]

GAP_BAND = 6   # fundamental gap lies between sorted bands 6 and 7 (diamond_dw_sweep)

n_seg = 7


def kpath(a):
    G = np.array([0.0, 0.0])
    M = np.array([np.pi / a, np.pi / (a * np.sqrt(3))])
    K = np.array([4 * np.pi / (3 * a), 0.0])

    def _seg(start, end, n):
        return [start + (end - start) * i / n for i in range(n + 1)]

    raw = _seg(G, M, n_seg) + _seg(M, K, n_seg)[1:] + _seg(K, G, n_seg)[1:]
    seen, kpts = set(), []
    for kv in raw:
        key = (round(kv[0]), round(kv[1]))
        if key not in seen:
            seen.add(key)
            kpts.append((float(kv[0]), float(kv[1])))
    return kpts


def all_complete_gaps(freqs_arr):
    """List of (band_below, f_lo_GHz, f_hi_GHz) for every complete gap > 0 (1-based band index)."""
    sb = np.sort(np.abs(np.real(freqs_arr)), axis=1) * 1e-9
    gaps = []
    for b in range(sb.shape[1] - 1):
        top, bot = sb[:, b].max(), sb[:, b + 1].min()
        if bot > top and top > 1.0:
            gaps.append((b + 1, top, bot))
    return gaps


# --- Connect -----------------------------------------------------------------

client, model = start_client('unit_cell_3.mph')
m     = model.java
solid = m.component('comp1').physics('solid')

for name, val in [('t', t), ('f_r', f_r), ('N_mode', N_mode),
                  ('scaling', 1.0), ('kFx', 0.0), ('kFy', 0.0)]:
    m.param().set(name, str(val))

m.material('mat1').propertyGroup('def').set('rho', str(rho_diamond))
m.material('mat1').propertyGroup('Enu').set('E',   str(E_diamond))
m.material('mat1').propertyGroup('Enu').set('nu',  str(nu_diamond))
m.material('mat1').propertyGroup('Enu').set('rho', str(rho_diamond))
m.material('mat1').label('Diamond')

print(f'Diamond: E={E_diamond/1e9:.0f} GPa, nu={nu_diamond}, rho={rho_diamond} kg/m^3')
sys.stdout.flush()

# --- Sweep -------------------------------------------------------------------

n_combos = len(a_vals) * len(da_vals) * len(wa_vals)
combo    = 0
t_start  = time.time()

for a in a_vals:
    a_nm    = int(round(a * 1e9))
    f_mech  = 10e9 * (300e-9 / a)
    kpoints = kpath(a)
    n_kpts  = len(kpoints)
    m.param().set('a', str(a))
    m.param().set('f_mech', str(f_mech))

    for da in da_vals:
        for wa in wa_vals:
            combo += 1
            d, w = da * a, wa * a
            tag   = f'a{a_nm}_da{int(round(da*100)):02d}_wa{int(round(wa*100)):02d}'
            fname = DATA / f'sweep_{tag}.npz'
            if fname.exists():
                print(f'\n=== Combo {combo}/{n_combos}: {tag} -- exists, skipping ===')
                sys.stdout.flush()
                continue

            print(f'\n=== Combo {combo}/{n_combos}: a={a_nm}nm  d={d*1e9:.1f}nm  '
                  f'w={w*1e9:.1f}nm  f_mech={f_mech/1e9:.1f}GHz  '
                  f'(elapsed {(time.time()-t_start)/3600:.2f} h) ===')
            sys.stdout.flush()

            m.param().set('d', str(d))
            m.param().set('w', str(w))

            freqs = np.zeros((n_kpts, 2 * N_mode))
            try:
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
            except Exception as e:
                # Geometry/mesh failure for this combo -- log and move on, don't kill the sweep
                print(f'  !! FAILED {tag}: {e}')
                sys.stdout.flush()
                continue

            gaps = all_complete_gaps(freqs)
            fund = [g for g in gaps if g[0] == GAP_BAND]
            gc, gw = ((fund[0][1] + fund[0][2]) / 2, fund[0][2] - fund[0][1]) if fund else (0.0, 0.0)
            print(f'  --> Band {GAP_BAND}-{GAP_BAND+1} gap: center={gc:.2f} GHz  width={gw:.2f} GHz')
            for b, lo, hi in gaps:
                print(f'      complete gap above band {b}: {lo:.2f}-{hi:.2f} GHz')
            sys.stdout.flush()

            np.savez(str(fname), freqs=freqs, kpoints=np.array(kpoints),
                     a=a, d=d, w=w, t=t, f_r=f_r, da=da, wa=wa, f_mech=f_mech,
                     gap_cen=gc, gap_wid=gw,
                     all_gaps=np.array(gaps) if gaps else np.zeros((0, 3)))
            print(f'  Saved: {fname.name}')
            sys.stdout.flush()

client.clear()
print(f'\nAll combos done. Total {(time.time()-t_start)/3600:.2f} h')
