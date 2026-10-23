"""
build_shield_cavity.py  (Windows; mph)  -- runs/shield_619
Mechanical Q of a 1D nanobeam OMC anchored into a 2D diamond slab, with or without a square-lattice CROSS phonon shield
around the anchor (Chan 2012 APL / Oh 2026 style). Mechanics only (the optical mode is far from the anchor).

ONE-EIGHTH model (Symmetry on x = 0, y = 0, z = 0 -> breathing class +++):
  beam    0 < x < X_in, 0 < y < w/2, 0 < z < t/2, minus the cavity's elliptical holes (cavity_taper.layout, as build_cavity_model)
  slab    X_in < x < X_in + Lc + m_out + d_pml, 0 < y < Yc + m_out + d_pml, same thickness. The slab edge x = X_in, y > w/2 is free
          (the beam is suspended over a trench and meets the slab only at its end face).
  shield  cross holes (bar length h, width w_c, fillet) centred at (X_in + x_off + (i+1/2) a_s, (k+1/2) a_s), i, k < n_pad + Ns, except the
          solid anchor pad i < n_pad, k < n_pad_y (the beam lands on it). So the pad is surrounded by >= Ns shield periods.
          Lc = Yc = (n_pad + Ns) a_s in both cases (no shield = the same slab, unpatterned).
  PML     slab layers of thickness d_pml on +x and +y (outgoing slab waves absorbed); far faces free.
Q_m = |Im lambda| / (2 |Re lambda|). Breathing mode = localized (x < 1500 nm) mode near f_target.
"""
import math
import sys
import time

import mph
import numpy as np
from cavity_taper import layout, beam_half_length
from comsol_utils import mphglobal


def p(*a):
    print(*a); sys.stdout.flush()


def _box(comp, tag, dim, x, y, z, label, condition='inside'):
    s = comp.selection().create(tag, 'Box'); s.label(label); s.set('entitydim', str(dim))
    for ax, (lo, hi) in zip('xyz', (x, y, z)):
        s.set(f'{ax}min', lo); s.set(f'{ax}max', hi)
    s.set('condition', condition)
    return s


