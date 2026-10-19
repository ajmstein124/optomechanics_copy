"""
cavity_pipeline.py  (Windows; numpy + mph)
Generic 619 nm cavity design pipeline for one mirror cell and one minimum feature size, resumable,
one COMSOL session. Steps (data in <run_dir>/data):
  1. template   build the 1/8 cavity model for the cell (build_cavity_model.build), small air/PML box
                (600/500 nm; validated in runs/cavity_619/data/pad_check.json)
  2. ad         (a, d) sweep with a baseline taper shape that is fabricable over the grid -> ad_*.npz
  3. line       a(d) where the optical cavity resonance = 619.4 nm (linear interpolation along a)
  4. shape      (xi, chi) shapes fabricable at MIN_FEATURE on the 619 nm line, 2 a values each (+ an
                extrapolated third if 619 nm is not bracketed) -> sh_*.npz
  5. finalize   best design = breathing <= 10 GHz (else lowest), then highest Q_o, interpolated to 619 nm;
                one confirmation solve at that exact a; saves best_<label>.npz and best_<label>.mph
Mode identification as cavity_eval.py. Every geometry is checked against MIN_FEATURE before solving.
"""
import glob
import json
import sys
import time
from pathlib import Path

import mph
import numpy as np
from build_cavity_model import build, set_layout, op_class, mech_class
from cavity_taper import layout, min_features
import cavity_eval as E
from comsol_utils import mphglobal

LAM0, X_LOC = 619.4, 1500.0


def p(*a):
    print(*a); sys.stdout.flush()


S_MIN = 0.7


def breathing_index(loc, B, g, S=None):
    """Breathing mode = localized (loc > 0.8) mode with in-phase sidewalls (B > 0.5) and the largest
    optomechanical overlap |g| (relative). -1 if none (e.g. outside the eigenvalue window). The earlier
    'largest |g| among localized modes' rule picked weak non-breathing modes when the breathing mode
    was missing (2026-10-15). If the sidewall amplitude ratio S is given (files from 2026-10-15 on),
    also S >= S_MIN: B is amplitude-blind and passed a hole-centered hybrid (S 0.35) at w650 d0.13."""
    g = np.abs(np.asarray(g, float)); g = np.where(np.isfinite(g), g, 0)
    ok = (np.asarray(loc) > 0.8) & (np.asarray(B) > 0.5) & (g > 0)
    if S is not None:
        ok &= np.nan_to_num(np.asarray(S, float)) >= S_MIN
    return int(np.where(ok)[0][np.argmax(g[ok])]) if ok.any() else -1


