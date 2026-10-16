"""
sweep_ad.py  (remote)  -- runs/cavity_619
2D sweep of mirror period a and taper depth d for the 619 nm cavity (user plan 2026-10-14: find the
(a, d) pairs that put the optical cavity resonance exactly at 619 nm with the breathing mode <= 10 GHz,
BEFORE optimizing the rest of the taper). Fixed: hx/a 0.53, hy/w 0.77, w 550, t 120, M 10,
10 mirror cells, eta 1, xi 6, chi 3.5 (Oh 2026 shape).

0. Padding check at the template (a 220, d 0.18): air/PML 1000/800 nm vs 600/500 nm. The smaller box
   is used for the sweep only if the cavity mode agrees (|df|/f < 2e-4, Q within 15%).
1. Grid a 190..235 step 5 x d 0.10..0.22 step 0.03, ordered from the expected crossing outward.
   Per point: optics (TE class, N_op modes around 484 THz) -> cavity mode = most localized;
   mechanics (breathing class, fixed end, N_mode around f_mech) -> for each localized mode:
   localization, sidewall coherence B = |int_side v| / int_side |v| (breathing ~ in-phase sidewalls),
   and g0 (data only; not shown in figures for now).
Output: runs/cavity_619/data/ad_a<a>_d<dd>.npz, pad_check.json. Resumable.

Run via:
    python scripts/remote_runner.py runs/cavity_619/sweep_ad.py
"""
import json
import sys
import time
from pathlib import Path

import mph
import numpy as np
from comsol_utils import mphglobal
from build_cavity_model import set_layout, op_class, mech_class

OUT = Path('runs/cavity_619/data'); OUT.mkdir(parents=True, exist_ok=True)
A_LIST = list(range(190, 236, 5))
D_LIST = [0.10, 0.13, 0.16, 0.19, 0.22]
A0, D0 = 210, 0.16                       # expected crossing region -> run first
W, T = 550, 120
BASE = dict(w=W, t=T, M=10, n_mirror=10, eta=1.0, xi=6.0, chi=3.5, pad_x=1000)
N_OP, N_MODE, F_MECH = 20, 40, '10[GHz]'
P11, P12, P44 = -0.25, 0.043, -0.172
HBAR = 1.054571817e-34
X_LOC = 1500.0                           # nm: localization window (cavity ~ +/- 7 cells of 220 nm)


def p(*a):
    print(*a); sys.stdout.flush()


client = mph.start()
model = client.load('cavity_619.mph')
m = model.java
comp = m.component('comp1')
m.param().set('N_op', str(N_OP)); m.param().set('N_mode', str(N_MODE)); m.param().set('f_mech', F_MECH)
op_class(model, x='PEC', y='PEC', z='PMC'); mech_class(model, '+', '+', '+')

# --- evaluation helpers (defined BEFORE solving, so no updateSolution needed)
def box(tag, dim, x, y, z, label):
    s = comp.selection().create(tag, 'Box'); s.label(label); s.set('entitydim', str(dim))
    for ax, (lo, hi) in zip('xyz', (x, y, z)):
        s.set(f'{ax}min', lo); s.set(f'{ax}max', hi)
    s.set('condition', 'inside')
box('sel_side', 2, ('(-tol)', 'X_in+tol'), ('w/2-tol', 'w/2+tol'), ('(-tol)', 't/2+tol'), 'beam sidewall y=w/2')
mb = comp.selection().create('sel_mb', 'Difference'); mb.set('entitydim', '2'); mb.set('add', ['sel_beam_bnd'])
mb.set('subtract', ['sel_x0_all', 'sel_y0_all', 'sel_z0_all', 'sel_end'])
for tag, sel, dim in (('int_beam', 'sel_beam', 3), ('int_inner', 'sel_inner', 3), ('int_mb', 'sel_mb', 2),
                      ('int_side', 'sel_side', 2)):
    o = comp.cpl().create(tag, 'Integration'); o.selection().geom('geom1', dim); o.selection().named(sel)
mx = comp.cpl().create('max_beam', 'Maximum'); mx.selection().named('sel_beam')
vd = comp.variable().create('var_ind_d'); vd.selection().geom('geom1', 3); vd.selection().named('sel_beam_all'); vd.set('ind_d', '1')
va = comp.variable().create('var_ind_a'); va.selection().geom('geom1', 3); va.selection().named('sel_air'); va.set('ind_d', '0')
vb = comp.variable().create('var_mb'); vb.selection().geom('geom1', 2); vb.selection().named('sel_mb')
for c in 'xyz':
    vb.set(f'nO{c}', f'up(ind_d)*un{c}+down(ind_d)*dn{c}')
    vb.set(f'Ed{c}', f'if(up(ind_d)>0.5, up(ewfd.E{c}), down(ewfd.E{c}))')
