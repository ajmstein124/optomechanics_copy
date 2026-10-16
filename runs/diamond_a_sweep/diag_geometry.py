"""
diag_geometry.py
================
Read-only diagnostic for the diamond_a_sweep failures (all d/a=0.48 combos and
a=150, d/a=0.41). Does NOT save the model.

1. Dumps every geometry feature (top level + work plane) with all its properties,
   so the snowflake construction (Rectangle 1 size/pos/base, rotations, fillet)
   can be read directly from unit_cell_3.mph.
2. Dumps the Floquet / symmetry BC selections in solid mechanics (explicit
   boundary numbers vs named selections).
3. For a set of passing and failing (a, d/a, w/a) cases: rebuild geometry, report
   domain/boundary counts and the BC entity lists, then try one k=0 solve and print
   the FULL exception text on failure.

Run via:
    python scripts/remote_runner.py --block runs/diamond_a_sweep/diag_geometry.py
"""

import sys
import traceback
from comsol_utils import start_client


def p(*a):
    print(*a)
    sys.stdout.flush()


def dump_feature(f, indent='  '):
    try:
        label = str(f.label())
    except Exception:
        label = '?'
    try:
        ftype = str(f.getType())
    except Exception:
        ftype = '?'
    p(f'{indent}[{f.tag()}] "{label}" type={ftype}')
    try:
        names = [str(n) for n in f.properties()]
    except Exception:
        names = []
    for n in names:
        val = None
        for getter in ('getString', 'getStringArray', 'getStringMatrix'):
            try:
                v = getattr(f, getter)(n)
                if getter == 'getString':
                    val = str(v)
                elif getter == 'getStringArray':
                    val = '[' + ', '.join(str(x) for x in v) + ']'
                else:
                    val = '[' + '; '.join(', '.join(str(x) for x in row) for row in v) + ']'
                break
            except Exception:
                continue
        if val not in (None, '', '[]'):
            p(f'{indent}    {n} = {val}')


client, model = start_client('unit_cell_3.mph')
m    = model.java
comp = m.component('comp1')
geom = comp.geom('geom1')

p('\n=== PARAMETERS ===')
for n in m.param().varnames():
    p(f'  {n} = {m.param().get(n)}')

p('\n=== GEOMETRY FEATURES (geom1) ===')
for tag in geom.feature().tags():
    f = geom.feature(tag)
    dump_feature(f)
    try:
        wp_geom = f.geom()
        p(f'    --- work plane sub-features of {tag} ---')
        for t2 in wp_geom.feature().tags():
            dump_feature(wp_geom.feature(t2), indent='      ')
    except Exception:
        pass

solid = comp.physics('solid')


def dump_bc():
    for tag in solid.feature().tags():
        f = solid.feature(tag)
        try:
            ents = list(f.selection().entities())
        except Exception:
            ents = '?'
        try:
            named = str(f.selection().named())
        except Exception:
            named = ''
        p(f'  {str(tag):8s} "{f.label()}" active={f.isActive()} entities={ents} named="{named}"')
        try:
            for t2 in f.feature().tags():
                g = f.feature(t2)
                try:
                    e2 = list(g.selection().entities())
                except Exception:
                    e2 = '?'
                p(f'      sub {str(t2):8s} "{g.label()}" entities={e2}')
        except Exception:
            pass


p('\n=== SOLID BCs (as loaded) ===')
geom.run()
p(f'  domains={geom.getNDomains()} boundaries={geom.getNBoundaries()}')
dump_bc()

# Diamond material, as in sweep.py
m.material('mat1').propertyGroup('def').set('rho', '3500.0')
m.material('mat1').propertyGroup('Enu').set('E', '1050e9')
m.material('mat1').propertyGroup('Enu').set('nu', '0.07')
m.material('mat1').propertyGroup('Enu').set('rho', '3500.0')
for name, val in [('t', 140e-9), ('f_r', 16e-9), ('N_mode', 10), ('scaling', 1.0),
                  ('kFx', 0.0), ('kFy', 0.0)]:
    m.param().set(name, str(val))

cases = [
    (175, 0.41, 0.28, 'PASSED in sweep'),
    (150, 0.41, 0.28, 'FAILED in sweep'),
    (150, 0.35, 0.28, 'PASSED in sweep'),
    (300, 0.48, 0.36, 'd/a=0.48 (FAILED at all a)'),
    (300, 0.43, 0.36, 'probe: just below sqrt(3)/4=0.433'),
    (300, 0.44, 0.36, 'probe: just above sqrt(3)/4'),
]

for a_nm, da, wa, note in cases:
    a = a_nm * 1e-9
    p(f'\n=== CASE a={a_nm} d/a={da} w/a={wa}  ({note}) ===')
    m.param().set('a', str(a))
    m.param().set('d', str(da * a))
    m.param().set('w', str(wa * a))
    m.param().set('f_mech', str(10e9 * 300e-9 / a))
    try:
        geom.run()
        p(f'  geometry OK: domains={geom.getNDomains()} boundaries={geom.getNBoundaries()}')
    except Exception as e:
        p(f'  GEOMETRY FAILED: {e}')
        continue
    dump_bc()
    try:
        solid.feature('as1').active(False)
        solid.feature('sym1').active(True)
        m.sol('sol1').runAll()
        p('  k=0 sym solve OK')
    except Exception as e:
        p('  k=0 sym solve FAILED. Full message:')
        p(str(e))
        p(traceback.format_exc()[-3000:])

client.clear()
p('\nDiag done.')
