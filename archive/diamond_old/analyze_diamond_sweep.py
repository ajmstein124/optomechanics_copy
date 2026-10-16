"""
analyze_diamond_sweep.py  (runs locally on Mac)

Loads diamond 5x5 d/w sweep results and produces:
  1. Heatmaps: gap center (GHz) and gap width (GHz)
  2. Annotated band diagram for the center point (d=72nm, w=43nm)
  3. Annotated band diagrams for best and worst gap combos

Usage:
    python scripts/analyze_diamond_sweep.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scipy.io
from pathlib import Path

# Use v3 results if available (v3 fixes f0=5 GHz; v2 used f0=36 GHz and missed acoustic branches)
_v3 = Path('results') / 'diamond_mech_v3'
_v2 = Path('results') / 'diamond_mech_v2'
RESULTS     = _v3 if any(_v3.glob('*.mat')) else _v2
OUT         = Path('results') / 'analysis'
print(f'Loading from: {RESULTS}')
OUT.mkdir(parents=True, exist_ok=True)

d_nm = np.array([68, 70, 72, 74, 76])
w_nm = np.array([39, 41, 43, 45, 47])

BZ_LABELS = [r'$\Gamma$', 'M', 'K', r'$\Gamma$']
N_KS = 5  # segments; tick indices [0,4,8,12] (0-based)
BZ_TICKS = [1, N_KS, 2*N_KS-1, 3*N_KS-2]


def find_gap(freqs_arr):
    """Largest complete bandgap across all k-points. Returns (cen_GHz, wid_GHz, frac)."""
    sb = np.sort(np.real(freqs_arr), axis=1) * 1e-9
    best_cen, best_wid, best_frac = 0.0, 0.0, 0.0
    for n in range(sb.shape[1] - 1):
        top = sb[:, n].max()
        bot = sb[:, n + 1].min()
        if bot > top:
            cen = (top + bot) / 2
            wid = bot - top
            frac = wid / cen
            if wid > best_wid:
                best_cen, best_wid, best_frac = cen, wid, frac
    return best_cen, best_wid, best_frac


# ── Load all 25 combos ────────────────────────────────────────────────────────

gap_cen  = np.full((len(d_nm), len(w_nm)), np.nan)
gap_wid  = np.full((len(d_nm), len(w_nm)), np.nan)
gap_frac = np.full((len(d_nm), len(w_nm)), np.nan)
freqs_all = {}

for i, d in enumerate(d_nm):
    for j, w in enumerate(w_nm):
        p = RESULTS / f'diamond_Mech_bands_d_{d}nm_w_{w}nm_ii_13.mat'
        if not p.exists():
            # Try partial file from last completed k-point
            for kk in range(13, 0, -1):
                p2 = RESULTS / f'diamond_Mech_bands_d_{d}nm_w_{w}nm_ii_{kk}.mat'
                if p2.exists():
                    p = p2
                    break
        if p.exists():
            dat = scipy.io.loadmat(str(p))
            freqs = dat['freqs']
            gc, gw, gf = find_gap(freqs)
            gap_cen[i, j]  = gc
            gap_wid[i, j]  = gw
            gap_frac[i, j] = gf
            freqs_all[(d, w)] = freqs
        else:
            print(f'Missing: {p.name}')

print('Gap center (GHz):')
print(np.round(gap_cen, 2))
print('Gap width (GHz):')
print(np.round(gap_wid, 3))
print('Gap frac (%):')
print(np.round(gap_frac * 100, 1))

# ── Heatmaps ──────────────────────────────────────────────────────────────────

fig, axes = plt.subplots(1, 3, figsize=(14, 4))

for ax, data, title, unit, fmt in [
    (axes[0], gap_cen,       'Gap center frequency', 'GHz', '{:.1f}'),
    (axes[1], gap_wid,       'Gap width',            'GHz', '{:.2f}'),
    (axes[2], gap_frac*100,  'Fractional gap',       '%',   '{:.1f}'),
]:
    valid = data[~np.isnan(data)]
    vmin  = valid.min() * 0.97 if len(valid) else 0
    vmax  = valid.max() * 1.03 if len(valid) else 1
    cmap = plt.cm.RdYlGn.copy()
    cmap.set_bad('0.80')
    im = ax.imshow(data, origin='lower', cmap=cmap,
                   vmin=vmin, vmax=vmax, aspect='auto')
    ax.set_xticks(range(len(w_nm))); ax.set_xticklabels([f'{v}' for v in w_nm])
    ax.set_yticks(range(len(d_nm))); ax.set_yticklabels([f'{v}' for v in d_nm])
    ax.set_xlabel('arm width  w (nm)', fontsize=11)
    ax.set_ylabel('arm length  d (nm)', fontsize=11)
    ax.set_title(f'{title} ({unit})', fontsize=12)
    plt.colorbar(im, ax=ax, shrink=0.85, label=unit)
    for i in range(len(d_nm)):
        for j in range(len(w_nm)):
            v = data[i, j]
            txt = fmt.format(v) if not np.isnan(v) else '-'
            ax.text(j, i, txt, ha='center', va='center',
                    fontsize=9, fontweight='bold', color='k')

plt.suptitle('Diamond snowflake phononic sweep  (a=190nm, t=140nm)', fontsize=12)
plt.tight_layout()
out = OUT / 'diamond_sweep_heatmap.png'
plt.savefig(str(out), dpi=150, bbox_inches='tight')
print(f'\nSaved: {out}')
plt.close()


# ── Band diagram helper ───────────────────────────────────────────────────────

def plot_band(freqs, d, w, gc, gw, label, outpath):
    n_kpts, n_modes = freqs.shape
    N_freqs = n_modes // 2
    fig, ax = plt.subplots(figsize=(7, 5))
    for jj in range(n_kpts):
        ax.plot(np.full(N_freqs, jj+1), 1e-9*np.real(freqs[jj, :N_freqs]),
                'b.', markersize=7)
        ax.plot(np.full(N_freqs, jj+1), 1e-9*np.real(freqs[jj, N_freqs:]),
                'r.', markersize=7)

    if gw > 0:
        top = gc - gw/2
        bot = gc + gw/2
        ax.axhspan(top, bot, alpha=0.15, color='green', zorder=0)
        ax.axhline(top, color='green', lw=1.2, ls='--')
        ax.axhline(bot, color='green', lw=1.2, ls='--')
        ax.annotate(
            f'$f_{{gap}}$ = {gc:.1f} GHz\n'
            f'$\\Delta f$ = {gw:.2f} GHz  ({gw/gc*100:.0f}%)',
            xy=(n_kpts + 0.3, gc),
            xycoords='data',
            fontsize=10, va='center',
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='green', alpha=0.8),
            clip_on=False,
        )

    ax.set_ylabel('Frequency (GHz)', fontsize=12)
    ax.set_xticks(BZ_TICKS)
    ax.set_xticklabels(BZ_LABELS, fontsize=12)
    ax.set_xlim([1, n_kpts])
    ax.set_ylim([0, np.real(freqs).max()*1e-9 * 1.05])
    ax.legend(['Symmetric', 'Antisymmetric'], loc='upper left', fontsize=10)
    ax.set_title(f'Diamond: a=190nm, d={d}nm, w={w}nm, t=140nm  [{label}]', fontsize=11)
    ax.tick_params(labelsize=11)
    plt.subplots_adjust(right=0.78)
    plt.savefig(str(outpath), dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {outpath}')


# ── Center point band diagram ─────────────────────────────────────────────────

d_c, w_c = 72, 43
if (d_c, w_c) in freqs_all:
    f = freqs_all[(d_c, w_c)]
    gc, gw, _ = find_gap(f)
    plot_band(f, d_c, w_c, gc, gw, 'center',
              OUT / 'diamond_band_center.png')

# ── Best and worst gap band diagrams ─────────────────────────────────────────

valid_mask = ~np.isnan(gap_wid)
if valid_mask.any():
    best_idx = np.unravel_index(np.nanargmax(gap_wid), gap_wid.shape)
    worst_idx = np.unravel_index(np.nanargmin(gap_wid), gap_wid.shape)

    d_best, w_best = d_nm[best_idx[0]], w_nm[best_idx[1]]
    d_worst, w_worst = d_nm[worst_idx[0]], w_nm[worst_idx[1]]

    print(f'\nBest gap : d={d_best}nm, w={w_best}nm -> '
          f'{gap_cen[best_idx]:.2f} GHz center, {gap_wid[best_idx]:.3f} GHz wide '
          f'({gap_frac[best_idx]*100:.1f}%)')
    print(f'Worst gap: d={d_worst}nm, w={w_worst}nm -> '
          f'{gap_cen[worst_idx]:.2f} GHz center, {gap_wid[worst_idx]:.3f} GHz wide '
          f'({gap_frac[worst_idx]*100:.1f}%)')

    if (d_best, w_best) in freqs_all:
        f = freqs_all[(d_best, w_best)]
        gc, gw, _ = find_gap(f)
        plot_band(f, d_best, w_best, gc, gw, 'best gap',
                  OUT / 'diamond_band_best.png')

    if (d_worst, w_worst) in freqs_all and (d_worst, w_worst) != (d_best, w_best):
        f = freqs_all[(d_worst, w_worst)]
        gc, gw, _ = find_gap(f)
        plot_band(f, d_worst, w_worst, gc, gw, 'worst gap',
                  OUT / 'diamond_band_worst.png')

print('\nDone.')
