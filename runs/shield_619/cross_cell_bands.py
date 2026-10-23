"""
cross_cell_bands.py  (remote)  -- runs/shield_619
COMSOL check of the square-lattice cross shield cell chosen from the Dmitry-cloud sweep (runs/dmitry/shield1_dmitry):
a 450, cross bar length h 390, bar width 140, fillet 20, diamond t 120 nm (isotropic E 1050 GPa, nu 0.07, rho 3500).
Half-thickness cell (z = 0 Symmetry = 'sym', Antisymmetry = 'antisym', as the Dmitry spec), Floquet on x and y face pairs
(copy-face meshes), k path G-X-M-G with 8 steps per segment (same k points as the Dmitry run), 20 modes around 10 GHz.
Output runs/shield_619/data/cross_cell_bands.npz (k, f[sym/antisym]).
"""
import sys
import time
from pathlib import Path

import mph
import numpy as np
from comsol_utils import mphglobal

CELLS = [dict(a=460, h=395, w=150, fillet=20)]   # 65 nm cell (was a450 h390 w140)
T_NM, NS, NM = 120, 8, 20


def p(*a):
    print(*a); sys.stdout.flush()


def box(comp, tag, dim, x, y, z):
    s = comp.selection().create(tag, 'Box'); s.set('entitydim', str(dim))
    for ax, (lo, hi) in zip('xyz', (x, y, z)):
        s.set(f'{ax}min', lo); s.set(f'{ax}max', hi)
    s.set('condition', 'inside')


def kpath(a):
    G, X, M = np.array([0, 0]), np.array([np.pi / a, 0]), np.array([np.pi / a, np.pi / a])
    ks = [G + (X - G) * i / NS for i in range(NS)] + [X + (M - X) * i / NS for i in range(NS)] + [M + (G - M) * i / NS for i in range(NS + 1)]
    return np.array(ks)


DD = Path('runs/shield_619/data'); DD.mkdir(parents=True, exist_ok=True)
client = mph.start()
for c in CELLS:
    tag = f"cross_a{c['a']}_h{c['h']}_w{c['w']}"
    model = client.create(tag); m = model.java; P = m.param()
    for k, v in (('a', c['a']), ('hc', c['h']), ('wc', c['w']), ('tt', T_NM), ('tol', 1)):
        P.set(k, f'{v}[nm]')
    P.set('kx', '0[1/m]'); P.set('ky', '0[1/m]')
    m.component().create('comp1', True); comp = m.component('comp1')
    g = comp.geom().create('geom1', 3); g.lengthUnit('nm')
    b = g.create('blk', 'Block'); b.set('size', ['a', 'a', 'tt/2'])
    wp = g.create('wp1', 'WorkPlane'); wp.set('quickplane', 'xy'); wg = wp.geom()
    for q, (lx, ly) in enumerate((('hc', 'wc'), ('wc', 'hc'))):
        r = wg.create(f'r{q}', 'Rectangle'); r.set('size', [lx, ly]); r.set('base', 'center'); r.set('pos', ['a/2', 'a/2'])
    u = wg.create('uni', 'Union'); u.selection('input').set(['r0', 'r1']); u.set('intbnd', False)
    wg.run('uni'); nv = int(wg.obj('uni').getNVertices())
    f_ = wg.create('fil', 'Fillet'); f_.selection('point').set('uni', list(range(1, nv + 1))); f_.set('radius', str(c['fillet']))
    ex = g.create('ext', 'Extrude'); ex.selection('input').set(['wp1']); ex.setIndex('distance', 'tt/2', 0)
    d = g.create('dif', 'Difference'); d.selection('input').set(['blk']); d.selection('input2').set(['ext'])
    g.run('fin')
    T, BIG = '(-tol)', '1e6'
    box(comp, 'x0', 2, (T, 'tol'), (T, BIG), (T, BIG)); box(comp, 'xa', 2, ('a-tol', 'a+tol'), (T, BIG), (T, BIG))
    box(comp, 'y0', 2, (T, BIG), (T, 'tol'), (T, BIG)); box(comp, 'ya', 2, (T, BIG), ('a-tol', 'a+tol'), (T, BIG))
    box(comp, 'z0', 2, (T, BIG), (T, BIG), (T, 'tol'))
    for s_ in ('x', 'y'):
        un = comp.selection().create(f'{s_}pair', 'Union'); un.set('entitydim', '2'); un.set('input', [f'{s_}0', f'{s_}a'])
    mat = comp.material().create('mat1', 'Common'); mat.selection().all()
    mat.propertyGroup('def').set('density', '3500[kg/m^3]')
    enu = mat.propertyGroup().create('Enu', 'Enu', 'Enu'); enu.set('E', '1050[GPa]'); enu.set('nu', '0.07')
    sol = comp.physics().create('solid', 'SolidMechanics', 'geom1')
    for s_ in ('x', 'y'):
        pc = sol.create(f'pc_{s_}', 'PeriodicCondition', 2); pc.set('PeriodicType', 'Floquet')
        pc.set('kFloquet', ['kx', 'ky', '0']); pc.selection().named(f'{s_}pair')
    sy = sol.create('sym_z', 'SymmetrySolid', 2); sy.selection().named('z0')
    an = sol.create('as_z', 'Antisymmetry', 2); an.selection().named('z0'); an.active(False)
    ms = comp.mesh().create('mesh1')
    for s_ in ('x', 'y'):
        ft = ms.create(f'ftri_{s_}', 'FreeTri'); ft.selection().named(f'{s_}0')
        sz = ft.create('size1', 'Size'); sz.set('custom', 'on'); sz.set('hmax', 'tt/6'); sz.set('hmaxactive', 'on')
        cf = ms.create(f'cpf_{s_}', 'CopyFace'); cf.selection('source').named(f'{s_}0'); cf.selection('destination').named(f'{s_}a')
    tt = ms.create('ftet', 'FreeTet'); sz = tt.create('size1', 'Size'); sz.set('custom', 'on'); sz.set('hmax', 'tt/6'); sz.set('hmaxactive', 'on')
    ms.run(); p(f'{tag}: mesh {ms.getNumElem()} elements')
    st = m.study().create('std1'); eg = st.create('eig', 'Eigenfrequency')
    eg.set('neigsactive', 'on'); eg.set('neigs', str(NM)); eg.set('shiftactive', 'on'); eg.set('shift', '10[GHz]'); eg.set('eigunit', 'Hz')
    st.createAutoSequences('all')
    ks = kpath(c['a'] * 1e-9); F = np.full((2, len(ks), NM), np.nan); t0 = time.time()
    for ic, cls in enumerate(('sym', 'antisym')):
        sol.feature('sym_z').active(cls == 'sym'); sol.feature('as_z').active(cls == 'antisym')
        for ik, k in enumerate(ks):
            P.set('kx', f'{k[0]}[1/m]'); P.set('ky', f'{k[1]}[1/m]')
            m.sol('sol1').runAll()
            f = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1'))); F[ic, ik, :len(f)] = f[:NM]
        p(f'  {cls}: done ({time.time()-t0:.0f} s)')
    np.savez(str(DD / f'{tag}.npz'), k=ks, f=F, cell=str(c), nelem=int(ms.getNumElem()))
    client.remove(model)
client.clear()
p('cross cell bands done.')
