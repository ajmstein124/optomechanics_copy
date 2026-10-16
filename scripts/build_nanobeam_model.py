"""
build_nanobeam_model.py  (runs on the Windows COMSOL machine)
Build the 1D nanobeam quarter-cell model FROM SCRATCH and save it for GUI inspection.
Setup approved by the user 2026-10-14 (runs/nanobeam_1d/figures/schematic_proposed.png):

  geometry  quarter cell 0<x<a, 0<y<w/2, 0<z<t/2 (beam block minus elliptical hole centered
            at (a/2, 0), semi-axes hx/2, hy/2) + air block 0<x<a, 0<y<w/2+pad_y, 0<z<pad_z
  material  Diamond (isotropic E, nu, rho; n=2.41) on the beam, Air (n=1) on the air
  physics   Solid Mechanics on the BEAM ONLY: Linear Elastic (from material), Free (default),
            Floquet periodic on x=0 / x=a beam faces (k = (kx, 0, 0)),
            Symmetry + Antisymmetry on the y=0 beam faces and on the z=0 beam faces
            (exactly one of each pair active -> 4 mode classes Y+/-, Z+/-)
  meshes    mesh1 "Mech Mesh": beam only -- Free Tri on x=0 beam face -> Copy Face to x=a ->
            Free Tet (hmax = mesh_h); mesh2 "OP Mesh": beam + air, same periodic approach
            (built for a later optical study; not used by the mechanical study)
  study     std1 "Mech": Eigenfrequency, N_mode modes around shift f_mech, mesh1, solid only

COMSOL feature types / property names were read from unit_cell_3.mph by
runs/nanobeam_1d/discover_api.py (SymmetrySolid, Antisymmetry, PeriodicCondition/Floquet/kFloquet,
LinearElasticModel from_mat, material groups def/density, Enu/E,nu, RefractiveIndex/n,
Eigenfrequency neigs/neigsactive/shift/shiftactive/eigwhich/mesh).

Usage (remote, via scripts/remote_runner.py --block <a runs/... wrapper>), or import build().
"""
import sys
import time

import mph


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


