"""
build_cavity_model.py  (runs on the Windows COMSOL machine)
Full 1D nanobeam OMC cavity, ONE-EIGHTH model (symmetry planes x=0, y=0, z=0), built from scratch.
Hole layout from scripts/cavity_taper.py (Chan thesis taper, Oh 2026 start values).

  geometry  beam  0 < x < X_in + d_pml, 0 < y < w/2, 0 < z < t/2, minus elliptical holes centered at
                  (x_j, 0) (hole 0 = center hole, cut in half by x=0), j = 0 .. M + n_mirror
            air   block 0 < x < X_in + d_pml, 0 < y < w/2 + pad_y + d_pml, 0 < z < t/2 + pad_z + d_pml,
                  with PML layers (thickness d_pml) on the +x, +y, +z sides.
                  X_in = edge of last mirror cell + pad_x (plain waveguide); the beam runs on into the
                  +x PML (light leaving through the mirrors goes into the waveguide and is absorbed).
  material  Diamond (isotropic E, nu, rho; n) on the beam (incl. its PML part); Air (n=1) elsewhere
  solid     beam inside X_in only. Symmetry/Antisymmetry pairs on the x=0, y=0, z=0 beam faces
            (default Symmetry on all three = breathing mode, Oh Fig. 1c); Fixed constraint on the
            beam end face x = X_in (clamped to the support / shield).
  ewfd      beam + air; PML coordinate system on the PML domains; PEC/PMC pairs on the full
            x=0, y=0, z=0 planes. Default TE-like fundamental: x=0 PEC (Ey odd about the center
            hole; checked on Oh Fig. 1b), y=0 PEC, z=0 PMC (as the validated mirror-cell model).
  mesh      one mesh for both studies (same mesh -> no interpolation for g0 later):
            Free Tet, hmax h_air everywhere, h_beam in the beam.
  studies   std1 Mech: Eigenfrequency around f_mech, solid only. std2 OP: around f_op, ewfd only.

Usage: from build_cavity_model import build; client, model = build(cfg)  (see runs/cavity_*/build.py)
"""
import sys
import time

import mph
from cavity_taper import layout, beam_half_length


def p(*a):
    print(*a)
    sys.stdout.flush()


def _box(comp, tag, dim, x, y, z, label, condition='inside'):
    s = comp.selection().create(tag, 'Box')
    s.label(label)
    s.set('entitydim', str(dim))
    for ax, (lo, hi) in zip('xyz', (x, y, z)):
        s.set(f'{ax}min', lo)
        s.set(f'{ax}max', hi)
    s.set('condition', condition)
    return s


