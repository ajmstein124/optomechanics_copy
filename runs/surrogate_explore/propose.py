"""
propose.py  (Mac)  -- runs/surrogate_explore
Surrogate-guided batch proposal for the 619 nm / <= 10 GHz nanobeam (2026-10-16). Scaffolding follows Roman's
pccsim strip_pcw_bayes/analysis.py (GP per output, Sobol candidates, gated acquisition, 8 proposals) and his
disciplined-exploration guide (validate first, mixed batches, save predictions before evaluating).

Differences from a plain BO loop:
  * the period a is SOLVED per candidate from the lam/a surrogate (CV RMSE 0.025 nm), so every evaluation is one
    COMSOL solve landing on 619.4 nm instead of a 2-3 solve bracket;
  * minimum feature is applied EXACTLY (cavity_taper.min_features) before acquisition;
  * breathing frequency is modeled only on clean breathing modes (loc >= 0.8, 8-12.5 GHz).
Objective: maximize log10 Q_opt at 619.4 nm.  Constraint: breathing <= F_MAX (probability from the fb GP).
Batch: N_EI constrained-EI picks (diversity-penalized), N_EXPLORE high-uncertainty picks, optional hypothesis
and replication points.

Usage: python runs/surrogate_explore/propose.py --mf 80 --batch 1 [--extra-csv data/bo_results.csv]
Writes runs/surrogate_explore/batch_<n>.json (cfgs + predictions) for eval_batch.py.
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel as C, Matern, WhiteKernel

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from cavity_taper import layout, min_features   # noqa: E402

warnings.filterwarnings('ignore')
LAM0 = 619.4
X_COLS = ['w', 'hx_a', 'hy_w', 'd', 'xi', 'chi', 'a', 'lock_x', 'M', 'n_mirror', 'swa']
NORM = dict(w=(550, 700), hx_a=(0.45, 0.53), hy_w=(0.70, 0.77), d=(0.07, 0.22), xi=(2, 10), chi=(3, 6), a=(175, 240), lock_x=(0, 1), M=(10, 16), n_mirror=(10, 15), swa=(0, 15))
M_CHOICES, NM_CHOICES, SWA, SWA_ON = [10], [10], 0.0, False
BOX = dict(w=(620, 800), hx_a=(0.42, 0.56), hy_w=(0.60, 0.80), d=(0.06, 0.16), xi=(2, 8), chi=(2.5, 5.5))


def Xn(df):
    return np.column_stack([(np.asarray(df[c], float) - NORM[c][0]) / (NORM[c][1] - NORM[c][0]) for c in X_COLS])


def gp(X, y, kernel):
    mu, sd = y.mean(), y.std()
    m = GaussianProcessRegressor(kernel, n_restarts_optimizer=4, random_state=0).fit(X, (y - mu) / sd)
    return lambda Z: _pred(m, Z, mu, sd)


def _pred(m, Z, mu, sd):
    p, s = m.predict(Z, return_std=True)
    return p * sd + mu, s * sd


def load(extra):
    df = pd.read_csv(HERE / 'data' / 'points.csv')
    for e in extra or []:
        if Path(e).exists():
            df = pd.concat([df, pd.read_csv(e)], ignore_index=True)
    df['swa'] = df['swa'].fillna(0.0) if 'swa' in df else 0.0
    df['lam_a'] = df.lam / df.a
    df['logQ'] = np.log10(df.Q)
    return df


def fit_all(df):
    n = len(X_COLS)
    ard52 = C(1.0) * Matern(np.ones(n), nu=2.5) + WhiteKernel(1e-4, (1e-8, 1e-1))
    ard32 = C(1.0) * Matern(np.ones(n), nu=1.5) + WhiteKernel(1e-4, (1e-8, 1e-1))
    sh52 = C(1.0) * Matern(1.0, nu=2.5) + WhiteKernel(1e-4, (1e-8, 1e-1))
    ok = df.lam.notna()
    f_lam = gp(Xn(df[ok]), df.lam_a[ok].values, ard52)
    f_q = gp(Xn(df[ok]), df.logQ[ok].values, ard32)
    l3 = df['loc3'] if 'loc3' in df else pd.Series(np.nan, index=df.index)
    cl = (df['loc'].ge(0.8) | l3.ge(0.9)) & df.fb.between(8, 12.5)      # clean breathing: 1.5 um or (new) 3 um window
    f_fb = gp(Xn(df[cl]), df.fb[cl].values, sh52)
    return f_lam, f_q, f_fb


def candidates(n_log2, seed, lock_frac=0.15):
    u = qmc.Sobol(6, scramble=True, seed=seed).random_base2(n_log2)
    keys = list(BOX)
    c = pd.DataFrame({k: BOX[k][0] + u[:, i] * (BOX[k][1] - BOX[k][0]) for i, k in enumerate(keys)})
    rng = np.random.default_rng(seed)
    c['lock_x'] = (rng.random(len(c)) < lock_frac).astype(int)
    c['M'] = rng.choice(M_CHOICES, len(c)); c['n_mirror'] = rng.choice(NM_CHOICES, len(c)); c['swa'] = SWA
    return c


def solve_a(c, f_lam, iters=4):
    a = np.full(len(c), 188.0)
    for _ in range(iters):
        c = c.assign(a=a)
        r, _ = f_lam(Xn(c))
        a = LAM0 / r
    return a


def feasible(c, mf):
    out = np.zeros(len(c), bool); mfe = np.zeros(len(c))
    for i, r in enumerate(c.itertuples()):
        if r.chi * r.d >= 0.95:
            continue
        try:
            m = min(min_features(layout(r.a, r.hx_a * r.a, r.hy_w * r.w, int(r.M), int(r.n_mirror), r.d, 1.0, r.xi, r.chi, bool(r.lock_x)), r.w).values())
        except ValueError:
            continue
        if r.swa > 0:                      # holes narrow toward the bottom; keep >= 20 nm open
            L = layout(r.a, r.hx_a * r.a, r.hy_w * r.w, int(r.M), int(r.n_mirror), r.d, 1.0, r.xi, r.chi, bool(r.lock_x))
            if min(L['hx'].min(), L['hy'].min()) - 2 * 120 * np.tan(np.radians(r.swa)) < 20:
                continue
        mfe[i] = m; out[i] = m >= mf
    return out, mfe


def cfg_of(r):
    return dict(a_m=round(float(r.a), 2), w=round(float(r.w), 1), t=120, hx_m=round(float(r.hx_a * r.a), 3),
                hy_m=round(float(r.hy_w * r.w), 3), M=int(r.M), n_mirror=int(r.n_mirror), d=round(float(r.d), 4), eta=1.0,
                xi=round(float(r.xi), 3), chi=round(float(r.chi), 3), pad_x=1000, **({'lock_x': True} if r.lock_x else {}), **({'swa': float(r.swa)} if SWA_ON else {}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mf', type=float, default=80)
    ap.add_argument('--batch', type=int, required=True)
    ap.add_argument('--extra-csv', nargs='*', default=[str(HERE / 'data' / 'bo_results.csv')])
    ap.add_argument('--fmax', type=float, default=9.95)
    ap.add_argument('--n-ei', type=int, default=5)
    ap.add_argument('--n-explore', type=int, default=2)
    ap.add_argument('--n-feas', type=int, default=0, help='picks maximizing P(fb ok) among pred logQ >= --q-floor')
    ap.add_argument('--q-floor', type=float, default=6.8)
    ap.add_argument('--margin', type=float, default=0.03, help='min full-k mirror gap margin (legume fit, gap_margin_fit.json)')
    ap.add_argument('--hypothesis', default='', help="pandas query for one hypothesis point, e.g. 'hy_w < 0.66'")
    ap.add_argument('--replicate', default='', help='json cfg of an existing point to re-solve as a model check')
    ap.add_argument('--M', default='10'); ap.add_argument('--nm', default='10')
    ap.add_argument('--swa', type=float, default=None, help='sidewall angle (deg); full-thickness model')
    a = ap.parse_args()
    global M_CHOICES, NM_CHOICES, SWA, SWA_ON
    SWA = a.swa if a.swa is not None else 0.0; SWA_ON = a.swa is not None
    M_CHOICES = [int(v) for v in a.M.split(',')]; NM_CHOICES = [int(v) for v in a.nm.split(',')]

    df = load(a.extra_csv)
    f_lam, f_q, f_fb = fit_all(df)
    # incumbent: best observed log Q among clean designs within 1 nm of 619.4 with fb <= fmax (at this min feature)
    l3 = df['loc3'] if 'loc3' in df else pd.Series(np.nan, index=df.index)
    inc = df[(df.lam.sub(LAM0).abs() < 1.5) & df.fb.le(a.fmax) & (df['loc'].ge(0.8) | l3.ge(0.9)) & df.min_feature.ge(a.mf - 0.5) & df.M.isin(M_CHOICES) & df.n_mirror.isin(NM_CHOICES) & (df.swa - SWA).abs().lt(0.1)]   # same fixed length as candidates
    best = inc.logQ.max() if len(inc) else 6.0
    c = candidates(14, seed=1000 + a.batch)
    c['a'] = solve_a(c, f_lam)
    ok, mfe = feasible(c, a.mf)
    c['min_feature'] = mfe
    G = json.load(open(HERE / 'gap_margin_fit.json'))['coef']
    c['margin'] = (G[0] + G[1] * c.w / 1000 + G[2] * c.hx_a + G[3] * c.hy_w + G[4] * c.w / 1000 * c.hy_w + G[5] * c.hx_a * c.hy_w + G[6] * c.hy_w ** 2)
    c = c[ok & c.a.between(160, 240) & (c.margin >= a.margin)].reset_index(drop=True)
    X = Xn(c)
    mq, sq = f_q(X); mf, sf = f_fb(X); ml, sl = f_lam(X)
    pfeas = norm.cdf((a.fmax - mf) / np.maximum(sf, 1e-6))
    z = (mq - best) / np.maximum(sq, 1e-9)
    ei = (mq - best) * norm.cdf(z) + sq * norm.pdf(z)
    c = c.assign(pred_logQ=mq, sd_logQ=sq, pred_fb=mf, sd_fb=sf, pred_lam=ml * c.a, sd_lam=sl * c.a, p_fb_ok=pfeas, cei=ei * pfeas)
    picks, why = [], []
    U = np.column_stack([(c[k] - BOX[k][0]) / (BOX[k][1] - BOX[k][0]) for k in BOX] + [c.lock_x * 0.5, (c.M - 10) / 6 * 0.5, (c.n_mirror - 10) / 5 * 0.3])

    def far(i, rmin=0.18):
        return all(np.linalg.norm(U[i] - U[j]) > rmin for j in picks)

    for i in np.argsort(-c.cei.values):
        if len([w for w in why if w == 'cEI']) >= a.n_ei:
            break
        if far(i):
            picks.append(i); why.append('cEI')
    expl = np.where(c.p_fb_ok > 0.2)[0]
    for i in expl[np.argsort(-(c.sd_logQ.values[expl] + c.sd_fb.values[expl] / 0.5))]:
        if len([w for w in why if w == 'explore']) >= a.n_explore:
            break
        if far(i):
            picks.append(i); why.append('explore')
    fe = np.where(c.pred_logQ >= a.q_floor)[0]
    for i in fe[np.argsort(-c.p_fb_ok.values[fe])]:
        if len([w for w in why if w == 'feasibility']) >= a.n_feas:
            break
        if far(i):
            picks.append(i); why.append('feasibility')
    if a.hypothesis:
        h = c.query(a.hypothesis)
        for i in h.index[np.argsort(-h.cei.values)]:
            if far(i):
                picks.append(i); why.append(f'hypothesis: {a.hypothesis}'); break
    out = []
    for i, w in zip(picks, why):
        r = c.iloc[i]
        out.append(dict(cfg=cfg_of(r), why=w, pred=dict(lam=float(r.pred_lam), sd_lam=float(r.sd_lam), logQ=float(r.pred_logQ),
                    sd_logQ=float(r.sd_logQ), fb=float(r.pred_fb), sd_fb=float(r.sd_fb), p_fb_ok=float(r.p_fb_ok),
                    cei=float(r.cei), min_feature=float(r.min_feature))))
    if a.replicate:
        out.append(dict(cfg=json.loads(a.replicate), why='replicate (model check)', pred={}))
    json.dump(dict(batch=a.batch, min_feature=a.mf, fmax=a.fmax, swa=a.swa, incumbent_logQ=float(best), n_candidates=int(len(c)),
                   n_train=int(len(df)), points=out), open(HERE / f'batch_{a.batch}.json', 'w'), indent=1)
    print(f'batch {a.batch}: {len(c)} feasible candidates, incumbent log10 Q {best:.2f}')
    for o in out:
        cf, p = o['cfg'], o['pred']
        print(f"  {o['why'][:28]:28s} w {cf['w']:.0f} hx/a {cf['hx_m']/cf['a_m']:.3f} hy/w {cf['hy_m']/cf['w']:.3f} d {cf['d']:.3f} "
              f"xi {cf['xi']:.1f} chi {cf['chi']:.2f} lx {int(cf.get('lock_x', 0))} M {cf['M']} n {cf['n_mirror']} a {cf['a_m']:.1f} | "
              + (f"logQ {p['logQ']:.2f}±{p['sd_logQ']:.2f} fb {p['fb']:.2f}±{p['sd_fb']:.2f} P(ok) {p['p_fb_ok']:.2f} mf {p['min_feature']:.0f}" if p else ''))


if __name__ == '__main__':
    main()
