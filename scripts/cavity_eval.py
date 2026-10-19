"""
cavity_eval.py  (Windows; used by the cavity sweeps)
Evaluation helpers for the 1/8 full-cavity model (build_cavity_model.py): integration operators,
moving-boundary variables, optics/mechanics solves, mode metrics, and (relative) g0.
setup(model) must be called once BEFORE the first solve.
Optical cavity mode = most localized mode with Q > 1e3 (spurious Q~8 localized modes exist).
Breathing mode (cavity_pipeline.breathing_index): localized, in-phase sidewalls (B), and since 2026-10-15
the sidewall amplitude ratio S = max sidewall |v| / max beam |u| (inside x_loc): ~1.0 for a true breathing
mode, ~0.35 for the hole-centered hybrid found at w650 d0.13 (B alone is amplitude-blind).
"""
import numpy as np
from comsol_utils import mphglobal

P11, P12, P44 = -0.25, 0.043, -0.172
HBAR = 1.054571817e-34


def setup(model):
    m = model.java; comp = m.component('comp1')
    names = [str(n) for n in m.param().varnames()]
    if 'symf' not in names:                            # models built before 2026-10-18 (1/8 model)
        m.param().set('symf', '8')
    s = comp.selection().create('sel_side', 'Box'); s.set('entitydim', '2')
    full = 'sel_z0_all' not in [str(t) for t in comp.selection().tags()]     # sidewall-angle (full-thickness) model
    for ax, lo, hi in (('x', '(-tol)', 'X_in+tol'), ('y', 'w/2-tol', 'w/2+2*dsw+tol' if full else 'w/2+tol'),
                       ('z', '(-t/2-tol)' if full else '(-tol)', 't/2+tol')):
        s.set(f'{ax}min', lo); s.set(f'{ax}max', hi)
    s.set('condition', 'inside')
    mb = comp.selection().create('sel_mb', 'Difference'); mb.set('entitydim', '2'); mb.set('add', ['sel_beam_bnd'])
    mb.set('subtract', ['sel_x0_all', 'sel_y0_all', 'sel_end'] + ([] if full else ['sel_z0_all']))
    for tag, sel, dim in (('int_beam', 'sel_beam', 3), ('int_inner', 'sel_inner', 3), ('int_mb', 'sel_mb', 2),
                          ('int_side', 'sel_side', 2)):
        o = comp.cpl().create(tag, 'Integration'); o.selection().geom('geom1', dim); o.selection().named(sel)
    comp.cpl().create('max_beam', 'Maximum').selection().named('sel_beam')
    o = comp.cpl().create('max_side', 'Maximum'); o.selection().geom('geom1', 2); o.selection().named('sel_side')
    vd = comp.variable().create('var_ind_d'); vd.selection().geom('geom1', 3); vd.selection().named('sel_beam_all'); vd.set('ind_d', '1')
    va = comp.variable().create('var_ind_a'); va.selection().geom('geom1', 3); va.selection().named('sel_air'); va.set('ind_d', '0')
    vb = comp.variable().create('var_mb'); vb.selection().geom('geom1', 2); vb.selection().named('sel_mb')
    for c in 'xyz':
        vb.set(f'nO{c}', f'up(ind_d)*un{c}+down(ind_d)*dn{c}')
        vb.set(f'Ed{c}', f'if(up(ind_d)>0.5, up(ewfd.E{c}), down(ewfd.E{c}))')
    vb.set('En', 'Edx*nOx+Edy*nOy+Edz*nOz')
    vb.set('Epar2', 'abs(Edx)^2+abs(Edy)^2+abs(Edz)^2-abs(En)^2')
    vb.set('Dperp2', 'abs(epsilon0_const*n_d^2*En)^2')


def ev(m, expr, dset, solnum):
    e = m.result().numerical().create('_ev', 'EvalGlobal')
    try:
        e.set('data', dset); e.set('expr', expr); e.set('solnum', str(solnum))
        return float(e.getReal()[0][0])
    finally:
        m.result().numerical().remove('_ev')