def build(client, cfg, sh, name='shield_cavity'):
    """cfg: cavity cfg (final.npz). sh: dict(a, h, w, fillet, Ns, n_pad, n_pad_y, m_out, d_pml, use) in nm; use False = no holes."""
    lay = layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'], cfg['eta'], cfg['xi'], cfg['chi'])
    X_in = beam_half_length(lay, cfg['pad_x']); nh = len(lay['x'])
    a_s, n_pad, n_pad_y, Ns = sh['a'], sh['n_pad'], sh['n_pad_y'], sh['Ns']
    x_off = sh.get('x_off', 0)                     # lattice shift away from the trench edge (edge strip = x_off + (a_s - h)/2)
    Lc = x_off + (n_pad + Ns) * a_s; Yc = (max(n_pad, n_pad_y) + Ns) * a_s
    model = client.create(name); m = model.java; P = m.param()
    P.set('wbeam', f"{cfg['w']}[nm]"); P.set('t', f"{cfg['t']}[nm]")   # not 'w': that is the z displacement
    P.set('X_in', f'{X_in:.3f}[nm]'); P.set('Lc', f'{Lc}[nm]'); P.set('Yc', f'{Yc}[nm]')
    P.set('m_out', f"{sh['m_out']}[nm]"); P.set('d_pml', f"{sh['d_pml']}[nm]")
    P.set('E_d', '1050[GPa]'); P.set('nu_d', '0.07'); P.set('rho_d', '3500[kg/m^3]')
    P.set('f_mech', f"{cfg.get('f_target', 9.8e9)}[Hz]"); P.set('N_mode', str(cfg.get('N_mode', 40)))
    P.set('h_beam', 't/5'); P.set('h_slab', sh.get('h_slab', '30[nm]')); P.set('h_pml', '60[nm]'); P.set('tol', '1[nm]')
    m.component().create('comp1', True); comp = m.component('comp1')
    geom = comp.geom().create('geom1', 3); geom.lengthUnit('nm')
    b = geom.create('blk_beam', 'Block'); b.set('size', ['X_in', 'wbeam/2', 't/2']); b.set('pos', ['0', '0', '0'])
    s = geom.create('blk_slab', 'Block'); s.set('size', ['Lc+m_out+d_pml', 'Yc+m_out+d_pml', 't/2']); s.set('pos', ['X_in', '0', '0'])
    s.set('layername', ['PML']); s.setIndex('layer', 'd_pml', 0)
    for side, on in (('layerleft', False), ('layerright', True), ('layerfront', False), ('layerback', True),
                     ('layerbottom', False), ('layertop', False)):
        s.set(side, on)
    wp = geom.create('wp1', 'WorkPlane'); wp.set('quickplane', 'xy'); wg = wp.geom()
    for j in range(nh):
        el = wg.create(f'e{j}', 'Ellipse'); el.set('semiaxes', [f"{lay['hx'][j]/2:.4f}", f"{lay['hy'][j]/2:.4f}"])
        el.set('pos', [f"{lay['x'][j]:.4f}", '0'])
    ncross = 0
    if sh.get('use', True):
        rects = []
        for i in range(n_pad + Ns):
            for k in range(max(n_pad, n_pad_y) + Ns):
                if i < n_pad and k < n_pad_y:
                    continue
                cx, cy = X_in + x_off + (i + 0.5) * a_s, (k + 0.5) * a_s
                for q, (lx, ly) in enumerate(((sh['h'], sh['w']), (sh['w'], sh['h']))):
                    r = wg.create(f'r{i}_{k}_{q}', 'Rectangle'); r.set('size', [f'{lx}', f'{ly}']); r.set('base', 'center')
                    r.set('pos', [f'{cx:.4f}', f'{cy:.4f}']); rects.append(f'r{i}_{k}_{q}')
                ncross += 1
        u = wg.create('uni_c', 'Union'); u.selection('input').set(rects); u.set('intbnd', False)
        if sh.get('fillet', 0) > 0:
            wg.run('uni_c'); nv = int(wg.obj('uni_c').getNVertices())
            f = wg.create('fil_c', 'Fillet'); f.selection('point').set('uni_c', list(range(1, nv + 1))); f.set('radius', f"{sh['fillet']}")
    ext = geom.create('ext_holes', 'Extrude'); ext.selection('input').set(['wp1']); ext.setIndex('distance', 't/2', 0)
    dif = geom.create('dif', 'Difference'); dif.selection('input').set(['blk_beam', 'blk_slab']); dif.selection('input2').set(['ext_holes'])
    t0 = time.time(); geom.run('fin')
    p(f'geometry: {nh} beam holes, {ncross} crosses, X_in {X_in:.0f} nm, slab {Lc+sh["m_out"]:.0f} x {Yc+sh["m_out"]:.0f} nm + PML; '
      f'{int(geom.getNDomains())} domains ({time.time()-t0:.1f} s)')

    T = '(-tol)'; BIG = '1e7'
    _box(comp, 'sel_pmlx', 3, ('X_in+Lc+m_out-tol', BIG), (T, BIG), (T, BIG), 'PML +x')
    _box(comp, 'sel_pmly', 3, (T, BIG), ('Yc+m_out-tol', BIG), (T, BIG), 'PML +y')
    up = comp.selection().create('sel_pml', 'Union'); up.set('entitydim', '3'); up.set('input', ['sel_pmlx', 'sel_pmly'])
    ip = comp.selection().create('sel_inner', 'Complement'); ip.set('entitydim', '3'); ip.set('input', ['sel_pml'])
    _box(comp, 'sel_beam', 3, (T, 'X_in+tol'), (T, 'wbeam/2+tol'), (T, 't/2+tol'), 'beam')
    _box(comp, 'sel_x0', 2, (T, 'tol'), (T, BIG), (T, BIG), 'x=0 faces')
    _box(comp, 'sel_y0', 2, (T, BIG), (T, 'tol'), (T, BIG), 'y=0 faces')
    _box(comp, 'sel_z0', 2, (T, BIG), (T, BIG), (T, 'tol'), 'z=0 faces')
    for t_ in ('sel_pml', 'sel_inner', 'sel_beam', 'sel_x0', 'sel_y0', 'sel_z0'):
        p(f'  {t_}: {len(comp.selection(t_).entities())}')
    mat = comp.material().create('mat1', 'Common'); mat.label('Diamond (isotropic)'); mat.selection().all()
    mat.propertyGroup('def').set('density', 'rho_d')
    enu = mat.propertyGroup().create('Enu', 'Enu', "Young's modulus and Poisson's ratio"); enu.set('E', 'E_d'); enu.set('nu', 'nu_d')
    pml = comp.coordSystem().create('pml1', 'PML'); pml.selection().named('sel_pml')
    solid = comp.physics().create('solid', 'SolidMechanics', 'geom1')
    for pl in ('x0', 'y0', 'z0'):
        sy = solid.create(f'sym_{pl}', 'SymmetrySolid', 2); sy.selection().named(f'sel_{pl}')
    for tag, sel in (('int_in', 'sel_inner'), ('int_beam', 'sel_beam')):
        op = comp.cpl().create(tag, 'Integration'); op.selection().named(sel)
    op = comp.cpl().create('max_beam', 'Maximum'); op.selection().named('sel_beam')
    ms = comp.mesh().create('mesh1'); tt = ms.create('ftet1', 'FreeTet')
    for k_, (sel, h) in enumerate((('sel_pml', 'h_pml'), ('sel_inner', 'h_slab'), ('sel_beam', 'h_beam'))):
        sz = tt.create(f'size{k_}', 'Size'); sz.selection().geom('geom1', 3); sz.selection().named(sel)
        sz.set('custom', 'on'); sz.set('hmax', h); sz.set('hmaxactive', 'on')
    t0 = time.time(); ms.run(); p(f'mesh: {ms.getNumElem()} elements ({time.time()-t0:.1f} s)')
    st = m.study().create('std1'); eg = st.create('eig', 'Eigenfrequency')
    eg.set('neigsactive', 'on'); eg.set('neigs', 'N_mode'); eg.set('shiftactive', 'on'); eg.set('shift', 'f_mech'); eg.set('eigunit', 'Hz')
    st.createAutoSequences('all')
    return model, dict(X_in=X_in, Lc=Lc, Yc=Yc, ncross=ncross, nelem=int(ms.getNumElem()))


