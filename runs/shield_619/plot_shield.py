"""
plot_shield.py  (Mac)  -- runs/shield_619
Figures for the cross phonon shield on the best gap-confined device (60nm_w650_d0.086_xi1.79_chi-6.97_gapconf):
  figures/cell_compare.png     shield cell bands: COMSOL (this folder) vs Dmitry cloud (runs/dmitry/shield1_dmitry), with the gap
  figures/structure.png        top view of the 1/8 model with the shield (beam, anchor pad, crosses, PML)
  figures/disp_maps.png        breathing-mode |u|^2 (log) on the top face, without / with shield (n_mirror 4 and 10 if present)
  figures/qm_table.png         Q_m vs mirror cells, without / with shield
Run: python runs/shield_619/plot_shield.py [--pull]
"""
import json
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from matplotlib.patches import Ellipse, Rectangle
from matplotlib.tri import Triangulation

sys.path.insert(0, 'scripts')
from cavity_taper import layout, beam_half_length  # noqa: E402

R = Path('runs/shield_619'); DD = R / 'data'; FG = R / 'figures'; FG.mkdir(exist_ok=True)
DMC = Path('runs/dmitry/shield1_dmitry/cells_dmitry')
CASES = [f'nm{n}_{s}{v}' for v in ('', '65') for s in ('noshield', 'shield') for n in (2, 4, 10)] + ['nm10_shield65_pml3k']
CELL = {'': dict(tag='a450_h390_w140', gap=(9.397, 11.472), label='a 450, h 390, w 140'),
        '65': dict(tag='a460_h395_w150', gap=None, label='a 460, h 395, w 150 (65 nm bridges)')}
FB = (9.81, 10.57)


def pull():
    for c in CASES:
        if not (DD / f'{c}.npz').exists():
            subprocess.run(['scp', '-q', '-i', str(Path.home() / '.ssh/id_ed25519'),
                            f'<USER>@<COMSOL_HOST>:C:/Users/abby/comsol/runs/shield_619/data/{c}.npz', str(DD)], check=False)


def path_x(k, a):
    k = k * a / np.pi; kx, ky = k[:, 0], k[:, 1]
    diag = (np.abs(kx - ky) < 1e-6) & (kx > 1e-9) & (kx < 1 - 1e-6)
    return np.where(diag, 2 + (1 - kx) * np.sqrt(2), np.where(ky < 1e-9, kx, 1 + ky))


def comsol_gap(F):
    lo = np.nanmax([np.nanmin(F[:, i]) for i in range(F.shape[1])] + [0]); hi = np.nanmin(np.nanmax(F, axis=(0, 2)))
    f = np.sort(F[np.isfinite(F)]); f = f[(f >= lo) & (f <= hi)]
    g = [(f[i], f[i + 1]) for i in range(len(f) - 1) if f[i + 1] - f[i] > 0.8 and f[i] < FB[0] < f[i + 1]]
    return g[0] if g else None


