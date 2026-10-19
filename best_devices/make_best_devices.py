"""
make_best_devices.py  (Mac)  -- best_devices/
Result summary of the best 1D nanobeam OMC devices so far (the final device per minimum feature,
runs/cavity_619_final/data/final_<mf>.json). Per device folder:
  summary.md          parameters, optical + mechanical mode, Q, mirror-cell band gaps, min features, files
  modes.png           optical Ey (z = 0 midplane) + breathing mode on the deformed top face (runs/cavity_619/plot_fields.py)
  mode_spectrum.png   every optical mode (Q vs wavelength) and mechanical mode (localization vs frequency) of the final solve
  mirror_bands.png    mirror-cell bands Gamma -> X: optics in both y classes, mechanics in all 4 classes
  sweep_shapes.png    taper-shape maps of the device's (width, min feature) pipeline on the 619 nm line
  sweep_ad.png        (a, d) step of that pipeline: resonance, optical Q, breathing frequency vs a
  sweep_designs.csv   every 619 nm design of that pipeline with the selection flags and rank
Top level: README.md, selection.png, design_space.png, all_designs.csv (all pipelines).
Data must be local first (pulled from the COMSOL machine: runs/<pipeline>/data, runs/cavity_619_final/data).
Run from the project root:  python best_devices/make_best_devices.py
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, 'scripts')
import cavity_designs as CD            # noqa: E402
import plot_cavity_sweeps as S         # noqa: E402
from cavity_taper import layout, min_features   # noqa: E402

OUT = Path('best_devices')
C_NM_THZ = 299792.458
PIPES = [('w550 / 60 nm', 'runs/cavity_619', 60),
         ('w650 / 60 nm', 'runs/cavity_619_width/w650_mf60', 60),
         ('w600 / 60 nm', 'runs/cavity_619_width/w600_mf60', 60),
         ('w650 / 80 nm', 'runs/cavity_619_width/w650_mf80', 80),
         ('w600 / 80 nm', 'runs/cavity_619_width/w600_mf80', 80),
         ('w700 / 80 nm', 'runs/cavity_619_width/w700_mf80', 80)]
HBAR, KB = 1.054571817e-34, 1.380649e-23


def design_rows(rd, mf):
    D = CD.designs(rd)
    R = CD.rank(D, mf)
    rows = []
    for x in sorted(D, key=lambda x: (x['d'], x['xi'], x['chi'])):
        fab = x['min_feature'] >= mf - 0.5
        hyb = bool(np.isfinite(x['S']) and x['S'] < CD.S_MIN)
        rk = next((i + 1 for i, y in enumerate(R) if y is x), '')
        rows.append(dict(d=x['d'], xi=x['xi'], chi=x['chi'], a_nm=round(x['a'], 1), optical_Q=f"{x['Q']:.3g}",
                         breathing_GHz=round(x['fb'], 3) if np.isfinite(x['fb']) else '',
                         localization=round(x['lb'], 3) if np.isfinite(x['lb']) else '',
                         sidewall_ratio_S=round(x['S'], 2) if np.isfinite(x['S']) else '',
                         min_feature_nm=round(x['min_feature'], 1), fabricable=fab, hybrid=hyb,
                         meets_10GHz=bool(np.isfinite(x['fb']) and x['fb'] <= CD.F_TARGET), rank=rk))
    return rows


def write_csv(fn, rows):
    if rows:
        with open(fn, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def gaps(F):
    """F: (n_k, n_band) frequencies. Gaps between consecutive sorted bands over all k: [(lo, hi)]."""
    F = np.sort(F, axis=1)
    out = []
    for i in range(F.shape[1] - 1):
        lo, hi = np.nanmax(F[:, i]), np.nanmin(F[:, i + 1])
        if np.isfinite(lo) and np.isfinite(hi) and hi > lo:
            out.append((lo, hi))
    return out


def band_info(B, fb_GHz, lam):
    fo = B['f_opt'] / 1e12; fm = B['f_mech'] / 1e9; a = float(B['a'])
    f_t = C_NM_THZ / lam
    pec_X = np.sort(fo[-1, 0][np.isfinite(fo[-1, 0])]); pmc_X = np.sort(fo[-1, 1][np.isfinite(fo[-1, 1])])
    f_ll_X = C_NM_THZ / (2 * a)                      # air light line at X (kx = pi/a)
    info = dict(opt_X_band1=pec_X[0], opt_X_band2=pec_X[1], opt_light_line_X=f_ll_X, target_THz=f_t,
                opt_PMC_X_lowest=pmc_X[0], defect_fX=float(np.sort(B['defect_fX'])[0] / 1e12))
    g = gaps(fm[:, 0, :])                             # Y+Z+ (breathing) class quasi-gaps
    info['mech_YZ_gaps'] = [x for x in g if x[1] - x[0] > 0.2 and x[0] < 30]
    info['mech_YZ_gap_with_fb'] = next(((lo, hi) for lo, hi in g if lo < fb_GHz < hi), None)
    allm = fm.reshape(fm.shape[0], -1)
    info['mech_complete_gaps'] = [x for x in gaps(allm) if x[1] - x[0] > 0.2 and x[0] < 30]
    return info


def plot_bands(B, fb, lam, title, fn):
    fo = B['f_opt'] / 1e12; fm = B['f_mech'] / 1e9; k = B['k_frac']; a = float(B['a'])
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    for iy, (col, lab) in enumerate((('C0', 'y-even (cavity family)'), ('C1', 'y-odd'))):
        for j in range(fo.shape[2]):
            ax[0].plot(k, fo[:, iy, j], '-', color=col, lw=1.2, label=lab if j == 0 else None)
    ax[0].plot(k, C_NM_THZ * k / (2 * a), 'k--', lw=1, label='light line')
    ax[0].fill_between(k, C_NM_THZ * k / (2 * a), 900, color='0.85', zorder=0)
    ax[0].axhline(C_NM_THZ / lam, color='g', lw=1.2, label=f'{lam:.1f} nm cavity mode')
    ax[0].plot([1], [np.sort(B['defect_fX'])[0] / 1e12], 'r*', ms=12, label='center cell, X')
    ax[0].set_ylim(380, 820); ax[0].set_xlim(0, 1.03)
    ax[0].set_xlabel('k (π/a)'); ax[0].set_ylabel('f (THz)'); ax[0].set_title('optics (TE-like)', fontsize=11)
    ax[0].legend(fontsize=8, loc='lower right')
    names = list(B['classes'])
    cols = ['C3', '0.6', '0.6', '0.6']
    for ic in range(fm.shape[1]):
        for j in range(fm.shape[2]):
            ax[1].plot(k, fm[:, ic, j], '-', color=cols[ic], lw=1.6 if ic == 0 else 0.8,
                       label=(names[ic] + ' (breathing class)' if ic == 0 else 'other classes') if j == 0 and ic < 2 else None)
    for lo, hi in gaps(fm[:, 0, :]):
        if lo < fb < hi:
            ax[1].axhspan(lo, hi, color='C3', alpha=0.12)
    ax[1].axhline(fb, color='g', lw=1.2, label=f'breathing mode {fb:.2f} GHz')
    ax[1].set_ylim(0, 30); ax[1].set_xlim(0, 1)
    ax[1].set_xlabel('k (π/a)'); ax[1].set_ylabel('f (GHz)'); ax[1].set_title('mechanics', fontsize=11)
    ax[1].legend(fontsize=8, loc='upper left')
    fig.suptitle(title, fontsize=12)
    fig.tight_layout(); fig.savefig(fn, dpi=170, facecolor='white'); plt.close(fig)


def plot_spectrum(z, title, fn):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    lam = C_NM_THZ / (z['f_opt'] / 1e12)
    io = int(z['i_opt']) - 1
    sc = ax[0].scatter(lam, z['Q_opt'], c=z['loc_opt'], cmap='viridis', vmin=0, vmax=1, s=40, ec='k', lw=0.4)
    ax[0].scatter([lam[io]], [z['Q_opt'][io]], s=260, marker='*', fc='none', ec='r', lw=1.8, label='cavity mode')
    ax[0].set_yscale('log'); ax[0].set_xlabel('wavelength (nm)'); ax[0].set_ylabel('optical Q')
    ax[0].set_title('optical modes', fontsize=11); ax[0].legend(fontsize=8)
    fig.colorbar(sc, ax=ax[0], label='localization')
    f = z['f_mech'] / 1e9
    ib = int(z['i_breath'])
    ok = (z['B'] > 0.5)
    ax[1].scatter(f[~ok], z['loc_mech'][~ok], s=25, c='0.6', label='sidewalls out of phase')
    ax[1].scatter(f[ok], z['loc_mech'][ok], s=40, c='C3', ec='k', lw=0.4, label='sidewalls in phase')
    ax[1].scatter([f[ib]], [z['loc_mech'][ib]], s=260, marker='*', fc='none', ec='g', lw=1.8, label='breathing mode')
    ax[1].axhline(CD.LOC_MIN, color='k', ls=':', lw=0.8)
    ax[1].set_xlabel('f (GHz)'); ax[1].set_ylabel('localization'); ax[1].set_ylim(-0.02, 1.05)
    ax[1].set_title('mechanical modes', fontsize=11); ax[1].legend(fontsize=8, loc='upper right')
    fig.suptitle(title, fontsize=12)
    fig.tight_layout(); fig.savefig(fn, dpi=160, facecolor='white'); plt.close(fig)


def plot_ad(rd, title, fn):
    P = [p for p in CD.points(rd) if p['kind'] == 'ad']
    ds = sorted({p['cfg']['d'] for p in P})
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    for j, d in enumerate(ds):
        Q = sorted([p for p in P if p['cfg']['d'] == d], key=lambda p: p['cfg']['a_m'])
        a = [p['cfg']['a_m'] for p in Q]
        kw = dict(marker='o', color=f'C{j}', label=f'd {d:.2f}')
        ax[0].plot(a, [p['lam'] for p in Q], **kw); ax[1].semilogy(a, [p['Q'] for p in Q], **kw)
        ax[2].plot(a, [p['fb'] for p in Q], **kw)
    ax[0].axhline(CD.LAM0, color='g', lw=1); ax[2].axhline(CD.F_TARGET, color='g', lw=1, ls='--')
    for x, yl in zip(ax, ('resonance (nm)', 'optical Q', 'breathing (GHz)')):
        x.set_xlabel('mirror period a (nm)'); x.set_ylabel(yl); x.legend(fontsize=8)
    fig.suptitle(title, fontsize=12)
    fig.tight_layout(); fig.savefig(fn, dpi=150, facecolor='white'); plt.close(fig)


def fmt_gaps(G, unit):
    return ', '.join(f'{lo:.2f}–{hi:.2f} {unit}' for lo, hi in G) or 'none'


def device(mf):
    F = json.load(open(f'runs/cavity_619_final/data/final_{mf}.json'))
    rd, c = Path(F['run_dir']), F['cell']
    slug = f"{mf}_w{c['w']}_d{F['d']:.2f}_xi{F['xi']:g}_chi{F['chi']:g}"
    od = OUT / slug; od.mkdir(parents=True, exist_ok=True)
    z = np.load(rd / 'data' / f"confirm{F['rank']}.npz")
    zf = np.load(rd / 'data' / 'fields_final.npz')
    B = np.load(f'runs/cavity_619_final/data/bands_{mf}.npz')
    assert str(B['label']) == F['label'], 'bands file belongs to another device'
    cfg = json.loads(str(z['cfg']))
    lay = layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'], cfg['eta'], cfg['xi'], cfg['chi'])
    mfe = min_features(lay, cfg['w'])
    ib = int(z['i_breath'])
    fb = float(z['f_breath']); lam = float(z['lam']); Q = float(z['Q'])
    meff = float(z['meff'][ib]) if 'meff' in z else np.nan            # kg, normalized to max |u| (cavity_eval)
    xzpf = np.sqrt(HBAR / (2 * meff * 2 * np.pi * fb * 1e9)) if np.isfinite(meff) and meff > 0 else np.nan
    nth = {T: 1 / np.expm1(HBAR * 2 * np.pi * fb * 1e9 / (KB * T)) for T in (0.1, 1.7, 4.0)}
    info = band_info(B, fb, lam)
    tag = f"{mf} min feature: w {c['w']}, d {F['d']:.2f}, ξ {F['xi']:g}, χ {F['chi']:g}, a {F['a']:.1f} nm"

    subprocess.run([sys.executable, 'runs/cavity_619/plot_fields.py', str(rd / 'data'), str(od / 'modes.png'),
                    'final=me'], check=True, capture_output=True)
    plot_spectrum(z, tag, od / 'mode_spectrum.png')
    plot_bands(B, fb, lam, f'mirror cell: w {c["w"]}, a {F["a"]:.1f}, hx {float(B["hx"]):.1f}, hy {float(B["hy"]):.1f}, t {c["t"]} nm', od / 'mirror_bands.png')
    S.shape_maps(str(rd), int(mf[:2]), f'w{c["w"]} / {mf} min feature: taper shapes on the 619 nm line', od / 'sweep_shapes.png')
    plot_ad(rd, f'w{c["w"]} / {mf}: (a, d) step, base taper shape', od / 'sweep_ad.png')
    rows = design_rows(str(rd), int(mf[:2]))
    write_csv(od / 'sweep_designs.csv', rows)

    gap_opt = (info['opt_X_band1'], info['opt_X_band2'])
    gw = (gap_opt[1] - gap_opt[0]) / np.mean(gap_opt)
    yz = info['mech_YZ_gap_with_fb']
    md = f"""# Best {mf} device: w {c['w']} nm, d {F['d']:.2f}, ξ {F['xi']:g}, χ {F['chi']:g}, a {F['a']:.1f} nm

