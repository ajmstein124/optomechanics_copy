"""
bands_aniso.py  (remote)
Oh 2026 mirror-cell mechanical bands (all 4 classes, Gamma -> X, mesh t/5) with ANISOTROPIC cubic diamond,
C11, C12, C44 = 1076, 125, 578 GPa (Grimsditch & Ramdas 1975), for the beam axis (x) along [100] and along
[110] (crystal rotated 45 deg about z = [001], the membrane normal of Oh's (100) diamond). Compared with
the isotropic run (bands_t5.npz) against Oh Fig. 1(e) in compare_aniso.py. Oh does not state his model.

Output: runs/nanobeam_oh2026/data/bands_aniso100.npz, bands_aniso110.npz
Run via:  python scripts/remote_runner.py runs/nanobeam_oh2026/bands_aniso.py
"""
import sys, time
from pathlib import Path
import mph
import numpy as np
from comsol_utils import mphglobal

N_K = 21
CLASSES = [('+', '+'), ('-', '+'), ('+', '-'), ('-', '-')]
OUT = Path('runs/nanobeam_oh2026/data')
def p(*a): print(*a); sys.stdout.flush()

client = mph.start(); model = client.load('nanobeam_oh2026.mph'); m = model.java
comp = m.component('comp1'); solid = comp.physics('solid'); mesh1 = comp.mesh('mesh1')
mesh1.feature('ftri1').feature('size1').set('hmax', 't/5.33'); mesh1.feature('ftet1').feature('size1').set('hmax', 't/5')
mesh1.run()
lemm = solid.feature('lemm1')
lemm.set('SolidModel', 'Anisotropic'); lemm.set('CrystalSystem', 'Qubic3')   # COMSOL's spelling
lemm.set('c3cub_mat', 'userdef'); lemm.set('c3cub', ['1076[GPa]', '125[GPa]', '578[GPa]'])
lemm.set('rho_mat', 'userdef'); lemm.set('rho', 'rho_d')
cs = comp.coordSystem().create('sys_cr', 'Rotated'); cs.label('crystal axes')
lemm.set('coordinateSystem', 'sys_cr')
p('lemm1:', lemm.getString('SolidModel'), lemm.getString('CrystalSystem'), [str(s) for s in lemm.getStringArray('c3cub')])
a = 650e-9; n_mode = int(float(m.param().evaluate('N_mode'))); ks = np.linspace(0, np.pi / a, N_K)
for case, ang in (('aniso100', '0'), ('aniso110', '45')):
    fn = OUT / f'bands_{case}.npz'
    if fn.exists(): continue
    cs.set('angle', [ang + '[deg]', '0', '0'])
    freqs = np.full((N_K, 4, n_mode), np.nan); t0 = time.time()
    for ik, k in enumerate(ks):
        m.param().set('kx', f'{k}[1/m]')
        for ic, (yc, zc) in enumerate(CLASSES):
            for plane, c in (('y0', yc), ('z0', zc)):
                solid.feature(f'sym_{plane}').active(c == '+'); solid.feature(f'as_{plane}').active(c == '-')
            m.sol('sol1').runAll()
            f = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1')))[:n_mode]
            freqs[ik, ic, :len(f)] = f
        if ik in (0, N_K - 1):
            p(f'  {case} k {ik+1}/{N_K} ({time.time()-t0:.0f} s): Y+Z+ ' + ', '.join(f'{x/1e9:.2f}' for x in freqs[ik, 0, :4]))
    np.savez(str(fn), k=ks, k_frac=ks / ks[-1], freqs=freqs, classes=np.array(['Y+Z+', 'Y-Z+', 'Y+Z-', 'Y-Z-']),
             case=case, angle_deg=float(ang))
    p(f'Saved {fn}')
client.clear(); p('Aniso bands done.')