vb.set('En', 'Edx*nOx+Edy*nOy+Edz*nOz')
vb.set('Epar2', 'abs(Edx)^2+abs(Edy)^2+abs(Edz)^2-abs(En)^2')
vb.set('Dperp2', 'abs(epsilon0_const*n_d^2*En)^2')


def ev(expr, dset, solnum):
    e = m.result().numerical().create('_ev', 'EvalGlobal')
    try:
        e.set('data', dset); e.set('expr', expr); e.set('solnum', str(solnum))
        return float(e.getReal()[0][0])
    finally:
        m.result().numerical().remove('_ev')


def solve_optics():
    m.sol('sol2').runAll()
    f = np.real(mphglobal(m, 'ewfd.freq', 'dset2'))
    Q = np.real(mphglobal(m, 'ewfd.Qfactor', 'dset2'))
    loc = np.real(mphglobal(m, f'int_inner(ewfd.normE^2*(x<{X_LOC}[nm]))/int_inner(ewfd.normE^2)', 'dset2'))
    return f, Q, loc


def g0_of(k, io, f_o, f_m):
    W_ = lambda e: f"withsol('sol1',{e},setind(lambda,{k}))"
    den = ev('int_inner(epsilon0_const*(1+(n_d^2-1)*ind_d)*ewfd.normE^2)', 'dset2', io)
    Qn = f"({W_('real(u)')}*nOx+{W_('real(v)')}*nOy+{W_('real(w)')}*nOz)"
    mbi = ev(f'int_mb({Qn}*((epsilon0_const*(n_d^2-1))*Epar2-(1/(epsilon0_const*n_d^2)-1/epsilon0_const)*Dperp2))', 'dset2', io)
    S = {c: W_(f'real(solid.e{c})') for c in ('XX', 'YY', 'ZZ', 'XY', 'XZ', 'YZ')}
    pe = (f"2*real(conj(ewfd.Ex)*ewfd.Ey)*{P44}*2*{S['XY']}+2*real(conj(ewfd.Ex)*ewfd.Ez)*{P44}*2*{S['XZ']}"
          f"+2*real(conj(ewfd.Ey)*ewfd.Ez)*{P44}*2*{S['YZ']}"
          f"+abs(ewfd.Ex)^2*({P11}*{S['XX']}+{P12}*({S['YY']}+{S['ZZ']}))"
          f"+abs(ewfd.Ey)^2*({P11}*{S['YY']}+{P12}*({S['XX']}+{S['ZZ']}))"
          f"+abs(ewfd.Ez)^2*({P11}*{S['ZZ']}+{P12}*({S['XX']}+{S['YY']}))")
    pei = ev(f'epsilon0_const*n_d^4*int_beam({pe})', 'dset2', io)
    umax = ev('max_beam(solid.disp)', 'dset1', k)
    meff = ev('8*int_beam(rho_d*solid.disp^2)/max_beam(solid.disp^2)', 'dset1', k)
    xzpf = np.sqrt(HBAR / (2 * meff * 2 * np.pi * f_m))
    return -(f_o / 2) * mbi / den / umax * xzpf, (f_o / 2) * pei / den / umax * xzpf, meff