Final {mf}-minimum-feature device of the 1D nanobeam OMC track (diamond, t {c['t']} nm, suspended), selected by
`scripts/cavity_designs.py` (fabricable, breathing localization ≥ {CD.LOC_MIN}, sidewall ratio S ≥ {CD.S_MIN},
breathing ≤ {CD.F_TARGET:g} GHz first by highest optical Q). COMSOL confirmation solve: `{rd}/data/confirm{F['rank']}.npz`.

## Geometry
| | |
|---|---|
| beam width w / thickness t | {c['w']} / {c['t']} nm |
| mirror period a | {F['a']:.1f} nm |
| mirror hole hx × hy | {cfg['hx_m']:.1f} × {cfg['hy_m']:.1f} nm (hx/a {c['hx_a']}, hy/w {c['hy_w']}) |
| taper | Chan thesis: d {F['d']:.2f}, M {cfg['M']}, η {cfg['eta']:g}, ξ {F['xi']:g}, χ {F['chi']:g}; {cfg['n_mirror']} mirror cells per side |
| center cell | a {float(B['defect_a']):.1f}, hx {float(B['defect_hx']):.1f}, hy {float(B['defect_hy']):.1f} nm |
| min features | bridge {float(z['bridge']):.1f}, rail {float(z['rail']):.1f}, hole {float(z['hole']):.1f} nm (min {min(mfe.values()):.1f}) |

