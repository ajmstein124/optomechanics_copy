"""
make_gds.py  (Mac)  -- best_devices/
GDS layouts of the tracked devices, built from the same taper parameters the COMSOL models use (scripts/cavity_taper.layout).
Full device (both halves): beam of width w from -X_in to X_in (X_in = beam_half_length, pad_x 1 um past the last mirror cell),
elliptical holes (hx, hy = full axes), each end anchored in a slab of half-size S = (n_pad + Ns) a_s + m_out = 2.75 um, as in the
COMSOL anchor model (runs/shield_619). The shielded version adds the square-lattice cross shield (a 460, h 395, w 150, fillet 20 nm,
bridges 65 nm, lattice shifted 35 nm from the trench so the edge strip is 67.5 nm) around a solid pad at each anchor, exactly the cells of runs/shield_619/build_shield_cavity.py mirrored to the full device.
Layers: 1/0 diamond kept (positive), 2/0 etch (window minus diamond = holes + trench + shield crosses), 10/0 label (outside window).
Units um, precision 1 nm, curves to 1 nm. Writes:
  best_devices/<device>/<device>.gds (+ _shield.gds for the best gap-confined device), best_devices/gds/<tag>.gds for every
  gap-confined design, best_devices/not_gap_confined/<device>/<device>.gds, and a preview PNG next to each GDS.
Run from the project root:  python best_devices/make_gds.py
"""
import json
import sys
from pathlib import Path

import gdstk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection

sys.path.insert(0, 'scripts')
from cavity_taper import beam_half_length, layout, min_features  # noqa: E402

TOL = 1e-3                                          # um
SHIELD = dict(a=460, h=395, w=150, fillet=20, Ns=4, n_pad=1, n_pad_y=1, m_out=500, x_off=35)   # 65 nm cell (runs/shield_619 *_shield65)
MIN_FEATURE = 65                                    # nm, user 2026-10-22
G = Path('runs/surrogate_explore/gapconf')
BEST_TAG, BEST_DIR = 'w650_m186_c455_d086', Path('best_devices/60nm_w650_d0.086_xi1.79_chi-6.97_gapconf')
OLD = {'60nm_w650_d0.10_xi6_chi4': None, '80nm_w700_d0.10_xi4_chi3.5': None, '80nm_w713_d0.135_xi2.1_chi3.55_BO': None}


def cross(cx, cy, sh):
    h, w = sh['h'] / 2e3, sh['w'] / 2e3
    pts = [(h, w), (w, w), (w, h), (-w, h), (-w, w), (-h, w), (-h, -w), (-w, -w), (-w, -h), (w, -h), (w, -w), (h, -w)]
    p = gdstk.Polygon([(cx + x, cy + y) for x, y in pts])
    p.fillet(sh['fillet'] / 1e3, tolerance=TOL)
    return p


def device(cfg, name, shield=None):
    lay = layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'], cfg.get('eta', 1.0), cfg['xi'],
                 cfg['chi'], lock_x=cfg.get('lock_x', False), profile=cfg.get('profile'))
    X = beam_half_length(lay, cfg['pad_x']) / 1e3; hw = cfg['w'] / 2e3
    sh = SHIELD; S = (sh.get('x_off', 0) + (sh['n_pad'] + sh['Ns']) * sh['a'] + sh['m_out']) / 1e3
    solid = [gdstk.rectangle((-X, -hw), (X, hw))] + [gdstk.rectangle((s * X, -S), (s * (X + S), S)) for s in (1, -1)]
    holes = []
    for j in range(len(lay['x'])):
        for s in ((1,) if j == 0 else (1, -1)):
            holes.append(gdstk.ellipse((s * lay['x'][j] / 1e3, 0), (lay['hx'][j] / 2e3, lay['hy'][j] / 2e3), tolerance=TOL))
    if shield:
        feats = dict(bridge=shield['a'] - shield['h'], edge_strip=shield.get('x_off', 0) + (shield['a'] - shield['h']) / 2,
                     bar=shield['w'], block=shield['a'] - shield['w'])
        assert min(feats.values()) >= MIN_FEATURE, f'{name}: shield feature below {MIN_FEATURE} nm: {feats}'
        a = shield['a'] / 1e3; n = shield['n_pad'] + shield['Ns']; xo = shield.get('x_off', 0) / 1e3
        for i in range(n):
            for k in range(n):
                if i < shield['n_pad'] and k < shield['n_pad_y']:
                    continue
                for sx in (1, -1):
                    for sy in (1, -1):
                        holes.append(cross(sx * (X + xo + (i + .5) * a), sy * (k + .5) * a, shield))
    dia = gdstk.boolean(gdstk.boolean(solid, [], 'or'), holes, 'not', layer=1)
    win = gdstk.rectangle((-(X + S), -S), (X + S, S))
    etch = gdstk.boolean(win, dia, 'not', layer=2)
    c = gdstk.Cell(name)
    c.add(*dia, *etch)
    c.add(*gdstk.text(name, 0.4, (-(X + S), S + 0.3), layer=10))
    return c, lay, X, S


