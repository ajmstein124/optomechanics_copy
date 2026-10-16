"""
analyze.py  (runs locally on Mac)
Diamond lattice-constant sweep -- gap vs a for every (d/a, w/a), plus per-a heatmaps.
Works on partial data (missing combos shown grey / skipped).

Gap definitions (recomputed from freqs, NOT the values stored by sweep.py), counted only
below f_valid (complete-spectrum ceiling, see f_valid_ceiling):
  - tracked : complete gap between sorted bands GAP_BAND and GAP_BAND+1 (sym+antisym
              combined) -- the fundamental gap in every diamond_dw_sweep combo
  - widest  : widest complete gap below f_valid, any band pair
  If widest != tracked for a combo, it's flagged in the printout -- check the band plot
  before trusting the tracked-gap trend there.

Outputs (runs/diamond_a_sweep/figures/):
  gap_vs_a.png/.pdf      gap band (lo-hi) vs a, one panel per d/a, colour = w/a;
                         top axis a/lambda at 619 nm
  heatmaps_per_a.png     3x3 (d/a x w/a) tracked-gap center / width / fractional width per a
  summary.csv            one row per combo

Usage (from project root):
    python runs/diamond_a_sweep/analyze.py
"""

import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

DATA = Path('runs/diamond_a_sweep/data')
OUT  = Path('runs/diamond_a_sweep/figures')
OUT.mkdir(parents=True, exist_ok=True)

a_nm    = [150, 175, 200, 225, 250, 275]
da_vals = [0.35, 0.41, 0.48]
wa_vals = [0.28, 0.36, 0.43]
LAMBDA_NM    = 619.0
GAP_BAND     = 6
F_WIDEST_MAX = 60.0    # GHz at a=300 nm, scaled by 300/a (top of N_mode=10 window)
MIN_FLAG_GHZ = 0.5     # tracked gaps narrower than this are at k-sampling resolution

W_COLORS = {0.28: '#2C5F8A', 0.36: '#C0392B', 0.43: '#1E8449'}

# Combos that cannot be modelled with the rhombus cell (hole cannot fit any placement;
# bridges to neighbouring holes 0-5 nm) -- from fill_plan.json (scripts/cell_placement.py + shapely)
# --- Fabrication flag: narrowest slab bridge / arm width vs the project min feature --------
import sys as _sys
_sys.path.insert(0, 'scripts')
from sweep_plan import DEFAULT_MIN_FEATURE_NM as MIN_FEATURE_NM   # noqa: E402
from schematic import hole_poly, lattice                           # noqa: E402
from shapely import affinity as _aff                               # noqa: E402


def min_feature_nm(a, da, wa, fr=16.0):
    h = hole_poly(da * a, wa * a, fr)
    a1, a2 = lattice(a)
    br = min(h.distance(_aff.translate(h, *(sg * L))) for L in (a1, a2, a1 + a2) for sg in (1, -1))
    return min(br, wa * a), br


_plan_path = Path('runs/diamond_a_sweep/fill_plan.json')
INFEASIBLE = set()
if _plan_path.exists():
    import json
    INFEASIBLE = {(v['a_nm'], v['da'], v['wa']) for v in json.load(open(_plan_path)).values()
                  if not v['feasible']}


def tag(a, da, wa):
    return f'a{a}_da{int(round(da*100)):02d}_wa{int(round(wa*100)):02d}'


N_MODE = 10


def f_valid_ceiling(freqs):
    """Spectrum is complete only below the lowest (over k and symmetry class) of the
    highest computed mode -- ARPACK returns N_MODE modes per class around the shift.
    Gaps above this are truncation artifacts."""
    f = np.abs(np.real(freqs)) * 1e-9
    return min(f[:, :N_MODE].max(axis=1).min(), f[:, N_MODE:].max(axis=1).min())


def gaps_from_freqs(freqs):
    sb = np.sort(np.abs(np.real(freqs)), axis=1) * 1e-9
    fv = f_valid_ceiling(freqs)
    out = []
    for b in range(sb.shape[1] - 1):
        top, bot = sb[:, b].max(), sb[:, b + 1].min()
        if bot > top and top > 1.0 and bot <= fv:
            out.append((b + 1, top, bot))
    return out