## Optical cavity mode
| | |
|---|---|
| resonance | **{lam:.2f} nm** ({C_NM_THZ / lam:.2f} THz) |
| optical Q (radiation, COMSOL) | **{Q:.2e}** |
| localization (∫\\|E\\|² near center) | {float(z['loc_opt'][int(z['i_opt']) - 1]):.2f} |

## Mechanical breathing mode
| | |
|---|---|
| frequency | **{fb:.3f} GHz** |
| mechanical Q | **not computed**: the mechanical model is clamped with no mechanical PML, so its eigenvalues are real (any Q it prints is numerical noise). A physical Q_m needs a mechanical PML / support / shield model. Breathing localization stands in for it. |
| localization | {float(z['loc_mech'][ib]):.2f} |
| sidewall coherence B / sidewall ratio S | {float(z['B'][ib]):.2f} / {float(z['S'][ib]):.2f} (clean breathing: B > 0.5, S ≈ 1) |
| effective mass (max \\|u\\| normalization) | {meff * 1e18:.0f} fg |
| zero-point motion x_zpf | {xzpf * 1e15:.1f} fm |
| thermal occupation n_th | {nth[0.1]:.2g} (0.1 K), {nth[1.7]:.2g} (1.7 K), {nth[4.0]:.2g} (4 K) |

