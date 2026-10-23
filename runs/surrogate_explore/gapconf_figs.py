"""
gapconf_figs.py  (remote)  -- runs/surrogate_explore
Review data for the gap-confined designs (user 2026-10-20): per design
  1. re-solve the final cavity (exact cfg from gapconf/<tag>/data/final.npz) and export on cut planes:
       optical real(Ey), |E| on the z = 1 nm midplane
       breathing mode (lowest clean mode) real(u, v, w) on the top face z = t/2 - 1 nm
       breathing-mode strain real(eXX, eYY, eZZ, eXY) on the midplane and the top face
  2. mirror-cell bands Gamma -> X (final a_m, hx_m, hy_m): optics y0 PEC (cavity family) + y0 PMC, mechanics 4 classes
     center-cell bands (hole 0 of the taper): optics y0 PEC, mechanics Y+Z+
Output: gapconf/<tag>/data/{fields.npz, bands.npz}. Plot on the Mac: runs/surrogate_explore/plot_gapconf.py
"""
import json
import time
from pathlib import Path

import numpy as np
from build_nanobeam_model import build as build_cell, class_on, op_class
from cavity_pipeline import Pipeline, p
from cavity_taper import layout
from comsol_utils import mphglobal

ROOT = Path('runs/surrogate_explore/gapconf')
TAGS = ['w650_m186_c455_d086', 'w650_m186_c455_d118', 'w650_m192_hy66_c455_d146', 'w700_m186_c490_d118',
        'w700_m198_c420_d172', 'w700_m192_c420_d146', 'w700_m186_c420_d118']
N_K = 13
CLASSES = [('+', '+'), ('-', '+'), ('+', '-'), ('-', '-')]
XMAX = 4500.0


def lowest_clean(z):
    ok = (z['loc_mech'] >= 0.8) & (z['B'] > 0.5) & (np.nan_to_num(z['S']) >= 0.7)
    i = np.where(ok)[0]
    return int(i[np.argmin(z['f_mech'][i])]) + 1


def cut(m, dset, zc, expr, sn, fn, xmax, ymax):
    tag = 'cpx_fig'
    for lst in (m.result().dataset(), m.result().export()):
        if tag in [str(t) for t in lst.tags()]:
            lst.remove(tag)
    cp = m.result().dataset().create(tag, 'CutPlane')
    cp.set('data', dset); cp.set('quickplane', 'xy'); cp.set('quickz', f'{zc}[nm]')
    ex = m.result().export().create(tag, 'Data')
    ex.set('data', tag); ex.set('expr', expr); ex.set('location', 'fromdataset'); ex.set('solnum', [str(sn)])
    f = str(Path(fn).resolve()).replace('\\', '/')
    ex.set('filename', f); ex.run()
    A = np.loadtxt(f, comments='%')
    keep = np.isfinite(A[:, 3]) & (A[:, 0] <= xmax) & (A[:, 1] <= ymax)
    return A[keep, :3], A[keep, 3:]


# ------------------------------------------------------------------ 1. fields
todo = [t for t in TAGS if not (ROOT / t / 'data' / 'fields.npz').exists()]
if todo:
    z0 = np.load(ROOT / todo[0] / 'data' / 'final.npz')
    c0 = json.loads(str(z0['cfg']))
    P = Pipeline(str(ROOT / todo[0]), dict(w=c0['w'], t=120, hx_a=c0['hx_m'] / c0['a_m'], hy_w=c0['hy_m'] / c0['w']), 59.5, 'gapconf')
    try:
        for tag in todo:
            dd = ROOT / tag / 'data'
            c = json.loads(str(np.load(dd / 'final.npz')['cfg']))
            fn = dd / 'figsolve.npz'
            t0 = time.time()
            if fn.exists():
                fn.unlink()                                   # the model must hold this design's solution
            P.solve(c, fn, dict(tag=tag))
            z = np.load(fn)
            m = P.model.java
            W, T = float(c['w']), float(c['t'])
            io, ib = int(z['i_opt']), lowest_clean(z)
            out = dict(cfg=str(z['cfg']), i_opt=io, i_breath=ib, f_opt=float(z['f_opt'][io - 1]), Q_opt=float(z['Q_opt'][io - 1]),
                       f_breath=float(z['f_mech'][ib - 1]), loc_breath=float(z['loc_mech'][ib - 1]), S_breath=float(z['S'][ib - 1]),
                       meff=float(z['meff'][ib - 1]))
            out['opt_xyz'], out['opt_val'] = cut(m, 'dset2', 1.0, ['real(ewfd.Ey)', 'ewfd.normE'], io, dd / 'cut_opt.txt', XMAX, W / 2 + 400)
            out['mech_xyz'], out['mech_val'] = cut(m, 'dset1', T / 2 - 1, ['real(u)', 'real(v)', 'real(w)'], ib, dd / 'cut_mech.txt', XMAX, W / 2 + 1)
            se = ['real(solid.eXX)', 'real(solid.eYY)', 'real(solid.eZZ)', 'real(solid.eXY)', 'real(u)', 'real(v)', 'real(w)']
            out['strain_mid_xyz'], out['strain_mid_val'] = cut(m, 'dset1', 1.0, se, ib, dd / 'cut_strain_mid.txt', XMAX, W / 2 + 1)
            out['strain_top_xyz'], out['strain_top_val'] = cut(m, 'dset1', T / 2 - 1, se, ib, dd / 'cut_strain_top.txt', XMAX, W / 2 + 1)
            try:
                out['umax'] = float(np.real(mphglobal(m, 'max_beam(sqrt(abs(u)^2+abs(v)^2+abs(w)^2))', 'dset1'))[ib - 1])
            except Exception as e:
                p(f'  umax operator failed ({str(e)[:80]}); using the cut-plane maximum')
                out['umax'] = float(np.sqrt((out['strain_mid_val'][:, 4:] ** 2).sum(1)).max())
            np.savez(str(dd / 'fields.npz'), **out)
            p(f'[figs] {tag}: fields, optical {299792.458 / (out["f_opt"] / 1e12):.2f} nm, breathing {out["f_breath"]/1e9:.3f} GHz ({time.time()-t0:.0f} s)')
    finally:
        P.close()