# --- Load ---------------------------------------------------------------------

rows = []
for a in a_nm:
    for da in da_vals:
        for wa in wa_vals:
            p = DATA / f'sweep_{tag(a, da, wa)}.npz'
            mf, br = min_feature_nm(a, da, wa)
            r = dict(a=a, da=da, wa=wa, d=da*a, w=wa*a, present=p.exists(), f_valid=np.nan,
                     min_feat=mf, bridge=br, fab_ok=mf >= MIN_FEATURE_NM,
                     clearance_nm=np.nan, bridge_nm=np.nan, shifted=False,
                     t_lo=np.nan, t_hi=np.nan, w_band=np.nan, w_lo=np.nan, w_hi=np.nan)
            if p.exists():
                dat  = np.load(str(p))
                gaps = gaps_from_freqs(dat['freqs'])
                tr   = [g for g in gaps if g[0] == GAP_BAND]
                if tr:
                    r['t_lo'], r['t_hi'] = tr[0][1], tr[0][2]
                r['f_valid'] = f_valid_ceiling(dat['freqs'])
                for k_ in ('clearance_nm', 'bridge_nm'):
                    r[k_] = float(dat[k_]) if k_ in dat.files else np.nan
                r['shifted'] = 'cell_shift' in dat.files
                cand = gaps
                if cand:
                    b, lo, hi = max(cand, key=lambda g: g[2] - g[1])
                    r['w_band'], r['w_lo'], r['w_hi'] = b, lo, hi
            rows.append(r)

done = [r for r in rows if r['present']]
print(f'{len(done)}/{len(rows)} combos present, {len(INFEASIBLE)} geometrically infeasible '
      f'(d/a=0.48, w/a=0.43), {len(rows) - len(done) - len(INFEASIBLE)} still missing\n')
print(f'{"a":>4} {"d/a":>5} {"w/a":>5} {"d":>6} {"w":>6} | {"tracked 6-7 gap (GHz)":>28} | {"widest gap":>24}')
for r in done:
    tc, tw = 0.5 * (r['t_lo'] + r['t_hi']), r['t_hi'] - r['t_lo']
    ts = (f'{r["t_lo"]:6.2f}-{r["t_hi"]:6.2f} ({tw:5.2f}, {100*tw/tc:4.1f}%)'
          if np.isfinite(tc) else 'none')
    ws = (f'b{int(r["w_band"])}-{int(r["w_band"])+1} {r["w_lo"]:6.2f}-{r["w_hi"]:6.2f}'
          if np.isfinite(r['w_band']) else 'none')
    flag = ''
    if np.isfinite(r['w_band']) and r['w_band'] != GAP_BAND:
        flag = '  <-- widest gap is NOT bands 6-7'
    elif np.isfinite(tw) and tw < MIN_FLAG_GHZ:
        flag = '  <-- tracked gap < 0.5 GHz (resolution limit)'
    print(f'{r["a"]:4d} {r["da"]:5.2f} {r["wa"]:5.2f} {r["d"]:6.1f} {r["w"]:6.1f} | {ts:>28} | {ws:>24}{flag}')

with open(OUT / 'summary.csv', 'w', newline='') as f:
    wr = csv.writer(f)
    wr.writerow(['a_nm', 'd_over_a', 'w_over_a', 'd_nm', 'w_nm', 'a_over_lambda619',
                 'tracked_lo_GHz', 'tracked_hi_GHz', 'tracked_center_GHz', 'tracked_width_GHz',
                 'tracked_frac', 'widest_band_below', 'widest_lo_GHz', 'widest_hi_GHz',
                 'f_valid_GHz', 'cell_shifted', 'clearance_nm', 'bridge_nm', 'min_feature_nm',
                 f'fab_ok_{MIN_FEATURE_NM:g}nm'])
    for r in done:
        tc, tw = 0.5 * (r['t_lo'] + r['t_hi']), r['t_hi'] - r['t_lo']
        wr.writerow([r['a'], r['da'], r['wa'], f'{r["d"]:.1f}', f'{r["w"]:.1f}',
                     f'{r["a"]/LAMBDA_NM:.3f}', r['t_lo'], r['t_hi'], tc, tw,
                     tw / tc if np.isfinite(tc) else np.nan,
                     r['w_band'], r['w_lo'], r['w_hi'],
                     r['f_valid'], r['shifted'], r['clearance_nm'], round(r['bridge'], 2),
                     round(r['min_feat'], 2), r['fab_ok']])

