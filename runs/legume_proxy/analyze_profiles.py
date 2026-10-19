"""
analyze_profiles.py  (Mac)  -- runs/legume_proxy
Physics features from the legume taper profiles (profiles.npz) vs the COMSOL cavity results:
  1. cavity resonance vs center-cell band-1 edge (local band-edge picture)
  2. Quan & Loncar (Opt. Express 19, 18529, 2011) mirror strength per cell
       gamma_j = sqrt( ((f2-f1)/(f2+f1))^2 - ((f_res - f0)/f0)^2 ),  f0 = (f1+f2)/2
     features: gamma at the mirror, slope d gamma/dx and linearity (R^2) over the taper, cavity half-width where gamma
     turns on, largest cell-to-cell band-edge jump, resonance detuning above the center-cell edge.
  3. how well the features alone predict log10 Q (CV), vs the geometric GP (0.10 dex).
Figures -> runs/legume_proxy/figures/.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel as C, Matern, WhiteKernel
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_predict

HERE = Path(__file__).resolve().parent
FIG = HERE / 'figures'; FIG.mkdir(exist_ok=True)
CNT = 299792.458


def features(z):
    f1, f2, x = z['f1'], z['f2'], z['x']
    fres = CNT / z['lam']
    f0 = (f1 + f2) / 2
    g2 = ((f2 - f1) / (f2 + f1)) ** 2 - ((fres[:, None] - f0) / f0) ** 2
    gam = np.sqrt(np.clip(g2, 0, None))
    F = {}
    F['det_center'] = (fres - f1[:, 0]) / f1[:, 0]                 # resonance above the center-cell dielectric edge
    F['gam_mirror'] = gam[:, -1]
    F['jump_max'] = np.nanmax(np.abs(np.diff(f1, axis=1)), axis=1) / f1[:, -1]
    slope, lin, x_on = [], [], []
    for i in range(len(fres)):
        m = gam[i] > 0
        if m.sum() >= 3:
            A = np.polyfit(x[i][m], gam[i][m], 1); pr = np.polyval(A, x[i][m])
            slope.append(A[0] * 1e3); lin.append(1 - np.var(gam[i][m] - pr) / max(np.var(gam[i][m]), 1e-12))
            x_on.append(x[i][m][0])
        else:
            slope.append(np.nan); lin.append(np.nan); x_on.append(np.nan)
    F['gam_slope'] = np.array(slope); F['gam_lin'] = np.array(lin); F['x_on'] = np.array(x_on)
    return F, gam


if __name__ == '__main__':
    z = dict(np.load(HERE / 'profiles.npz', allow_pickle=True))
    ok = np.isfinite(z['lam']) & np.all(np.isfinite(z['f1']), axis=1) & np.all(np.isfinite(z['f2']), axis=1)
    z = {k: (v[ok] if np.ndim(v) and len(v) == len(ok) else v) for k, v in z.items()}
    F, gam = features(z)
    logQ = np.log10(z['Q'])
    # 1. resonance vs center-cell edge
    fres = CNT / z['lam']
    A = np.polyfit(z['f1'][:, 0], fres, 1); res = fres - np.polyval(A, z['f1'][:, 0])
    print(f'resonance vs center-cell band-1 edge: fit RMSE {res.std():.2f} THz = {res.std()/fres.mean()*619:.2f} nm; '
          f'mean detuning above edge {np.mean(F["det_center"])*100:.2f} %  (sd {np.std(F["det_center"])*100:.2f} %)')
    # 2/3. features -> logQ
    names = ['det_center', 'gam_mirror', 'jump_max', 'gam_slope', 'gam_lin', 'x_on']
    Xf = np.column_stack([F[n] for n in names]); good = np.all(np.isfinite(Xf), axis=1)
    print(f'{good.sum()} designs with all features')
    for n in names:
        r = np.corrcoef(F[n][good], logQ[good])[0, 1]
        print(f'  corr(logQ, {n:10s}) = {r:+.2f}')
    Xs = (Xf[good] - Xf[good].mean(0)) / Xf[good].std(0)
    kf = KFold(10, shuffle=True, random_state=1)
    for name, model in (('linear', LinearRegression()),
                        ('GP Matern52 ARD', GaussianProcessRegressor(C(1.0) * Matern(np.ones(len(names)), nu=2.5) + WhiteKernel(1e-2), normalize_y=True, n_restarts_optimizer=3))):
        pr = cross_val_predict(model, Xs, logQ[good], cv=kf)
        print(f'  physics features -> logQ, {name}: CV RMSE {np.sqrt(np.mean((pr-logQ[good])**2)):.3f} dex, '
              f'R2 {1-np.var(pr-logQ[good])/np.var(logQ[good]):.3f}')
    # figures
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    ax[0].scatter(z['f1'][:, 0], fres, c=logQ, s=14, cmap='viridis'); ax[0].plot(z['f1'][:, 0], np.polyval(A, z['f1'][:, 0]), 'k-', lw=0.8)
    ax[0].set_xlabel('center-cell band-1 edge at X (THz, legume cal.)'); ax[0].set_ylabel('cavity resonance (THz, COMSOL)')
    ax[0].set_title(f'local band edge predicts resonance ({res.std()/fres.mean()*619:.1f} nm rms)')
    for k, (n, lab) in enumerate((('gam_lin', 'mirror-strength linearity R² over the taper'), ('gam_mirror', 'mirror strength at mirror cell'))):
        sc = ax[k + 1].scatter(F[n], logQ, c=z['d'], s=14, cmap='plasma'); ax[k + 1].set_xlabel(lab); ax[k + 1].set_ylabel('log10 Q (COMSOL)')
    fig.colorbar(sc, ax=ax[2], label='d')
    fig.tight_layout(); fig.savefig(FIG / 'profile_features.png', dpi=140)
    # example profiles: best, median, worst Q
    fig, ax = plt.subplots(1, 3, figsize=(15, 3.8))
    for k, i in enumerate((np.argmax(logQ), np.argsort(logQ)[len(logQ) // 2], np.argmin(logQ))):
        x = z['x'][i]
        ax[k].fill_between(x, z['f1'][i], z['f2'][i], color='0.85', label='local gap (band 1 to 2)')
        ax[k].axhline(fres[i], color='C3', lw=1, label='cavity resonance')
        ax2 = ax[k].twinx(); ax2.plot(x, gam[i], 'C0.-', lw=1); ax2.set_ylabel('mirror strength γ', color='C0')
        ax[k].set_title(f"w {z['w'][i]:.0f} d {z['d'][i]:.2f} ξ {z['xi'][i]:g} χ {z['chi'][i]:g}: Q {z['Q'][i]:.1e}", fontsize=9)
        ax[k].set_xlabel('x (nm)'); ax[k].set_ylabel('THz')
    ax[0].legend(fontsize=7, loc='lower right')
    fig.tight_layout(); fig.savefig(FIG / 'profile_examples.png', dpi=140)
    np.savez(HERE / 'features.npz', **F, logQ=logQ, keep=good)
