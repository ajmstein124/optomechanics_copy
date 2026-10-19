"""
cavity_taper.py  (Mac + Windows; numpy only)
Hole layout of a full 1D nanobeam OMC cavity, Chan PhD thesis (Caltech 2012) eqs. 3.48-3.53,
the parameterization Oh 2026 (Supplement S3) says they used.

Cell j = 0 (defect, on the beam center x = 0) ... M (= mirror cell), then n_mirror more mirror cells.
  x = j/M,  y = remap(x; eta)
  a_j / a_m  = 1 - d (2y^3 - 3y^2 + 1)
  s_j (hole area / mirror hole area):   1 - s_j = chi (1 - a_j/a_m)
  r_j ((hy/hx) / (hy/hx)_mirror):       r_j = (a_j/a_m)^xi
  -> hy_j = hy_m sqrt(s_j r_j),  hx_j = hx_m sqrt(s_j / r_j)
  lock_x (2026-10-16): hx_j = hx_m a_j / a_m instead (x fill fraction hx/a constant along the beam; holes shrink in x
  with the period, center bridges shrink only by (1 - d)); hy_j unchanged. ~ Chan's family on the line chi = xi + 2.
  profile (2026-10-16): explicit a_j/a_m list for j = 0..M replacing the cubic (d then only sets chi's area law via 1 - a_j/a_m).
Hole j is centered in cell j; cells abut, so x_0 = 0 and x_{j+1} = x_j + (a_j + a_{j+1}) / 2.
"""
import numpy as np


def remap(x, eta):
    x = np.clip(np.asarray(x, float), 0, 1)
    return np.where(x <= 0.5, 0.5 * (2 * x) ** eta, 1 - 0.5 * (2 * (1 - x)) ** eta)


def layout(a_m, hx_m, hy_m, M, n_mirror, d, eta=1.0, xi=0.0, chi=1.0, lock_x=False, profile=None):
    """Return dict of arrays over holes j = 0 .. M + n_mirror: x, a, hx, hy (same length units as inputs)."""
    j = np.arange(M + n_mirror + 1)
    y = remap(j / M, eta)
    an = 1 - d * (2 * y ** 3 - 3 * y ** 2 + 1)           # a_j / a_m
    if profile is not None:                               # explicit a_j / a_m for j = 0..M (e.g. legume linear-mirror-strength design)
        pr = np.asarray(profile, float)
        an = np.concatenate([pr, np.ones(len(j) - len(pr))]) if len(pr) < len(j) else pr[:len(j)]
    s = 1 - chi * (1 - an)
    r = an ** xi
    if np.any(s <= 0):
        raise ValueError(f'hole area scale <= 0 (chi*d >= 1): chi={chi}, d={d}')
    a = a_m * an
    x = np.concatenate([[0.0], np.cumsum((a[:-1] + a[1:]) / 2)])
    hx = hx_m * an if lock_x else hx_m * np.sqrt(s / r)
    return dict(j=j, x=x, a=a, hx=hx, hy=hy_m * np.sqrt(s * r), s=s, r=r)


def beam_half_length(lay, pad_x):
    """Beam end (inner region) = edge of the last cell + pad_x of plain waveguide."""
    return lay['x'][-1] + lay['a'][-1] / 2 + pad_x


def min_features(lay, w):
    """Narrowest fabricated features [same units]: bridge between adjacent hole edges (along x),
    side rail (w - hy)/2, smallest hole dimension. Center hole 0 is shared with its mirror image, so the
    bridges listed are between holes j and j+1 (j >= 0)."""
    x, hx, hy = lay['x'], lay['hx'], lay['hy']
    bridge = np.diff(x) - (hx[:-1] + hx[1:]) / 2
    return dict(bridge=float(bridge.min()), rail=float(((w - hy) / 2).min()),
                hole=float(min(hx.min(), hy.min())))