# --- Figure 1: gap vs a (top: absolute gap band, bottom: fractional width) -------

fig, axes = plt.subplots(2, 3, figsize=(15, 8.5), sharey='row',
                         gridspec_kw=dict(height_ratios=[1.6, 1]))
for col, da in enumerate(da_vals):
    ax, axf = axes[0, col], axes[1, col]
    for k, wa in enumerate(wa_vals):
        sel = [r for r in done if r['da'] == da and r['wa'] == wa and np.isfinite(r['t_lo'])]
        if not sel:
            continue
        x  = np.array([r['a'] for r in sel]) + (k - 1) * 3.0     # small offset so bars don't overlap
        lo = np.array([r['t_lo'] for r in sel])
        hi = np.array([r['t_hi'] for r in sel])
        c  = 0.5 * (lo + hi)
        ok = np.array([r['fab_ok'] for r in sel])
        ax.vlines(x[ok], lo[ok], hi[ok], color=W_COLORS[wa], lw=6, alpha=0.75, label=f'w/a={wa}')
        ax.vlines(x[~ok], lo[~ok], hi[~ok], color='0.6', lw=6, alpha=0.45)
        ax.plot(x, c, '-', color=W_COLORS[wa], lw=0.8)
        ax.plot(x[ok], c[ok], 'o', color=W_COLORS[wa], ms=3)
        ax.plot(x[~ok], c[~ok], 'o', mfc='white', mec='0.45', ms=4)
        fr_ = 100 * (hi - lo) / c
        axf.plot(x, fr_, '-', color=W_COLORS[wa], lw=1.2)
        axf.plot(x[ok], fr_[ok], 'o', color=W_COLORS[wa], ms=4)
        axf.plot(x[~ok], fr_[~ok], 'o', mfc='white', mec='0.45', ms=5)
    for a_ in (ax, axf):
        a_.set_xlim(a_nm[0] - 12, a_nm[-1] + 12)
        a_.set_xticks(a_nm)
        a_.grid(alpha=0.3)
    ax.set_title(f'd/a = {da}', fontsize=11, fontweight='bold')
    sec = ax.secondary_xaxis('top', functions=(lambda x: x / LAMBDA_NM, lambda y: y * LAMBDA_NM))
    sec.set_xlabel(r'$a/\lambda$  ($\lambda$ = 619 nm)', fontsize=9)
    axf.set_xlabel('lattice constant a (nm)')
axes[0, 0].set_ylabel('complete gap, bands 6-7 (GHz)')
axes[1, 0].set_ylabel('fractional width (%)')
fr_all = [100 * (r['t_hi'] - r['t_lo']) / (0.5 * (r['t_hi'] + r['t_lo'])) for r in done if np.isfinite(r['t_lo'])]
axes[1, 0].set_ylim(0, (max(fr_all) * 1.1) if fr_all else 1)
axes[0, 0].legend(fontsize=9)
fig.suptitle('Diamond snowflake -- phononic gap vs lattice constant  '
             '(t=140 nm, f_r=16 nm fixed; d, w scale with a)\n'
             f'bar = gap lo-hi, dot = center; grey bar / open marker = min feature < {MIN_FEATURE_NM:g} nm (not fabricable). '
             'Fractional width isolates geometry (t/a grows as a shrinks) from the trivial 1/a shift',
             fontsize=10.5)
fig.tight_layout()
for ext in ('png', 'pdf'):
    fig.savefig(str(OUT / f'gap_vs_a.{ext}'), dpi=150, facecolor='white')
plt.close(fig)

# --- Figure 2: per-a heatmaps (shared color scale per metric row) ----------------

