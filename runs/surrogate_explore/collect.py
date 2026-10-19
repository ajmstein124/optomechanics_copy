"""collect.py (Mac): pull bo*.npz from the remote, convert to data/bo_results.csv (same columns as points.csv) and
print predicted vs observed per batch (Roman's guide: predictions are saved before evaluating)."""
import glob
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from cavity_designs import opt_mode, breathing   # noqa: E402
from cavity_taper import layout, min_features    # noqa: E402

if '--no-pull' not in sys.argv:
    subprocess.run(f'scp -q -i ~/.ssh/id_ed25519 "<USER>@<COMSOL_HOST>:C:/Users/abby/comsol/runs/surrogate_explore/data/bo*.npz" '
                   f'"{HERE}/data/"', shell=True)
rows = []
for fn in sorted(glob.glob(str(HERE / 'data' / 'bo*.npz'))):
    z = np.load(fn, allow_pickle=True)
    if 'skipped' in z and bool(z['skipped']):
        print(Path(fn).name, 'SKIPPED'); continue
    c = json.loads(str(z['cfg'])); lx = bool(c.get('lock_x', False))
    lam, Q = opt_mode(z); fb, lb = breathing(z)
    loc3 = clamp = np.nan
    if 'loc_mech3' in z and np.isfinite(fb):
        i_b = int(np.argmin(np.abs(z['f_mech'] / 1e9 - fb)))
        loc3, clamp = float(z['loc_mech3'][i_b]), float(z['clamp_frac'][i_b])
    mf = min(min_features(layout(c['a_m'], c['hx_m'], c['hy_m'], c.get('M', 10), c.get('n_mirror', 10), c['d'], 1.0, c['xi'], c['chi'], lx), c['w']).values())
    row = dict(run='bo', kind=Path(fn).stem, w=c['w'], hx_a=c['hx_m'] / c['a_m'], hy_w=c['hy_m'] / c['w'], d=c['d'], xi=c['xi'],
               chi=c['chi'], a=c['a_m'], lock_x=int(lx), M=c.get('M', 10), n_mirror=c.get('n_mirror', 10), swa=c.get('swa', 0.0), lam=lam, Q=Q, fb=fb, loc=lb, min_feature=mf, why=str(z['why']), loc3=loc3, clamp=clamp)
    for k in ('lam', 'logQ', 'fb', 'sd_logQ', 'sd_fb'):
        row[f'pred_{k}'] = float(z[f'pred_{k}']) if f'pred_{k}' in z else np.nan
    rows.append(row)
df = pd.DataFrame(rows)
df.to_csv(HERE / 'data' / 'bo_results.csv', index=False)
if len(df):
    df['logQ'] = np.log10(df.Q)
    with pd.option_context('display.width', 250, 'display.max_columns', 30):
        print(df[['kind', 'why', 'w', 'hx_a', 'hy_w', 'd', 'xi', 'chi', 'lock_x', 'M', 'n_mirror', 'swa', 'a', 'lam', 'pred_lam', 'logQ', 'pred_logQ',
                  'fb', 'pred_fb', 'loc', 'loc3', 'clamp', 'min_feature']].round(3).to_string(index=False))
