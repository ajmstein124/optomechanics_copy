"""
plot_gapconf.py  (Mac)  -- runs/surrogate_explore
Review figures for the gap-confined designs (data from gapconf_figs.py; user 2026-10-20).
Per design, gapconf/figures/<tag>.png:
  top:    mirror-cell bands Gamma -> X with the cavity modes drawn where they sit
          optics: cavity family (y0 PEC) solid, y0 PMC grey, center cell dashed, light cone shaded, cavity mode red
          mechanics: breathing class Y+Z+ red, other classes grey, center cell Y+Z+ dashed, Y+Z+ gap shaded,
                     breathing mode green (other localized breathing-like modes thin green)
  below (same x axis): optical Ey | breathing mode on the deformed top face (|u|) | strain on the midplane:
          volumetric strain eXX+eYY+eZZ and eXX-eYY, as zero-point strain (x_zpf from m_eff), optical |E| = 50 % contour
Plus gapconf/figures/overview_bands.png (all designs, mechanics) and overview_fields.png (optics + breathing mode).
Usage: python runs/surrogate_explore/plot_gapconf.py [--pull]
"""
import json
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
from matplotlib.patches import Ellipse
from scipy.interpolate import griddata

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from cavity_taper import layout   # noqa: E402

G = ROOT / 'runs/surrogate_explore/gapconf'
FIG = G / 'figures'; FIG.mkdir(exist_ok=True)
TAGS = ['w650_m186_c455_d086', 'w650_m186_c455_d118', 'w650_m192_hy66_c455_d146', 'w700_m186_c490_d118',
        'w700_m198_c420_d172', 'w700_m192_c420_d146', 'w700_m186_c420_d118']
XL, AMP = 3000.0, 50.0
HBAR, C = 1.054571817e-34, 299792458.0

if __name__ == '__main__' and '--pull' in sys.argv:
    for t in TAGS:
        for f in ('fields.npz', 'bands.npz', 'figsolve.npz'):
            subprocess.run(f'scp -q -i ~/.ssh/id_ed25519 "<USER>@<COMSOL_HOST>:C:/Users/abby/comsol/runs/surrogate_explore/gapconf/{t}/data/{f}" "{G / t / "data"}/"',
                           shell=True, stderr=subprocess.DEVNULL)


# ------------------------------------------------------------------ geometry / field helpers
def lay_of(c):
    return layout(c['a_m'], c['hx_m'], c['hy_m'], c['M'], c['n_mirror'], c['d'], c['eta'], c['xi'], c['chi'])


def outline(ax, lay, w, color='k', lw=0.5, fill=True):
    xl, w = XL / 1e3, w / 1e3
    for s in (1, -1):
        ax.plot([-xl, xl], [s * w / 2] * 2, color=color, lw=lw)
    for xc, hx, hy in zip(lay['x'] / 1e3, lay['hx'] / 1e3, lay['hy'] / 1e3):
        for s in ((1, -1) if xc > 0 else (1,)):
            if abs(xc) <= xl:
                ax.add_patch(Ellipse((s * xc, 0), hx, hy, fill=fill, fc='w', ec=color, lw=lw))


def in_hole(x, y, lay):
    h = np.zeros_like(x, bool)
    for xc, hx, hy in zip(lay['x'], lay['hx'], lay['hy']):
        for s in (1, -1):
            h |= ((x - s * xc) / (hx / 2)) ** 2 + (y / (hy / 2)) ** 2 < 1
    return h


def unfold(xyz, val, sx, sy):
    x, y = xyz[:, 0], xyz[:, 1]
    return (np.concatenate([x, -x, x, -x]), np.concatenate([y, y, -y, -y]),
            np.concatenate([val, sx * val, sy * val, sx * sy * val]))


def grid(X, Y, V, ymax, lay=None, n=(1200, 220)):
    gx = np.linspace(-XL, XL, n[0]); gy = np.linspace(-ymax, ymax, n[1])
    GX, GY = np.meshgrid(gx, gy)
    sel = np.abs(X) <= XL + 150
    g = griddata((X[sel], Y[sel]), V[sel], (GX, GY), method='linear')
    if lay is not None:
        g[in_hole(GX, GY, lay) | (np.abs(GY) > ymax)] = np.nan
    return gx, gy, g


