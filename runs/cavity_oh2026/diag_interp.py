import sys, mph, jpype
import numpy as np
def p(*a): print(*a); sys.stdout.flush()
client = mph.start(); model = client.load('cavity_oh2026_solved.mph'); m = model.java
it = m.result().numerical().create('itp', 'Interp')
it.set('data', 'dset1'); it.set('expr', ['real(v)', 'solid.disp']); it.set('edim', '3'); it.set('solnum', '16')
for scale in (1.0, 1e-9):
    C = jpype.JArray(jpype.JDouble, 2)([[100.0*scale, 300.0*scale], [395.0*scale, 395.0*scale], [124.0*scale, 124.0*scale]])
    it.setInterpolationCoordinates(C)
    for meth in ('getReal', 'getData'):
        try:
            r = getattr(it, meth)()
            p(scale, meth, np.array(r, dtype=object).shape, [list(x) for x in r][:2])
        except Exception as e:
            p(scale, meth, 'ERR', str(e)[:150])
    try:
        it.run(); r = it.getReal(); p(scale, 'after run', [list(x) for x in r][:2])
    except Exception as e:
        p(scale, 'run ERR', str(e)[:150])
client.clear()