def cell_compare(v=''):
    C = CELL[v]; fn = DD / f"cross_{C['tag']}.npz"
    if not fn.exists():
        return None
    z = np.load(fn); K = z['k']; F = z['f'] / 1e9; a = int(C['tag'][1:4]) * 1e-9; DM = DMC / f"{C['tag']}_dmitry"
    gap = comsol_gap(F)
    x = path_x(K, a); L = 2 + np.sqrt(2); x[-1] = L          # last k point is Gamma at the end of the path
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    for ic, s in enumerate(('sym', 'antisym')):
        for j in range(F.shape[2]):
            ax.plot(x, F[ic, :, j], '-', color=('tab:blue', 'tab:red')[ic], lw=0.8, alpha=0.8,
                    label=f'COMSOL z-{s}' if j == 0 else None)
        A = np.loadtxt(DM / f'shield_dmitry_{s}.csv', delimiter=',', usecols=(0, 1, 2))
        ax.plot(path_x(A[:, :2], a), A[:, 2] / 1e9, 'o', mfc='none', ms=3.5, color=('tab:blue', 'tab:red')[ic],
                label=f'Dmitry cloud z-{s}')
    dm = []
    for ic, s in enumerate(('sym', 'antisym')):
        A = np.loadtxt(DM / f'shield_dmitry_{s}.csv', delimiter=',', usecols=(0, 1, 2))
        for ik, k in enumerate(K):
            fd = np.sort(A[(np.abs(A[:, 0] - k[0]) < 1) & (np.abs(A[:, 1] - k[1]) < 1), 2] / 1e9); fc = np.sort(F[ic, ik][np.isfinite(F[ic, ik])])
            m = min(len(fd), len(fc)); ok = fc[:m] > 0.1; dm += list((np.abs(fd[:m] - fc[:m]) / fc[:m])[ok])   # skip the zero-frequency modes at Gamma
    cmp_ = dict(n=len(dm), median=float(np.median(dm)), max=float(np.max(dm)))
    if gap:
        ax.axhspan(*gap, color='gold', alpha=0.35, lw=0, label=f'complete gap {gap[0]:.2f}–{gap[1]:.2f} GHz')
    for f, ls in zip(FB, ('-', '--')):
        ax.axhline(f, color='k', ls=ls, lw=1); ax.text(L * 0.99, f, f'cavity mode {f} GHz', ha='right', va='bottom', fontsize=7)
    for xv in (1, 2): ax.axvline(xv, color='0.7', lw=0.6)
    ax.set_xticks([0, 1, 2, L]); ax.set_xticklabels(['Γ', 'X', 'M', 'Γ']); ax.set_xlim(0, L); ax.set_ylim(0, 20)
    ax.set_ylabel('frequency (GHz)')
    ax.set_title(f"cross cell {C['label']}, fillet 20, t 120 nm: COMSOL vs Dmitry cloud "
                 f"(median |Δf/f| {cmp_['median']:.1e}, max {cmp_['max']:.1e})", fontsize=8)
    ax.legend(fontsize=6.5, loc='upper left', ncol=2)
    fig.tight_layout(); fig.savefig(FG / f'cell_compare{v}.png', dpi=170); plt.close(fig)
    json.dump(dict(cmp_, gap=gap), open(DD / f'cell_compare{v}.json', 'w'), indent=1)
    return cmp_


def load_case(c):
    fn = DD / f'{c}.npz'
    return np.load(fn, allow_pickle=True) if fn.exists() else None


def draw_structure(ax, cfg, sh, show_shield=True, alpha=1.0):
    lay = layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'], cfg['eta'], cfg['xi'], cfg['chi'])
    X = beam_half_length(lay, cfg['pad_x']); a = sh['a']; n = sh['n_pad'] + sh['Ns']; xo = sh.get('x_off', 0)
    Lc = xo + n * a; mo = sh['m_out']; dp = sh['d_pml']
    ax.add_patch(Rectangle((0, 0), X / 1e3, cfg['w'] / 2e3, color='0.7', alpha=alpha))
    ax.add_patch(Rectangle((X / 1e3, 0), (Lc + mo) / 1e3, (Lc + mo) / 1e3, color='0.7', alpha=alpha))
    ax.add_patch(Rectangle(((X + Lc + mo) / 1e3, 0), dp / 1e3, (Lc + mo + dp) / 1e3, color='tab:purple', alpha=0.25 * alpha))
    ax.add_patch(Rectangle((X / 1e3, (Lc + mo) / 1e3), (Lc + mo) / 1e3, dp / 1e3, color='tab:purple', alpha=0.25 * alpha))
    for j in range(len(lay['x'])):
        ax.add_patch(Ellipse((lay['x'][j] / 1e3, 0), lay['hx'][j] / 1e3, lay['hy'][j] / 1e3, color='white'))
    if show_shield:
        for i in range(n):
            for k in range(n):
                if i < sh['n_pad'] and k < sh['n_pad_y']:
                    continue
                cx, cy = (X + xo + (i + .5) * a) / 1e3, (k + .5) * a / 1e3
                for lx, ly in ((sh['h'], sh['w']), (sh['w'], sh['h'])):
                    ax.add_patch(Rectangle((cx - lx / 2e3, cy - ly / 2e3), lx / 1e3, ly / 1e3, color='white'))
    return X, Lc, mo, dp