def deformed(ax, xyz, uvw, lay, w):
    x, y = xyz[:, 0], xyz[:, 1]
    u, v, wz = uvw.T
    X = np.concatenate([x, -x, x, -x]); Y = np.concatenate([y, y, -y, -y])
    U = np.concatenate([u, -u, u, -u]); V = np.concatenate([v, v, -v, -v]); M = np.sqrt(np.tile(u**2 + v**2 + wz**2, 4))
    sel = np.abs(X) <= XL + 200
    X, Y, U, V, M = X[sel], Y[sel], U[sel], V[sel], M[sel]
    sc = AMP / M.max()
    GX, GY = np.meshgrid(np.linspace(-XL, XL, 1500), np.linspace(-w / 2, w / 2, 140))
    out = []
    for q in (U, V, M):
        g = griddata((X, Y), q, (GX, GY), method='linear'); bad = ~np.isfinite(g)
        g[bad] = griddata((X, Y), q, (GX[bad], GY[bad]), method='nearest'); out.append(g)
    GU, GV, GM = out
    t0 = mtri.Triangulation(GX.ravel(), GY.ravel())
    tri = mtri.Triangulation((GX + sc * GU).ravel() / 1e3, (GY + sc * GV).ravel() / 1e3, t0.triangles)
    tri.set_mask(in_hole(GX.ravel()[t0.triangles].mean(1), GY.ravel()[t0.triangles].mean(1), lay))
    tp = ax.tripcolor(tri, (GM / GM.max()).ravel(), cmap='inferno', shading='gouraud', vmin=0, vmax=1)
    outline(ax, lay, w, color='0.6', lw=0.5, fill=False)
    return tp


# ------------------------------------------------------------------ bands
def clean_bands(F):
    """F (n_k, n_band) Hz -> GHz, rigid k = 0 modes removed, NaN padded."""
    F = np.sort(F, axis=1) / 1e9
    return np.where(F > 0.5, F, np.nan)


def yz_gap(F, k):
    """Breathing-class quasi-gap (band 1 max over k, band 2 min over k); band 1 is 0 at Gamma."""
    lo, hi = 0.0, np.inf
    for ik in range(len(k)):
        r = F[ik][np.isfinite(F[ik])]
        if k[ik] == 0:
            hi = min(hi, r[0])
        else:
            lo, hi = max(lo, r[0]), min(hi, r[1])
    return lo, hi


def plot_bands(axo, axm, B, S, lam, title=True):
    k = B['mirror_k_frac']; kc = B['center_k_frac']
    # optics
    fo = B['mirror_f_opt'] / 1e12; fc = B['center_f_opt'] / 1e12
    a = float(B['mirror_cell'][0]); ac = float(B['center_cell'][0])
    ll = C * (k * np.pi / (a * 1e-9)) / (2 * np.pi) / 1e12
    llc = C * (kc * np.pi / (ac * 1e-9)) / (2 * np.pi) / 1e12
    fo = np.where(fo < ll[:, None, None], fo, np.nan)        # guided (below the light line) only; box modes dropped
    fc = np.where(fc < llc[:, None, None], fc, np.nan)
    if axo is not None:
        axo.fill_between(k, ll, 900, color='0.88', lw=0, label='light cone')
        for j in range(fo.shape[2]):
            axo.plot(k, fo[:, 1, j], color='0.7', lw=0.7, label='mirror, y-odd class' if j == 0 else None)
        for j in range(fo.shape[2]):
            axo.plot(k, fo[:, 0, j], color='C0', lw=1.3, label='mirror, cavity class' if j == 0 else None)
        for j in range(fc.shape[2]):
            axo.plot(kc, fc[:, 0, j], color='C0', lw=1.0, ls='--', label='center cell' if j == 0 else None)
        b1, b2 = (list(np.sort(fo[-1, 0][np.isfinite(fo[-1, 0])])) + [ll[-1]])[:2]
        axo.axhspan(b1, b2, color='C0', alpha=0.08, lw=0)
        fcav = C / (lam * 1e-9) / 1e12
        axo.axhline(fcav, color='r', lw=1.6, label=f'cavity mode {lam:.1f} nm')
        axo.set_ylim(fcav - 90, fcav + 110); axo.set_xlim(0, 1)
        axo.set_xticks([0, 1]); axo.set_xticklabels(['Γ', 'X']); axo.set_ylabel('frequency (THz)')
        axo.legend(fontsize=6.5, loc='upper left', framealpha=0.9)
        if title:
            axo.set_title('optics: mirror-cell bands', fontsize=9)
    # mechanics
    fm = B['mirror_f_mech']; fmc = B['center_f_mech']
    for ic, name in ((1, 'Y−Z+'), (2, 'Y+Z−'), (3, 'Y−Z−')):
        F = clean_bands(fm[:, ic])
        for j in range(F.shape[1]):
            axm.plot(k, F[:, j], color='0.75', lw=0.7, label='other classes' if (ic == 1 and j == 0) else None)
    F = clean_bands(fm[:, 0])
    for j in range(F.shape[1]):
        axm.plot(k, F[:, j], color='C3', lw=1.4, label='mirror, breathing class (Y+Z+)' if j == 0 else None)
    Fc = clean_bands(fmc[:, 0])
    for j in range(Fc.shape[1]):
        axm.plot(kc, Fc[:, j], color='C3', lw=1.0, ls='--', label='center cell, Y+Z+' if j == 0 else None)
    lo, hi = yz_gap(F, k)
    axm.axhspan(lo, hi, color='C3', alpha=0.09, lw=0, label=f'Y+Z+ gap {lo:.2f}–{hi:.2f} GHz')
    fb, others = S['fb'], S['others']
    for f_ in others:
        axm.axhline(f_, color='g', lw=0.7, ls=':')
    axm.axhline(fb, color='g', lw=1.8, label=f'breathing mode {fb:.2f} GHz')
    axm.set_ylim(0, 16); axm.set_xlim(0, 1)
    axm.set_xticks([0, 1]); axm.set_xticklabels(['Γ', 'X']); axm.set_ylabel('frequency (GHz)')
    axm.legend(fontsize=6.5, loc='upper left', framealpha=0.9)
    if title:
        axm.set_title('mechanics: mirror-cell bands', fontsize=9)
    return lo, hi


