"""
bands.py  (remote)
Full Gamma -> X mechanical band structure of the Oh 2026 mirror cell, all 4 symmetry classes,
for two Mech-mesh sizes (convergence check). Loads nanobeam_oh2026.mph built by build_model.py.

Output: runs/nanobeam_oh2026/data/bands_<mesh>.npz  with k (1/m), k_frac, freqs[k, class, mode] (Hz),
classes = ['Y+Z+', 'Y-Z+', 'Y+Z-', 'Y-Z-'].

Run via:
    python scripts/remote_runner.py --block runs/nanobeam_oh2026/bands.py
"""
import sys
import time
from pathlib import Path

import mph
import numpy as np
from comsol_utils import mphglobal

N_K = 21
CLASSES = [('+', '+'), ('-', '+'), ('+', '-'), ('-', '-')]
MESHES = {'t5': ('t/5.33', 't/5'), 't8': ('t/8', 't/8')}
OUT = Path('runs/nanobeam_oh2026/data'); OUT.mkdir(parents=True, exist_ok=True)


def p(*a):
    print(*a); sys.stdout.flush()


client = mph.start()
model = client.load('nanobeam_oh2026.mph')
m = model.java
comp = m.component('comp1')
solid = comp.physics('solid')
mesh1 = comp.mesh('mesh1')
a = 650e-9
n_mode = int(float(m.param().evaluate('N_mode')))
ks = np.linspace(0, np.pi / a, N_K)

for mname, (h_tri, h_tet) in MESHES.items():
    fn = OUT / f'bands_{mname}.npz'
    if fn.exists():
        p(f'{fn} exists, skipping'); continue
    mesh1.feature('ftri1').feature('size1').set('hmax', h_tri)
    mesh1.feature('ftet1').feature('size1').set('hmax', h_tet)
    mesh1.run()
    p(f'\n=== mesh {mname}: {mesh1.getNumElem()} elements ===')
    freqs = np.full((N_K, 4, n_mode), np.nan)
    t0 = time.time()
    for ik, k in enumerate(ks):
        m.param().set('kx', f'{k}[1/m]')
        for ic, (yc, zc) in enumerate(CLASSES):
            for plane, c in (('y0', yc), ('z0', zc)):
                solid.feature(f'sym_{plane}').active(c == '+')
                solid.feature(f'as_{plane}').active(c == '-')
            m.sol('sol1').runAll()
            f = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1')))[:n_mode]
            freqs[ik, ic, :len(f)] = f
        p(f'  k {ik+1}/{N_K}  ({time.time()-t0:.0f} s)')
    np.savez(str(fn), k=ks, k_frac=ks / ks[-1], freqs=freqs, classes=np.array(['Y+Z+', 'Y-Z+', 'Y+Z-', 'Y-Z-']),
             n_elem=mesh1.getNumElem(), mesh=mname)
    p(f'Saved {fn}')
client.clear()
p('Bands done.')
