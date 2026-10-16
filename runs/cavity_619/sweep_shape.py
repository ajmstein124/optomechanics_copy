"""
sweep_shape.py  (remote)  -- runs/cavity_619
Taper hole-shape sweep (user 2026-10-14): pull the breathing mode to <= 10 GHz with the center-hole
aspect (xi) and area (chi), keeping the optical resonance at 619 nm by re-adjusting the mirror period a.
Mirror cell fixed (w 550, t 120, hx/a 0.53, hy/w 0.77); M 10, 10 mirror cells, eta 1.
Fabrication: every point must have min bridge, rail and hole dimension >= MIN_FEATURE = 60 nm
(user setting 2026-10-14; may become 80 nm later); infeasible points are skipped and logged.

Shapes (xi, chi) at d = 0.13 and 0.16 = those feasible at 60 nm on the 619 nm line; strongest pull
(highest xi) first. Per shape: a on the (a, d)-sweep 619 nm line and 8 nm below; a third, extrapolated
a if 619 nm is not bracketed. Small air/PML box (600/500 nm, validated by pad_check.json).
Waits for sweep_ad.py to finish first (one COMSOL session at a time).

Output: runs/cavity_619/data/sh_d<dd>_xi<xi>_chi<chi>_a<a>.npz
Run via:  python scripts/remote_runner.py runs/cavity_619/sweep_shape.py
"""
import json
import sys
import time
from pathlib import Path

import mph
import numpy as np
from build_cavity_model import set_layout, op_class, mech_class
from cavity_taper import layout, min_features
import cavity_eval as E

OUT = Path('runs/cavity_619/data')
MIN_FEATURE = 60.0
W, T, HXA, HYW = 550, 120, 0.53, 0.77
A_LINE = {0.13: 200.7, 0.16: 205.7}           # 619 nm line from the (a, d) sweep (Oh shape)
SHAPES = {0.13: [(8, 5.0), (8, 5.5), (6, 4.0), (6, 4.5), (6, 5.0), (6, 5.5), (4, 4.0), (4, 5.0)],
          0.16: [(10, 5.5), (8, 5.0), (8, 5.5), (6, 4.0), (6, 4.5), (6, 5.0), (4, 4.0), (4, 5.0)]}
X_LOC, LAM0 = 1500.0, 619.4
AD_LOG = Path(r'C:\Users\abby\comsol\job_log_cavity_619__sweep_ad.txt')


def p(*a):
    print(*a); sys.stdout.flush()


# wait for the (a, d) sweep (single COMSOL session at a time)
t_w = time.time()
while AD_LOG.exists() and 'Sweep (a, d) done.' not in AD_LOG.read_text(errors='ignore'):
    if time.time() - t_w > 4 * 3600:
        p('waited 4 h for sweep_ad; starting anyway'); break
    time.sleep(60)
p(f'starting shape sweep ({time.time()-t_w:.0f} s wait)')

client = mph.start()
model = client.load('cavity_619.mph')
m = model.java
pc = json.load(open(OUT / 'pad_check.json'))
for k, v in (('pad_y', pc[pc['use']]['pad']), ('pad_z', pc[pc['use']]['pad']), ('d_pml', pc[pc['use']]['pml'])):
    m.param().set(k, f'{v}[nm]')
m.param().set('N_op', '20'); m.param().set('N_mode', '40'); m.param().set('f_mech', '10[GHz]')
op_class(model, x='PEC', y='PEC', z='PMC'); mech_class(model, '+', '+', '+')
E.setup(model)


def run_point(d, xi, chi, a):
    a = round(float(a), 1)
    tag = f'sh_d{int(round(d*100)):02d}_xi{xi}_chi{chi:.1f}_a{a:.1f}'
    fn = OUT / f'{tag}.npz'
    if fn.exists():
        z = np.load(fn); return float(z['lam']) if 'lam' in z else None
    cfg = dict(a_m=a, w=W, t=T, hx_m=round(HXA * a, 3), hy_m=round(HYW * W, 3), M=10, n_mirror=10,
               d=d, eta=1.0, xi=float(xi), chi=float(chi), pad_x=1000)
    mf = min_features(layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], 10, 10, d, 1.0, xi, chi), W)
    if min(mf.values()) < MIN_FEATURE:
        p(f'{tag}: SKIP below {MIN_FEATURE:.0f} nm min feature {mf}')
        np.savez(str(fn), skipped=True, **{k: v for k, v in mf.items()}); return None
    set_layout(model, cfg)
    t0 = time.time()
    fo, Qo, loco, io = E.solve_optics(m, X_LOC)
    fm, locm, B = E.solve_mech(m, X_LOC)
    g = np.full((len(fm), 3), np.nan)
    for k in range(1, len(fm) + 1):
        if locm[k - 1] > 0.8:
            try:
                g[k - 1] = E.g0_of(m, k, io, fo[io - 1], fm[k - 1])
            except Exception as e:
                p(f'    g0 mode {k} failed: {str(e)[:150]}')
    gt = np.abs(g[:, 0] + g[:, 1]); gt = np.where(np.isfinite(gt), gt, 0)
    ib = int(np.argmax(gt)) if gt.max() > 0 else -1
    lam = 299792.458 / (fo[io - 1] / 1e12)
    np.savez(str(fn), skipped=False, d=d, xi=xi, chi=chi, a=a, cfg=json.dumps(cfg), lam=lam,
             f_opt=fo, Q_opt=Qo, loc_opt=loco, i_opt=io, f_mech=fm, loc_mech=locm, B=B,
             gMB=g[:, 0], gPE=g[:, 1], meff=g[:, 2], i_breath=ib, **{k: v for k, v in mf.items()})
    br = f'{fm[ib]/1e9:.3f} GHz' if ib >= 0 else 'none'
    p(f'{tag}: optical {lam:.1f} nm Q={Qo[io-1]:.3g} | breathing {br} | min feat {min(mf.values()):.0f} nm | {time.time()-t0:.0f} s')
    return lam


t_all = time.time()
for d in (0.13, 0.16):
    for xi, chi in SHAPES[d]:
        a1, a2 = A_LINE[d], A_LINE[d] - 8
        l1, l2 = run_point(d, xi, chi, a1), run_point(d, xi, chi, a2)
        if l1 is not None and l2 is not None and not (min(l1, l2) < LAM0 < max(l1, l2)):
            slope = (l1 - l2) / (a1 - a2)
            a3 = float(np.clip(a1 + (LAM0 - l1) / slope, a2 - 15, a1 + 15))
            run_point(d, xi, chi, a3)
        p(f'  (shape d {d} xi {xi} chi {chi} done, {time.time()-t_all:.0f} s elapsed)')
client.clear()
p('Shape sweep done.')