def build(params, hole=True, mesh_h='t/5', mesh_tri='t/5.33', name='nanobeam_1d'):
    """params: dict name -> COMSOL expression string (lengths with units)."""
    client = mph.start()
    model = client.create(name)
    m = model.java

    for k, v in params.items():
        m.param().set(k, v)
    m.param().set('kx', m.param().get('kx') if 'kx' in params else '0[1/m]')
    m.param().set('tol', '1[nm]', 'selection tolerance')

    m.component().create('comp1', True)
    comp = m.component('comp1')
    geom = comp.geom().create('geom1', 3)
    geom.lengthUnit('nm')

    beam = geom.create('blk_beam', 'Block'); beam.label('beam quarter')
    beam.set('size', ['a', 'w/2', 't/2']); beam.set('pos', ['0', '0', '0'])
    air = geom.create('blk_air', 'Block'); air.label('air box')
    air.set('size', ['a', 'w/2+pad_y', 'pad_z']); air.set('pos', ['0', '0', '0'])
    wp = geom.create('wp1', 'WorkPlane'); wp.label('hole work plane (z=0)')
    wp.set('quickplane', 'xy')
    el = wp.geom().create('e1', 'Ellipse'); el.label('elliptical hole')
    el.set('semiaxes', ['hx/2', 'hy/2']); el.set('pos', ['a/2', '0'])
    ext = geom.create('ext_hole', 'Extrude'); ext.label('hole cylinder')
    ext.set('workplane', 'wp1'); ext.selection('input').set(['wp1'])
    ext.setIndex('distance', 't/2', 0)
    dif = geom.create('dif_hole', 'Difference'); dif.label('beam minus hole')
    dif.selection('input').set(['blk_beam']); dif.selection('input2').set(['ext_hole'])
    if not hole:
        for f in (wp, ext, dif):
            f.active(False)
    geom.run('fin')
    nd, nb = int(geom.getNDomains()), int(geom.getNBoundaries())
    p(f'geometry: {nd} domains, {nb} boundaries (hole={"on" if hole else "off"})')

    T = '(-tol)'
    sel_beam = _box(comp, 'sel_beam', 3, (T, 'a+tol'), (T, 'w/2+tol'), (T, 't/2+tol'), 'beam domain')
    sel_air = comp.selection().create('sel_air', 'Complement'); sel_air.label('air domain')
    sel_air.set('entitydim', '3'); sel_air.set('input', ['sel_beam'])
    _box(comp, 'sel_x0_beam', 2, (T, 'tol'), (T, 'w/2+tol'), (T, 't/2+tol'), 'beam face x=0')
    _box(comp, 'sel_xa_beam', 2, ('a-tol', 'a+tol'), (T, 'w/2+tol'), (T, 't/2+tol'), 'beam face x=a')
    xf = comp.selection().create('sel_xfaces_beam', 'Union'); xf.label('beam faces x=0, x=a')
    xf.set('entitydim', '2'); xf.set('input', ['sel_x0_beam', 'sel_xa_beam'])
    adj = comp.selection().create('sel_beam_bnd', 'Adjacent'); adj.label('beam boundaries')
    adj.set('input', ['sel_beam']); adj.set('outputdim', '2')
    for tag, lab, box in (('y0', 'y=0', ((T, 'a+tol'), (T, 'tol'), (T, 't/2+tol'))),
                          ('z0', 'z=0', ((T, 'a+tol'), (T, 'w/2+tol'), (T, 'tol')))):
        _box(comp, f'sel_{tag}_box', 2, *box, f'{lab} plane faces (box)')
        it = comp.selection().create(f'sel_{tag}_beam', 'Intersection'); it.label(f'beam faces {lab}')
        it.set('entitydim', '2'); it.set('input', [f'sel_{tag}_box', 'sel_beam_bnd'])
    _box(comp, 'sel_x0_all', 2, (T, 'tol'), (T, 'w/2+pad_y+tol'), (T, 'pad_z+tol'), 'all faces x=0')
    _box(comp, 'sel_xa_all', 2, ('a-tol', 'a+tol'), (T, 'w/2+pad_y+tol'), (T, 'pad_z+tol'), 'all faces x=a')
    xa = comp.selection().create('sel_xfaces_all', 'Union'); xa.label('all faces x=0, x=a')
    xa.set('entitydim', '2'); xa.set('input', ['sel_x0_all', 'sel_xa_all'])
    _box(comp, 'sel_y0_all', 2, (T, 'a+tol'), (T, 'tol'), (T, 'pad_z+tol'), 'whole y=0 plane (beam+air)')
    _box(comp, 'sel_z0_all', 2, (T, 'a+tol'), (T, 'w/2+pad_y+tol'), (T, 'tol'), 'whole z=0 plane (beam+air)')

    for t in ('sel_beam', 'sel_air', 'sel_x0_beam', 'sel_xa_beam', 'sel_y0_beam', 'sel_z0_beam',
              'sel_x0_all', 'sel_xa_all'):
        p(f'  selection {t}: {len(comp.selection(t).entities())} entities')

    # materials
    mat = comp.material().create('mat1', 'Common'); mat.label('Diamond (isotropic)')
    mat.selection().named('sel_beam')
    mat.propertyGroup('def').set('density', 'rho_d')
    enu = mat.propertyGroup().create('Enu', 'Enu', "Young's modulus and Poisson's ratio")
    enu.set('E', 'E_d'); enu.set('nu', 'nu_d')
    ri = mat.propertyGroup().create('RefractiveIndex', 'RefractiveIndex', 'Refractive index')
    ri.set('n', 'n_d'); ri.set('ki', '0')
    air_m = comp.material().create('mat2', 'Common'); air_m.label('Air (vacuum for phonons)')
    air_m.selection().named('sel_air')
    air_m.propertyGroup('def').set('relpermittivity', '1')
    ri2 = air_m.propertyGroup().create('RefractiveIndex', 'RefractiveIndex', 'Refractive index')
    ri2.set('n', '1'); ri2.set('ki', '0')

    # solid mechanics on the beam only
    solid = comp.physics().create('solid', 'SolidMechanics', 'geom1')
    solid.selection().named('sel_beam')
    pc = solid.create('pc1', 'PeriodicCondition', 2); pc.label('Floquet x=0 <-> x=a')
    pc.set('PeriodicType', 'Floquet'); pc.set('kFloquet', ['kx', '0', '0'])
    pc.selection().named('sel_xfaces_beam')
    for plane in ('y0', 'z0'):
        sy = solid.create(f'sym_{plane}', 'SymmetrySolid', 2); sy.label(f'Symmetry {plane} (class +)')
        sy.selection().named(f'sel_{plane}_beam')
        an = solid.create(f'as_{plane}', 'Antisymmetry', 2); an.label(f'Antisymmetry {plane} (class -)')
        an.selection().named(f'sel_{plane}_beam')
        an.active(False)                       # default class Y+ Z+
    p('solid features: ' + ', '.join(str(t) for t in solid.feature().tags()))

    # optics (ewfd) on beam + air, same conventions as unit_cell_3.mph OP study:
    # wave equation with n from material, default PEC on exterior (outer air faces),
    # Floquet on all x faces, PEC/PMC on the full y=0 and z=0 planes.
    # TE-like (Oh 2026 Fig 1d: odd vector symmetry in y, even in z): y=0 PEC, z=0 PMC (default here).
    ew = comp.physics().create('ewfd', 'ElectromagneticWavesFrequencyDomain', 'geom1')
    pco = ew.create('pc1', 'PeriodicCondition', 2); pco.label('Floquet x=0 <-> x=a (all faces)')
    pco.set('PeriodicType', 'Floquet'); pco.set('kFloquet', ['kx', '0', '0'])
    pco.selection().named('sel_xfaces_all')
    for plane in ('y0', 'z0'):
        pe = ew.create(f'pec_{plane}', 'PerfectElectricConductor', 2); pe.label(f'PEC {plane} plane')
        pe.selection().named(f'sel_{plane}_all')
        pm = ew.create(f'pmc_{plane}', 'PerfectMagneticConductor', 2); pm.label(f'PMC {plane} plane')
        pm.selection().named(f'sel_{plane}_all')
    op_class(model, y='PEC', z='PMC')
    p('ewfd features: ' + ', '.join(str(t) for t in ew.feature().tags()))

    # meshes
    def periodic_mesh(tag, label, src, dst, tet_sel, h_tri, h_tet, extra_sizes=()):
        ms = comp.mesh().create(tag); ms.label(label)
        ft = ms.create('ftri1', 'FreeTri'); ft.selection().named(src)
        s1 = ft.create('size1', 'Size'); s1.set('custom', 'on'); s1.set('hmax', h_tri); s1.set('hmaxactive', 'on')
        cf = ms.create('cpf1', 'CopyFace')
        cf.selection('source').named(src); cf.selection('destination').named(dst)
        tt = ms.create('ftet1', 'FreeTet')
        if tet_sel:
            tt.selection().geom('geom1', 3); tt.selection().named(tet_sel)
        s2 = tt.create('size1', 'Size'); s2.set('custom', 'on'); s2.set('hmax', h_tet); s2.set('hmaxactive', 'on')
        for i, (sel, h) in enumerate(extra_sizes, 2):
            sx = tt.create(f'size{i}', 'Size'); sx.selection().geom('geom1', 3); sx.selection().named(sel)
            sx.set('custom', 'on'); sx.set('hmax', h); sx.set('hmaxactive', 'on')
        return ms

    mesh1 = periodic_mesh('mesh1', 'Mech Mesh (beam only)', 'sel_x0_beam', 'sel_xa_beam', 'sel_beam',
                          mesh_tri, mesh_h)
    t0 = time.time(); mesh1.run()
    p(f'mesh1 (mech): {mesh1.getNumElem()} elements ({time.time()-t0:.1f} s)')
    mesh2 = periodic_mesh('mesh2', 'OP Mesh (beam + air, for later optics)', 'sel_x0_all', 'sel_xa_all', None,
                          'pad_z/10', 'pad_z/10', extra_sizes=(('sel_beam', 't/6'),))
    try:
        t0 = time.time(); mesh2.run()
        p(f'mesh2 (optical): {mesh2.getNumElem()} elements ({time.time()-t0:.1f} s)')
    except Exception as e:
        p(f'mesh2 (optical) did not build (not needed for mechanics): {str(e)[:300]}')

    # mechanical eigenfrequency study
    std = m.study().create('std1'); std.label('Mech Study')
    eig = std.create('eig', 'Eigenfrequency')
    eig.set('neigsactive', 'on'); eig.set('neigs', 'N_mode')
    eig.set('shiftactive', 'on'); eig.set('shift', 'f_mech'); eig.set('eigunit', 'Hz')
    eig.set('mesh', ['geom1', 'mesh1'])
    eig.set('activate', ['solid', 'on', 'ewfd', 'off', 'frame:spatial1', 'on', 'frame:material1', 'on'])
    std.createAutoSequences('all')

    # optical eigenfrequency study (ewfd only, OP mesh)
    std2 = m.study().create('std2'); std2.label('OP Study')
    eo = std2.create('eig', 'Eigenfrequency')
    eo.set('neigsactive', 'on'); eo.set('neigs', 'N_op')
    eo.set('shiftactive', 'on'); eo.set('shift', 'f_op'); eo.set('eigunit', 'Hz')
    eo.set('mesh', ['geom1', 'mesh2'])
    eo.set('activate', ['solid', 'off', 'ewfd', 'on', 'frame:spatial1', 'on', 'frame:material1', 'on'])
    std2.createAutoSequences('all')
    p(f'solvers: {[str(t) for t in m.sol().tags()]}')
    return client, model


def op_class(model, y='PEC', z='PMC'):
    """Optical symmetry class: which of PEC/PMC is active on the y=0 and z=0 planes."""
    ew = model.java.component('comp1').physics('ewfd')
    for plane, kind in (('y0', y), ('z0', z)):
        ew.feature(f'pec_{plane}').active(kind == 'PEC')
        ew.feature(f'pmc_{plane}').active(kind == 'PMC')


def class_on(model, yclass, zclass):
    """yclass/zclass in {'+','-'}: activate Symmetry ('+') or Antisymmetry ('-') on each plane."""
    solid = model.java.component('comp1').physics('solid')
    for plane, c in (('y0', yclass), ('z0', zclass)):
        solid.feature(f'sym_{plane}').active(c == '+')
        solid.feature(f'as_{plane}').active(c == '-')
