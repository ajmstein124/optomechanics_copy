"""
post.py  (remote)  -- runs/cavity_oh2026
Post-process cavity_oh2026_solved.mph (no re-solve):
  1. optical Q = Re f / (2 Im f) (solve.py read only Re f)
  2. g0 = g_MB + g_PE between the optical cavity mode and every localized mechanical mode
     (Chan APL 2012 eqs. 1-3; Johnson PRE 2002). One shared mesh -> mech fields enter the optical
     dataset through withsol('sol1', ..., setind(lambda, k)).
       g_MB/2pi = -(f_o/2) * int_S (Q.n)(d_eps |E_par|^2 - d_epsinv |D_perp|^2) dS / int eps |E|^2 dV
       g_PE/2pi = +(f_o/2) * eps0 n^4 int_beam E.(p:S).E dV / int eps |E|^2 dV    (cubic m3m, x || [100])
       Q normalized to max|u| = 1; g0 = g_OM * x_zpf, x_zpf = sqrt(hbar / (2 m_eff w_m)),
       m_eff = 8 * int_beam rho |u|^2 / max|u|^2 (1/8 model -> x8). Ratios of 1/8 integrals are exact.
     n = outward normal from diamond, built from up/down normals and a diamond indicator; checked on
     the beam top face (must give +z).
  3. z=0 plane field values for plotting.
Diamond photoelastic (p11, p12, p44) = (-0.25, 0.043, -0.172) (Burek 2016 / Lang 2009).

Run via:
    python scripts/remote_runner.py --block runs/cavity_oh2026/post.py
"""
import sys
from pathlib import Path

import mph
import numpy as np
from comsol_utils import mphglobal

OUT = Path('runs/cavity_oh2026/data')
P11, P12, P44 = -0.25, 0.043, -0.172
HBAR = 1.054571817e-34
LOC_MIN = 0.9


def p(*a):
    print(*a); sys.stdout.flush()


client = mph.start()
model = client.load('cavity_oh2026_solved.mph')
m = model.java
comp = m.component('comp1')


def ev(expr, dset, solnum):
    tag = '_ev'
    e = m.result().numerical().create(tag, 'EvalGlobal')
    try:
        e.set('data', dset); e.set('expr', expr); e.set('solnum', str(solnum))
        return complex(float(e.getReal()[0][0]), float(e.getImag()[0][0])) if True else None
    finally:
        m.result().numerical().remove(tag)


# --- selections, operators, variables (remove copies saved by an earlier post run first)
for tag in ('var_mb', 'var_ind_a', 'var_ind_d'):
    if tag in [str(t) for t in comp.variable().tags()]: comp.variable().remove(tag)
for tag in ('int_mb', 'int_top', 'max_beam'):
    if tag in [str(t) for t in comp.cpl().tags()]: comp.cpl().remove(tag)
for tag in ('sel_mb', 'sel_top'):
    if tag in [str(t) for t in comp.selection().tags()]: comp.selection().remove(tag)
mb = comp.selection().create('sel_mb', 'Difference'); mb.label('moving boundaries (beam surfaces)')
mb.set('entitydim', '2'); mb.set('add', ['sel_beam_bnd'])
mb.set('subtract', ['sel_x0_all', 'sel_y0_all', 'sel_z0_all', 'sel_end'])
top = comp.selection().create('sel_top', 'Box'); top.label('beam top face (normal check)')
top.set('entitydim', '2')
for ax, lo, hi in (('x', '(-tol)', 'X_in+tol'), ('y', '(-tol)', 'w/2+tol'), ('z', 't/2-tol', 't/2+tol')):
    top.set(f'{ax}min', lo); top.set(f'{ax}max', hi)
top.set('condition', 'inside')
p(f"moving-boundary faces: {len(comp.selection('sel_mb').entities())}, top faces: {len(comp.selection('sel_top').entities())}")
for tag, sel, dim in (('int_mb', 'sel_mb', 2), ('int_top', 'sel_top', 2)):
    o = comp.cpl().create(tag, 'Integration'); o.selection().geom('geom1', dim); o.selection().named(sel)