def build(cfg, name='cavity'):
    """cfg: dict with numbers in nm unless noted:
    a_m, w, t, hx_m, hy_m, M, n_mirror, d, eta, xi, chi, pad_x, pad_y, pad_z, d_pml, h_beam (expr),
    h_air (expr), E_d, nu_d, rho_d, n_d (strings with units / plain), f_mech, f_op (strings), N_mode, N_op."""
    lay = layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'],
                 cfg['eta'], cfg['xi'], cfg['chi'])
    X_in = beam_half_length(lay, cfg['pad_x'])
    nh = len(lay['x'])

    client = mph.start()
    model = client.create(name)
    m = model.java
    P = m.param()
    for k in ('a_m', 'w', 't', 'hx_m', 'hy_m', 'pad_x', 'pad_y', 'pad_z', 'd_pml'):
        P.set(k, f"{cfg[k]}[nm]")
    for k, desc in (('M', 'taper cells (j=0..M)'), ('n_mirror', 'mirror cells beyond the taper'),
                    ('d', 'defect depth'), ('eta', 'taper slope remap'), ('xi', 'aspect: r=a^xi'),
                    ('chi', 'area: 1-s=chi(1-a)')):
        P.set(k, str(cfg[k]), desc + ' -- documentation only; holes below are computed by cavity_taper.py')
    P.set('X_in', f'{X_in:.3f}[nm]', 'beam half-length inside the PML (last cell edge + pad_x)')
    for k in ('E_d', 'nu_d', 'rho_d', 'n_d', 'f_mech', 'f_op', 'N_mode', 'N_op', 'h_beam', 'h_air'):
        P.set(k, str(cfg[k]))
    P.set('tol', '1[nm]', 'selection tolerance')
    for j in range(nh):
        P.set(f'x{j}', f"{lay['x'][j]:.3f}[nm]", f'hole {j} center')
        P.set(f'hx{j}', f"{lay['hx'][j]:.3f}[nm]", f'hole {j} full x axis')
        P.set(f'hy{j}', f"{lay['hy'][j]:.3f}[nm]", f'hole {j} full y axis')

    m.component().create('comp1', True)
    comp = m.component('comp1')
    geom = comp.geom().create('geom1', 3)
    geom.lengthUnit('nm')
    beam = geom.create('blk_beam', 'Block'); beam.label('beam (1/8)')
    beam.set('size', ['X_in+d_pml', 'w/2', 't/2']); beam.set('pos', ['0', '0', '0'])
    air = geom.create('blk_air', 'Block'); air.label('air box + PML layers')
    air.set('size', ['X_in+d_pml', 'w/2+pad_y+d_pml', 't/2+pad_z+d_pml']); air.set('pos', ['0', '0', '0'])
    air.set('layername', ['PML']); air.setIndex('layer', 'd_pml', 0)
    for side, on in (('layerleft', False), ('layerright', True), ('layerfront', False),
                     ('layerback', True), ('layerbottom', False), ('layertop', True)):
        air.set(side, on)
    wp = geom.create('wp1', 'WorkPlane'); wp.label('holes work plane (z=0)')
    wp.set('quickplane', 'xy')
    for j in range(nh):
        el = wp.geom().create(f'e{j}', 'Ellipse'); el.label(f'hole {j}')
        el.set('semiaxes', [f'hx{j}/2', f'hy{j}/2']); el.set('pos', [f'x{j}', '0'])
    ext = geom.create('ext_holes', 'Extrude'); ext.label('hole cylinders')
    ext.set('workplane', 'wp1'); ext.selection('input').set(['wp1'])
    ext.setIndex('distance', 't/2', 0)
    dif = geom.create('dif_holes', 'Difference'); dif.label('beam minus holes')
    dif.selection('input').set(['blk_beam']); dif.selection('input2').set(['ext_holes'])
    t0 = time.time()
    geom.run('fin')
    p(f'geometry: {nh} holes on the half beam (hole 0 = center), X_in = {X_in:.0f} nm; '
      f'{int(geom.getNDomains())} domains, {int(geom.getNBoundaries())} boundaries ({time.time()-t0:.1f} s)')

    T = '(-tol)'
    Ytop, Ztop = 'w/2+pad_y+d_pml+tol', 't/2+pad_z+d_pml+tol'
    _box(comp, 'sel_beam_all', 3, (T, 'X_in+d_pml+tol'), (T, 'w/2+tol'), (T, 't/2+tol'), 'beam domains (incl. PML part)')
    _box(comp, 'sel_beam', 3, (T, 'X_in+tol'), (T, 'w/2+tol'), (T, 't/2+tol'), 'beam domains (inside X_in)')
    a_ = comp.selection().create('sel_air', 'Complement'); a_.label('air domains')
    a_.set('entitydim', '3'); a_.set('input', ['sel_beam_all'])
    _box(comp, 'sel_inner', 3, (T, 'X_in+tol'), (T, 'w/2+pad_y+tol'), (T, 't/2+pad_z+tol'), 'inner region (no PML)')
    pm = comp.selection().create('sel_pml', 'Complement'); pm.label('PML domains')
    pm.set('entitydim', '3'); pm.set('input', ['sel_inner'])
    adj = comp.selection().create('sel_beam_bnd', 'Adjacent'); adj.label('beam boundaries')
    adj.set('input', ['sel_beam']); adj.set('outputdim', '2')
    planes = {'x0': ((T, 'tol'), (T, Ytop), (T, Ztop)),
              'y0': ((T, 'X_in+d_pml+tol'), (T, 'tol'), (T, Ztop)),
              'z0': ((T, 'X_in+d_pml+tol'), (T, Ytop), (T, 'tol'))}
    for pl, box in planes.items():
        _box(comp, f'sel_{pl}_all', 2, *box, f'whole {pl[0]}=0 plane')
        it = comp.selection().create(f'sel_{pl}_beam', 'Intersection'); it.label(f'beam faces {pl[0]}=0')
        it.set('entitydim', '2'); it.set('input', [f'sel_{pl}_all', 'sel_beam_bnd'])
    _box(comp, 'sel_end', 2, ('X_in-tol', 'X_in+tol'), (T, 'w/2+tol'), (T, 't/2+tol'), 'beam end face x=X_in')
    for t in ('sel_beam_all', 'sel_beam', 'sel_air', 'sel_pml', 'sel_x0_beam', 'sel_y0_beam', 'sel_z0_beam',
              'sel_x0_all', 'sel_end'):
        p(f'  selection {t}: {len(comp.selection(t).entities())} entities')

    mat = comp.material().create('mat1', 'Common'); mat.label('Diamond (isotropic)')
    mat.selection().named('sel_beam_all')
    mat.propertyGroup('def').set('density', 'rho_d')
    enu = mat.propertyGroup().create('Enu', 'Enu', "Young's modulus and Poisson's ratio")
    enu.set('E', 'E_d'); enu.set('nu', 'nu_d')
    ri = mat.propertyGroup().create('RefractiveIndex', 'RefractiveIndex', 'Refractive index')
    ri.set('n', 'n_d'); ri.set('ki', '0')
    am = comp.material().create('mat2', 'Common'); am.label('Air')
    am.selection().named('sel_air')
    am.propertyGroup('def').set('relpermittivity', '1')
    ri2 = am.propertyGroup().create('RefractiveIndex', 'RefractiveIndex', 'Refractive index')
    ri2.set('n', '1'); ri2.set('ki', '0')

    pml = comp.coordSystem().create('pml1', 'PML'); pml.label('PML (+x, +y, +z)')
    pml.selection().named('sel_pml')

    solid = comp.physics().create('solid', 'SolidMechanics', 'geom1')
    solid.selection().named('sel_beam')
    for pl in ('x0', 'y0', 'z0'):
        sy = solid.create(f'sym_{pl}', 'SymmetrySolid', 2); sy.label(f'Symmetry {pl}')
        sy.selection().named(f'sel_{pl}_beam')
        an = solid.create(f'as_{pl}', 'Antisymmetry', 2); an.label(f'Antisymmetry {pl}')
        an.selection().named(f'sel_{pl}_beam'); an.active(False)
    fx = solid.create('fix_end', 'Fixed', 2); fx.label('Fixed: beam end (support)')
    fx.selection().named('sel_end')
    p('solid features: ' + ', '.join(str(t) for t in solid.feature().tags()))

    ew = comp.physics().create('ewfd', 'ElectromagneticWavesFrequencyDomain', 'geom1')
    for pl in ('x0', 'y0', 'z0'):
        pe = ew.create(f'pec_{pl}', 'PerfectElectricConductor', 2); pe.label(f'PEC {pl} plane')
        pe.selection().named(f'sel_{pl}_all')
        pc = ew.create(f'pmc_{pl}', 'PerfectMagneticConductor', 2); pc.label(f'PMC {pl} plane')
        pc.selection().named(f'sel_{pl}_all')
    op_class(model, x='PEC', y='PEC', z='PMC')
    p('ewfd features: ' + ', '.join(str(t) for t in ew.feature().tags()))

    ms = comp.mesh().create('mesh1'); ms.label('Mesh (beam h_beam, air/PML h_air)')
    tt = ms.create('ftet1', 'FreeTet')
    s1 = tt.create('size1', 'Size'); s1.set('custom', 'on'); s1.set('hmax', 'h_air'); s1.set('hmaxactive', 'on')
    s2 = tt.create('size2', 'Size'); s2.selection().geom('geom1', 3); s2.selection().named('sel_beam_all')
    s2.set('custom', 'on'); s2.set('hmax', 'h_beam'); s2.set('hmaxactive', 'on')
    t0 = time.time()
    try:
        ms.run()
        p(f'mesh: {ms.getNumElem()} elements ({time.time()-t0:.1f} s)')
    except Exception as e:
        p(f'mesh FAILED: {str(e)[:300]}')

    for tag, lab, n, sh, phys in (('std1', 'Mech Study', 'N_mode', 'f_mech', ('on', 'off')),
                                  ('std2', 'OP Study', 'N_op', 'f_op', ('off', 'on'))):
        st = m.study().create(tag); st.label(lab)
        eg = st.create('eig', 'Eigenfrequency')
        eg.set('neigsactive', 'on'); eg.set('neigs', n)
        eg.set('shiftactive', 'on'); eg.set('shift', sh); eg.set('eigunit', 'Hz')
        eg.set('mesh', ['geom1', 'mesh1'])
        eg.set('activate', ['solid', phys[0], 'ewfd', phys[1], 'frame:spatial1', 'on', 'frame:material1', 'on'])
        st.createAutoSequences('all')
    p(f'solvers: {[str(t) for t in m.sol().tags()]}')
    return client, model, lay