class Pipeline:
    def __init__(self, run_dir, cell, min_feature, label, n_mirror=10, M=10, swa=None):
        """cell: dict w, t, hx_a, hy_w. label: short name for files/logs. n_mirror: mirror cells beyond the
        M = 10 taper cells (fixed per pipeline: the model is built once with this hole count)."""
        self.rd = Path(run_dir); self.dd = self.rd / 'data'; self.dd.mkdir(parents=True, exist_ok=True)
        self.cell, self.mf, self.label, self.n_mirror, self.M = cell, float(min_feature), label, int(n_mirror), int(M)
        self.swa = swa                                    # sidewall angle (deg); not None -> full-thickness model
        self.client = None

    # ---------------------------------------------------------------- helpers
    def cfg(self, a, d, xi, chi):
        c = self.cell
        return dict(a_m=round(float(a), 1), w=c['w'], t=c['t'], hx_m=round(c['hx_a'] * a, 3),
                    hy_m=round(c['hy_w'] * c['w'], 3), M=self.M, n_mirror=self.n_mirror, d=float(d), eta=1.0,
                    xi=float(xi), chi=float(chi), pad_x=1000, **({'lock_x': True} if c.get('lock_x') else {}),
                    **({'swa': float(self.swa)} if self.swa is not None else {}))

    def feasible(self, cfg):
        mf = min_features(layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'], 1.0, cfg['xi'], cfg['chi'], cfg.get('lock_x', False), cfg.get('profile')),
                          cfg['w'])
        if cfg.get('swa') is not None:                       # holes narrow toward the bottom: must stay open (>= 20 nm)
            lay = layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'], 1.0, cfg['xi'], cfg['chi'],
                         cfg.get('lock_x', False), cfg.get('profile'))
            mf = dict(mf, hole_bottom=float(min(lay['hx'].min(), lay['hy'].min()) - 2 * cfg['t'] * np.tan(np.radians(cfg['swa']))))
            return min(v for k, v in mf.items() if k != 'hole_bottom') >= self.mf and mf['hole_bottom'] >= 20.0, mf
        return min(mf.values()) >= self.mf, mf

    def open(self):
        if self.client is not None:
            return
        mph_path = f'cavity_619_{self.label}.mph'
        if not Path(mph_path).exists():
            c0 = self.cfg(220, 0.13, 4.0, 3.5)
            full = dict(c0, pad_y=600, pad_z=600, d_pml=500, h_beam='t/5', h_air='c_const/f_op/6',
                        E_d='1050[GPa]', nu_d='0.07', rho_d='3500[kg/m^3]', n_d='2.41',
                        f_mech='10[GHz]', f_op='484[THz]', N_mode='40', N_op='20')
            client, model, _ = build(full, name=f'cavity_619_{self.label}')
            for t in model.java.sol().tags():
                model.java.sol(str(t)).clearSolutionData()
            model.save(mph_path)
            self.client, self.model = client, model
            p(f'[{self.label}] built {mph_path}')
        else:
            self.client = mph.start()
            self.model = self.client.load(mph_path)
        m = self.model.java
        for k, v in (('pad_y', 600), ('pad_z', 600), ('d_pml', 500)):
            m.param().set(k, f'{v}[nm]')
        full = self.swa is not None
        m.param().set('N_op', '30' if full else '20'); m.param().set('N_mode', '100' if full else '60'); m.param().set('f_mech', '10.5[GHz]' if full else '11[GHz]')
        op_class(self.model, x='PEC', y='PEC', z='PMC'); mech_class(self.model, '+', '+', '+')
        E.setup(self.model)

    def solve(self, cfg, fn, extra=None):
        ok, mf = self.feasible(cfg)
        if not ok:
            np.savez(str(fn), skipped=True, **mf)
            p(f'[{self.label}] {fn.name}: SKIP below {self.mf:.0f} nm {mf}')
            return None
        self.open()
        m = self.model.java
        set_layout(self.model, cfg)
        t0 = time.time()
        fo, Qo, loco, io = E.solve_optics(m, X_LOC)
        fm, locm, B = E.solve_mech(m, X_LOC)
        g = np.full((len(fm), 3), np.nan)
        for k in range(1, len(fm) + 1):
            if locm[k - 1] > 0.8 and B[k - 1] > 0.5:      # breathing-like only (full-thickness models have many localized flexural modes)
                try:
                    g[k - 1] = E.g0_of(m, k, io, fo[io - 1], fm[k - 1])
                except Exception as e:
                    p(f'    g0 mode {k} failed: {str(e)[:150]}')
        try:                                                  # wide-window localization (2026-10-17): broad gentle-taper modes score low at 1.5 um
            loc3 = np.real(mphglobal(m, 'int_beam(solid.disp^2*(x<3000[nm]))/int_beam(solid.disp^2)', 'dset1'))
            clamp = np.real(mphglobal(m, f'int_beam(solid.disp^2*(x>X_in-500[nm]))/int_beam(solid.disp^2)', 'dset1'))
        except Exception:
            loc3 = np.full(len(fm), np.nan); clamp = np.full(len(fm), np.nan)
        S = np.full(len(fm), np.nan)                          # sidewall amplitude ratio, breathing candidates only
        for k in np.where((locm > 0.5) & (B > 0.5))[0]:
            S[k] = E.sidewall_ratio(m, X_LOC, k + 1)
        ib = breathing_index(locm, B, g[:, 0] + g[:, 1], S)
        lam = 299792.458 / (fo[io - 1] / 1e12)
        fb = fm[ib] / 1e9 if ib >= 0 else np.nan
        np.savez(str(fn), skipped=False, cfg=json.dumps(cfg), lam=lam, Q=Qo[io - 1], f_breath=fb,
                 f_opt=fo, Q_opt=Qo, loc_opt=loco, i_opt=io, f_mech=fm, loc_mech=locm, B=B, S=S,
                 gMB=g[:, 0], gPE=g[:, 1], meff=g[:, 2], i_breath=ib, loc_mech3=loc3, clamp_frac=clamp, **mf, **(extra or {}))
        p(f'[{self.label}] {fn.name}: {lam:.1f} nm Q={Qo[io-1]:.3g} | breathing {fb:.3f} GHz | '
          f'min feat {min(mf.values()):.0f} nm | {time.time()-t0:.0f} s')
        wk = [f'{fm[i]/1e9:.2f} (loc {locm[i]:.2f}/{loc3[i]:.2f}, clamp {clamp[i]:.1e}, S {S[i]:.2f})' for i in np.argsort(fm) if B[i] > 0.5 and locm[i] > 0.5]
        if wk:
            p(f'    breathing-like (B > 0.5, loc > 0.5): ' + ', '.join(wk[:4]))
        return dict(lam=lam, Q=Qo[io - 1], fb=fb)

    @staticmethod
    def load(fn):
        """Works for pipeline files and for the earlier sweep_ad/sweep_shape files (no Q/f_breath keys)."""
        z = np.load(fn)
        if 'skipped' in z and bool(z['skipped']):
            return None
        io = int(z['i_opt'])
        if 'Q' in z:
            Q = float(z['Q'])
        else:                                    # re-identify: most localized mode with Q > 1e3
            ok = z['Q_opt'] > 1e3
            io = int(np.where(ok)[0][np.argmax(z['loc_opt'][ok])]) + 1 if ok.any() else io
            Q = float(z['Q_opt'][io - 1])
        lam = 299792.458 / (z['f_opt'][io - 1] / 1e12)
        ib = breathing_index(z['loc_mech'], z['B'], z['gMB'] + z['gPE'], z['S'] if 'S' in z else None)
        fb = float(z['f_mech'][ib] / 1e9) if ib >= 0 else np.nan        # NaN = breathing mode not in the window
        return dict(lam=float(lam), Q=Q, fb=fb)

    def point(self, cfg, fn, extra=None):
        return self.load(fn) if fn.exists() else self.solve(cfg, fn, extra)

    # ---------------------------------------------------------------- steps
    def ad(self, a_list, d_list, base_shape):
        xi, chi = base_shape
        pts = sorted(((a, d) for a in a_list for d in d_list),
                     key=lambda q: ((q[0] - 205) / 15) ** 2 + ((q[1] - 0.13) / 0.04) ** 2)
        for a, d in pts:
            self.point(self.cfg(a, d, xi, chi), self.dd / f'ad_a{a}_d{int(round(d*100)):02d}.npz',
                       dict(a=a, d=d, xi=xi, chi=chi))
        p(f'[{self.label}] (a, d) sweep done')

    def bracket(self, d, a0, base_shape, slope=2.3, max_solves=5):
        """(a, d) points along a at this d until 619.4 nm is bracketed (runs/cavity_619_width, 2026-10-15).
        slope = nm of resonance per nm of a. Infeasible a are stepped up (bridges grow with a).
        Returns the interpolated a on the 619 nm line (a0 if not bracketed)."""
        xi, chi = base_shape
        R = {}
        a = int(round(a0))
        for _ in range(max_solves):
            while not self.feasible(self.cfg(a, d, xi, chi))[0] and a < 240:
                a += 3
            fn = self.dd / f'ad_a{a}_d{int(round(d*100)):02d}.npz'
            r = self.point(self.cfg(a, d, xi, chi), fn, dict(a=a, d=d, xi=xi, chi=chi))
            if r is None:
                break
            R[a] = r['lam']
            if min(R.values()) < LAM0 < max(R.values()):
                break
            step = (LAM0 - r['lam']) / slope
            step = np.sign(step) * max(3.0, min(abs(step) * 1.3, 25.0))
            a_new = int(round(a + step))
            a = a_new + (int(np.sign(step)) * 3 if a_new in R else 0)
        p(f'[{self.label}] d {d}: ' + ', '.join(f'a {k}: {v:.1f} nm' for k, v in sorted(R.items())))
        if len(R) >= 2 and min(R.values()) < LAM0 < max(R.values()):
            L, A = zip(*sorted((v, k) for k, v in R.items()))
            return float(np.interp(LAM0, L, A))
        return a0

    def line(self, d_list):
        out = {}
        for d in d_list:
            R = []
            for fn in glob.glob(str(self.dd / f'ad_a*_d{int(round(d*100)):02d}.npz')):
                r = self.load(fn)
                if r:
                    R.append((float(np.load(fn)['a']), r['lam']))
            R.sort()
            if len(R) >= 2:
                A, L = np.array(R).T
                if L.min() < LAM0 < L.max():
                    o = np.argsort(L); out[d] = float(np.interp(LAM0, L[o], A[o]))
        json.dump(out, open(self.dd / 'line_619.json', 'w'), indent=1)
        p(f'[{self.label}] 619 nm line: ' + ', '.join(f'd {d}: a {a:.1f}' for d, a in out.items()))
        return out

    def shapes(self, line, xi_list, chi_list, da=8.0, max_shapes=12, only=None):
        cands = []
        for d, a0 in line.items():
            for xi in xi_list:
                for chi in chi_list:
                    if chi * d >= 0.95 or (only is not None and (xi, chi) not in only):
                        continue
                    if all(self.feasible(self.cfg(a, d, xi, chi))[0] for a in (a0 - da, a0)):
                        cands.append((d, xi, chi, a0))
        cands.sort(key=lambda c: (-c[1], -c[2], c[0]))           # strongest pull first
        cands = cands[:max_shapes]
        p(f'[{self.label}] {len(cands)} fabricable shapes at {self.mf:.0f} nm: ' +
          ' '.join(f'd{c[0]}/xi{c[1]}/chi{c[2]}' for c in cands))
        for d, xi, chi, a0 in cands:
            fn = lambda a: self.dd / f'sh_d{int(round(d*100)):02d}_xi{xi}_chi{chi:.1f}_a{a:.1f}.npz'
            ex = dict(d=d, xi=xi, chi=chi)
            r1 = self.point(self.cfg(a0, d, xi, chi), fn(round(a0, 1)), dict(ex, a=round(a0, 1)))
            a2 = round(a0 - da, 1)
            r2 = self.point(self.cfg(a2, d, xi, chi), fn(a2), dict(ex, a=a2))
            if r1 and r2 and not (min(r1['lam'], r2['lam']) < LAM0 < max(r1['lam'], r2['lam'])):
                slope = (r1['lam'] - r2['lam']) / (a0 - a2)
                a3 = round(float(np.clip(a0 + (LAM0 - r1['lam']) / slope, a2 - 15, a0 + 15)), 1)
                self.point(self.cfg(a3, d, xi, chi), fn(a3), dict(ex, a=a3))
        p(f'[{self.label}] shape sweep done')

    def candidates(self):
        """Per shape: interpolate (a, Q, breathing) to 619.4 nm from its sh_ points."""
        groups = {}
        for fn in glob.glob(str(self.dd / 'sh_*.npz')):
            z = np.load(fn)
            r = self.load(fn)
            if r is None:
                continue
            key = (float(z['d']), float(z['xi']), float(z['chi']))
            groups.setdefault(key, []).append((float(z['a']), r['lam'], r['Q'], r['fb']))
        out = []
        for (d, xi, chi), R in groups.items():
            R.sort()
            if len(R) < 2:
                continue
            A, L, Q, F = np.array(R).T
            if not (L.min() < LAM0 < L.max()):
                continue
            o = np.argsort(L)
            a = float(np.interp(LAM0, L[o], A[o]))
            okF = np.isfinite(F)
            fb = float(np.interp(a, A[okF], F[okF])) if okF.sum() >= 2 else (float(F[okF][0]) if okF.any() else np.nan)
            out.append(dict(d=d, xi=xi, chi=chi, a=a, Q=float(10 ** np.interp(a, A, np.log10(Q))),
                            fb=fb, fb_points=int(okF.sum())))
        return out

    def finalize(self, n_best=2):
        C = self.candidates()
        if not C:
            p(f'[{self.label}] finalize: no shape brackets 619 nm'); return
        C = [c for c in C if np.isfinite(c['fb'])]
        ok = [c for c in C if c['fb'] <= 10.0]
        pool = sorted(ok, key=lambda c: -c['Q']) if ok else sorted(C, key=lambda c: c['fb'])
        json.dump(dict(all=C, chosen=pool[:n_best], breathing_ok=bool(ok)), open(self.dd / 'candidates.json', 'w'), indent=1)
        for i, c in enumerate(pool[:n_best], 1):
            fn = self.dd / f'best{i}_{self.label}.npz'
            cfg = self.cfg(c['a'], c['d'], c['xi'], c['chi'])
            r = self.point(cfg, fn, dict({f'cand_{k}': v for k, v in c.items()}, rank=i,
                                         a=c['a'], d=c['d'], xi=c['xi'], chi=c['chi']))   # cand_* avoid key clashes with solve()
            if r and fn.exists():
                self.model.save(f'best{i}_{self.label}.mph')
            p(f'[{self.label}] BEST {i}: d {c["d"]} xi {c["xi"]} chi {c["chi"]} a {c["a"]:.1f} -> {r}')

    def close(self):
        if self.client is not None:
            self.client.clear(); self.client = None
