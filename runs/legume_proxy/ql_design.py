"""
ql_design.py  (Mac, pccsim_main venv)  -- runs/legume_proxy
Deterministic taper design (Quan & Loncar, Opt. Express 19, 18529, 2011) with calibrated legume band edges:
pick per-cell period scales s_j = a_j / a_m (holes follow the period: hx_j = (hx/a) a_j, hy_j = hy_m * hyscale_j) so
the mirror strength rises as gamma_j = gamma_mirror (j/M)^p (p = 1: linear -> Gaussian envelope, minimal radiation).
The resonance is placed at the center cell's dielectric (band-1) edge plus a detuning `det` (fraction; COMSOL cavities
sit ~det above the center-cell edge, measured by analyze_profiles.py). a_m is rescaled so the predicted resonance is
619.4 nm (resonance ~ 1/a at fixed shape; 2 iterations).
design(w, hx_a, hy_w, d, M=10, p=1.0) -> dict(profile=[s_0..s_M], a_m, gamma, f1, f2, f_res)
"""
import numpy as np
from taper_profiles import calibrate, CAL
from nb_pccsim import bands_X

CNT = 299792.458
LAM0 = 619.4


def edges(w, a, hx_a, hy):
    f, _ = bands_X(w, a, hx_a * a, hy, gmax=4.01)
    return (calibrate(f[0], w, a, hx_a, hy / w, CAL[0]), calibrate(f[1], w, a, hx_a, hy / w, CAL[1])) if f.size >= 2 else (np.nan, np.nan)


def gamma(f1, f2, fres):
    f0 = (f1 + f2) / 2
    return np.sqrt(np.clip(((f2 - f1) / (f2 + f1)) ** 2 - ((fres - f0) / f0) ** 2, 0, None))


def design(w, hx_a, hy_w, d, M=10, p=1.0, det=0.0, a_m=190.0, ns=13, iters=2):
    for _ in range(iters):
        S = np.linspace(1 - d - 0.02, 1.0, ns)
        T = np.array([edges(w, a_m * s, hx_a, hy_w * w) for s in S])          # (ns, 2) band edges vs s
        f1c = np.interp(1 - d, S, T[:, 0])
        fres = f1c * (1 + det)
        g = gamma(T[:, 0], T[:, 1], fres)                                        # gamma(s) at this resonance
        gm = g[-1]
        target = gm * (np.arange(M + 1) / M) ** p
        # gamma(s) increases with s above s_on (where the band-1 edge crosses fres); invert on the monotone part
        mono = np.maximum.accumulate(g)
        prof = np.interp(target, mono + np.arange(ns) * 1e-9, S)
        prof[0] = 1 - d
        lam = CNT / fres
        a_m = a_m * LAM0 / lam
    return dict(profile=[float(v) for v in prof], a_m=float(a_m), gamma_mirror=float(gm), f_res=float(fres), lam_pred=float(lam),
                table_s=S.tolist(), table_f=T.tolist())


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../../scripts')
    for d in (0.06, 0.10):
        r = design(700, 0.45, 0.70, d)
        print(f"d {d}: a_m {r['a_m']:.1f}  profile {np.round(r['profile'], 4)}  gamma_m {r['gamma_mirror']:.4f}")
        y = np.linspace(0, 1, 11); print('   chan cubic       ', np.round(1 - d * (2 * y**3 - 3 * y**2 + 1), 4))