def solve_summary(zs):
    ok = (zs['loc_mech'] >= 0.8) & (zs['B'] > 0.5) & (np.nan_to_num(zs['S']) >= 0.7)
    f = np.sort(zs['f_mech'][ok]) / 1e9
    return dict(fb=f[0], others=list(f[1:4]))


# ------------------------------------------------------------------ per design
def main():
    rows = []
    for tag in TAGS:
        dd = G / tag / 'data'
        if not (dd / 'fields.npz').exists() or not (dd / 'bands.npz').exists():
            print(f'{tag}: pending'); continue
        z = np.load(dd / 'fields.npz'); B = np.load(dd / 'bands.npz'); zs = np.load(dd / 'figsolve.npz')
        c = json.loads(str(z['cfg'])); lay = lay_of(c); w = c['w']
        lam = C / float(z['f_opt']) * 1e9
        S = solve_summary(zs)
        head = (f"{tag}:  w {w:g}, a {c['a_m']:.1f}, mirror hx/a {c['hx_m']/c['a_m']:.2f} hy/w {c['hy_m']/w:.2f}, "
                f"taper d {c['d']}, ξ {c['xi']:g}, χ {c['chi']:g}")

        fig = plt.figure(figsize=(15, 14))
        gs = fig.add_gridspec(5, 2, height_ratios=[2.6, 1, 1, 1, 1], hspace=0.38, wspace=0.18, top=0.93, bottom=0.04)
        lo, hi = plot_bands(fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), B, S, lam)
        rows.append(dict(tag=tag, lam=lam, Q=float(z['Q_opt']), fb=S['fb'], lo=lo, hi=hi, c=c))

        # optical Ey
        ax = fig.add_subplot(gs[1, :])
        X, Y, V = unfold(z['opt_xyz'], z['opt_val'][:, 0], -1, 1)
        gx, gy, Gm = grid(X, Y, V, w / 2 + 400); Gm /= np.nanmax(np.abs(Gm))
        pm = ax.pcolormesh(gx / 1e3, gy / 1e3, Gm, cmap='RdBu_r', vmin=-1, vmax=1, shading='auto', rasterized=True)
        outline(ax, lay, w)
        fig.colorbar(pm, ax=ax, fraction=0.012, pad=0.005, label='Ey (norm.)')
        ax.set_title(f'optical mode, Ey (z = 0): {lam:.2f} nm, Q {float(z["Q_opt"]):.2g}', fontsize=9)

        # breathing displacement
        ax = fig.add_subplot(gs[2, :])
        tp = deformed(ax, z['mech_xyz'], z['mech_val'], lay, w)
        ax.set_title(f'breathing mode, deformed top face (|u|, peak drawn as {AMP:g} nm): {float(z["f_breath"])/1e9:.2f} GHz, '
                     f'localization {float(z["loc_breath"]):.2f}', fontsize=9)
        fig.colorbar(tp, ax=ax, fraction=0.012, pad=0.005, label='|u| (norm.)')

        # strain (midplane), zero-point units
        meff = float(z['meff']); om = 2 * np.pi * float(z['f_breath'])
        xzpf = np.sqrt(HBAR / (2 * meff * om)) if np.isfinite(meff) and meff > 0 else np.nan
        umax_m = float(z['umax']) * 1e-9                     # COMSOL exports u in the model length unit (nm)
        scale = xzpf / umax_m if np.isfinite(xzpf) else 1.0 / umax_m
        sv = z['strain_mid_val']
        X, Y, Vol = unfold(z['strain_mid_xyz'], (sv[:, 0] + sv[:, 1] + sv[:, 2]) * scale, 1, 1)
        _, _, Dif = unfold(z['strain_mid_xyz'], (sv[:, 0] - sv[:, 1]) * scale, 1, 1)
        Xo, Yo, Eo = unfold(z['opt_xyz'], z['opt_val'][:, 1], 1, 1)
        gxo, gyo, GE = grid(Xo, Yo, Eo ** 2, w / 2, lay); GE /= np.nanmax(GE)
        unit = 'zero-point strain' if np.isfinite(xzpf) else 'strain (per m of max |u|)'
        for r, (V, lab) in enumerate(((Vol, 'volumetric strain εxx+εyy+εzz'), (Dif, 'εxx − εyy'))):
            ax = fig.add_subplot(gs[3 + r, :])
            gx, gy, Gs = grid(X, Y, V, w / 2, lay)
            vm = np.nanmax(np.abs(Gs))
            pm = ax.pcolormesh(gx / 1e3, gy / 1e3, Gs, cmap='PuOr_r', vmin=-vm, vmax=vm, shading='auto', rasterized=True)
            ax.contour(gxo / 1e3, gyo / 1e3, GE, levels=[0.5], colors='k', linewidths=0.8)
            outline(ax, lay, w, fill=False)
            fig.colorbar(pm, ax=ax, fraction=0.012, pad=0.005, format='%.1e', label=unit)
            ax.set_title(f'breathing-mode {lab} on the midplane (peak {vm:.2g}); black: optical |E|² = 50 %', fontsize=9)
        for ax in fig.axes[2:]:
            if ax.get_label() == '<colorbar>':
                continue
            ax.set_aspect('equal'); ax.set_xlim(-XL / 1e3, XL / 1e3); ax.set_ylim(-0.43, 0.43); ax.set_xlabel('x (µm)'); ax.set_ylabel('y (µm)')
        fig.suptitle(head + f'\nx_zpf {xzpf*1e15:.2f} fm, m_eff {meff*1e18:.0f} fg' if np.isfinite(xzpf) else head, fontsize=10, y=0.985)
        fig.savefig(FIG / f'{tag}.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f'wrote {FIG / tag}.png  (breathing {S["fb"]:.2f} in gap {lo:.2f}-{hi:.2f})')

    # ------------------------------------------------------------------ overviews
    if rows:
        n = len(rows); nc = min(4, n); nr = int(np.ceil(n / nc))
        fig, axs = plt.subplots(nr, nc, figsize=(4 * nc, 4.2 * nr), squeeze=False)
        for ax, r in zip(axs.flat, rows):
            dd = G / r['tag'] / 'data'
            plot_bands(None, ax, np.load(dd / 'bands.npz'), solve_summary(np.load(dd / 'figsolve.npz')), r['lam'], title=False)
            ax.set_title(f"{r['tag']}\nQ {r['Q']:.2g}, breathing {r['fb']:.2f} GHz", fontsize=8)
            ax.legend().set_visible(False)
        for ax in list(axs.flat)[n:]:
            ax.axis('off')
        axs.flat[0].legend(fontsize=6, loc='upper left')
        fig.suptitle('Mirror-cell breathing-class bands (red) and the cavity breathing mode (green); shaded: Y+Z+ gap', fontsize=10)
        fig.tight_layout(); fig.savefig(FIG / 'overview_bands.png', dpi=150); plt.close(fig)

        fig, axs = plt.subplots(n, 2, figsize=(16, 1.9 * n + 0.5), squeeze=False)
        for i, r in enumerate(rows):
            z = np.load(G / r['tag'] / 'data' / 'fields.npz'); c = r['c']; lay = lay_of(c); w = c['w']
            X, Y, V = unfold(z['opt_xyz'], z['opt_val'][:, 0], -1, 1)
            gx, gy, Gm = grid(X, Y, V, w / 2 + 400); Gm /= np.nanmax(np.abs(Gm))
            axs[i, 0].pcolormesh(gx / 1e3, gy / 1e3, Gm, cmap='RdBu_r', vmin=-1, vmax=1, shading='auto', rasterized=True)
            outline(axs[i, 0], lay, w)
            axs[i, 0].set_title(f"{r['tag']}: Ey, {r['lam']:.2f} nm, Q {r['Q']:.2g}", fontsize=8)
            deformed(axs[i, 1], z['mech_xyz'], z['mech_val'], lay, w)
            axs[i, 1].set_title(f"breathing {r['fb']:.2f} GHz (gap {r['lo']:.2f}–{r['hi']:.2f})", fontsize=8)
            axs[i, 1].set_ylim(-w / 2e3 - 0.08, w / 2e3 + 0.08)
            for ax in axs[i]:
                ax.set_aspect('equal'); ax.set_xlim(-XL / 1e3, XL / 1e3); ax.tick_params(labelsize=7)
        fig.tight_layout(); fig.savefig(FIG / 'overview_fields.png', dpi=140); plt.close(fig)
        print('wrote overview_bands.png, overview_fields.png')


if __name__ == '__main__':
    main()
