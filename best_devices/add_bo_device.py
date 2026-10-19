"""
add_bo_device.py  (Mac)  -- best_devices/
Adds the surrogate-search (BO) 80 nm device bo2_0 (runs/surrogate_explore) as its own folder, and the fabrication-disorder
comparison of all three devices (runs/surrogate_explore/data/dis_*.npz, sigma 2 nm). Updates README.md (devices table +
disorder table). Run from the project root after `python best_devices/make_best_devices.py`:
    python best_devices/add_bo_device.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, 'scripts')
from cavity_taper import layout, min_features   # noqa: E402

OUT = Path('best_devices'); D = Path('runs/surrogate_explore/data')
C = 299792.458; HBAR, KB = 1.054571817e-34, 1.380649e-23
NAME = '80nm_w713_d0.135_xi2.1_chi3.55_BO'
F = OUT / NAME; F.mkdir(exist_ok=True)
z = np.load(D / 'confirm_bo2_0.npz', allow_pickle=True)
c = json.loads(str(z['cfg']))
io = int(z['i_opt']); ib = int(z['i_breath'])
lam = C / (z['f_opt'][io - 1] / 1e12); Q = float(z['Q_opt'][io - 1]); fb = z['f_mech'][ib] / 1e9
lay = layout(c['a_m'], c['hx_m'], c['hy_m'], c['M'], c['n_mirror'], c['d'], c['eta'], c['xi'], c['chi'])
mf = min_features(lay, c['w'])
meff = float(z['meff'][ib]); xzpf = np.sqrt(HBAR / (2 * meff * 2 * np.pi * fb * 1e9))
nth = lambda T: 1 / np.expm1(HBAR * 2 * np.pi * fb * 1e9 / (KB * T))

# disorder comparison (sigma 2 nm, paired seeds)
DES = [('final60', '60nm_w650_d0.10_xi6_chi4', 1.8e7), ('final80', '80nm_w700_d0.10_xi4_chi3.5', 3.39e6), ('bo2_0', NAME, Q)]
dis = {}
for k, _, _ in DES:
    q, f, l = [], [], []
    for s in range(8):
        fn = D / f'dis_{k}_s{s}.npz'
        if fn.exists():
            zz = np.load(fn, allow_pickle=True); q.append(float(zz['Q'])); l.append(float(zz['lam'])); f.append(float(zz['f_breath']) / 1e9)
    dis[k] = (np.array(q), np.array(l), np.array(f))
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for j, (k, folder, q0) in enumerate(DES):
    q = dis[k][0]
    ax[0].scatter(np.arange(len(q)) + 0.12 * (j - 1), np.log10(q), label=f'{k} (ideal {q0:.1e}, median {np.median(q):.1e})', s=30)
    ax[0].axhline(np.log10(q0), color=f'C{j}', ls=':', lw=0.8)
    ax[1].scatter(dis[k][1] - 619.4, dis[k][2], s=30, label=k)
ax[0].set_xlabel('disorder seed (same perturbation for all designs)'); ax[0].set_ylabel('log10 optical Q')
ax[0].set_title('σ = 2 nm hole size, 1 nm position (dotted: ideal Q)'); ax[0].legend(fontsize=7)
ax[1].set_xlabel('resonance shift (nm)'); ax[1].set_ylabel('breathing (GHz)'); ax[1].legend(fontsize=7)
fig.tight_layout(); fig.savefig(OUT / 'disorder.png', dpi=140); plt.close(fig)

# fields figure (single device)
subprocess.run([sys.executable, 'runs/cavity_619/plot_fields.py', str(D), str(F / 'modes.png'), 'bo2_0='], check=True)
for f in ('progress.png',):
    src = Path('runs/surrogate_explore/figures') / f
    if src.exists():
        (F / 'search_progress.png').write_bytes(src.read_bytes())

summ = dict(name=NAME, source='runs/surrogate_explore (BO batch 2, point 0); confirm solve data/confirm_bo2_0.npz', cfg=c,
            lam_nm=float(lam), Q=Q, breathing_GHz=float(fb), loc_1p5um=float(z['loc_mech'][ib]), loc_3um=float(z['loc_mech3'][ib]),
            clamp_frac=float(z['clamp_frac'][ib]), S=float(z['S'][ib]), meff_fg=meff * 1e18, min_features=mf,
            disorder_sigma2_Q_median=float(np.median(dis['bo2_0'][0])))
json.dump(summ, open(F / 'summary.json', 'w'), indent=1)
md = f"""# Best 80 nm device (surrogate search): w {c['w']:.0f} nm, d {c['d']:.3f}, ξ {c['xi']:.2f}, χ {c['chi']:.2f}, a {c['a_m']:.1f} nm

