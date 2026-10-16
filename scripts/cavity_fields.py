"""
cavity_fields.py  (Windows; mph)
Export the optical cavity mode and the breathing mode of a SOLVED 1/8 cavity model for plotting
(runs/cavity_619/plot_fields.py). Same method as runs/cavity_619/export_fields.py: CutPlane + COMSOL
Data export (mph evaluate on the full mesh runs out of memory), 0 < x < XMAX.
  optical: real(Ey), normE on the z = 1 nm midplane, y < w/2 + 400 nm
  breathing (B > 0.5, loc > 0.5, most localized): real(u, v, w) on the top face z = t/2 - 1 nm
"""
import json
import sys
from pathlib import Path

import numpy as np


def p(*a):
    print(*a); sys.stdout.flush()


def breath_k(z):
    loc, B, f = z['loc_mech'], z['B'], z['f_mech']
    ok = (B > 0.5) & (loc > 0.5) & (f > 5e9)
    if 'S' in z:
        ok &= np.nan_to_num(z['S']) >= 0.7
    return int(np.where(ok)[0][np.argmax(loc[ok])]) + 1


def export(m, z, dev, out_dir, xmax=4000.0):
    """m: model.java with solutions; z: the point's npz; writes <out_dir>/fields_<dev>.npz."""
    out_dir = Path(out_dir)
    c = json.loads(str(z['cfg'])); W, T = float(c['w']), float(c['t'])
    io, ib = int(z['i_opt']), breath_k(z)
    out = dict(cfg=str(z['cfg']), i_opt=io, i_breath=ib, f_opt=float(z['f_opt'][io - 1]),
               Q_opt=float(z['Q_opt'][io - 1]), f_breath=float(z['f_mech'][ib - 1]),
               loc_breath=float(z['loc_mech'][ib - 1]), B_breath=float(z['B'][ib - 1]))
    for kind, dset, zc, expr, sn, ymax in (
            ('opt', 'dset2', 1.0, ['real(ewfd.Ey)', 'ewfd.normE'], io, W / 2 + 400),
            ('mech', 'dset1', T / 2 - 1, ['real(u)', 'real(v)', 'real(w)'], ib, W / 2 + 1)):
        tag = f'cpx_{kind}'
        for lst in (m.result().dataset(), m.result().export()):
            if tag in [str(t) for t in lst.tags()]:
                lst.remove(tag)
        cp = m.result().dataset().create(tag, 'CutPlane')
        cp.set('data', dset); cp.set('quickplane', 'xy'); cp.set('quickz', f'{zc}[nm]')
        ex = m.result().export().create(tag, 'Data')
        ex.set('data', tag); ex.set('expr', expr); ex.set('location', 'fromdataset')
        ex.set('solnum', [str(sn)])
        fn = str((out_dir / f'cut_{dev}_{kind}.txt').resolve()).replace('\\', '/')
        ex.set('filename', fn); ex.run()
        A = np.loadtxt(fn, comments='%')
        keep = np.isfinite(A[:, 3]) & (A[:, 0] <= xmax) & (A[:, 1] <= ymax)
        out[f'{kind}_xyz'] = A[keep, :3]; out[f'{kind}_val'] = A[keep, 3:]
        p(f'{dev} {kind}: mode {sn}, {int(keep.sum())} points')
    np.savez(str(out_dir / f'fields_{dev}.npz'), **out)
    p(f'{dev}: optical {299792.458 / (out["f_opt"] / 1e12):.2f} nm Q {out["Q_opt"]:.3g}; '
      f'breathing {out["f_breath"] / 1e9:.3f} GHz loc {out["loc_breath"]:.2f}')
