"""
analyze_ad.py  (Mac)
(a, d) sweep of the 619 nm cavity: maps of the optical cavity resonance (619 nm contour), optical Q,
and breathing-mode frequency (10 GHz contour). Works on partial data (grey = pending).
Mode identification (offline, from all saved modes):
  optical cavity mode = most localized mode with Q > 1e3 (the sweep's own pick sometimes grabbed a
                        spurious Q ~ 8 localized mode)
  breathing mode      = in-phase sidewall motion (B > 0.5) and localized (loc > 0.5), most localized one
                        (2026-10-15; the earlier 'largest optomechanical overlap' rule picked non-breathing
                        modes, see mech_eval.png / mode_profiles.png). Its localization is the 4th panel.
Writes ad_summary.csv.

Usage (from project root):
    python runs/cavity_619/analyze_ad.py
"""
import csv
import glob
from pathlib import Path

import json
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, 'scripts')
from cavity_taper import layout, min_features  # noqa: E402

RD = Path('runs/cavity_619')
MIN_FEATURE = 60.0             # nm, user setting; hatched = below
A_LIST = list(range(190, 236, 5))
D_LIST = [0.10, 0.13, 0.16, 0.19, 0.22]
LAM0 = 619.4

lam = np.full((len(D_LIST), len(A_LIST)), np.nan); Q = lam.copy(); fb = lam.copy(); lb = lam.copy(); mfeat = lam.copy()
rows = []
for fn in glob.glob(str(RD / 'data' / 'ad_a*_d*.npz')):
    d = np.load(fn)
    ia, idd = A_LIST.index(int(d['a'])), D_LIST.index(round(float(d['d']), 2))
    c = json.loads(str(d['cfg']))
    mfeat[idd, ia] = min(min_features(layout(c['a_m'], c['hx_m'], c['hy_m'], c['M'], c['n_mirror'], c['d'],
                                             c['eta'], c['xi'], c['chi']), c['w']).values())
    ok = d['Q_opt'] > 1e3
    if ok.any():
        i = np.where(ok)[0][np.argmax(d['loc_opt'][ok])]
        lam[idd, ia] = 299792.458 / (d['f_opt'][i] / 1e12); Q[idd, ia] = d['Q_opt'][i]
    okb = (d['B'] > 0.5) & (d['loc_mech'] > 0.5) & (d['f_mech'] > 5e9)
    if okb.any():
        ib = np.where(okb)[0][np.argmax(d['loc_mech'][okb])]
        fb[idd, ia] = d['f_mech'][ib] / 1e9; lb[idd, ia] = d['loc_mech'][ib]
    rows.append([int(d['a']), float(d['d']), lam[idd, ia], Q[idd, ia], fb[idd, ia], lb[idd, ia], float(d['bridge_min'])])
n_done = len(rows)
print(f'{n_done}/{len(A_LIST) * len(D_LIST)} points')
with open(RD / 'ad_summary.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['a_nm', 'd', 'lambda_nm', 'Q_opt', 'f_breathing_GHz', 'breathing_localization', 'min_bridge_nm'])
    w.writerows(sorted(rows))

# 619 nm crossing a(d) by linear interpolation along a
cross = []
for idd, D in enumerate(D_LIST):
    L = lam[idd]; m = np.isfinite(L)
    if m.sum() >= 2 and np.nanmin(L) < LAM0 < np.nanmax(L):
        A = np.array(A_LIST)[m]; o = np.argsort(L[m])
        ac = float(np.interp(LAM0, L[m][o], A[o]))
        qc = float(10 ** np.interp(ac, A, np.log10(Q[idd][m])))
        fc = float(np.interp(ac, A, fb[idd][m])) if np.isfinite(fb[idd][m]).all() else np.nan
        cross.append((D, ac, qc, fc))
        print(f'd={D:.2f}: 619 nm at a = {ac:.1f} nm, Q ~ {qc:.2g}, breathing ~ {fc:.2f} GHz')

def text_color(cm, x):
    r, g, b, _ = cm(float(np.clip(x, 0, 1)))
    return 'white' if 0.299 * r + 0.587 * g + 0.114 * b < 0.5 else 'k'


ext = [A_LIST[0] - 2.5, A_LIST[-1] + 2.5, D_LIST[0] - 0.015, D_LIST[-1] + 0.015]
fig, axes = plt.subplots(1, 4, figsize=(22, 5.2))
panels = [(lam - LAM0, 'RdBu_r', (-60, 60), 'resonance - 619 nm (nm)', lam, '{:.0f}'),
          (np.log10(Q), 'viridis', (3, 8), 'log$_{10}$ Q$_o$', Q, '{:.0e}'),
          (fb - 10, 'RdBu_r', (-1.5, 1.5), 'breathing - 10 GHz (GHz)', fb, '{:.2f}'),
          (lb, 'magma', (0.5, 1.0), 'localization', lb, '{:.2f}')]
for ax, (Z, cmap, (vmin, vmax), lab, raw, fmt) in zip(axes, panels):
    cm = plt.get_cmap(cmap).copy(); cm.set_bad('0.88')
    im = ax.imshow(np.ma.masked_invalid(Z), origin='lower', aspect='auto', extent=ext, cmap=cm, vmin=vmin, vmax=vmax)
    for idd, D in enumerate(D_LIST):
        for ia, A in enumerate(A_LIST):
            if np.isfinite(raw[idd, ia]):
                s = fmt.format(raw[idd, ia]).replace('e+0', 'e')
                ax.text(A, D, s, ha='center', va='center', fontsize=6.5,
                        color=text_color(cm, (Z[idd, ia] - vmin) / (vmax - vmin)))
    for idd, D in enumerate(D_LIST):
        for ia, A in enumerate(A_LIST):
            if np.isfinite(mfeat[idd, ia]) and mfeat[idd, ia] < MIN_FEATURE:
                ax.add_patch(plt.Rectangle((A - 2.5, D - 0.015), 5, 0.03, fc='none', ec='0.3', hatch='///', lw=0))
    ax.set_xticks(A_LIST); ax.set_yticks(D_LIST); ax.tick_params(labelsize=8)
    ax.set_xlabel('mirror period a (nm)'); ax.set_ylabel('taper depth d')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, label=lab)
axes[0].set_title('optical cavity resonance (nm)', fontweight='bold')
axes[1].set_title('optical Q', fontweight='bold')
axes[2].set_title('breathing mode (GHz)', fontweight='bold')
axes[3].set_title('breathing localization', fontweight='bold')
fig.suptitle(f'619 nm cavity, (a, d) sweep: w 550, t 120, hx/a 0.53, hy/w 0.77, Oh taper shape   [{n_done}/50 points; hatched < 60 nm feature]',
             fontsize=12, fontweight='bold')
fig.tight_layout()
fig.savefig(RD / 'ad_sweep.png', dpi=140, facecolor='white')
print(f'Saved {RD}/ad_sweep.png')