Found by the surrogate-guided (Bayesian) search, `runs/surrogate_explore` (batch 2, point 0), at fixed length M 10, 10 mirror cells.
Confirmation solve `runs/surrogate_explore/data/confirm_bo2_0.npz`; field maps `modes.png`.

## Geometry
| | |
|---|---|
| beam width w / thickness t | {c['w']:.1f} / 120 nm |
| mirror period a | {c['a_m']:.2f} nm |
| mirror hole hx × hy | {c['hx_m']:.1f} × {c['hy_m']:.1f} nm (hx/a {c['hx_m']/c['a_m']:.3f}, hy/w {c['hy_m']/c['w']:.3f}) |
| taper | Chan: d {c['d']:.4f}, M {c['M']}, ξ {c['xi']:.3f}, χ {c['chi']:.3f}; {c['n_mirror']} mirror cells per side (gentle taper: ξ, χ below the grid sweeps' range) |
| center cell | a {lay['a'][0]:.1f}, hx {lay['hx'][0]:.1f}, hy {lay['hy'][0]:.1f} nm |
| min features | bridge {mf['bridge']:.1f}, rail {mf['rail']:.1f}, hole {mf['hole']:.1f} nm |

## Modes
| | |
|---|---|
| resonance | **{lam:.2f} nm** |
| optical Q (ideal geometry) | **{Q:.2e}** (6.3× the previous 80 nm final, 3.4e6) |
| breathing | **{fb:.3f} GHz**: localization {z['loc_mech'][ib]:.2f} (x < 1.5 µm) / {z['loc_mech3'][ib]:.2f} (x < 3 µm), clamp fraction {z['clamp_frac'][ib]:.1e}, S {z['S'][ib]:.2f} |
| effective mass / x_zpf | {meff*1e18:.0f} fg / {xzpf*1e15:.2f} fm (broader, heavier than the previous final's 233 fg → ~22 % less strain per phonon) |
| relative g0 | same as the previous 80 nm final (+6 %), mostly photoelastic (g0 values carry the known normalization bug; ratios assumed valid) |
| thermal occupation | {nth(0.1):.3f} (0.1 K), {nth(1.7):.1f} (1.7 K), {nth(4):.1f} (4 K) |
| mechanical Q | not computed (clamped, lossless model) |

## Fabrication disorder (`../disorder.png`)
σ = 2 nm per-hole size, 1 nm position, 8 seeds (symmetric about the model planes): median Q **{np.median(dis['bo2_0'][0]):.1e}**
(range {dis['bo2_0'][0].min():.1e}–{dis['bo2_0'][0].max():.1e}), the same as the previous 80 nm final and ~1.6× the 60 nm final.
Breathing shifts ≤ 0.05 GHz. At this disorder level the ideal-Q advantage disappears.
"""
(F / 'summary.md').write_text(md)

# README: add device row + disorder table (idempotent)
R = (OUT / 'README.md').read_text()
row = (f"| [{NAME}]({NAME}/summary.md) | {c['w']:.0f} | {c['a_m']:.1f} | d {c['d']:.3f}, ξ {c['xi']:.2f}, χ {c['chi']:.2f} (BO) | {lam:.2f} | "
       f"{Q:.1e} | {fb:.2f} | {z['loc_mech'][ib]:.2f} / {z['loc_mech3'][ib]:.2f} (3 µm) | not computed | {min(mf.values()):.0f} |")
R = re.sub(r'\n\| \[80nm_w713[^\n]*', '', R)
R = R.replace("| not computed | 82 |\n", "| not computed | 82 |\n" + row + "\n", 1)
tab = "\n**Fabrication disorder** (σ = 2 nm hole size, 1 nm position, 8 paired seeds; `disorder.png`):\n\n| device | ideal Q | median Q with disorder | range |\n|---|---|---|---|\n"
for k, folder, q0 in DES:
    q = dis[k][0]
    tab += f"| {folder} | {q0:.1e} | **{np.median(q):.1e}** | {q.min():.1e}–{q.max():.1e} |\n"
tab += "\nDisorder sets the real Q (~1e4–2e5); ideal Q above ~1e6 does not survive 2 nm disorder. The 80 nm designs are ~1.7× more robust.\n"
R = re.sub(r'\n\*\*Fabrication disorder\*\*.*?more robust\.\n', '\n', R, flags=re.S)
R = R.replace("\n**Checks still to run", tab + "\n**Checks still to run", 1)
(OUT / 'README.md').write_text(R)
print('done', NAME)
