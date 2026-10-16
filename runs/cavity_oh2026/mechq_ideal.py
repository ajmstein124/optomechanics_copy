"""
mechq_ideal.py  (remote)  -- runs/cavity_oh2026
Mechanical Q benchmark, step 1 (ideal, symmetric geometry): radiation through the mirrors into the
beam's PML section. Solid Mechanics extended to the beam part inside the +x PML (pml1 covers it),
Fixed constraint off. Breathing class (Sym x0, y0, z0). Q_m = |Im lambda| / (2 |Re lambda|). Also the effective mass
(m_eff = 8 int rho|u|^2 / max|u|^2) evaluated in one dataset.
Oh: Q_m is measured only (1.9e6 at 4 K); Oh does not simulate Q_m.

Run via:
    python scripts/remote_runner.py --block runs/cavity_oh2026/mechq_ideal.py
"""
import sys
import mph
import numpy as np
from comsol_utils import mphglobal
from build_cavity_model import mech_class

def p(*a): print(*a); sys.stdout.flush()
client = mph.start(); model = client.load('cavity_oh2026_solved.mph'); m = model.java
comp = m.component('comp1'); solid = comp.physics('solid')
solid.selection().named('sel_beam_all'); solid.feature('fix_end').active(False)
mech_class(model, '+', '+', '+')
m.param().set('N_mode', '30')
m.sol('sol1').runAll()
f = np.real(mphglobal(m, 'solid.freq', 'dset1'))
lam = mphglobal(m, 'lambda', 'dset1')          # lambda = damping - i*omega
Q = np.abs(lam.imag) / (2 * np.abs(lam.real))
loc = np.real(mphglobal(m, 'int_beam(solid.disp^2*(x<4000[nm]))/int_beam(solid.disp^2)', 'dset1'))
meff = np.real(mphglobal(m, '8*int_beam(rho_d*solid.disp^2)/max_beam(solid.disp^2)', 'dset1'))
p('mode  f [GHz]   loc    Q_m        m_eff [fg]')
for i in range(len(f)):
    if loc[i] > 0.5:
        p(f'{i+1:3d}  {f[i]/1e9:8.4f}  {loc[i]:.3f}  {Q[i]:10.3g}  {meff[i]*1e18:8.1f}')
np.savez('runs/cavity_oh2026/data/mechq_ideal.npz', f=f, Q=Q, loc=loc, meff=meff)
model.save('cavity_oh2026_mechq_ideal.mph')
client.clear()