mx = comp.cpl().create('max_beam', 'Maximum'); mx.selection().named('sel_beam')
names = [str(t) for t in comp.cpl().tags()]
if 'int_beam' not in names:
    for tag, sel in (('int_beam', 'sel_beam'), ('int_inner', 'sel_inner')):
        o = comp.cpl().create(tag, 'Integration'); o.selection().named(sel)

vd = comp.variable().create('var_ind_d'); vd.label('diamond indicator (beam)')
vd.selection().geom('geom1', 3); vd.selection().named('sel_beam_all'); vd.set('ind_d', '1')
va = comp.variable().create('var_ind_a'); va.label('diamond indicator (air)')
va.selection().geom('geom1', 3); va.selection().named('sel_air'); va.set('ind_d', '0')
vb = comp.variable().create('var_mb'); vb.label('moving-boundary fields (diamond side)')
vb.selection().geom('geom1', 2); vb.selection().named('sel_mb')
for c in 'xyz':
    vb.set(f'nO{c}', f'up(ind_d)*un{c}+down(ind_d)*dn{c}')
    vb.set(f'Ed{c}', f'if(up(ind_d)>0.5, up(ewfd.E{c}), down(ewfd.E{c}))')
vb.set('En', 'Edx*nOx+Edy*nOy+Edz*nOz')
vb.set('Epar2', 'abs(Edx)^2+abs(Edy)^2+abs(Edz)^2-abs(En)^2')
vb.set('Dperp2', 'abs(epsilon0_const*n_d^2*En)^2')

for st in ('sol1', 'sol2'):
    m.sol(st).updateSolution()           # make operators/variables defined after the solve evaluable
ntop = ev('int_top(nOz)/int_top(1)', 'dset2', 1).real
p(f'normal check on beam top face: <n_out . z> = {ntop:+.3f} (must be +1)')
sgn = 1.0 if ntop > 0 else -1.0

# --- optics
fo = mphglobal(m, 'ewfd.freq', 'dset2')
fre = np.real(fo)
Qo = np.real(mphglobal(m, 'ewfd.Qfactor', 'dset2'))   # ewfd.freq is Re only; damping is in lambda
loc_o = np.real(mphglobal(m, 'int_inner(ewfd.normE^2*(x<4000[nm]))/int_inner(ewfd.normE^2)', 'dset2'))
io = int(np.argmax(loc_o)) + 1
p('optical modes: f [THz], Q, loc')
for i in range(len(fo)):
    p(f'  {i+1:2d} {fre[i]/1e12:8.3f}  Q={Qo[i]:.3g}  loc={loc_o[i]:.3f}' + ('   <-- cavity' if i + 1 == io else ''))
f_o = fre[io - 1]