# ------------------------------------------------------------------ 2. bands
def params(w, t, a, hx, hy):
    return {'a': f'{a}[nm]', 'w': f'{w}[nm]', 't': f'{t}[nm]', 'hx': f'{hx}[nm]', 'hy': f'{hy}[nm]',
            'pad_y': '1.5[um]', 'pad_z': '1.5[um]', 'E_d': '1050[GPa]', 'nu_d': '0.07', 'rho_d': '3500[kg/m^3]',
            'n_d': '2.41', 'kx': '0[1/m]', 'f_mech': '8[GHz]', 'N_mode': '15', 'f_op': '300[THz]', 'N_op': '30'}


def bands(m, model, sol_op, a, opt_classes, mech_classes):
    ks = np.linspace(0, np.pi / (a * 1e-9), N_K)
    fo = np.full((N_K, len(opt_classes), 30), np.nan); fm = np.full((N_K, len(mech_classes), 15), np.nan)
    for ik, k in enumerate(ks):
        m.param().set('kx', f'{k}[1/m]')
        for iy, yc in enumerate(opt_classes):
            op_class(model, y=yc, z='PMC'); m.sol(sol_op).runAll()
            f = np.sort(np.real(mphglobal(m, 'ewfd.freq', 'dset2'))); f = f[f > 1e12][:30]; fo[ik, iy, :len(f)] = f
        for ic, (yc, zc) in enumerate(mech_classes):
            class_on(model, yc, zc); m.sol('sol1').runAll()
            g = np.sort(np.real(mphglobal(m, 'solid.freq', 'dset1')))[:15]; fm[ik, ic, :len(g)] = g
    return ks, fo, fm


client = model = None
for tag in TAGS:
    dd = ROOT / tag / 'data'
    if (dd / 'bands.npz').exists():
        continue
    t0 = time.time()
    c = json.loads(str(np.load(dd / 'final.npz')['cfg']))
    lay = layout(c['a_m'], c['hx_m'], c['hy_m'], c['M'], c['n_mirror'], c['d'], c['eta'], c['xi'], c['chi'])
    cells = dict(mirror=(c['a_m'], c['hx_m'], c['hy_m']), center=(float(lay['a'][0]), float(lay['hx'][0]), float(lay['hy'][0])))
    if model is None:
        client, model = build_cell(params(c['w'], c['t'], *cells['mirror']), hole=True, name='gapconf_cell')
    m = model.java
    sol_op = [str(t) for t in m.sol().tags()][-1]
    out = dict(cfg=json.dumps(c))
    for name, (a, hx, hy) in cells.items():
        for k_, v in (('a', a), ('hx', hx), ('hy', hy), ('w', c['w'])):
            m.param().set(k_, f'{v}[nm]')
        oc, mc = (('PEC', 'PMC'), CLASSES) if name == 'mirror' else (('PEC',), CLASSES[:1])
        ks, fo, fm = bands(m, model, sol_op, a, oc, mc)
        out.update({f'{name}_k_frac': ks / ks[-1], f'{name}_f_opt': fo, f'{name}_f_mech': fm, f'{name}_cell': np.array([a, hx, hy])})
    np.savez(str(dd / 'bands.npz'), **out)
    p(f'[figs] {tag}: bands ({time.time()-t0:.0f} s)')
if client is not None:
    client.clear()
p('gapconf figs done.')