def solve(model, f_target, x_loc=1500.0):
    m = model.java; t0 = time.time(); m.sol('sol1').runAll()
    lam = mphglobal(m, 'lambda', 'dset1'); f = np.real(mphglobal(m, 'solid.freq', 'dset1'))
    Q = np.abs(lam.imag) / (2 * np.abs(lam.real))
    loc = np.real(mphglobal(m, f'int_in(solid.disp^2*(x<{x_loc}[nm]))/int_in(solid.disp^2)', 'dset1'))
    beam = np.real(mphglobal(m, 'int_beam(solid.disp^2)/int_in(solid.disp^2)', 'dset1'))
    meff = np.real(mphglobal(m, '8*int_beam(rho_d*solid.disp^2)/max_beam(solid.disp^2)', 'dset1'))
    side = np.real(mphglobal(m, 'int_beam(real(v)*(y>wbeam/2-tol)*(x<1500[nm]))', 'dset1'))
    ok = (loc > 0.8) & (np.abs(f - f_target) < 0.08 * f_target)
    ib = int(np.where(ok)[0][np.argmax(loc[ok])]) + 1 if ok.any() else -1
    p(f'solve: {len(f)} modes ({time.time()-t0:.0f} s); breathing index {ib}')
    for i in np.argsort(f):
        if loc[i] > 0.5:
            p(f'  {i+1:3d} f {f[i]/1e9:8.4f} GHz  Q {Q[i]:10.3g}  loc {loc[i]:.3f}  beam {beam[i]:.3f}  meff {meff[i]*1e18:7.1f} fg')
    return dict(f=f, Q=Q, loc=loc, beam_frac=beam, meff=meff, side=side, i_breath=ib)


def export_top(model, ib, fn, xmax, ymax, zc):
    """real(u, v, w) and |u|^2 on the top face z = t/2 - 1 nm for mode ib (1-based)."""
    m = model.java; tag = 'cp_top'
    cp = m.result().dataset().create(tag, 'CutPlane'); cp.set('data', 'dset1'); cp.set('quickplane', 'xy'); cp.set('quickz', f'{zc}')   # plain number in nm (geometry unit)
    ex = m.result().export().create(tag, 'Data'); ex.set('data', tag)
    ex.set('expr', ['real(u)', 'real(v)', 'real(w)', 'solid.disp^2']); ex.set('location', 'fromdataset')
    ex.set('solnum', [str(ib)]); ex.set('filename', str(fn).replace('\\', '/')); ex.run()
    A = np.loadtxt(str(fn), comments='%')
    keep = np.isfinite(A[:, 3]) & (A[:, 0] <= xmax) & (A[:, 1] <= ymax)
    return A[keep, :2], A[keep, 3:]