## Mirror-cell band gaps (`mirror_bands.png`)
Optics (TE-like, y-even = cavity family, at X):
- dielectric band {gap_opt[0]:.1f} THz ({C_NM_THZ / gap_opt[0]:.0f} nm), next mode {gap_opt[1]:.1f} THz ({C_NM_THZ / gap_opt[1]:.0f} nm):
  gap {gap_opt[1] - gap_opt[0]:.1f} THz ({100 * gw:.0f} %); cavity mode at {C_NM_THZ / lam:.1f} THz sits {C_NM_THZ / lam - gap_opt[0]:.1f} THz above the band edge
- air light line at X {info['opt_light_line_X']:.0f} THz (gap below it)
- center (defect) cell band edge at X: {info['defect_fX']:.1f} THz
- y-odd family lowest at X: {info['opt_PMC_X_lowest']:.1f} THz ({C_NM_THZ / info['opt_PMC_X_lowest']:.0f} nm), {'above' if info['opt_PMC_X_lowest'] > C_NM_THZ / lam else 'BELOW'} the cavity mode

Mechanics:
- breathing class (Y+Z+) quasi-gaps below 30 GHz: {fmt_gaps(info['mech_YZ_gaps'], 'GHz')}
- breathing mode {fb:.2f} GHz {'inside the Y+Z+ quasi-gap ' + f'{yz[0]:.2f}–{yz[1]:.2f} GHz' if yz else 'NOT inside a Y+Z+ quasi-gap: it overlaps a breathing-class band of the mirror cell, so the mirror does not forbid it from leaking along the beam. Its confinement over the simulated beam (localization above) comes from the taper and the finite mirror; the real Q_m is the open question this raises.'}
- complete gap (all four symmetry classes) below 30 GHz: {fmt_gaps(info['mech_complete_gaps'], 'GHz')}

