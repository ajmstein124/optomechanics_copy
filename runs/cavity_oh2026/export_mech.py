"""
export_mech.py  (remote)  -- runs/cavity_oh2026
Cut-plane export of real(u), real(v), real(w) of every localized mechanical mode (loc > 0.5) of
cavity_oh2026_solved.mph on a regular grid over the beam, on the top face (z = t/2 - 1 nm; what a
top-view plot shows) and the midplane (z = 1 nm), for 0 < x < 9 um. Points inside holes come back NaN.
(A full-mesh export ran out of Java heap: the mesh is mostly air.)
Output: runs/cavity_oh2026/data/mech_fields.npz
"""
import sys
import mph
import numpy as np
from comsol_utils import mphglobal

def p(*a): print(*a); sys.stdout.flush()
client = mph.start(); model = client.load('cavity_oh2026_solved.mph'); m = model.java
f = np.real(mphglobal(m, 'solid.freq', 'dset1'))
loc = np.real(mphglobal(m, 'int_beam(solid.disp^2*(x<4000[nm]))/int_beam(solid.disp^2)', 'dset1'))
ks = [i + 1 for i in range(len(f)) if loc[i] > 0.5]
W2, T = 400.0, 250.0
xs, ys = np.arange(0, 9001, 15.0), np.linspace(0, W2 - 0.5, 41)
GX, GY = np.meshgrid(xs, ys)
out = dict(k=np.array(ks), f=f[np.array(ks) - 1], loc=loc[np.array(ks) - 1], gx=xs, gy=ys)
for name, z in (('top', T / 2 - 1), ('mid', 1.0)):
    cp = m.result().dataset().create(f'cp_{name}', 'CutPlane'); cp.label(f'cut {name}')
    cp.set('data', 'dset1'); cp.set('quickplane', 'xy'); cp.set('quickz', f'{z}[nm]')
    ex = m.result().export().create(f'dex_{name}', 'Data')
    ex.set('data', f'cp_{name}'); ex.set('expr', ['real(u)', 'real(v)', 'real(w)'])
    ex.set('location', 'fromdataset')
    for k in ks:
        fn = f'C:/Users/abby/comsol/runs/cavity_oh2026/data/cut_{name}_{k}.txt'
        ex.set('solnum', [str(k)]); ex.set('filename', fn); ex.run()
        A = np.loadtxt(fn, comments='%')
        keep = np.isfinite(A[:, 3]) & (A[:, 1] <= W2 + 1) & (A[:, 0] <= 9500)
        for c_, key in enumerate(('x', 'y', None, 'u', 'v', 'w')):
            if key:
                out[f'{name}_{key}_{k}'] = A[keep, c_]
        p(f'{name} mode {k}: {f[k-1]/1e9:.4f} GHz, {int(keep.sum())} points, cols {A.shape[1]}')
np.savez('runs/cavity_oh2026/data/mech_fields.npz', **out)
client.clear()