# --- mechanics vs this optical mode
fm = np.real(mphglobal(m, 'solid.freq', 'dset1'))
loc_m = np.real(mphglobal(m, 'int_beam(solid.disp^2*(x<4000[nm]))/int_beam(solid.disp^2)', 'dset1'))
den = ev('int_inner(epsilon0_const*(1+(n_d^2-1)*ind_d)*ewfd.normE^2)', 'dset2', io).real
d_eps = '(epsilon0_const*(n_d^2-1))'
d_epsinv = '(1/(epsilon0_const*n_d^2)-1/epsilon0_const)'
rows = []
for k in range(1, len(fm) + 1):
    if loc_m[k - 1] < LOC_MIN:
        continue
    W = lambda e: f"withsol('sol1',{e},setind(lambda,{k}))"
    try:
        umax = ev('max_beam(solid.disp)', 'dset1', k).real
        im_frac = ev(f"int_beam({W('abs(imag(u))^2+abs(imag(v))^2+abs(imag(w))^2')})/int_beam({W('solid.disp^2')})", 'dset2', io).real
        Qn = f"({W('real(u)')}*nOx+{W('real(v)')}*nOy+{W('real(w)')}*nOz)"
        mbi = ev(f'int_mb({Qn}*({d_eps}*Epar2-{d_epsinv}*Dperp2))', 'dset2', io).real * sgn
        S = {c: W(f'real(solid.e{c})') for c in ('XX', 'YY', 'ZZ', 'XY', 'XZ', 'YZ')}
        pe_expr = (f"2*real(conj(ewfd.Ex)*ewfd.Ey)*{P44}*2*{S['XY']}+2*real(conj(ewfd.Ex)*ewfd.Ez)*{P44}*2*{S['XZ']}"
                   f"+2*real(conj(ewfd.Ey)*ewfd.Ez)*{P44}*2*{S['YZ']}"
                   f"+abs(ewfd.Ex)^2*({P11}*{S['XX']}+{P12}*({S['YY']}+{S['ZZ']}))"
                   f"+abs(ewfd.Ey)^2*({P11}*{S['YY']}+{P12}*({S['XX']}+{S['ZZ']}))"
                   f"+abs(ewfd.Ez)^2*({P11}*{S['ZZ']}+{P12}*({S['XX']}+{S['YY']}))")
        pei = ev(f'epsilon0_const*n_d^4*int_beam({pe_expr})', 'dset2', io).real
        meff = ev('8*int_beam(rho_d*solid.disp^2)/max_beam(solid.disp^2)', 'dset1', k).real   # one dataset, consistent units
    except Exception as e:
        p(f'  mode {k}: g0 evaluation FAILED: {str(e)[:300]}'); continue
    xzpf = np.sqrt(HBAR / (2 * meff * 2 * np.pi * fm[k - 1]))
    gMB = -(f_o / 2) * mbi / den / umax * xzpf
    gPE = (f_o / 2) * pei / den / umax * xzpf
    rows.append((k, fm[k - 1], loc_m[k - 1], meff, xzpf, gMB, gPE, gMB + gPE, im_frac))
    p(f'  mech {k:2d} {fm[k-1]/1e9:7.4f} GHz loc={loc_m[k-1]:.3f}  m_eff={meff*1e18:7.1f} fg  x_zpf={xzpf*1e15:5.2f} fm  '
      f'g_MB={gMB/1e3:+7.1f}  g_PE={gPE/1e3:+7.1f}  g0={(gMB+gPE)/1e3:+7.1f} kHz  (imag(u) frac {im_frac:.1e})')
R = np.array(rows) if rows else np.zeros((0, 9))
best = int(np.argmax(np.abs(R[:, 7]))) if len(R) else None
if best is not None:
    p(f'BEST: mech mode {int(R[best,0])} at {R[best,1]/1e9:.4f} GHz, |g0|/2pi = {abs(R[best,7])/1e3:.1f} kHz '
      f'(Oh sim: 6.34 GHz, 184 kHz) with optical {f_o/1e12:.3f} THz, Q_o = {Qo[io-1]:.3g} (Oh: 192 THz)')

# --- z=0 plane fields
dnames = [str(d) for d in model.datasets()]
p(f'mph datasets: {dnames}')
fields = {}
try:
    for key, dn, expr, idx in (('Ey_opt', dnames[1], 'real(ewfd.Ey)', [io]),
                               ('disp', dnames[0], 'solid.disp', [int(r[0]) for r in R]),
                               ('v', dnames[0], 'real(v)', [int(r[0]) for r in R])):
        cols = []
        for i in idx:
            X, Y, Z, F = (np.asarray(a).ravel() for a in model.evaluate(['x', 'y', 'z', expr], dataset=dn, inner=[i]))
            on = Z < Z.min() + 1e-6 * (Z.max() - Z.min())
            cols.append((X[on], Y[on], F[on]))
        fields[f'{key}_x'], fields[f'{key}_y'] = cols[0][0], cols[0][1]
        fields[key] = np.stack([c[2] for c in cols]) if len({len(c[2]) for c in cols}) == 1 else np.array([c[2] for c in cols], dtype=object)
except Exception as e:
    p(f'field export failed: {str(e)[:300]}')
np.savez(str(OUT / 'post.npz'), f_opt=fre, Q_opt=Qo, loc_opt=loc_o, i_opt=io, f_mech=fm, loc_mech=loc_m,
         g_rows=R, g_cols=np.array(['k', 'f', 'loc', 'meff', 'xzpf', 'gMB', 'gPE', 'g0', 'imfrac']),
         normal_check=ntop, **fields)
model.save('cavity_oh2026_solved.mph')
p('post done')
client.clear()
