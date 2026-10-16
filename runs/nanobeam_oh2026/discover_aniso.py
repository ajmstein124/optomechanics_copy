"""discover_aniso.py (remote, read-only): property names for an anisotropic Linear Elastic Material and a rotated coordinate system."""
import sys, mph
def p(*a): print(*a); sys.stdout.flush()
client = mph.start(); model = client.load('nanobeam_oh2026.mph'); m = model.java
comp = m.component('comp1'); lemm = comp.physics('solid').feature('lemm1')
p('lemm1 props:', [str(s) for s in lemm.properties()])
for k in ('SolidModel', 'D', 'D_mat', 'coordinateSystem', 'MixedFormulationIncompressible'):
    try: p(f'  {k} =', lemm.getString(k))
    except Exception as e: p(f'  {k}: n/a')
try:
    lemm.set('SolidModel', 'Anisotropic'); p('after Anisotropic:', [str(s) for s in lemm.properties() if 'D' in str(s) or 'C' in str(s)])
    for k in ('D', 'D_mat', 'DVo', 'DVo_mat'):
        try: p(f'  {k} =', [str(x) for x in lemm.getStringArray(k)])
        except Exception: pass
except Exception as e: p('Anisotropic set failed', str(e)[:200])
cs = comp.coordSystem().create('sys_rot', 'Rotated')
p('Rotated props:', [str(s) for s in cs.properties()])
client.clear()
