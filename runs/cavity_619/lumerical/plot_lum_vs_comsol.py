"""
plot_lum_vs_comsol.py  (Mac)
Lumerical replicas of the COMSOL optics heat maps, side by side, from a finished .lsf sweep
(make_lsf.py: <name>_points.json here + <name>_summary.txt written by the .lsf into its run folder; --pull fetches
it from the old PC DESKTOP-BBQLCD3, where the Lumerical sweeps run (runs/cavity_619/lumerical/oldpc/)).
  (a, d) sweep  (lum_ad_*): rows COMSOL / Lumerical; columns resonance (nm), log10 Q, over the a x d grid
  shape sweep   (lum_*shape*): per method, each (d, xi, chi) shape reduced to the 619.4 nm line by linear
                interpolation in a (as scripts/cavity_designs.py); maps of Q at 619 nm and of the resonance at
                COMSOL's 619 nm period (shows the solver offset directly)
  all           parity plots: Lumerical vs COMSOL resonance and Q per point
Points Lumerical has not run yet are grey; works on partial sweeps.
Usage (from project root):
    python runs/cavity_619/lumerical/plot_lum_vs_comsol.py lum_ad_mf60 [--pull]
Output: runs/cavity_619/lumerical/<name>_vs_comsol.png
"""
import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path('runs/cavity_619/lumerical')
KEY = str(Path('~/.ssh/id_ed25519').expanduser())
# Lumerical runs happen on the old PC DESKTOP-BBQLCD3 (user 2026-10-15; never on the COMSOL machine)
PULL_FROM = '<USER>@<LUMERICAL_HOST>:C:/Users/JVadmin/Documents/optomechanics/lumerical'
LAM0 = 619.4


def load(name, pull):
    pts = json.load(open(HERE / f'{name}_points.json'))['points']
    summ = HERE / f'{name}_summary.txt'
    if pull:
        subprocess.run(['scp', '-q', '-i', KEY, f'{PULL_FROM}/{name}_summary.txt', str(summ)])
    lum = {}
    if summ.exists():
        for line in summ.read_text().splitlines()[1:]:
            v = line.split()
            if len(v) >= 7 and float(v[6]) > 0:
                lum[int(v[0])] = (float(v[5]), float(v[6]))         # point -> (lambda nm, Q)
    for i, q in enumerate(pts, 1):
        q['lum_lam'], q['lum_Q'] = lum.get(i, (np.nan, np.nan))
        if 'comsol_lam_nm' not in q:                                # lum_ad_mf60 predates the stored COMSOL values
            q['comsol_lam_nm'], q['comsol_Q'] = comsol_ad(q)
    return pts, len(lum)


def comsol_ad(q):
    fn = Path(f"runs/cavity_619/data/ad_a{int(q['a'])}_d{int(round(q['d'] * 100)):02d}.npz")
    if not fn.exists():
        return np.nan, np.nan
    sys.path.insert(0, 'scripts')
    from cavity_designs import opt_mode
    return opt_mode(np.load(fn))


def grid_maps(fig, gs_row, pts, keyl, keyq, label):
    A = sorted({q['a'] for q in pts}); D = sorted({q['d'] for q in pts})
    L = np.full((len(D), len(A)), np.nan); Q = L.copy()
    for q in pts:
        L[D.index(q['d']), A.index(q['a'])] = q[keyl]; Q[D.index(q['d']), A.index(q['a'])] = q[keyq]
    ext = (A[0] - 2.5, A[-1] + 2.5, -0.5, len(D) - 0.5)
    for j, (Z, cm, (lo, hi), cb) in enumerate(((L - LAM0, 'RdBu_r', (-60, 60), 'resonance - 619 nm (nm)'),
                                               (np.log10(Q), 'viridis', (3, 8), 'log$_{10}$ Q'))):
        ax = fig.add_subplot(gs_row[j]); c = plt.get_cmap(cm).copy(); c.set_bad('0.88')
        im = ax.imshow(np.ma.masked_invalid(Z), origin='lower', aspect='auto', cmap=c, vmin=lo, vmax=hi, extent=ext)
        raw = L if j == 0 else Q
        for i, d in enumerate(D):
            for k, a in enumerate(A):
                if np.isfinite(raw[i, k]):
                    ax.text(a, i, f'{raw[i, k]:.0f}' if j == 0 else f'{raw[i, k]:.0e}'.replace('e+0', 'e'),
                            ha='center', va='center', fontsize=6)
        ax.set_yticks(range(len(D)), [f'{d:.2f}' for d in D]); ax.set_xlabel('mirror period a (nm)'); ax.set_ylabel('taper depth d')
        ax.set_title(f'{label}: ' + ('resonance (nm)' if j == 0 else 'optical Q'), fontweight='bold')
        fig.colorbar(im, ax=ax, label=cb, fraction=0.046)


def on_line(pts, keyl, keyq, a_ref=None):
    """Per shape: (Q at 619.4 nm, resonance at a_ref[shape]) by linear interpolation in a."""
    groups = {}
    for q in pts:
        if np.isfinite(q[keyl]):
            groups.setdefault((q['d'], q['xi'], q['chi']), []).append(q)
    out = {}
    for key, G in groups.items():
        G = sorted(G, key=lambda q: q['a'])
        if len(G) < 2:
            continue
        A = np.array([q['a'] for q in G]); L = np.array([q[keyl] for q in G]); Q = np.log10([q[keyq] for q in G])
        a619 = float(np.interp(LAM0, L[np.argsort(L)], A[np.argsort(L)])) if L.min() < LAM0 < L.max() else np.nan
        ar = a_ref.get(key, np.nan) if a_ref else a619
        out[key] = dict(a619=a619, Q=10 ** np.interp(a619, A, Q) if np.isfinite(a619) else np.nan,
                        lam_at_ref=float(np.interp(ar, A, L)) if np.isfinite(ar) and A.min() <= ar <= A.max() else np.nan)
    return out


