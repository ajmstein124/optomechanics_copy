"""
diag_mesh_convergence.py  (read-only; does not save the model)
Compare eigenfrequencies at Gamma and X (sym1 + as1, N_mode=12) for the original Mech Mesh
(ftri1/size1 hmax=t/8, ftet1/size1 hmax=t/7.5) against coarser candidates, at a=1000 nm,
for an easy cell and the thinnest-bridge cell. Reports max relative deviation and timing.

Run via:
    python scripts/remote_runner.py --block runs/diamond_a_large/diag_mesh_convergence.py
"""
import json
import sys
import time

import numpy as np
from comsol_utils import start_client, mphglobal


def p(*a):
    print(*a)
    sys.stdout.flush()


MESHES = {'orig t/7.5': ('t/8', 't/7.5'), 'coarse t/5': ('t/5.33', 't/5'), 'coarse t/3.75': ('t/4', 't/3.75')}
N_MODE = 12

client, model = start_client('unit_cell_3.mph')
m = model.java
comp = m.component('comp1')
for name, val in [('t', 140e-9), ('f_r', 16e-9), ('N_mode', N_MODE), ('scaling', 1.0), ('kFx', 0.0), ('kFy', 0.0)]:
    m.param().set(name, str(val))
m.material('mat1').propertyGroup('def').set('rho', '3500.0')
m.material('mat1').propertyGroup('Enu').set('E', '1050e9')
m.material('mat1').propertyGroup('Enu').set('nu', '0.07')
m.material('mat1').propertyGroup('Enu').set('rho', '3500.0')
geom = comp.geom('geom1')
movs = [geom.feature('wp1').geom().feature('mov1'), geom.feature('wp2').geom().feature('mov1')]
solid = comp.physics('solid')
mesh = comp.mesh('mesh1')
plan = {c['tag']: c for c in json.load(open('diamond_a_large__plan.json'))['combos']}

results = {}
for tag in ('a1000_da41_wa22', 'a1000_da48_wa30'):
    c = plan[tag]
    a = c['a_nm'] * 1e-9
    m.param().set('a', str(a)); m.param().set('d', str(c['d_nm'] * 1e-9)); m.param().set('w', str(c['w_nm'] * 1e-9))
    m.param().set('f_mech', str(10e9 * 300e-9 / a))
    for mv in movs:
        mv.set('displx', str(c['shift_x'])); mv.set('disply', str(c['shift_y']))
    geom.run()
    kX = (np.pi / a, np.pi / (a * np.sqrt(3)))          # M point (zone boundary) -- 2D cell
    for mname, (h_tri, h_tet) in MESHES.items():
        mesh.feature('ftri1').feature('size1').set('hmax', h_tri)
        mesh.feature('ftet1').feature('size1').set('hmax', h_tet)
        mesh.run()
        ne = mesh.getNumElem()
        freqs, t0 = [], time.time()
        for kx, ky in ((0.0, 0.0), kX):
            m.param().set('kFx', str(kx)); m.param().set('kFy', str(ky))
            for on, off in (('sym1', 'as1'), ('as1', 'sym1')):
                solid.feature(off).active(False); solid.feature(on).active(True)
                m.sol('sol1').runAll()
                freqs.append(np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1')[:N_MODE])))
        dt = time.time() - t0
        results[(tag, mname)] = np.concatenate(freqs)
        p(f'{tag} {mname:14s}: {ne:7d} elements, 4 solves in {dt:6.1f} s ({dt/4:.1f} s/solve)')
    ref = results[(tag, 'orig t/7.5')]
    for mname in list(MESHES)[1:]:
        f = results[(tag, mname)]
        ok = ref > 1e9
        rel = np.abs(f[ok] - ref[ok]) / ref[ok]
        p(f'  {mname:14s} vs orig: max rel dev {rel.max():.2e}, median {np.median(rel):.2e}, '
          f'max abs {np.abs(f[ok]-ref[ok]).max()/1e6:.1f} MHz')

# restore original mesh settings in memory (model is not saved anyway)
mesh.feature('ftri1').feature('size1').set('hmax', 't/8')
mesh.feature('ftet1').feature('size1').set('hmax', 't/7.5')
client.clear()
p('Diag done.')