def op_class(model, x='PEC', y='PEC', z='PMC'):
    ew = model.java.component('comp1').physics('ewfd')
    for pl, kind in (('x0', x), ('y0', y), ('z0', z)):
        ew.feature(f'pec_{pl}').active(kind == 'PEC')
        ew.feature(f'pmc_{pl}').active(kind == 'PMC')


def mech_class(model, x='+', y='+', z='+'):
    solid = model.java.component('comp1').physics('solid')
    for pl, c in (('x0', x), ('y0', y), ('z0', z)):
        solid.feature(f'sym_{pl}').active(c == '+')
        solid.feature(f'as_{pl}').active(c == '-')


def set_layout(model, cfg):
    """Re-layout an existing cavity model for new (a_m, hx_m, hy_m, d, ...) with the SAME hole count
    (M + n_mirror unchanged): updates the hole parameters and X_in, rebuilds geometry and mesh.
    Returns the layout dict."""
    lay = layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'],
                 cfg['eta'], cfg['xi'], cfg['chi'])
    m = model.java
    P = m.param()
    nh = len(lay['x'])
    if int(round(float(P.evaluate('M')))) + int(round(float(P.evaluate('n_mirror')))) + 1 != nh:
        raise ValueError('hole count changed; rebuild the model instead')
    for k in ('a_m', 'hx_m', 'hy_m'):
        P.set(k, f"{cfg[k]}[nm]")
    for k in ('d', 'eta', 'xi', 'chi'):
        P.set(k, str(cfg[k]))
    P.set('X_in', f'{beam_half_length(lay, cfg["pad_x"]):.3f}[nm]')
    for j in range(nh):
        P.set(f'x{j}', f"{lay['x'][j]:.3f}[nm]")
        P.set(f'hx{j}', f"{lay['hx'][j]:.3f}[nm]")
        P.set(f'hy{j}', f"{lay['hy'][j]:.3f}[nm]")
    comp = m.component('comp1')
    comp.geom('geom1').run('fin')
    comp.mesh('mesh1').run()
    return lay