metrics = [('center (GHz)', 'Blues'), ('width (GHz)', 'Greens'), ('fractional width (%)', 'Purples')]
grids = {a: {m: np.full((3, 3), np.nan) for m, _ in metrics} for a in a_nm}
for r in rows:
    if not np.isfinite(r['t_lo']):
        continue
    i, k = da_vals.index(r['da']), wa_vals.index(r['wa'])
    c, wdt = 0.5 * (r['t_lo'] + r['t_hi']), r['t_hi'] - r['t_lo']
    grids[r['a']]['center (GHz)'][i, k] = c
    grids[r['a']]['width (GHz)'][i, k] = wdt
    grids[r['a']]['fractional width (%)'][i, k] = 100 * wdt / c

# one vmin/vmax per metric across ALL lattice constants -> colors comparable between panels
limits = {}
for m, _ in metrics:
    allv = np.concatenate([grids[a][m][np.isfinite(grids[a][m])] for a in a_nm])
    lo, hi = (float(allv.min()), float(allv.max())) if allv.size else (0.0, 1.0)
    limits[m] = (lo, hi if hi > lo else lo + 1)

fig, axes = plt.subplots(len(metrics), len(a_nm), figsize=(3.0 * len(a_nm) + 1.2, 8.5),
                         gridspec_kw=dict(right=0.93))
for m_i, (m, cmap) in enumerate(metrics):
    vmin, vmax = limits[m]
    cm = plt.get_cmap(cmap).copy(); cm.set_bad('0.88')
    for j, a in enumerate(a_nm):
        ax = axes[m_i, j]
        data = grids[a][m]
        im = ax.imshow(data, origin='lower', cmap=cm, vmin=vmin, vmax=vmax, aspect='auto')
        for i in range(3):
            for k in range(3):
                v = data[i, k]
                present = any(r['present'] for r in rows
                              if r['a'] == a and r['da'] == da_vals[i] and r['wa'] == wa_vals[k])
                infeas = (a, da_vals[i], wa_vals[k]) in INFEASIBLE
                txt = (f'{v:.1f}' if np.isfinite(v) else
                       'n/a\n(geom)' if infeas else ('closed' if present else '--'))
                dark = np.isfinite(v) and (v - vmin) / (vmax - vmin) > 0.55
                rr = next(r for r in rows if r['a'] == a and r['da'] == da_vals[i] and r['wa'] == wa_vals[k])
                if not rr['fab_ok'] and not infeas:
                    ax.add_patch(plt.Rectangle((k - 0.5, i - 0.5), 1, 1, fc='0.55', alpha=0.6,
                                               ec='0.35', hatch='//', lw=0.5, zorder=3))
                    txt += f"\n<{MIN_FEATURE_NM:g} nm\n({rr['min_feat']:.0f} nm)"
                    dark = False
                ax.text(k, i, txt, ha='center', va='center', fontsize=7.5 if txt.count('\n') >= 2 else 8.5,
                        color='white' if dark else '0.1', fontweight='bold', zorder=4)
        ax.set_xticks(range(3)); ax.set_xticklabels(wa_vals, fontsize=8)
        ax.set_yticks(range(3)); ax.set_yticklabels(da_vals, fontsize=8)
        if m_i == 0:
            ax.set_title(f'a = {a} nm  (a/λ={a/LAMBDA_NM:.2f})', fontsize=10, fontweight='bold')
        if m_i == len(metrics) - 1:
            ax.set_xlabel('w/a', fontsize=9)
        if j == 0:
            ax.set_ylabel(f'{m}\n\nd/a', fontsize=9)
    fig.colorbar(im, ax=list(axes[m_i, :]), fraction=0.012, pad=0.01, label=m)
fig.suptitle('Diamond a-sweep -- tracked gap (bands 6-7) per lattice constant; one color scale per row (comparable across a)\n'
             f'grey hatched = not fabricable: min feature (slab bridge / arm width) < {MIN_FEATURE_NM:g} nm, actual value in brackets;  '
             '"closed" = run but no complete 6-7 gap,  "--" = not run yet,  '
             '"n/a (geom)" = hole cannot fit the rhombus cell (meets its periodic images)', fontsize=11)
fig.savefig(str(OUT / 'heatmaps_per_a.png'), dpi=150, facecolor='white', bbox_inches='tight')
plt.close(fig)

print(f'\nSaved: {OUT}/gap_vs_a.png, heatmaps_per_a.png, summary.csv')