def shape_maps(fig, gs, pts):
    C = on_line(pts, 'comsol_lam_nm', 'comsol_Q')
    Lm = on_line(pts, 'lum_lam', 'lum_Q', a_ref={k: v['a619'] for k, v in C.items()})
    Ds = sorted({k[0] for k in C}); XI = sorted({k[1] for k in C}); CHI = sorted({k[2] for k in C})
    rows = [(C, 'Q', 'COMSOL: Q at 619 nm'), (Lm, 'Q', 'Lumerical: Q at its 619 nm a'),
            (Lm, 'lam_at_ref', 'Lumerical: resonance at COMSOL 619 nm a')]
    for r, (S, key, title) in enumerate(rows):
        for j, d in enumerate(Ds):
            ax = fig.add_subplot(gs[r, j])
            Z = np.full((len(XI), len(CHI)), np.nan)
            for (dd, xi, chi), v in S.items():
                if dd == d:
                    Z[XI.index(xi), CHI.index(chi)] = np.log10(v[key]) if key == 'Q' else v[key] - LAM0
            cm = plt.get_cmap('viridis' if key == 'Q' else 'RdBu_r').copy(); cm.set_bad('0.88')
            im = ax.imshow(np.ma.masked_invalid(Z), origin='lower', aspect='auto', cmap=cm,
                           vmin=3 if key == 'Q' else -15, vmax=8 if key == 'Q' else 15)
            for (dd, xi, chi), v in S.items():
                if dd == d and np.isfinite(v[key]):
                    ax.text(CHI.index(chi), XI.index(xi), f'{v[key]:.0e}'.replace('e+0', 'e') if key == 'Q' else f'{v[key]:.1f}',
                            ha='center', va='center', fontsize=7)
            ax.set_xticks(range(len(CHI)), [f'{c:g}' for c in CHI]); ax.set_yticks(range(len(XI)), [f'{x:g}' for x in XI])
            ax.set_title(f'{title}\nd = {d:.2f}', fontsize=9, fontweight='bold')
            ax.set_xlabel('χ'); ax.set_ylabel('ξ')
            if j == len(Ds) - 1:
                fig.colorbar(im, ax=ax, fraction=0.05, label='log$_{10}$ Q' if key == 'Q' else 'nm')


def parity(fig, gs_row, pts):
    for j, (kc, kl, lab, log) in enumerate((('comsol_lam_nm', 'lum_lam', 'resonance (nm)', False),
                                            ('comsol_Q', 'lum_Q', 'optical Q', True))):
        ax = fig.add_subplot(gs_row[j])
        x = np.array([q[kc] for q in pts], float); y = np.array([q[kl] for q in pts], float)
        ax.scatter(x, y, s=18, edgecolor='k', lw=0.4)
        ok = np.isfinite(x) & np.isfinite(y)
        lo, hi = (np.nanmin(np.r_[x, y][np.isfinite(np.r_[x, y])]), np.nanmax(np.r_[x, y][np.isfinite(np.r_[x, y])])) if ok.any() else (1, 2)
        ax.plot([lo, hi], [lo, hi], 'k--', lw=0.8)
        if log:
            ax.set_xscale('log'); ax.set_yscale('log')
        ax.set_xlabel(f'COMSOL {lab}'); ax.set_ylabel(f'Lumerical {lab}')
        if ok.any() and not log:
            dl = y[ok] - x[ok]; ax.set_title(f'resonance: Lumerical - COMSOL = {np.median(dl):+.2f} nm (median, {ok.sum()} pts)', fontsize=9)
        elif ok.any():
            ax.set_title(f'Q ratio Lumerical/COMSOL (median) = {np.median(y[ok] / x[ok]):.2g}', fontsize=9)


if __name__ == '__main__':
    name = sys.argv[1]
    pts, n_lum = load(name, '--pull' in sys.argv)
    is_ad = 'ad' in name.split('_')
    if is_ad:
        fig = plt.figure(figsize=(14, 13)); gs = fig.add_gridspec(3, 2)
        grid_maps(fig, gs[0, :].subgridspec(1, 2), pts, 'comsol_lam_nm', 'comsol_Q', 'COMSOL')
        grid_maps(fig, gs[1, :].subgridspec(1, 2), pts, 'lum_lam', 'lum_Q', 'Lumerical')
        parity(fig, gs[2, :].subgridspec(1, 2), pts)
    else:
        nd = len({q['d'] for q in pts})
        fig = plt.figure(figsize=(4.5 * nd + 1, 15)); gs = fig.add_gridspec(4, nd)
        shape_maps(fig, gs, pts)
        parity(fig, gs[3, :].subgridspec(1, 2), pts)
    fig.suptitle(f'{name}: Lumerical vs COMSOL  [{n_lum}/{len(pts)} Lumerical points]', fontsize=13, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = HERE / f'{name}_vs_comsol.png'
    fig.savefig(out, dpi=130, facecolor='white')
    print(f'wrote {out}')
