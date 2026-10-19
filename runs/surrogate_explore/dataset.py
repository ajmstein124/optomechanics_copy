"""
dataset.py  (Mac)  -- runs/surrogate_explore
Collect every solved 1D-cavity point (ad_/sh_ npz from all 619 nm pipelines) into one table for surrogate modeling
(Roman's disciplined-exploration guide, 2026-10-16). Inputs: w, hx/a, hy/w, d, xi, chi, a, lock_x (n_mirror = 10 only).
Outputs: lam (nm), log10 Q, breathing f (GHz, NaN if no clean breathing mode), breathing localization.
Writes runs/surrogate_explore/data/points.csv.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from cavity_designs import points          # noqa: E402
from cavity_taper import layout, min_features   # noqa: E402

RUNS = ['runs/cavity_619', 'runs/cavity_619_mf80'] + sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'runs/cavity_619_width').glob('w*_mf*'))


def build():
    rows = []
    for rd in RUNS:
        for q in points(ROOT / rd):
            c = q['cfg']
            lx = bool(c.get('lock_x', False))
            mf = min_features(layout(c['a_m'], c['hx_m'], c['hy_m'], c.get('M', 10), c.get('n_mirror', 10), c['d'], c['eta'], c['xi'], c['chi'], lx), c['w'])
            rows.append(dict(run=rd.split('/')[-1], kind=q['kind'], w=c['w'], hx_a=c['hx_m'] / c['a_m'], hy_w=c['hy_m'] / c['w'],
                             d=c['d'], xi=c['xi'], chi=c['chi'], a=c['a_m'], lock_x=int(lx), M=c.get('M', 10), n_mirror=c.get('n_mirror', 10), lam=q['lam'], Q=q['Q'],
                             fb=q['fb'], loc=q['lb'], min_feature=min(mf.values())))
    df = pd.DataFrame(rows).drop_duplicates(subset=['w', 'hx_a', 'hy_w', 'd', 'xi', 'chi', 'a', 'lock_x', 'M', 'n_mirror'])
    out = Path(__file__).parent / 'data'; out.mkdir(exist_ok=True)
    df.to_csv(out / 'points.csv', index=False)
    return df


if __name__ == '__main__':
    df = build()
    print(len(df), 'points'); print(df.groupby('run').size())
    print(df[['w', 'hx_a', 'hy_w', 'd', 'xi', 'chi', 'a']].describe().loc[['min', 'max']])
    print('breathing found:', df.fb.notna().sum(), '| lam range', df.lam.min(), df.lam.max())
