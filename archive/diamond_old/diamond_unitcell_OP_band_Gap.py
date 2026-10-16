"""
Optical band structure of snowflake unit cell -- diamond at 619 nm.
11x11 sweep over d and w. Target: photonic gap at 484.7 THz (619 nm, SnV ZPL).

Run via:
    python scripts/remote_runner.py scripts/diamond_unitcell_OP_band_Gap.py
"""

import sys
import numpy as np
import scipy.io
import matplotlib.pyplot as plt
from pathlib import Path
from comsol_utils import start_client, mphglobal, make_bz_path, bz_ticks, BZ_LABELS

SAVE_FOLDER = Path('simu_data') / 'diamond_optical'
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

TARGET_THz = 484.7   # 619 nm SnV ZPL

client, model = start_client('unit_cell_3.mph')
m = model.java

# Diamond material overrides (mechanical + optical)
mat = m.material('mat1').propertyGroup('def')
mat.set('density',       '3500[kg/m^3]')
mat.set('youngsmodulus', '1050e9[Pa]')
mat.set('poissonsratio', '0.07')
# n=2.41 -> eps_r = n^2 = 5.81
mat.set('relpermittivity', ['5.81', '0', '0', '0', '5.81', '0', '0', '0', '5.81'])

a      = 190e-9
t      = 140e-9
N_freqs = 12
f0     = 400e12   # search center; target is 484.7 THz
N_ks   = 5

ds = 64e-9 + np.linspace(-8e-9, 8e-9, 11)
ws = 37e-9 + np.linspace(-4e-9, 4e-9, 11)
dm, wm = np.meshgrid(ds, ws)
comb = np.column_stack([dm.ravel(), wm.ravel()])

ewfd = m.component('comp1').physics('ewfd')

for ic in range(len(comb)):
    d, w = comb[ic]
    print(f'--- combo {ic+1}/{len(comb)}  d={d*1e9:.1f}nm  w={w*1e9:.1f}nm ---')
    sys.stdout.flush()

    for name, val in [('a', a), ('d', d), ('w', w), ('f_r', 10e-9),
                       ('t', t), ('N_mode', N_freqs), ('f_op', f0)]:
        m.param().set(name, str(val))

    ks = make_bz_path(a, N_ks)
    n_kpts = ks.shape[1]
    freqs = np.zeros((n_kpts, 2*N_freqs), dtype=complex)

    for ii in range(n_kpts):
        print(f'  k-point {ii+1}/{n_kpts}  kx={ks[0,ii]:.3e}  ky={ks[1,ii]:.3e}')
        sys.stdout.flush()
        m.param().set('kFx', str(ks[0, ii]))
        m.param().set('kFy', str(ks[1, ii]))

        # PMC boundary -- TE-like modes
        ewfd.feature('pec2').active(False)
        ewfd.feature('pmc1').active(True)
        m.sol('sol2').runAll()
        pmc_f = mphglobal(m, 'freq', 'dset2')
        freqs[ii, :N_freqs] = pmc_f[:N_freqs]

        # PEC boundary -- TM-like modes
        ewfd.feature('pmc1').active(False)
        ewfd.feature('pec2').active(True)
        m.sol('sol2').runAll()
        pec_f = mphglobal(m, 'freq', 'dset2')
        freqs[ii, N_freqs:] = pec_f[:N_freqs]

        scipy.io.savemat(
            str(SAVE_FOLDER / f'diamond_OP_bands_d_{d*1e9:.0f}nm_w_{w*1e9:.0f}nm_ii_{ii+1}.mat'),
            {'freqs': freqs, 'ks': ks, 'a': a, 'd': d,
             'w': w, 't': t, 'f0': f0, 'N_ks': N_ks}
        )

    fig, ax = plt.subplots(figsize=(8, 6))
    for jj in range(n_kpts):
        ax.plot(np.full(N_freqs, jj+1), 1e-12*np.real(freqs[jj, :N_freqs]),  'b.', markersize=8)
        ax.plot(np.full(N_freqs, jj+1), 1e-12*np.real(freqs[jj, N_freqs:]), 'r.', markersize=8)
    ax.axhline(TARGET_THz, color='k', linestyle='--', label='619 nm')
    ax.set_ylabel('Frequency (THz)')
    ax.set_xticks(bz_ticks(N_ks))
    ax.set_xticklabels(BZ_LABELS)
    ax.set_xlim([1, 3*N_ks-2])
    ax.legend(['PMC (TE-like)', 'PEC (TM-like)', '619 nm'])
    ax.set_title(f'Diamond optical, a=190nm, d={d*1e9:.0f}nm, w={w*1e9:.0f}nm, t=140nm')
    ax.tick_params(labelsize=12)
    plt.tight_layout()
    plt.savefig(str(SAVE_FOLDER / f'diamond_OP_band_d_{d*1e9:.0f}nm_w_{w*1e9:.0f}nm.jpg'), dpi=150)
    plt.close(fig)
    print(f'  Plot saved.')
    sys.stdout.flush()

print('All done.')
client.clear()
