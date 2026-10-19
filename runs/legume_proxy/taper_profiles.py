"""
taper_profiles.py  (Mac, pccsim_main venv)  -- runs/legume_proxy
For every solved cavity design (runs/surrogate_explore/data/points.csv + bo_results.csv): legume X-point bands 1 and 2
(cavity family) of each taper cell j = 0..20, calibrated to COMSOL (cal_band{1,2}.npy, 72 unit cells w >= 550: 1.0 / 0.4 nm).
Saves profiles.npz: per design f1[j], f2[j] (THz), x[j] (nm), plus the design columns.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from cavity_taper import layout   # noqa: E402
from nb_pccsim import bands_X     # noqa: E402

CAL = [np.load(HERE / f'cal_band{b}.npy') for b in (1, 2)]


def calibrate(l, w, a, hxa, hyw, coef):
    return coef @ np.array([l, l * w / a, l * hxa, l * hyw, 1.0])


def profile(r):
    L = layout(r.a, r.hx_a * r.a, r.hy_w * r.w, 10, 10, r.d, 1.0, r.xi, r.chi, bool(r.lock_x))
    f1 = np.full(21, np.nan); f2 = np.full(21, np.nan)
    for j in range(21):
        a, hx, hy = L['a'][j], L['hx'][j], L['hy'][j]
        f, _ = bands_X(r.w, a, hx, hy, gmax=4.01)
        if f.size >= 2:
            f1[j] = calibrate(f[0], r.w, a, hx / a, hy / r.w, CAL[0])
            f2[j] = calibrate(f[1], r.w, a, hx / a, hy / r.w, CAL[1])
    return L['x'], f1, f2


if __name__ == '__main__':
    dfs = [pd.read_csv(ROOT / 'runs/surrogate_explore/data/points.csv')]
    bo = ROOT / 'runs/surrogate_explore/data/bo_results.csv'
    if bo.exists() and bo.stat().st_size > 10:
        dfs.append(pd.read_csv(bo))
    df = pd.concat(dfs, ignore_index=True)
    out = HERE / 'profiles.npz'
    t0 = time.time(); X, F1, F2 = [], [], []
    for i, r in enumerate(df.itertuples()):
        x, f1, f2 = profile(r); X.append(x); F1.append(f1); F2.append(f2)
        if i % 20 == 0:
            print(f'{i}/{len(df)} ({time.time()-t0:.0f} s)', flush=True)
    np.savez(out, x=np.array(X), f1=np.array(F1), f2=np.array(F2), **{c: df[c].values for c in df.columns if df[c].dtype != object},
             run=df.run.values.astype(str), kind=df.kind.values.astype(str))
    print('done', out, f'{time.time()-t0:.0f} s')