def preview(cell, lay, X, S, out, title):
    polys = [p.points for p in cell.polygons if p.layer == 1]
    fig, ax = plt.subplots(2, 1, figsize=(11, 6.4), gridspec_kw=dict(height_ratios=[1.25, 1]))
    for a_, (xl, yl) in zip(ax, (((-(X + S), X + S), (-S, S)), ((-1.6, 1.6), (-0.5, 0.5)))):
        a_.add_collection(PolyCollection(polys, facecolor='0.55', edgecolor='none'))
        a_.set_xlim(*xl); a_.set_ylim(*yl); a_.set_aspect('equal'); a_.set_facecolor('white')
        a_.set_xlabel('x (µm)'); a_.set_ylabel('y (µm)')
    ax[0].set_title(title, fontsize=9); ax[1].set_title('cavity center (gray = diamond, white = etched)', fontsize=8)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)


def write(cfg, name, out, title, shield=None, check=None):
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    cell, lay, X, S = device(cfg, name, shield)
    lib.add(cell); out.parent.mkdir(parents=True, exist_ok=True); lib.write_gds(str(out))
    mf = min_features(lay, cfg['w'])
    if check:
        bad = {k: (mf[k], v) for k, v in check.items() if abs(mf[k] - v) > 0.5}
        assert not bad, f'{name}: layout does not reproduce the stored min features {bad}'
    if min(mf['bridge'], mf['rail']) < MIN_FEATURE:
        print(f'  NOTE {name}: beam feature below {MIN_FEATURE} nm (bridge {mf["bridge"]:.0f}, rail {mf["rail"]:.0f})')
    preview(cell, lay, X, S, out.with_suffix('.png'), f"{title}  ({2 * (X + S):.1f} × {2 * S:.1f} µm window; "
            f"min bridge {mf['bridge']:.0f}, rail {mf['rail']:.0f} nm)")
    print(f'wrote {out}  ({len(cell.polygons)} polygons, beam {2 * X:.2f} µm)')
    return dict(gds=str(out), beam_um=2 * X, window_um=[2 * (X + S), 2 * S], min_features=mf)


if __name__ == '__main__':
    rec = {}
    for tag in sorted(p.name for p in G.iterdir() if (p / 'data' / 'fields.npz').exists()):
        cfg = json.loads(str(np.load(G / tag / 'data' / 'fields.npz', allow_pickle=True)['cfg']))
        zs = np.load(G / tag / 'data' / 'figsolve.npz')
        chk = {k: float(zs[k]) for k in ('bridge', 'rail', 'hole')}
        rec[tag] = write(cfg, tag, Path('best_devices/gds') / f'{tag}.gds', f'{tag} (gap-confined), plain anchors', check=chk)
        if tag == BEST_TAG:
            rec[tag + '_dev'] = write(cfg, BEST_DIR.name, BEST_DIR / f'{BEST_DIR.name}.gds', 'best gap-confined device, plain anchors', check=chk)
            rec[tag + '_shield'] = write(cfg, BEST_DIR.name + '_shield', BEST_DIR / f'{BEST_DIR.name}_shield.gds',
                                         'best gap-confined device + cross phonon shield (a 460, h 395, w 150 nm; 65 nm features)', shield=SHIELD, check=chk)
    ng = Path('best_devices/not_gap_confined')
    for d in OLD:
        j = json.load(open(ng / d / 'summary.json'))
        if 'cfg' in j:
            cfg = j['cfg']
        else:                                         # width-study devices: mirror cell ratios, M 10, 10 mirror cells
            c = j['cell']; cfg = dict(a_m=j['a'], w=c['w'], t=c['t'], hx_m=c['hx_a'] * j['a'], hy_m=c['hy_w'] * c['w'], M=10,
                                      n_mirror=10, d=j['d'], eta=1.0, xi=j['xi'], chi=j['chi'], pad_x=1000)
        rec[d] = write(cfg, d, ng / d / f'{d}.gds', f'{d} (breathing mode above the mirror gap)', check=j['min_features'])
    json.dump(rec, open('best_devices/gds/index.json', 'w'), indent=1)