def structure(v=''):
    J = json.load(open(R / 'cases.json')); cfg = dict(J['cavity'])
    sh = dict(J['shield'], h=390, w=140) if not v else dict(J['shield'], a=460, h=395, w=150, x_off=35)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    X, Lc, mo, dp = draw_structure(ax, cfg, sh)
    ax.text((X + Lc + mo + dp / 2) / 1e3, (Lc + mo) / 2e3, 'PML', ha='center', color='tab:purple', rotation=90)
    ax.text(X / 2e3, cfg['w'] / 2e3 + 0.12, 'nanobeam cavity (center at x = 0)', ha='center', fontsize=8)
    ax.text((X + 0.5 * sh['a']) / 1e3, 0.2, 'anchor\npad', ha='center', fontsize=7)
    ax.text((X + 3 * sh['a']) / 1e3, (Lc + mo) / 1e3 + 0.1, f"cross shield, {sh['Ns']} periods around the pad", ha='center', fontsize=8)
    ax.set_xlim(-0.1, (X + Lc + mo + dp) / 1e3 + 0.1); ax.set_ylim(-0.05, (Lc + mo + dp) / 1e3 + 0.05); ax.set_aspect('equal')
    ax.set_xlabel('x (µm)'); ax.set_ylabel('y (µm)')
    ax.set_title('Full structure, top view of the modeled 1/8 (mirror planes x = 0, y = 0, z = 0); 10 mirror cells'
                 + ('; 65 nm shield, lattice 35 nm from the trench' if v else ''), fontsize=9)
    fig.tight_layout(); fig.savefig(FG / f'structure{v}.png', dpi=170); plt.close(fig)


def disp_maps(v=''):
    pairs = [(n, f'nm{n}_noshield{v}', f'nm{n}_shield{v}') for n in (4, 10)]
    pairs = [p for p in pairs if load_case(p[1]) is not None and load_case(p[2]) is not None]
    if not pairs:
        return
    fig, axs = plt.subplots(len(pairs), 2, figsize=(12, 2.9 * len(pairs)), squeeze=False)
    for r, (n, c0, c1) in enumerate(pairs):
        for col, c in enumerate((c0, c1)):
            z = load_case(c); ax = axs[r, col]
            if 'top_xy' not in z.files:
                ax.set_title(f'{c}: no field export'); continue
            xy, tv = z['top_xy'] / 1e3, z['top_val']; u2 = tv[:, 3]; u2 = u2 / u2.max()
            tri = Triangulation(xy[:, 0], xy[:, 1])
            P_ = xy[tri.triangles]; e = np.max([np.hypot(*(P_[:, i] - P_[:, (i + 1) % 3]).T) for i in range(3)], axis=0)
            tri.set_mask(e > 0.05)                         # drop triangles spanning holes / the trench (> 50 nm edges)
            tc = ax.tripcolor(tri, np.clip(u2, 1e-12, 1), norm=LogNorm(1e-12, 1), cmap='magma', shading='gouraud')
            cfg = json.loads(str(z['cfg'])); sh = json.loads(str(z['shield']))
            ib = int(z['i_breath'])
            ax.set_title(f"{n} mirror cells, {'with' if 'noshield' not in c else 'no'} shield: "
                         f"{z['f'][ib-1]/1e9:.3f} GHz, Q_m {z['Q'][ib-1]:.2g}", fontsize=8)
            ax.set_aspect('equal'); ax.set_xlabel('x (µm)'); ax.set_ylabel('y (µm)')
            fig.colorbar(tc, ax=ax, label='|u|² (norm., log)', shrink=0.8)
    fig.tight_layout(); fig.savefig(FG / f'disp_maps{v}.png', dpi=170); plt.close(fig)


def qm_table(v=''):
    rows = []
    for n in (2, 4, 10):
        r = [n]
        for s in ('noshield', 'shield'):
            z = load_case(f'nm{n}_{s}{v}')
            if z is None or int(z['i_breath']) < 1:
                r += [np.nan, np.nan]
            else:
                ib = int(z['i_breath']); r += [z['f'][ib - 1] / 1e9, z['Q'][ib - 1]]
        rows.append(r)
    rows = [[x.item() if hasattr(x, 'item') else x for x in r] for r in rows]
    json.dump(rows, open(DD / f'qm_summary{v}.json', 'w'), indent=1)
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    n = [r[0] for r in rows]
    ax.semilogy(n, [r[2] for r in rows], 'o-', label='no shield (plain slab)')
    ax.semilogy(n, [r[4] for r in rows], 's-', label='cross shield (4 periods)' + (', 65 nm' if v else ''))
    ax.set_xlabel('mirror cells beyond the taper'); ax.set_ylabel('breathing-mode Q_m (anchor loss)')
    ax.set_xticks(n); ax.grid(alpha=0.3); ax.legend(fontsize=8)
    ax.set_title('9.81 GHz breathing mode, COMSOL, ideal geometry', fontsize=9)
    fig.tight_layout(); fig.savefig(FG / f'qm_table{v}.png', dpi=170); plt.close(fig)
    return rows


if __name__ == '__main__':
    if '--pull' in sys.argv:
        pull()
    for v in ('', '65'):
        print(v, cell_compare(v)); structure(v); disp_maps(v); print(qm_table(v))
