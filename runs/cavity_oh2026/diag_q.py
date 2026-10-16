"""diag_q.py (remote): why does the optical cavity mode come back with Im f = 0? Read-only checks."""
import sys
import mph
import numpy as np
def p(*a): print(*a); sys.stdout.flush()
client = mph.start(); model = client.load('cavity_oh2026_solved.mph'); m = model.java
comp = m.component('comp1')
p('coord systems:', [str(t) for t in comp.coordSystem().tags()])
pml = comp.coordSystem('pml1'); p('pml1 entities:', list(pml.selection().entities(3)))
p('sel_pml entities:', list(comp.selection('sel_pml').entities()))
for tag in ('dset2',):
    for expr in ('lambda', 'ewfd.freq', 'ewfd.Qfactor', 'ewfd.omega', 'ewfd.damp'):
        e = m.result().numerical().create('_e', 'EvalGlobal')
        try:
            e.set('data', tag); e.set('expr', expr); e.set('solnum', '8')
            try: e.set('complexout', 'on')
            except Exception: pass
            p(f'  {expr:14s} re={e.getReal()[0][0]!r} im={e.getImag()[0][0]!r}')
        except Exception as ex:
            p(f'  {expr:14s} ERROR {str(ex)[:120]}')
        finally:
            m.result().numerical().remove('_e')
eig = m.study('std2').feature('eig')
for prop in ('eigwhich', 'shift', 'neigs'):
    try: p(f'  std2 eig {prop} = {eig.getString(prop)}')
    except Exception as ex: p(f'  {prop}: {str(ex)[:80]}')
client.clear()
