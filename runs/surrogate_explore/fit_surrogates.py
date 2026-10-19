"""
fit_surrogates.py  (Mac)  -- runs/surrogate_explore
GP surrogates on points.csv, validated by 10-fold cross-validation (Roman's guide, Stage 6): inputs scaled to [0, 1],
outputs standardized, kernels Matern-5/2 ARD / shared, Matern-3/2 ARD, RBF ARD (+ small white noise), vs a linear baseline.
Targets: lam/a (removes the trivial period scaling), log10 Q, breathing f (GHz).
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel as C, Matern, RBF, WhiteKernel
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold

warnings.filterwarnings('ignore')
X_COLS = ['w', 'hx_a', 'hy_w', 'd', 'xi', 'chi', 'a', 'lock_x']
BOUNDS = dict(w=(550, 700), hx_a=(0.45, 0.53), hy_w=(0.70, 0.77), d=(0.07, 0.22), xi=(2, 10), chi=(3, 6), a=(175, 240), lock_x=(0, 1))


def X_of(df):
    return np.column_stack([(df[c] - BOUNDS[c][0]) / (BOUNDS[c][1] - BOUNDS[c][0]) for c in X_COLS])


def kernels(n):
    return {'Matern52 ARD': C(1.0) * Matern(np.ones(n), nu=2.5) + WhiteKernel(1e-4, (1e-8, 1e-1)),
            'Matern52 shared': C(1.0) * Matern(1.0, nu=2.5) + WhiteKernel(1e-4, (1e-8, 1e-1)),
            'Matern32 ARD': C(1.0) * Matern(np.ones(n), nu=1.5) + WhiteKernel(1e-4, (1e-8, 1e-1)),
            'RBF ARD': C(1.0) * RBF(np.ones(n)) + WhiteKernel(1e-4, (1e-8, 1e-1))}


def fit(X, y, kern):
    mu, sd = y.mean(), y.std()
    gp = GaussianProcessRegressor(kern, normalize_y=False, n_restarts_optimizer=3, random_state=0)
    gp.fit(X, (y - mu) / sd)
    return gp, mu, sd


def cv(X, y, make, k=10):
    pred = np.zeros_like(y); psd = np.zeros_like(y)
    for tr, te in KFold(k, shuffle=True, random_state=1).split(X):
        m = make()
        if isinstance(m, LinearRegression):
            m.fit(X[tr], y[tr]); pred[te] = m.predict(X[te]); psd[te] = np.nan
        else:
            gp, mu, sd = fit(X[tr], y[tr], m)
            p, s = gp.predict(X[te], return_std=True); pred[te] = p * sd + mu; psd[te] = s * sd
    return pred, psd


if __name__ == '__main__':
    df = pd.read_csv(Path(__file__).parent / 'data' / 'points.csv')
    df['lam_a'] = df.lam / df.a; df['logQ'] = np.log10(df.Q)
    X = X_of(df)
    for tgt, unit in (('lam_a', 'lam (nm)'), ('logQ', 'log10 Q'), ('fb', 'GHz')):
        ok = df[tgt].notna().values
        y = df[tgt].values[ok]; Xo = X[ok]
        print(f'\n== {tgt} ({ok.sum()} points), CV RMSE in {unit}')
        cands = dict(kernels(len(X_COLS)), linear=None)
        for name, k in cands.items():
            make = (lambda: LinearRegression()) if k is None else (lambda k=k: k)
            pred, psd = cv(Xo, y, make)
            err = pred - y
            if tgt == 'lam_a':
                err = err * df.a.values[ok]
            r2 = 1 - np.sum((pred - y) ** 2) / np.sum((y - y.mean()) ** 2)
            cover = np.mean(np.abs(pred - y) < 1.96 * psd) if np.isfinite(psd).all() else np.nan
            print(f'  {name:16s} RMSE {np.sqrt(np.mean(err**2)):.3f}  R2 {r2:.3f}  95% coverage {cover:.2f}')
