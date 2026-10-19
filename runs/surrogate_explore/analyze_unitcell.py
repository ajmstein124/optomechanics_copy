"""analyze_unitcell.py (Mac): COMSOL unit-cell proxy (uc_*.npz: breathing-class Gamma modes, cavity-family X bands) vs the
full-cavity results in points.csv. Which unit-cell band tracks the cavity breathing mode, and how well?"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from cavity_taper import layout   # noqa: E402

df = pd.read_csv(HERE / 'data' / 'points.csv')
uc = {}
for fn in (HERE / 'data').glob('uc_*.npz'):
    z = np.load(fn); uc[fn.stem[3:]] = (z['f_mech_G'] / 1e9, z['f_opt_X'] / 1e12, float(z['light_line_X']) / 1e12)


def tag(w, a, hx, hy):
    return f"w{w:.0f}_a{a:.2f}_hx{hx:.2f}_hy{hy:.2f}"


rows = []
for r in df.itertuples():
    L = layout(r.a, r.hx_a * r.a, r.hy_w * r.w, 10, 10, r.d, 1.0, r.xi, r.chi, bool(r.lock_x))
    tc = tag(r.w, round(L['a'][0], 2), round(L['hx'][0], 2), round(L['hy'][0], 2))
    tm = tag(r.w, round(L['a'][20], 2), round(L['hx'][20], 2), round(L['hy'][20], 2))
    if tc in uc and tm in uc:
        rows.append(dict(i=r.Index, fb=r.fb, loc=r.loc, lam=r.lam, Q=r.Q, w=r.w, d=r.d,
                         cG=uc[tc][0], mG=uc[tm][0], cX=uc[tc][1][uc[tc][1] < uc[tc][2]], mX=uc[tm][1][uc[tm][1] < uc[tm][2]]))
print(len(rows), 'designs with both cells solved')
clean = [q for q in rows if q['loc'] >= 0.8 and 8 < q['fb'] < 12.5]
# which Gamma band index is nearest the cavity breathing mode?
idx_c = [int(np.argmin(np.abs(q['cG'] - q['fb']))) for q in clean]
idx_m = [int(np.argmin(np.abs(q['mG'] - q['fb']))) for q in clean]
print('nearest center-cell Gamma band index:', np.bincount(idx_c), '| mirror:', np.bincount(idx_m))
kc = int(np.bincount(idx_c).argmax()); km = int(np.bincount(idx_m).argmax())
fb = np.array([q['fb'] for q in clean]); fc = np.array([q['cG'][kc] for q in clean]); fm = np.array([q['mG'][km] for q in clean])
for name, x in (('center cell', fc), ('mirror cell', fm)):
    A = np.polyfit(x, fb, 1); res = fb - np.polyval(A, x)
    print(f'cavity breathing vs {name} Gamma band {kc if name[0]=="c" else km}: slope {A[0]:.2f}, rms {res.std():.3f} GHz, R2 {1-res.var()/fb.var():.3f}; '
          f'mean (cavity - cell) {np.mean(fb - x):+.3f} GHz')
X = np.column_stack([fc, fm, np.ones_like(fc)]); b = np.linalg.lstsq(X, fb, rcond=None)[0]; res = fb - X @ b
print(f'cavity breathing ~ {b[0]:.2f} center + {b[1]:.2f} mirror + {b[2]:.2f}: rms {res.std():.3f} GHz, R2 {1-res.var()/fb.var():.3f}')
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
for k, (x, lab) in enumerate(((fc, f'center-cell Γ breathing band (GHz)'), (fm, 'mirror-cell Γ breathing band (GHz)'))):
    sc = ax[k].scatter(x, fb, c=[q['w'] for q in clean], cmap='viridis', s=18)
    lo, hi = min(x.min(), fb.min()), max(x.max(), fb.max()); ax[k].plot([lo, hi], [lo, hi], 'k:', lw=0.8)
    ax[k].set_xlabel(lab); ax[k].set_ylabel('cavity breathing (GHz, COMSOL)')
fig.colorbar(sc, ax=ax[1], label='w (nm)'); fig.tight_layout(); fig.savefig(HERE / 'figures' / 'unitcell_vs_cavity.png', dpi=140)