## Sweep that found it
Pipeline `{rd}`: (a, d) step with the base taper shape → 619 nm line a(d) → taper shapes (ξ, χ) on that line.
`sweep_ad.png` (a, d) step, `sweep_shapes.png` shape maps (outlined = base shape, hatched = below min feature,
red slash = not a breathing mode), `sweep_designs.csv` every design on the 619 nm line with flags and rank (rank 1 = this device).
Comparison across all widths: `../selection.png`, `../design_space.png`, `../all_designs.csv`.

## Figures
- `modes.png`: optical Ey on the z = 0 midplane; breathing mode on the deformed top face (color \\|u\\|)
- `mode_spectrum.png`: every optical and mechanical mode of the solve; stars = cavity / breathing modes
- `mirror_bands.png`: mirror-cell bands, optics and mechanics
"""
    (od / 'summary.md').write_text(md)
    json.dump(dict(F, slug=slug, lam_nm=lam, Q_opt=Q, f_breath_GHz=fb, loc_mech=float(z['loc_mech'][ib]),
                   S=float(z['S'][ib]), B=float(z['B'][ib]), meff_fg=meff * 1e18, x_zpf_fm=xzpf * 1e15,
                   min_features=dict(bridge=float(z['bridge']), rail=float(z['rail']), hole=float(z['hole'])),
                   bands={k: v for k, v in info.items()}, Q_mech=None),
              open(od / 'summary.json', 'w'), indent=1, default=float)
    print('wrote', od)
    return slug, F, lam, Q, fb, float(z['loc_mech'][ib]), min(mfe.values()), yz


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    devs = [device(mf) for mf in ('60nm', '80nm')]
    S.selection_table(PIPES, OUT / 'selection.png')
    S.design_space(PIPES, OUT / 'design_space.png')
    allrows = []
    for label, rd, mf in PIPES:
        for r in design_rows(rd, mf):
            allrows.append(dict(pipeline=label, **r))
    write_csv(OUT / 'all_designs.csv', allrows)
    lines = ['# Best 1D nanobeam OMC devices (diamond, 619 nm, t 120 nm)', '',
             'Generated by `python best_devices/make_best_devices.py` from the COMSOL results (pull the data first).', '',
             '| device | w (nm) | a (nm) | taper | λ (nm) | optical Q | breathing (GHz) | localization | mech. Q | min feature (nm) |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for slug, F, lam, Q, fb, loc, mfe, yz in devs:
        lines.append(f"| [{slug}]({slug}/summary.md) | {F['cell']['w']} | {F['a']:.1f} | d {F['d']:.2f}, ξ {F['xi']:g}, χ {F['chi']:g} | "
                     f"{lam:.2f} | {Q:.1e} | {fb:.2f} | {loc:.2f} | not computed | {mfe:.0f} |")
    lines += ['', '- `selection.png`: best design per width and minimum feature (green = selected).',
              '- `design_space.png`: every fabricable 619 nm design, breathing vs optical Q.',
              '- `all_designs.csv`: every design on the 619 nm line from all six pipelines, with flags and rank.',
              '- Mechanical Q is not computed for any device: the mechanical model is clamped with no PML, so its eigenvalues are real.', '']
    (OUT / 'README.md').write_text('\n'.join(lines))
    print('wrote', OUT / 'README.md')
