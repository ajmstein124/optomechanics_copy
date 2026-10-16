"""
analyze_plan.py  (runs locally on Mac)
Generic analysis for plan-based snowflake sweeps (scripts/sweep_plan.py -> plan_runner.py).
Works on partial data.

Gap definition: complete gaps (all k, sym1 + as1 combined) counted only below the
complete-spectrum ceiling (min over k and symmetry class of the highest computed mode).
Reported gap per combo = the WIDEST such gap, with its band index (no fixed band-pair
assumption -- mode ordering can change between regimes, e.g. thin slabs).

Outputs in runs/<run>/figures/:
  heatmaps.png      rows = center / width / fractional width, columns = a; ONE color scale
                    per row; cells: value, "<min feat>" (flagged, not run), "n/a (geom)",
                    "no gap", "--" (pending). Below-threshold cells show '<X nm' and '(y nm)' on separate lines.
  gap_vs_a.png      gap band vs a per d/a panel, color = w/a, target line
  bands_a<a>.png    band-structure grid per a (rows d/a, cols w/a)
  summary.csv

Usage (from project root):
    python scripts/analyze_plan.py <run> [--target-GHz 10] [--no-bands]
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LAMBDA_NM = 619.0


def gaps_below_ceiling(freqs, n_mode):
    f = np.abs(np.real(freqs)) * 1e-9
    ceiling = min(f[:, :n_mode].max(axis=1).min(), f[:, n_mode:].max(axis=1).min())
    sb = np.sort(f, axis=1)
    out = []
    for b in range(sb.shape[1] - 1):
        top, bot = sb[:, b].max(), sb[:, b + 1].min()
        if bot > top and top > 1.0 and bot <= ceiling:
            out.append((b + 1, top, bot))
    return out, ceiling


def load(run):
    rd = Path('runs') / run
    plan = json.load(open(rd / 'plan.json'))
    n_mode = int(plan['solver']['N_mode'])
    rows = []
    for c in plan['combos']:
        r = dict(c)
        p = rd / 'data' / f"sweep_{c['tag']}.npz"
        r['present'] = p.exists()
        r['gap'] = None
        if p.exists():
            dat = np.load(str(p))
            gaps, ceil = gaps_below_ceiling(dat['freqs'], int(dat['N_mode']) if 'N_mode' in dat.files else n_mode)
            r['ceiling'] = ceil
            r['all_gaps'] = gaps
            if gaps:
                r['gap'] = max(gaps, key=lambda g: g[2] - g[1])
        rows.append(r)
    return plan, rows


def cell_text(r, metric):
    if r['present']:
        if r['gap'] is None:
            return 'no gap', np.nan
        b, lo, hi = r['gap']
        v = {'center (GHz)': 0.5 * (lo + hi), 'width (GHz)': hi - lo,
             'fractional width (%)': 200 * (hi - lo) / (lo + hi)}[metric]
        dag = (f"\n<{r['_mf']:g} nm\n({r['min_feature_nm']:.0f} nm)"
               if r['status'] == 'below_min_feature' else '')
        sub = f'\nb{b}-{b+1}' if metric == 'center (GHz)' else ''
        return f'{v:.1f}{dag}{sub}', v
    if r['status'] == 'infeasible_geom':
        return 'n/a\n(geom)', np.nan
    if not r['run']:
        return f"not run\n<{r['_mf']:g} nm\n({r['min_feature_nm']:.0f} nm)", np.nan
    return '--', np.nan


def heatmaps(plan, rows, out, target):
    a_vals = sorted({r['a_nm'] for r in rows})
    da_vals = sorted({r['da'] for r in rows})
    wa_vals = sorted({r['wa'] for r in rows})
    mf = plan['fab_check']['min_feature_nm']
    for r in rows:
        r['_mf'] = mf if mf is not None else 0
    metrics = [('center (GHz)', 'Blues_r'), ('width (GHz)', 'Greens'), ('fractional width (%)', 'Purples')]
    lookup = {(r['a_nm'], r['da'], r['wa']): r for r in rows}
    grids = {m: {a: np.full((len(da_vals), len(wa_vals)), np.nan) for a in a_vals} for m, _ in metrics}
    texts = {m: {a: [[''] * len(wa_vals) for _ in da_vals] for a in a_vals} for m, _ in metrics}
    for m, _ in metrics:
        for a in a_vals:
            for i, da in enumerate(da_vals):
                for k, wa in enumerate(wa_vals):
                    t, v = cell_text(lookup[(a, da, wa)], m)
                    grids[m][a][i, k] = v
                    texts[m][a][i][k] = t
    fig, axes = plt.subplots(3, len(a_vals), figsize=(2.9 * len(a_vals) + 1.3, 8.8), squeeze=False)
    for mi, (m, cmap) in enumerate(metrics):
        allv = np.concatenate([g[np.isfinite(g)] for g in grids[m].values()])
        vmin, vmax = (allv.min(), allv.max()) if allv.size else (0, 1)
        if vmax <= vmin:
            vmax = vmin + 1
        cm = plt.get_cmap(cmap).copy(); cm.set_bad('0.88')
        for j, a in enumerate(a_vals):
            ax = axes[mi, j]
            im = ax.imshow(grids[m][a], origin='lower', cmap=cm, vmin=vmin, vmax=vmax, aspect='auto')
            for i in range(len(da_vals)):
                for k in range(len(wa_vals)):
                    v = grids[m][a][i, k]
                    frac = (v - vmin) / (vmax - vmin) if np.isfinite(v) else 0
                    dark = np.isfinite(v) and ((1 - frac) if cmap.endswith('_r') else frac) > 0.55
                    hit = (m == 'center (GHz)' and np.isfinite(v) and v <= target)
                    ax.text(k, i, texts[m][a][i][k], ha='center', va='center',
                            fontsize=7 if texts[m][a][i][k].count('\n') >= 2 else 8,
                            color='white' if dark else '0.15', fontweight='bold')
                    if hit:
                        ax.add_patch(plt.Rectangle((k - 0.5, i - 0.5), 1, 1, fc='none', ec='#E67E22', lw=2.5))
            ax.set_xticks(range(len(wa_vals))); ax.set_xticklabels(wa_vals, fontsize=8)
            ax.set_yticks(range(len(da_vals))); ax.set_yticklabels(da_vals, fontsize=8)
            if mi == 0:
                ax.set_title(f'a = {a:g} nm (a/λ={a/LAMBDA_NM:.2f})', fontsize=9.5, fontweight='bold')
            if mi == 2:
                ax.set_xlabel('w/a', fontsize=9)
            if j == 0:
                ax.set_ylabel(f'{m}\n\nd/a', fontsize=9)
        fig.colorbar(im, ax=list(axes[mi, :]), fraction=0.012, pad=0.01, label=m)
    fc = plan['fab_check']
    fig.suptitle(f'{out.parent.name} -- widest complete gap (band index shown); one color scale per row; '
                 f'orange box = center <= {target:g} GHz\n'
                 f"min-feature check {'ON' if fc['enforce'] else 'OFF'} at {fc['min_feature_nm']} nm "
                 f'(bridge, arm width): "<X nm (y)" = not run, y = its min feature; † = below threshold but run; '
                 '"n/a (geom)" = hole cannot fit the rhombus cell; "--" = pending', fontsize=10)
    fig.savefig(str(out / 'heatmaps.png'), dpi=150, facecolor='white', bbox_inches='tight')
    plt.close(fig)


def gap_vs_a(plan, rows, out, target):
    da_vals = sorted({r['da'] for r in rows})
    wa_vals = sorted({r['wa'] for r in rows})
    colors = plt.cm.viridis(np.linspace(0.05, 0.85, len(wa_vals)))
    fig, axes = plt.subplots(2, len(da_vals), figsize=(5 * len(da_vals), 8.5), sharey='row', squeeze=False,
                             gridspec_kw=dict(height_ratios=[1.6, 1]))
    a_all = sorted({r['a_nm'] for r in rows})
    frs = []
    for col, da in enumerate(da_vals):
        ax, axf = axes[0, col], axes[1, col]
        for k, wa in enumerate(wa_vals):
            sel = [r for r in rows if r['da'] == da and r['wa'] == wa and r['gap'] is not None]
            if not sel:
                continue
            x = np.array([r['a_nm'] for r in sel]) + (k - (len(wa_vals) - 1) / 2) * 0.012 * (a_all[-1] - a_all[0] + 1)
            lo = np.array([r['gap'][1] for r in sel]); hi = np.array([r['gap'][2] for r in sel])
            ax.vlines(x, lo, hi, color=colors[k], lw=6, alpha=0.8, label=f'w/a={wa}')
            ax.plot(x, 0.5 * (lo + hi), 'o-', color=colors[k], ms=3, lw=0.8)
            fr = 200 * (hi - lo) / (hi + lo); frs.extend(fr)
            axf.plot(x, fr, 'o-', color=colors[k], ms=4, lw=1.2)
        ax.axhline(target, color='#E67E22', ls='--', lw=1.5)
        ax.text(a_all[0], target, f' {target:g} GHz target', color='#E67E22', va='bottom', fontsize=8)
        for a_ in (ax, axf):
            a_.set_xticks(a_all); a_.grid(alpha=0.3)
            a_.set_xlim(a_all[0] - 0.06 * (a_all[-1] - a_all[0] + 1), a_all[-1] + 0.06 * (a_all[-1] - a_all[0] + 1))
        ax.set_title(f'd/a = {da}', fontweight='bold')
        sec = ax.secondary_xaxis('top', functions=(lambda x: x / LAMBDA_NM, lambda y: y * LAMBDA_NM))
        sec.set_xlabel(r'$a/\lambda$ ($\lambda$=619 nm)', fontsize=9)
        axf.set_xlabel('lattice constant a (nm)')
    axes[0, 0].set_ylabel('widest complete gap (GHz)')
    axes[1, 0].set_ylabel('fractional width (%)')
    axes[1, 0].set_ylim(0, max(frs) * 1.1 if frs else 1)
    if axes[0, 0].get_legend_handles_labels()[0]:
        axes[0, 0].legend(fontsize=9)
    fig.suptitle(f'{out.parent.name} -- widest complete gap vs a (only combos that ran)', fontsize=11)
    fig.tight_layout()
    fig.savefig(str(out / 'gap_vs_a.png'), dpi=150, facecolor='white')
    plt.close(fig)


def band_grids(plan, rows, run, out):
    n_mode = int(plan['solver']['N_mode'])
    da_vals = sorted({r['da'] for r in rows}, reverse=True)
    wa_vals = sorted({r['wa'] for r in rows})
    for a in sorted({r['a_nm'] for r in rows}):
        sel = {(r['da'], r['wa']): r for r in rows if r['a_nm'] == a}
        if not any(r['present'] for r in sel.values()):
            continue
        fmax = 60.0 * 300.0 / a * (1.6 if n_mode > 10 else 1.0)
        fig, axes = plt.subplots(len(da_vals), len(wa_vals), figsize=(4.3 * len(wa_vals), 3.9 * len(da_vals)),
                                 sharey=True, squeeze=False)
        for i, da in enumerate(da_vals):
            for j, wa in enumerate(wa_vals):
                ax, r = axes[i, j], sel[(da, wa)]
                ax.set_title(f"d/a={da}, w/a={wa}  (bridge {r['bridge_nm']:.0f} nm)", fontsize=9)
                if not r['present']:
                    ax.text(0.5, 0.5, {'infeasible_geom': 'n/a (geom)'}.get(
                        r['status'], 'not run' if not r['run'] else 'pending'),
                        transform=ax.transAxes, ha='center', va='center', color='0.5')
                    ax.set_xticks([])
                    continue
                dat = np.load(str(Path('runs') / run / 'data' / f"sweep_{r['tag']}.npz"))
                f = np.abs(np.real(dat['freqs'])) * 1e-9
                kp = dat['kpoints']
                dk = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(kp, axis=0), axis=1))]
                kx = np.r_[dk, dk[-1] + np.linalg.norm(kp[-1])]
                fp = np.vstack([f, f[0]])
                for b in range(n_mode):
                    ax.plot(kx, np.sort(fp[:, :n_mode], axis=1)[:, b], '-', color='#2C5F8A', lw=0.9)
                    ax.plot(kx, np.sort(fp[:, n_mode:], axis=1)[:, b], '--', color='#C0392B', lw=0.9)
                ax.axhspan(r['ceiling'], fmax, color='0.85', alpha=0.5, zorder=0)
                for b, lo, hi in r['all_gaps']:
                    best = r['gap'] is not None and b == r['gap'][0]
                    ax.axhspan(lo, hi, color='#F4D03F' if best else 'none', alpha=0.4 if best else 1,
                               ec=None if best else '#7D3C98', ls=':', zorder=0)
                lbl = 'no complete gap' if r['gap'] is None else \
                    f"b{r['gap'][0]}-{r['gap'][0]+1}: {0.5*(r['gap'][1]+r['gap'][2]):.1f} GHz, " \
                    f"{r['gap'][2]-r['gap'][1]:.2f} wide"
                ax.text(0.97, 0.03, lbl, transform=ax.transAxes, ha='right', va='bottom', fontsize=8,
                        bbox=dict(fc='white', ec='#999', lw=0.5))
                a_m = float(dat['a'])
                M = np.array([np.pi / a_m, np.pi / (a_m * np.sqrt(3))]); K = np.array([4 * np.pi / (3 * a_m), 0])
                t = [0, kx[np.argmin(np.linalg.norm(kp - M, axis=1))], kx[np.argmin(np.linalg.norm(kp - K, axis=1))], kx[-1]]
                for tt in t:
                    ax.axvline(tt, color='#bbb', lw=0.6, zorder=0)
                ax.set_xticks(t, [r'$\Gamma$', 'M', 'K', r'$\Gamma$'])
                ax.set_xlim(0, kx[-1]); ax.set_ylim(0, fmax)
                if j == 0:
                    ax.set_ylabel('Frequency (GHz)')
        fig.suptitle(f'{run} -- a = {a:g} nm | blue = sym1, red dashed = as1 | yellow = widest complete gap, '
                     'purple dotted = other complete gaps, grey = above complete-spectrum ceiling', fontsize=10)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        fig.savefig(str(out / f'bands_a{a:g}.png'), dpi=120, facecolor='white')
        plt.close(fig)


def summary(rows, out):
    with open(out / 'summary.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['tag', 'a_nm', 'd_over_a', 'w_over_a', 'status', 'run', 'present', 'bridge_nm', 'w_nm',
                    'gap_band_below', 'gap_lo_GHz', 'gap_hi_GHz', 'gap_center_GHz', 'gap_width_GHz', 'gap_frac'])
        for r in rows:
            g = r['gap']
            w.writerow([r['tag'], r['a_nm'], r['da'], r['wa'], r['status'], r['run'], r['present'],
                        r['bridge_nm'], r['w_nm']] +
                       ([g[0], g[1], g[2], 0.5 * (g[1] + g[2]), g[2] - g[1], 2 * (g[2] - g[1]) / (g[1] + g[2])]
                        if g else [''] * 6))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--target-GHz', type=float, default=10.0)
    ap.add_argument('--no-bands', action='store_true')
    args = ap.parse_args()
    plan, rows = load(args.run)
    out = Path('runs') / args.run / 'figures'
    out.mkdir(parents=True, exist_ok=True)
    n_present = sum(r['present'] for r in rows); n_run = sum(r['run'] for r in rows)
    print(f'{n_present}/{n_run} planned runs present ({len(rows)} combos in plan)')
    for r in rows:
        if r['present']:
            g = r['gap']
            print(f"  {r['tag']:>18} [{r['status']:>17}] bridge {r['bridge_nm']:6.1f} nm | " +
                  (f"b{g[0]}-{g[0]+1} {g[1]:6.2f}-{g[2]:6.2f} GHz  center {0.5*(g[1]+g[2]):6.2f}  "
                   f"frac {200*(g[2]-g[1])/(g[1]+g[2]):5.1f}%" if g else 'no complete gap'))
    summary(rows, out)
    heatmaps(plan, rows, out, args.target_GHz)
    gap_vs_a(plan, rows, out, args.target_GHz)
    if not args.no_bands:
        band_grids(plan, rows, args.run, out)
    print(f'Saved figures to {out}')
