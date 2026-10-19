"""fit_clean.py -- breathing f surrogate on clean breathing modes only (loc >= 0.8, 8 < fb < 12.5 GHz), and loc surrogate."""
import warnings
from pathlib import Path
import numpy as np, pandas as pd
from fit_surrogates import X_of, kernels, cv, X_COLS
warnings.filterwarnings('ignore')
df = pd.read_csv(Path(__file__).parent / 'data' / 'points.csv')
clean = df['loc'].ge(0.8) & df.fb.between(8, 12.5)
print('clean breathing points:', clean.sum(), 'of', len(df))
X = X_of(df)
for tgt, mask in (('fb', clean), ('fbw', clean), ('loc', df['loc'].notna())):
    y = (df.fb * df.w / 650).values if tgt == 'fbw' else df[tgt if tgt != 'fbw' else 'fb'].values
    m = mask.values
    print(f'== {tgt}  ({m.sum()} pts)')
    for name in ('Matern52 ARD', 'Matern52 shared', 'Matern32 ARD'):
        k = kernels(len(X_COLS))[name]
        pred, psd = cv(X[m], y[m], lambda k=k: k)
        err = pred - y[m]
        if tgt == 'fbw': err = err * 650 / df.w.values[m]
        r2 = 1 - np.sum((pred - y[m])**2) / np.sum((y[m] - y[m].mean())**2)
        print(f'  {name:16s} RMSE {np.sqrt(np.mean(err**2)):.3f}  R2 {r2:.3f}  cov {np.mean(np.abs(pred-y[m]) < 1.96*psd):.2f}')
