"""
Debug why mphglobal returns only 1 eigenvalue repeated N times.
Runs one k-point (M point) and tries multiple extraction approaches.
"""
import sys
import numpy as np
import mph

COMSOL_DIR = r'C:\Program Files\COMSOL\COMSOL64\Multiphysics_copy1'

print('Starting COMSOL...')
sys.stdout.flush()
client = mph.start()
model  = client.load('unit_cell_3.mph')
m      = model.java

# Si nominal params
a = 448e-9 * 1.067
m.param().set('a',      str(a))
m.param().set('d',      '182e-9')
m.param().set('w',      '99e-9')
m.param().set('t',      '220e-9')
m.param().set('N_mode', '10')
m.param().set('f_mech', '7e9')

# M point
kx = np.pi / a
ky = np.pi / a / np.sqrt(3)
m.param().set('kFx', str(kx))
m.param().set('kFy', str(ky))

# Symmetric modes only
solid = m.component('comp1').physics('solid')
solid.feature('as1').active(False)
solid.feature('sym1').active(True)

# --- Diagnostic 0: study tree ---
print('\n--- All studies ---')
for stag in [str(t) for t in m.study().tags()]:
    std = m.study(stag)
    print(f'Study {stag}:')
    for ftag in [str(t) for t in std.feature().tags()]:
        feat = std.feature(ftag)
        ftype = feat.getType()
        print(f'  {ftag}: {ftype}')
        for prop in ['neigs','neigsactive','shift','shiftactive','modeFreq']:
            try: print(f'    {prop}={feat.getString(prop)}')
            except: pass
sys.stdout.flush()

print('\nRunning sol1...')
sys.stdout.flush()
m.sol('sol1').runAll()
print('Done.')
sys.stdout.flush()

# --- Diagnostic 1: inspect sol1 features ---
print('\n--- sol1 features ---')
sol = m.sol('sol1')
for tag in [str(t) for t in sol.feature().tags()]:
    feat = sol.feature(tag)
    ftype = feat.getType()
    print(f'  {tag}: {ftype}')
    for prop in ['neigs','neigsactive','shift','shiftactive']:
        try: print(f'    {prop}={feat.getString(prop)}')
        except: pass
sys.stdout.flush()

# --- Diagnostic 2: EvalGlobal getReal() ---
print('\n--- EvalGlobal getReal() ---')
ev = m.result().numerical().create('ev_test1', 'EvalGlobal')
ev.set('data', 'dset1')
ev.set('expr', ['solid.freq'])
re = ev.getReal()
print(f'  len(re) = {len(re)}')
print(f'  values (GHz): {[float(re[i][0])*1e-9 for i in range(len(re))]}')
m.result().numerical().remove('ev_test1')
sys.stdout.flush()

sys.stdout.flush()

# --- Diagnostic 4: check N_mode value and force neigs ---
print('\n--- N_mode value check ---')
try:
    print(f'  N_mode (get): {m.param().get("N_mode")}')
    print(f'  f_mech (get): {m.param().get("f_mech")}')
except Exception as e:
    print(f'  error: {e}')
sys.stdout.flush()

print('\n--- Force neigs=10 explicitly, rerun ---')
m.sol('sol1').feature('e1').set('neigs', '10')
m.sol('sol1').runAll()
ev4 = m.result().numerical().create('ev_test4', 'EvalGlobal')
ev4.set('data', 'dset1')
ev4.set('expr', ['solid.freq'])
re4 = ev4.getReal()
print(f'  len(re4) = {len(re4)}')
print(f'  values (GHz): {[float(re4[i][0])*1e-9 for i in range(min(len(re4),20))]}')
m.result().numerical().remove('ev_test4')
sys.stdout.flush()

# --- Diagnostic 5: try Global instead of EvalGlobal ---
print('\n--- Global node (not EvalGlobal) ---')
ev5 = m.result().numerical().create('ev_test5', 'Global')
ev5.set('data', 'dset1')
ev5.set('expr', ['solid.freq'])
try:
    raw5 = ev5.getData()
    print(f'  getData len={len(raw5)}, values={[str(raw5[i][0]) for i in range(min(len(raw5),20))]}')
except Exception as e:
    print(f'  getData error: {e}')
re5 = ev5.getReal()
print(f'  getReal len={len(re5)}, values (GHz)={[float(re5[i][0])*1e-9 for i in range(min(len(re5),20))]}')
m.result().numerical().remove('ev_test5')
sys.stdout.flush()

client.clear()
print('\nDone.')
