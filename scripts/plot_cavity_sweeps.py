"""
plot_cavity_sweeps.py  (Mac)
Heat maps of a 619 nm cavity pipeline folder (runs/cavity_619 or runs/cavity_619_width/<label>): every
(d, xi, chi) design is reduced to its point ON the 619.4 nm line (linear interpolation in a between the
solved points that bracket 619.4 nm; designs that don't bracket it are left grey).
Design reduction and selection rule: scripts/cavity_designs.py.
  shape_maps()   one column per taper depth d; rows = optical Q, breathing (GHz), breathing localization,
                 min feature; x = chi (hole-area pull), y = xi (hole-aspect pull). Outlined = base shape of
                 the (a, d) step; hatched = below the minimum feature at the 619 nm a; grey = not run;
                 red slash = field map shows the mode is not a breathing mode (sidewall ratio < 0.7).
  designs()      the 619 nm designs as a list of dicts (also used by the width summary / final selection)
Usage:  python scripts/plot_cavity_sweeps.py <run_dir> <min_feature_nm> "<title>" <out.png>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from cavity_taper import layout, min_features   # noqa: E402

from cavity_designs import designs, line_619, select, LAM0, S_MIN   # noqa: E402,F401


def text_color(cm, x):
    r, g, b, _ = cm(float(np.clip(x, 0, 1)))
    return 'white' if 0.299 * r + 0.587 * g + 0.114 * b < 0.5 else 'k'


def shape_maps(run_dir, min_feature, title, out_png):
    D = designs(run_dir)
    line = line_619(run_dir)
    ds = sorted({x['d'] for x in D} | set(line))
    XI = sorted({x['xi'] for x in D} | {2.0, 4.0, 6.0, 8.0, 10.0})
    CHI = sorted({x['chi'] for x in D} | {3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0})
    c0 = D[0]['cfg'] if D else None
    rows = [('Q', 'optical Q', 'viridis', (3, 8), lambda v: np.log10(v), '{:.0e}', 'log$_{10}$ Q$_o$'),
            ('fb', 'breathing (GHz)', 'RdBu_r', (7.5, 12.5), lambda v: v, '{:.2f}', 'GHz'),
            ('lb', 'breathing localization', 'magma', (0.5, 1.0), lambda v: v, '{:.2f}', 'localization'),
            ('min_feature', 'min feature (nm)', 'cividis', (min_feature - 10, min_feature + 40), lambda v: v, '{:.0f}', 'nm')]
    fig, axes = plt.subplots(len(rows), len(ds), figsize=(4.2 * len(ds) + 1.2, 3.0 * len(rows) + 0.8), squeeze=False)
    for j, d in enumerate(ds):
        cell = {(x['xi'], x['chi']): x for x in D if x['d'] == d}
        for i, (key, lab, cmap, (vmin, vmax), f, fmt, cb) in enumerate(rows):
            ax = axes[i, j]
            cm = plt.get_cmap(cmap).copy(); cm.set_bad('0.88')
            Z = np.full((len(XI), len(CHI)), np.nan)
            for (xi, chi), x in cell.items():
                if xi in XI and chi in CHI and np.isfinite(x[key]):
                    Z[XI.index(xi), CHI.index(chi)] = f(x[key])
            im = ax.imshow(np.ma.masked_invalid(Z), origin='lower', aspect='auto', cmap=cm, vmin=vmin, vmax=vmax,
                           extent=(-0.5, len(CHI) - 0.5, -0.5, len(XI) - 0.5))
            for (xi, chi), x in cell.items():
                if xi in XI and chi in CHI and np.isfinite(x[key]):
                    s = fmt.format(x[key]).replace('e+0', 'e')
                    ax.text(CHI.index(chi), XI.index(xi), s, ha='center', va='center', fontsize=7,
                            color=text_color(cm, (f(x[key]) - vmin) / (vmax - vmin)))
                    if x['base']:
                        ax.add_patch(plt.Rectangle((CHI.index(chi) - 0.5, XI.index(xi) - 0.5), 1, 1, fc='none', ec='k', lw=1.6))
                    if np.isfinite(x['S']) and x['S'] < S_MIN and key in ('fb', 'lb'):   # field map: not a breathing mode
                        ax.plot([CHI.index(chi) - 0.45, CHI.index(chi) + 0.45], [XI.index(xi) - 0.45, XI.index(xi) + 0.45],
                                color='red', lw=1.5)
            if c0 is not None and d in line:            # hatch shapes below the min feature at the 619 nm a
                a = line[d]
                for ii, xi in enumerate(XI):
                    for jj, chi in enumerate(CHI):
                        if (xi, chi) in cell or chi * d >= 0.95:
                            continue
                        mf = min(min_features(layout(a, c0['hx_m'] / c0['a_m'] * a, c0['hy_m'], 10, 10, d, 1.0, xi, chi),
                                              c0['w']).values())
                        if mf < min_feature:
                            ax.add_patch(plt.Rectangle((jj - 0.5, ii - 0.5), 1, 1, fc='none', ec='0.45', hatch='///', lw=0))
            ax.set_xticks(range(len(CHI)), [f'{c:g}' for c in CHI], fontsize=8)
            ax.set_yticks(range(len(XI)), [f'{x:g}' for x in XI], fontsize=8)
            if i == 0:
                ax.set_title(f'd = {d:.2f}' + (f'   (a ≈ {line[d]:.0f} nm)' if d in line else ''), fontweight='bold')
            if i == len(rows) - 1:
                ax.set_xlabel('χ (hole-area pull)')
            if j == 0:
                ax.set_ylabel(f'{lab}\n\nξ (hole-aspect pull)')
            if j == len(ds) - 1:
                fig.colorbar(im, ax=ax, fraction=0.05, pad=0.03, label=cb)
    fig.suptitle(title, fontsize=13, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(out_png, dpi=140, facecolor='white')
    plt.close(fig)
    return out_png


def design_space(pipes, out_png):
    """pipes: list of (label, run_dir, min_feature). All 619 nm designs: breathing vs Q, one panel per
    min feature; marker = width, color = breathing localization; target region shaded; star = selected."""
    mfs = sorted({mf for _, _, mf in pipes})
    fig, axes = plt.subplots(1, len(mfs), figsize=(7.2 * len(mfs), 5.4), squeeze=False)
    marks = {550: 'o', 600: 's', 650: 'D', 700: '^'}
    for ax, mf in zip(axes[0], mfs):
        allD = []
        for label, rd, m in pipes:
            if m != mf or not Path(rd, 'data').exists():
                continue
            D = [x for x in designs(rd) if x['min_feature'] >= mf - 0.5 and np.isfinite(x['fb'])]
            allD += D
            if D:
                sc = ax.scatter([x['Q'] for x in D], [x['fb'] for x in D], c=[x['lb'] for x in D], cmap='magma',
                                vmin=0.5, vmax=1.0, marker=marks.get(int(D[0]['w']), 'o'), s=70, edgecolor='k', lw=0.6,
                                label=f"w {int(D[0]['w'])}")
        hyb = [x for x in allD if np.isfinite(x['S']) and x['S'] < S_MIN]
        if hyb:
            ax.scatter([x['Q'] for x in hyb], [x['fb'] for x in hyb], marker='x', s=160, color='red', lw=2,
                       zorder=6, label='not breathing (field map)')
        best, ok = select(allD, mf)
        if best:
            ax.scatter([best['Q']], [best['fb']], marker='*', s=520, facecolor='none', edgecolor='lime', lw=2.2, zorder=5)
        ax.axhspan(0, 10, xmin=0, xmax=1, color='tab:green', alpha=0.07)
        ax.axhline(10, color='tab:green', lw=1, ls='--')
        ax.set_xscale('log'); ax.set_xlim(1e3, 2e8); ax.set_ylim(9.0, 13.5)
        ax.set_xlabel('optical Q at 619 nm'); ax.set_ylabel('breathing mode (GHz)')
        ax.set_title(f'{mf:.0f} nm minimum feature', fontweight='bold')
        ax.legend(loc='upper left', fontsize=9)
        if allD:
            fig.colorbar(sc, ax=ax, label='breathing localization')
    fig.suptitle('All fabricable 619 nm designs  (star = selected)', fontsize=13, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_png, dpi=140, facecolor='white'); plt.close(fig)
    return out_png


def selection_table(pipes, out_png):
    """Best design per (width, min feature) and the final pick per min feature, as a table figure."""
    rows, finals = [], {}
    for label, rd, mf in pipes:
        width = label.split(' / ')[0].lstrip('w')
        if not Path(rd, 'data').exists() or not designs(rd):
            rows.append([width, 'pending', '', '', '', f'{mf}']); continue
        D = designs(rd)
        b, ok = select(D, mf)
        if b is None:
            rows.append([width, 'none', '', '', '', f'{mf}']); continue
        rows.append([width, f"d {b['d']:.2f}, ξ {b['xi']:g}, χ {b['chi']:g}", f"{b['a']:.1f}", f"{b['Q']:.1e}",
                     f"{b['fb']:.2f}", f"{b['min_feature']:.0f}"])
        if mf not in finals or (ok, b['Q'] if ok else -b['fb']) > finals[mf][1]:
            finals[mf] = (len(rows) - 1, (ok, b['Q'] if ok else -b['fb']))
    head = ['width (nm)', 'taper', 'a (nm)', 'optical Q at 619 nm', 'breathing (GHz)', 'min feat. (nm)']
    fig, ax = plt.subplots(figsize=(11, 0.55 * len(rows) + 1.4)); ax.axis('off')
    tb = ax.table(cellText=rows, colLabels=head, loc='center', cellLoc='center')
    tb.auto_set_font_size(False); tb.set_fontsize(10); tb.scale(1, 1.6)
    picked = {v[0] for v in finals.values()}
    for (r, c), cl in tb.get_celld().items():
        if r == 0:
            cl.set_text_props(fontweight='bold'); cl.set_facecolor('0.9')
        elif r - 1 in picked:
            cl.set_facecolor('#d9f2d9')
    ax.set_title('Best design per width and minimum feature (green = selected per minimum feature)',
                 fontsize=12, fontweight='bold')
    fig.tight_layout(); fig.savefig(out_png, dpi=140, facecolor='white'); plt.close(fig)
    return out_png


if __name__ == '__main__':
    print(shape_maps(sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]))
