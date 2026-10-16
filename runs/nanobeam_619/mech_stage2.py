"""
mech_stage2.py  (remote)
Stage 2 of the 619 nm / 10 GHz nanobeam design: breathing-mode class (Y+Z+, Symmetry on y=0 and
z=0 -- the class validated against Oh 2026 Fig 1e) band structure Gamma -> X for every stage-1
cell whose TE gap at X contains 619 nm (484 THz). Order: widest w first, then smallest |detuning|.
t = 120 nm, isotropic diamond, Mech mesh t/5 (validated: <2e-3 vs t/8 on the Oh cell).
Shift 8 GHz, N_mode 15 (window well above 10-20 GHz); completeness ceiling stored.

Output: runs/nanobeam_619/data/mech_<tag>.npz (k, freqs[k, mode] Hz, ceiling). Resumable.

Run via:
    python scripts/remote_runner.py runs/nanobeam_619/mech_stage2.py
"""
import glob
import sys
import time
from pathlib import Path

import mph
import numpy as np
from comsol_utils import mphglobal
from build_nanobeam_model import class_on

N_K = 21
F0_THZ = 484.0
DATA = Path('runs/nanobeam_619/data')


def p(*a):
    print(*a); sys.stdout.flush()


cands = []
for fn in glob.glob(str(DATA / 'optX_*.npz')):
    d = np.load(fn)
    g = d['guided_THz']
    if g.size >= 2 and g[0] < F0_THZ < g[1]:
        det = 0.5 * (299792.458 / g[0] + 299792.458 / g[1]) - 299792.458 / F0_THZ
        cands.append((-int(d['w']), abs(det), Path(fn).stem.replace('optX_', ''), d))
cands.sort(key=lambda c: (c[0], c[1]))
p(f'{len(cands)} stage-1 cells contain 619 nm -> mechanical Y+Z+ bands, widest w first')

client = mph.start()
model = client.load('nanobeam_619.mph')
m = model.java
mesh1 = m.component('comp1').mesh('mesh1')
mesh1.feature('ftri1').feature('size1').set('hmax', 't/5.33')
mesh1.feature('ftet1').feature('size1').set('hmax', 't/5')
m.param().set('f_mech', '8[GHz]'); m.param().set('N_mode', '15')
class_on(model, '+', '+')                  # breathing-mode class Y+Z+

t0 = time.time()
for i, (_, det, tag, d) in enumerate(cands, 1):
    fn = DATA / f'mech_{tag}.npz'
    if fn.exists():
        continue
    a = float(d['a']) * 1e-9
    for k_, v in (('a', float(d['a'])), ('w', float(d['w'])), ('hx', float(d['hx'])), ('hy', float(d['hy']))):
        m.param().set(k_, f'{v}[nm]')
    ks = np.linspace(0, np.pi / a, N_K)
    freqs = np.full((N_K, 15), np.nan)
    try:
        for ik, k in enumerate(ks):
            m.param().set('kx', f'{k}[1/m]')
            m.sol('sol1').runAll()
            f = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1')))[:15]
            freqs[ik, :len(f)] = f
    except Exception as e:
        p(f'{i}/{len(cands)} {tag}: FAILED {str(e)[:200]}'); continue
    ceil = np.nanmin(np.nanmax(freqs, axis=1)) / 1e9
    sb = np.sort(freqs, axis=1) / 1e9
    gaps = [(b + 1, sb[:, b].max(), sb[:, b + 1].min()) for b in range(sb.shape[1] - 1)
            if sb[:, b + 1].min() > sb[:, b].max() and sb[:, b + 1].min() <= ceil and sb[:, b].max() > 0.5]
    np.savez(str(fn), k=ks, k_frac=ks / ks[-1], freqs=freqs, ceiling_GHz=ceil, gaps=np.array(gaps) if gaps else np.zeros((0, 3)),
             w=d['w'], a=d['a'], hx=d['hx'], hy=d['hy'], t=120.0, hx_a=d['hx_a'], hy_w=d['hy_w'],
             detuning_nm=det, bridge_nm=d['bridge_nm'], rail_nm=d['rail_nm'])
    big = max(gaps, key=lambda g: g[2] - g[1]) if gaps else None
    p(f'{i}/{len(cands)} {tag}: Y+Z+ gaps ' + (', '.join(f'{lo:.1f}-{hi:.1f}' for _, lo, hi in gaps[:4]) or 'none') +
      f' GHz (ceiling {ceil:.0f})' + (f'  widest {big[1]:.1f}-{big[2]:.1f}' if big else '') + f'  ({time.time()-t0:.0f} s)')
client.clear()
p('Mech stage 2 done.')
