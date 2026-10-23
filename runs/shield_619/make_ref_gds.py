"""
make_ref_gds.py  (Mac)  -- runs/shield_619
Reference GDS of EXACTLY the geometry the COMSOL anchor/shield models solved (build_shield_cavity.py + cases.json), for the
Dmitry-team validation (laghai/nanophotonics-cloud #163 / #176). Full device (both halves, mirrored about x = 0 and y = 0);
the COMSOL model is its 1/8 (Symmetry on x = 0, y = 0, z = 0).
Layers: 1/0 diamond solid INCLUDING the PML layers (the slab continues into the PML), 2/0 etch (window minus diamond),
3/0 PML regions (d_pml on the outer +-x and +-y sides of each anchor slab), 4/0 localization box (|x| < 1500 nm, beam),
10/0 label. Units um, 1 nm precision. Thickness t = 120 nm, vertical walls, isotropic diamond E 1050 GPa, nu 0.07, rho 3500.
Writes runs/shield_619/gds/<case>.gds + .png.  Run: python runs/shield_619/make_ref_gds.py
"""
import json
import sys
from pathlib import Path

import gdstk
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

sys.path.insert(0, 'scripts')
from cavity_taper import beam_half_length, layout  # noqa: E402

TOL = 1e-3
R = Path('runs/shield_619'); OUT = R / 'gds'; OUT.mkdir(exist_ok=True)
REF = {'ref_noshield_a450': 'nm10_noshield', 'ref_shield_a450_h390_w140': 'nm10_shield',
       'ref_noshield_a460_xoff35': 'nm10_noshield65', 'ref_shield65_a460_h395_w150_xoff35': 'nm10_shield65'}


def cross(cx, cy, sh):
    h, w = sh['h'] / 2e3, sh['w'] / 2e3
    pts = [(h, w), (w, w), (w, h), (-w, h), (-w, w), (-h, w), (-h, -w), (-w, -w), (-w, -h), (w, -h), (w, -w), (h, -w)]
    p = gdstk.Polygon([(cx + x, cy + y) for x, y in pts]); p.fillet(sh['fillet'] / 1e3, tolerance=TOL)
    return p


def build(cfg, sh, name):
    lay = layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'], cfg['eta'], cfg['xi'], cfg['chi'])
    X = beam_half_length(lay, cfg['pad_x']) / 1e3; hw = cfg['w'] / 2e3
    a_s, n_pad, n_pad_y, Ns, xo = sh['a'], sh['n_pad'], sh['n_pad_y'], sh['Ns'], sh.get('x_off', 0)
    Lc = (xo + (n_pad + Ns) * a_s) / 1e3; Yc = ((max(n_pad, n_pad_y) + Ns) * a_s) / 1e3
    mo, dp = sh['m_out'] / 1e3, sh['d_pml'] / 1e3
    Sx, Sy = Lc + mo, Yc + mo                                   # inner slab; PML beyond
    solid = [gdstk.rectangle((-X, -hw), (X, hw))] + [gdstk.rectangle((s * X, -(Sy + dp)), (s * (X + Sx + dp), Sy + dp)) for s in (1, -1)]
    holes = [gdstk.ellipse((s * lay['x'][j] / 1e3, 0), (lay['hx'][j] / 2e3, lay['hy'][j] / 2e3), tolerance=TOL)
             for j in range(len(lay['x'])) for s in ((1,) if j == 0 else (1, -1))]
    if sh['use']:
        for i in range(n_pad + Ns):
            for k in range(max(n_pad, n_pad_y) + Ns):
                if i < n_pad and k < n_pad_y:
                    continue
                holes += [cross(sx * (X + (xo + (i + .5) * a_s) / 1e3), sy * (k + .5) * a_s / 1e3, sh) for sx in (1, -1) for sy in (1, -1)]
    dia = gdstk.boolean(gdstk.boolean(solid, [], 'or'), holes, 'not', layer=1)
    win = gdstk.rectangle((-(X + Sx + dp), -(Sy + dp)), (X + Sx + dp, Sy + dp))
    etch = gdstk.boolean(win, dia, 'not', layer=2)
    pml = []
    for s in (1, -1):
        outer = gdstk.rectangle((s * X, -(Sy + dp)), (s * (X + Sx + dp), Sy + dp))
        inner = gdstk.rectangle((s * X, -Sy), (s * (X + Sx), Sy))
        pml += gdstk.boolean(outer, inner, 'not', layer=3)
    c = gdstk.Cell(name); c.add(*dia, *etch, *pml, gdstk.rectangle((-1.5, -hw), (1.5, hw), layer=4))
    c.add(*gdstk.text(name, 0.4, (-(X + Sx + dp), Sy + dp + 0.3), layer=10))
    return c, dict(X_in_nm=X * 1e3, slab_inner_nm=[Sx * 1e3, Sy * 1e3], d_pml_nm=dp * 1e3, n_crosses_full=4 * sum(
        1 for i in range(n_pad + Ns) for k in range(max(n_pad, n_pad_y) + Ns) if not (i < n_pad and k < n_pad_y)) if sh['use'] else 0)


if __name__ == '__main__':
    J = json.load(open(R / 'cases.json')); cases = {c['name']: c for c in J['cases']}; meta = {}
    for fn, cn in REF.items():
        c = cases[cn]; cfg = dict(J['cavity'], n_mirror=c['n_mirror'])
        sh = dict(J['shield'], use=c['shield'], **c.get('shield_override', {}))
        cell, info = build(cfg, sh, fn)
        lib = gdstk.Library(unit=1e-6, precision=1e-9); lib.add(cell); lib.write_gds(str(OUT / f'{fn}.gds'))
        meta[fn] = dict(info, comsol_case=cn, cavity=cfg, shield=sh)
        fig, ax = plt.subplots(figsize=(11, 4.2))
        for L, fc in ((1, '0.55'), (3, (0.6, 0.3, 0.8, 0.35))):
            ax.add_collection(PolyCollection([p.points for p in cell.polygons if p.layer == L], facecolor=fc, edgecolor='none'))
        b = cell.bounding_box(); ax.set_xlim(b[0][0], b[1][0]); ax.set_ylim(b[0][1], b[1][1] - 0.6); ax.set_aspect('equal')
        ax.set_title(f'{fn} (COMSOL case {cn}); gray diamond, purple PML (layer 3)', fontsize=9); ax.set_xlabel('x (µm)')
        fig.tight_layout(); fig.savefig(OUT / f'{fn}.png', dpi=150); plt.close(fig)
        print('wrote', OUT / f'{fn}.gds', info)
    json.dump(meta, open(OUT / 'index.json', 'w'), indent=1)
