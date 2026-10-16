"""
discover_api.py  (read-only; does not save)
Print the exact COMSOL feature TYPES and PROPERTY NAMES/VALUES used in unit_cell_3.mph for
every feature the nanobeam builder will recreate: Solid Mechanics features (Linear Elastic,
Free, Periodic Condition, Symmetry, Antisymmetry, Initial Values), material property groups,
Mech Mesh features, the Mech Study eigenfrequency step and solver, and component selections.

Run via:
    python scripts/remote_runner.py --block runs/nanobeam_1d/discover_api.py
"""
import sys
from comsol_utils import start_client


def p(*a):
    print(*a)
    sys.stdout.flush()


def dump(f, ind='  ', with_props=True):
    try:
        typ = str(f.getType())
    except Exception:
        typ = '?'
    try:
        lbl = str(f.label())
    except Exception:
        lbl = '?'
    p(f'{ind}[{f.tag()}] type="{typ}" label="{lbl}"')
    if with_props:
        try:
            names = [str(n) for n in f.properties()]
        except Exception:
            names = []
        for n in names:
            for g in ('getString', 'getStringArray', 'getStringMatrix'):
                try:
                    v = getattr(f, g)(n)
                    if g == 'getString':
                        v = str(v)
                    elif g == 'getStringArray':
                        v = '[' + ', '.join(str(x) for x in v) + ']'
                    else:
                        v = '[' + '; '.join(', '.join(str(x) for x in r) for r in v) + ']'
                    p(f'{ind}    {n} = {v}')
                    break
                except Exception:
                    continue
    try:
        for t in f.feature().tags():
            dump(f.feature(t), ind + '    ', with_props)
    except Exception:
        pass


client, model = start_client('unit_cell_3.mph')
m = model.java
comp = m.component('comp1')

p('\n=== SOLID MECHANICS (solid) ===')
solid = comp.physics('solid')
p(f'  physics type = {solid.getType()}')
for t in solid.feature().tags():
    dump(solid.feature(t))

p('\n=== MATERIALS ===')
for t in comp.material().tags():
    mat = comp.material(t)
    p(f'  [{t}] label={mat.label()}')
    for g in mat.propertyGroup().tags():
        pg = mat.propertyGroup(g)
        p(f'    group [{g}] label="{pg.label()}"')
        try:
            for n in pg.properties():
                try:
                    p(f'        {n} = {pg.getString(str(n))}')
                except Exception:
                    p(f'        {n} = [' + ', '.join(str(x) for x in pg.getStringArray(str(n))) + ']')
        except Exception as e:
            p(f'        (props unreadable: {e})')

p('\n=== MECH MESH (mesh1) ===')
for t in comp.mesh('mesh1').feature().tags():
    dump(comp.mesh('mesh1').feature(t))

p('\n=== MECH STUDY (std1) ===')
for t in m.study('std1').feature().tags():
    dump(m.study('std1').feature(t))

p('\n=== SOLVER sol1 ===')
for t in m.sol('sol1').feature().tags():
    dump(m.sol('sol1').feature(t), with_props=True)

p('\n=== COMPONENT SELECTIONS ===')
try:
    for t in comp.selection().tags():
        dump(comp.selection(t))
except Exception as e:
    p(f'  none / unreadable: {e}')

client.clear()
p('\nDiscover done.')
