"""
diag_mesh.py  (read-only; does not save the model)
Dump every mesh sequence in unit_cell_3.mph with all feature properties, then build the
mechanical mesh for a few (a, d/a, w/a) cases and report element counts and the time for
one k=0 sym solve. Used to decide how to scale the mesh with a.

Run via:
    python scripts/remote_runner.py --block runs/diamond_a_large/diag_mesh.py
"""
import sys
import time
from comsol_utils import start_client

sys.path.insert(0, '.')


def p(*a):
    print(*a)
    sys.stdout.flush()


def dump(f, ind='  '):
    try:
        lbl, typ = str(f.label()), str(f.getType())
    except Exception:
        lbl, typ = '?', '?'
    p(f'{ind}[{f.tag()}] "{lbl}" type={typ}')
    try:
        names = [str(n) for n in f.properties()]
    except Exception:
        names = []
    for n in names:
        for g in ('getString', 'getStringArray'):
            try:
                v = getattr(f, g)(n)
                v = str(v) if g == 'getString' else '[' + ', '.join(str(x) for x in v) + ']'
                if v not in ('', '[]'):
                    p(f'{ind}    {n} = {v}')
                break
            except Exception:
                continue
    try:
        for t2 in f.feature().tags():
            dump(f.feature(t2), ind + '    ')
    except Exception:
        pass


client, model = start_client('unit_cell_3.mph')
m = model.java
comp = m.component('comp1')
p('\n=== MESH SEQUENCES ===')
for mt in comp.mesh().tags():
    ms = comp.mesh(mt)
    p(f'mesh {mt} "{ms.label()}"')
    for ft in ms.feature().tags():
        dump(ms.feature(ft), '  ')

p('\n=== which mesh does the Mech Study (std1/sol1) use? ===')
try:
    st = m.study('std1').feature('eig')
    for n in st.properties():
        n = str(n)
        if 'mesh' in n.lower():
            try:
                p(f'  std1/eig {n} = {st.getString(n)}')
            except Exception:
                p(f'  std1/eig {n} = [' + ', '.join(str(x) for x in st.getStringArray(n)) + ']')
except Exception as e:
    p(f'  could not read: {e}')

# diamond + geometry
for name, val in [('t', 140e-9), ('f_r', 16e-9), ('N_mode', 12), ('scaling', 1.0), ('kFx', 0.0), ('kFy', 0.0)]:
    m.param().set(name, str(val))
m.material('mat1').propertyGroup('def').set('rho', '3500.0')
m.material('mat1').propertyGroup('Enu').set('E', '1050e9')
m.material('mat1').propertyGroup('Enu').set('nu', '0.07')
m.material('mat1').propertyGroup('Enu').set('rho', '3500.0')
geom = comp.geom('geom1')
movs = [geom.feature('wp1').geom().feature('mov1'), geom.feature('wp2').geom().feature('mov1')]
solid = comp.physics('solid')
import json
plan = json.load(open('diamond_a_large__plan.json'))
shifts = {c['tag']: (c['shift_x'], c['shift_y']) for c in plan['combos']}

cases = [(300, 0.41, 0.22, (50e-9, -50e-9 / 3 ** 0.5)), (1000, 0.41, 0.22, shifts['a1000_da41_wa22']),
         (600, 0.41, 0.22, shifts['a600_da41_wa22'])]
for a_nm, da, wa, sh in cases:
    a = a_nm * 1e-9
    m.param().set('a', str(a)); m.param().set('d', str(da * a)); m.param().set('w', str(wa * a))
    m.param().set('f_mech', str(10e9 * 300e-9 / a))
    for mv in movs:
        mv.set('displx', str(sh[0])); mv.set('disply', str(sh[1]))
    geom.run()
    p(f'\n=== a={a_nm} d/a={da} w/a={wa}: domains={geom.getNDomains()} boundaries={geom.getNBoundaries()}')
    for mt in comp.mesh().tags():
        ms = comp.mesh(mt)
        t0 = time.time()
        try:
            ms.run()
            p(f'  mesh {mt} "{ms.label()}": {ms.getNumElem()} elements, {ms.getNumVertex()} vertices '
              f'(built in {time.time()-t0:.1f} s)')
        except Exception as e:
            p(f'  mesh {mt} failed: {str(e)[:300]}')
    solid.feature('as1').active(False); solid.feature('sym1').active(True)
    t0 = time.time()
    m.sol('sol1').runAll()
    p(f'  one k=0 sym solve (N_mode=12): {time.time()-t0:.1f} s')

client.clear()
p('\nDiag done.')
