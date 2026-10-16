"""
export_fields.py  (remote)  -- runs/cavity_619
Field maps for the two w550 / 60 nm candidates (user 2026-10-15: mode profiles on the device):
  shape : best1_mf60.mph (shape-sweep pick d 0.10, xi 6, chi 4.0, a 193.4; solution stored)
  ad    : (a, d) design d 0.10, a 195.2 (619 nm line), Oh shape xi 6 / chi 3.5 -- solved here, saved as
          pick_mf60_ad_d10.mph
Exports (CutPlane + Data export, as runs/cavity_oh2026/export_mech.py), 0 < x < 4 um:
  optical cavity mode: real(Ey), normE on the z = 1 nm midplane (beam + air, y < w/2 + 400 nm)
  breathing mode (B > 0.5, loc > 0.5, highest loc): real(u, v, w) on the top face z = t/2 - 1 nm
Output: runs/cavity_619/data/fields_<dev>.npz
Run via:  python scripts/remote_runner.py runs/cavity_619/export_fields.py
"""
from pathlib import Path

import mph
import numpy as np
from cavity_pipeline import Pipeline, p

D = Path('runs/cavity_619/data')
W, T, XMAX = 550.0, 120.0, 4000.0


def breath_k(z):
    loc, B, f = z['loc_mech'], z['B'], z['f_mech']
    ok = (B > 0.5) & (loc > 0.5) & (f > 5e9)
    return int(np.where(ok)[0][np.argmax(loc[ok])]) + 1


def export(m, z, dev):
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
        fn = str((D / f'cut_{dev}_{kind}.txt').resolve()).replace('\\', '/')
        ex.set('filename', fn); ex.run()
        A = np.loadtxt(fn, comments='%')
        keep = np.isfinite(A[:, 3]) & (A[:, 0] <= XMAX) & (A[:, 1] <= ymax)
        out[f'{kind}_xyz'] = A[keep, :3]; out[f'{kind}_val'] = A[keep, 3:]
        p(f'{dev} {kind}: mode {sn}, {int(keep.sum())} points')
    np.savez(str(D / f'fields_{dev}.npz'), **out)
    p(f'{dev}: optical {299792.458 / (out["f_opt"] / 1e12):.2f} nm Q {out["Q_opt"]:.3g}; '
      f'breathing {out["f_breath"] / 1e9:.3f} GHz loc {out["loc_breath"]:.2f}')


# 1. shape-sweep pick (stored solution)
client = mph.start()
model = client.load('best1_mf60.mph')
export(model.java, np.load(D / 'best1_mf60.npz'), 'shape')
client.clear()

# 2. (a, d) design on the 619 nm line
a619 = 195.2                    # analyze_ad.py: 619 nm line at d 0.10 (sweep_ad.py wrote no line_619.json)
P = Pipeline('runs/cavity_619', dict(w=550, t=120, hx_a=0.53, hy_w=0.77), 60, 'mf60')
try:
    fn = D / 'pick_ad_d10.npz'
    if not fn.exists():
        P.solve(P.cfg(a619, 0.10, 6.0, 3.5), fn, dict(a=round(a619, 1), d=0.10, xi=6.0, chi=3.5))
        P.model.save('pick_mf60_ad_d10.mph')
    else:
        P.open(); P.model = P.client.load('pick_mf60_ad_d10.mph')
    export(P.model.java, np.load(fn), 'ad')
finally:
    P.close()
p('Field export done.')