def run_point(a, d):
    cfg = dict(BASE, a_m=a, hx_m=round(0.53 * a, 3), hy_m=round(0.77 * W, 3), d=d)
    lay = set_layout(model, cfg)
    n_el = comp.mesh('mesh1').getNumElem()
    t0 = time.time()
    fo, Qo, loco = solve_optics()
    io = int(np.argmax(loco)) + 1
    t_op = time.time() - t0
    m.sol('sol1').runAll()
    fm = np.real(mphglobal(m, 'solid.freq', 'dset1'))
    locm = np.real(mphglobal(m, f'int_beam(solid.disp^2*(x<{X_LOC}[nm]))/int_beam(solid.disp^2)', 'dset1'))
    B = np.real(mphglobal(m, f'abs(int_side(real(v)*(x<{X_LOC}[nm])))/int_side(abs(real(v))*(x<{X_LOC}[nm]))', 'dset1'))
    gMB = np.full(len(fm), np.nan); gPE = np.full(len(fm), np.nan); meff = np.full(len(fm), np.nan)
    for k in range(1, len(fm) + 1):
        if locm[k - 1] > 0.8 and B[k - 1] > 0.3:
            try:
                gMB[k - 1], gPE[k - 1], meff[k - 1] = g0_of(k, io, fo[io - 1], fm[k - 1])
            except Exception as e:
                p(f'    g0 mode {k} failed: {str(e)[:150]}')
    cand = [i for i in range(len(fm)) if locm[i] > 0.8 and B[i] > 0.3]
    ib = min(cand, key=lambda i: fm[i]) if cand else None       # first (lowest) breathing mode
    np.savez(str(OUT / f'ad_a{a}_d{int(round(d*100)):02d}.npz'), a=a, d=d, cfg=json.dumps(cfg),
             f_opt=fo, Q_opt=Qo, loc_opt=loco, i_opt=io, f_mech=fm, loc_mech=locm, B=B, gMB=gMB, gPE=gPE,
             meff=meff, i_breath=-1 if ib is None else ib, n_elem=n_el,
             hx=lay['hx'], hy=lay['hy'], ax=lay['a'], bridge_min=float(np.min(lay['a'] - lay['hx'])))
    lam = 299792.458 / (fo[io - 1] / 1e12)
    br = f'{fm[ib]/1e9:.3f} GHz (B {B[ib]:.2f})' if ib is not None else 'none found'
    p(f'a={a} d={d:.2f}: optical {lam:.1f} nm Q={Qo[io-1]:.3g} loc={loco[io-1]:.2f} | breathing {br} | '
      f'{n_el} el, optics {t_op:.0f} s, total {time.time()-t0:.0f} s')
    return fo[io - 1], Qo[io - 1]


# ---- 0. padding check
pc_fn = OUT / 'pad_check.json'
if pc_fn.exists():
    pc = json.load(open(pc_fn))
else:
    res = {}
    for name, (pad, pml) in (('big', (1000, 800)), ('small', (600, 500))):
        for k, v in (('pad_y', pad), ('pad_z', pad), ('d_pml', pml)):
            m.param().set(k, f'{v}[nm]')
        cfg = dict(BASE, a_m=220, hx_m=round(0.53 * 220, 3), hy_m=round(0.77 * W, 3), d=0.18)
        set_layout(model, cfg)
        t0 = time.time()
        fo, Qo, loco = solve_optics(); io = int(np.argmax(loco)) + 1
        res[name] = dict(pad=pad, pml=pml, f=float(fo[io - 1]), Q=float(Qo[io - 1]), loc=float(loco[io - 1]),
                         n_elem=int(comp.mesh('mesh1').getNumElem()), t_s=time.time() - t0)
        p(f'pad check {name}: {res[name]}')
    df = abs(res['small']['f'] - res['big']['f']) / res['big']['f']
    dq = abs(res['small']['Q'] - res['big']['Q']) / res['big']['Q']
    use = 'small' if (df < 2e-4 and dq < 0.15) else 'big'
    pc = dict(res, df=df, dQ=dq, use=use)
    json.dump(pc, open(pc_fn, 'w'), indent=1)
    p(f'pad check: df/f = {df:.1e}, dQ/Q = {dq:.2f} -> using {use} box')
pad, pml = pc[pc['use']]['pad'], pc[pc['use']]['pml']
for k, v in (('pad_y', pad), ('pad_z', pad), ('d_pml', pml)):
    m.param().set(k, f'{v}[nm]')

# ---- 1. grid, expected crossing first
pts = sorted(((a, d) for a in A_LIST for d in D_LIST),
             key=lambda q: ((q[0] - A0) / 15) ** 2 + ((q[1] - D0) / 0.04) ** 2)
t_all = time.time()
for i, (a, d) in enumerate(pts, 1):
    if (OUT / f'ad_a{a}_d{int(round(d*100)):02d}.npz').exists():
        continue
    try:
        p(f'[{i}/{len(pts)}] ', end='') if False else None
        run_point(a, d)
    except Exception as e:
        p(f'a={a} d={d:.2f}: FAILED {str(e)[:250]}')
    p(f'  ({i}/{len(pts)} done, {time.time()-t_all:.0f} s elapsed)')
model.save('cavity_619_sweep_last.mph')
client.clear()
p('Sweep (a, d) done.')