def solve_optics(m, x_loc):
    m.sol('sol2').runAll()
    f = np.real(mphglobal(m, 'ewfd.freq', 'dset2'))
    Q = np.real(mphglobal(m, 'ewfd.Qfactor', 'dset2'))
    loc = np.real(mphglobal(m, f'int_inner(ewfd.normE^2*(x<{x_loc}[nm]))/int_inner(ewfd.normE^2)', 'dset2'))
    ok = Q > 1e3
    io = int(np.where(ok)[0][np.argmax(loc[ok])]) + 1 if ok.any() else int(np.argmax(loc)) + 1
    return f, Q, loc, io


def solve_mech(m, x_loc):
    m.sol('sol1').runAll()
    fm = np.real(mphglobal(m, 'solid.freq', 'dset1'))
    loc = np.real(mphglobal(m, f'int_beam(solid.disp^2*(x<{x_loc}[nm]))/int_beam(solid.disp^2)', 'dset1'))
    B = np.real(mphglobal(m, f'abs(int_side(real(v)*(x<{x_loc}[nm])))/int_side(abs(real(v))*(x<{x_loc}[nm]))', 'dset1'))
    return fm, loc, B


def sidewall_ratio(m, x_loc, k):
    """S of mechanical mode k (1-based; call after solve_mech): max sidewall |real v| / max beam |real u|, x < x_loc."""
    return (ev(m, f'max_side(abs(real(v))*(x<{x_loc}[nm]))', 'dset1', k) /
            ev(m, f'max_beam(sqrt(real(u)^2+real(v)^2+real(w)^2)*(x<{x_loc}[nm]))', 'dset1', k))


def g0_of(m, k, io, f_o, f_m):
    W_ = lambda e: f"withsol('sol1',{e},setind(lambda,{k}))"
    den = ev(m, 'int_inner(epsilon0_const*(1+(n_d^2-1)*ind_d)*ewfd.normE^2)', 'dset2', io)
    Qn = f"({W_('real(u)')}*nOx+{W_('real(v)')}*nOy+{W_('real(w)')}*nOz)"
    mbi = ev(m, f'int_mb({Qn}*((epsilon0_const*(n_d^2-1))*Epar2-(1/(epsilon0_const*n_d^2)-1/epsilon0_const)*Dperp2))', 'dset2', io)
    S = {c: W_(f'real(solid.e{c})') for c in ('XX', 'YY', 'ZZ', 'XY', 'XZ', 'YZ')}
    pe = (f"2*real(conj(ewfd.Ex)*ewfd.Ey)*{P44}*2*{S['XY']}+2*real(conj(ewfd.Ex)*ewfd.Ez)*{P44}*2*{S['XZ']}"
          f"+2*real(conj(ewfd.Ey)*ewfd.Ez)*{P44}*2*{S['YZ']}"
          f"+abs(ewfd.Ex)^2*({P11}*{S['XX']}+{P12}*({S['YY']}+{S['ZZ']}))"
          f"+abs(ewfd.Ey)^2*({P11}*{S['YY']}+{P12}*({S['XX']}+{S['ZZ']}))"
          f"+abs(ewfd.Ez)^2*({P11}*{S['ZZ']}+{P12}*({S['XX']}+{S['YY']}))")
    pei = ev(m, f'epsilon0_const*n_d^4*int_beam({pe})', 'dset2', io)
    umax = ev(m, 'max_beam(solid.disp)', 'dset1', k)
    meff = ev(m, 'symf*int_beam(rho_d*solid.disp^2)/max_beam(solid.disp^2)', 'dset1', k)
    xzpf = np.sqrt(HBAR / (2 * meff * 2 * np.pi * f_m))
    return -(f_o / 2) * mbi / den / umax * xzpf, (f_o / 2) * pei / den / umax * xzpf, meff
