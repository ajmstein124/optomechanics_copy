"""
bands_optical.py  (remote)
TE-like optical bands (y=0 PEC, z=0 PMC) of the Oh 2026 mirror cell, Gamma -> X, for
n_diamond = 2.41 (project value at 619 nm) and 2.39 (diamond near 1559 nm; Oh's n not stated),
plus a finer OP mesh at n=2.39 (convergence). Guided modes = below the air light line,
selected in compare_optical.py.

Output: runs/nanobeam_oh2026/data/optical_<case>.npz  (k, k_frac, freqs[k, mode] Hz)

Run via:
    python scripts/remote_runner.py --block runs/nanobeam_oh2026/bands_optical.py
"""
import sys
import time
from pathlib import Path

import mph
import numpy as np
from comsol_utils import mphglobal

N_K = 21
A = 650e-9
CASES = {'n241': ('2.41', None), 'n239': ('2.39', None), 'n239_fine': ('2.39', ('pad_z/15', 't/10'))}
OUT = Path('runs/nanobeam_oh2026/data'); OUT.mkdir(parents=True, exist_ok=True)


def p(*a):
    print(*a); sys.stdout.flush()


client = mph.start()
model = client.load('nanobeam_oh2026.mph')
m = model.java
comp = m.component('comp1')
mesh2 = comp.mesh('mesh2')
sol_op = [str(t) for t in m.sol().tags()][-1]
ks = np.linspace(0, np.pi / A, N_K)
n_op = int(float(m.param().evaluate('N_op')))

for case, (n_val, fine) in CASES.items():
    fn = OUT / f'optical_{case}.npz'
    if fn.exists():
        p(f'{fn} exists, skipping'); continue
    m.param().set('n_d', n_val)
    if fine:
        for tag in ('ftri1', 'ftet1'):
            mesh2.feature(tag).feature('size1').set('hmax', fine[0])
            mesh2.feature(tag).feature('size2').set('hmax', fine[1]) if 'size2' in [str(x) for x in mesh2.feature(tag).feature().tags()] else None
    mesh2.run()
    p(f'\n=== {case}: n={n_val}, OP mesh {mesh2.getNumElem()} elements ===')
    freqs = np.full((N_K, n_op), np.nan)
    t0 = time.time()
    for ik, k in enumerate(ks):
        m.param().set('kx', f'{k}[1/m]')
        m.sol(sol_op).runAll()
        f = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2')))[:n_op]
        freqs[ik, :len(f)] = f
        p(f'  k {ik+1}/{N_K} ({time.time()-t0:.0f} s): lowest {f[0]/1e12:.1f} THz')
    np.savez(str(fn), k=ks, k_frac=ks / ks[-1], freqs=freqs, n=float(n_val), n_elem=mesh2.getNumElem(), a=A)
    p(f'Saved {fn}')
client.clear()
p('Optical bands done.')
