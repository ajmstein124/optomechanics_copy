"""
bands_candidates.py  (remote)
Full TE-like optical bands Gamma -> X (y=0 PEC, z=0 PMC, same as optical_screen.py) for the
strongest stage-2 candidates. Mechanical Y+Z+ bands already exist (data/mech_<tag>.npz).
Shift 300 THz, N_op 30, 21 k-points.

Output: runs/nanobeam_619/data/optbands_<tag>.npz (k, k_frac, freqs[k, mode] Hz). Resumable.

Run via:
    python scripts/remote_runner.py runs/nanobeam_619/bands_candidates.py
"""
import sys
import time
from pathlib import Path

import mph
import numpy as np
from comsol_utils import mphglobal

CANDS = [(550, 220, 0.53, 0.77), (450, 245, 0.60, 0.77), (450, 220, 0.53, 0.77)]
N_K = 21
N_OP = 30
DATA = Path('runs/nanobeam_619/data')


def p(*a):
    print(*a); sys.stdout.flush()


client = mph.start()
model = client.load('nanobeam_619.mph')
m = model.java
sol_op = [str(t) for t in m.sol().tags()][-1]
m.param().set('f_op', '300[THz]'); m.param().set('N_op', str(N_OP))
t0 = time.time()
for w, a, hxa, hyw in CANDS:
    tag = f'w{w}_a{a}_hx{int(round(hxa*100))}_hy{int(round(hyw*100))}'
    fn = DATA / f'optbands_{tag}.npz'
    if fn.exists():
        continue
    for k_, v in (('a', a), ('w', w), ('hx', hxa * a), ('hy', hyw * w)):
        m.param().set(k_, f'{v}[nm]')
    ks = np.linspace(0, np.pi / (a * 1e-9), N_K)
    freqs = np.full((N_K, N_OP), np.nan)
    for ik, k in enumerate(ks):
        m.param().set('kx', f'{k}[1/m]')
        m.sol(sol_op).runAll()
        f = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2')))
        f = f[f >= 1e12][:N_OP]
        freqs[ik, :len(f)] = f
    np.savez(str(fn), k=ks, k_frac=ks / ks[-1], freqs=freqs, w=w, a=a, hx_a=hxa, hy_w=hyw, t=120.0)
    p(f'{tag}: done ({time.time()-t0:.0f} s); at X guided ' +
      ', '.join(f'{x/1e12:.0f}' for x in freqs[-1] if x < 299792458 / (2 * a * 1e-9)) + ' THz')
client.clear()
p('Candidate optical bands done.')
