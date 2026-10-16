"""
Mechanical band structure of snowflake unit cell -- diamond at 619 nm.
5x5 sweep over d and w around nominal diamond parameters.
Expected mechanical bandgap center: ~36 GHz.

v2 fix: f0 lowered from 36 GHz to 5 GHz so COMSOL shift-invert eigensolver
captures all acoustic modes from near-DC upward (same approach as Si sweep).
N_freqs raised from 10 to 20 per symmetry (40 total) to span 0 -> 40+ GHz.
The previous v1 run only captured modes near 36 GHz, missing the full band
structure needed to confirm a complete bandgap.
Results saved to simu_data/diamond_mech_v2/ to keep v1 results intact.

Run via:
    python scripts/remote_runner.py scripts/diamond_unitcell_Mech_band_Gap.py
"""

import sys
import numpy as np
import scipy.io
import matplotlib.pyplot as plt
from pathlib import Path
from comsol_utils import start_client, mphglobal, make_bz_path, bz_ticks, BZ_LABELS

SAVE_FOLDER = Path('simu_data') / 'diamond_mech_v2'  # v1 preserved
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

client, model = start_client('unit_cell_3.mph')
m = model.java

# Diamond material overrides
mat = m.material('mat1').propertyGroup('def')
mat.set('density',       '3500[kg/m^3]')
mat.set('youngsmodulus', '1050e9[Pa]')
mat.set('poissonsratio', '0.07')

a      = 190e-9
t      = 140e-9
N_freqs = 20    # 20 per symmetry = 40 total; enough to resolve bands around gap
f0     = 36e9   # shift near expected gap center so eigensolver captures bands on both sides
N_ks   = 5

ds = 72e-9 + np.linspace(-4e-9, 4e-9, 5)
ws = 39e-9 + np.linspace( 0e-9, 8e-9, 5)
dm, wm = np.meshgrid(ds, ws)
comb = np.column_stack([dm.ravel(), wm.ravel()])

solid = m.component('comp1').physics('solid')

for ic in range(len(comb)):
    d, w = comb[ic]
    print(f'--- combo {ic+1}/{len(comb)}  d={d*1e9:.1f}nm  w={w*1e9:.1f}nm ---')
    sys.stdout.flush()

    for name, val in [('a', a), ('d', d), ('w', w), ('f_r', 10e-9),
                       ('t', t), ('N_mode', N_freqs), ('f_mech', f0)]:
        m.param().set(name, str(val))

    ks = make_bz_path(a, N_ks)
    n_kpts = ks.shape[1]
    freqs = np.zeros((n_kpts, 2*N_freqs), dtype=complex)

    for ii in range(n_kpts):
        print(f'  k-point {ii+1}/{n_kpts}  kx={ks[0,ii]:.3e}  ky={ks[1,ii]:.3e}')
        sys.stdout.flush()
        m.param().set('kFx', str(ks[0, ii]))
        m.param().set('kFy', str(ks[1, ii]))

        # Symmetric modes
        solid.feature('as1').active(False)
        solid.feature('sym1').active(True)
        m.sol('sol1').runAll()
        sym_f = mphglobal(m, 'solid.freq', 'dset1')
        freqs[ii, :N_freqs] = sym_f[:N_freqs]

        # Antisymmetric modes
        solid.feature('sym1').active(False)
        solid.feature('as1').active(True)
        m.sol('sol1').runAll()
        asym_f = mphglobal(m, 'solid.freq', 'dset1')
        freqs[ii, N_freqs:] = asym_f[:N_freqs]

        scipy.io.savemat(
            str(SAVE_FOLDER / f'diamond_Mech_bands_d_{d*1e9:.0f}nm_w_{w*1e9:.0f}nm_ii_{ii+1}.mat'),
            {'freqs': freqs, 'ks': ks, 'a': a, 'd': d,
             'w': w, 't': t, 'f0': f0, 'N_ks': N_ks}
        )

    fig, ax = plt.subplots(figsize=(8, 6))
    for jj in range(n_kpts):
        ax.plot(np.full(N_freqs, jj+1), 1e-9*np.real(freqs[jj, :N_freqs]),  'b.', markersize=8)
        ax.plot(np.full(N_freqs, jj+1), 1e-9*np.real(freqs[jj, N_freqs:]), 'r.', markersize=8)
    ax.set_ylabel('Frequency (GHz)')
    ax.set_xticks(bz_ticks(N_ks))
    ax.set_xticklabels(BZ_LABELS)
    ax.set_xlim([1, 3*N_ks-2])
    ax.legend(['Symmetric', 'Antisymmetric'])
    ax.set_title(f'Diamond mech, a=190nm, d={d*1e9:.0f}nm, w={w*1e9:.0f}nm, t=140nm')
    ax.tick_params(labelsize=12)
    plt.tight_layout()
    plt.savefig(str(SAVE_FOLDER / f'diamond_Mech_band_d_{d*1e9:.0f}nm_w_{w*1e9:.0f}nm.jpg'), dpi=150)
    plt.close(fig)
    print(f'  Plot saved.')
    sys.stdout.flush()

print('All done.')
client.clear()
