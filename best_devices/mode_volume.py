"""
mode_volume.py  (Mac) -- optical mode volume and Q/V of the final devices from SAVED field data (no new simulation).
Saved data: COMSOL midplane cut of the cavity mode (fields_final.npz: |E| = ewfd.normE at z = 1 nm, quarter x >= 0, y >= 0,
out to y = w/2 + 400 nm). The 3D field itself is only in the saved final_<label>.mph on the COMSOL machine.
Estimate:  V = A_xy * L_z
  A_xy = integral over the midplane of eps|E|^2 / max(eps|E|^2)       (full plane = 4 x quarter; eps = 2.41^2 in diamond, 1 in holes/air)
  L_z  = integral eps(z)|E(z)|^2 dz / (eps|E|^2 at z = 0)              (TE0 mode of a t = 120 nm diamond slab in air at the resonance)
Assumptions: separable field (midplane x vertical slab profile) and the peak of eps|E|^2 on the midplane. Expected accuracy
~20-30 %; exact V needs one evaluation of the saved .mph solution (no re-solve).
Run from the project root:  python best_devices/mode_volume.py   -> best_devices/<device>/mode_volume.md, README table column
"""
import json
from pathlib import Path

import numpy as np
from matplotlib.path import Path as MPath
from scipy.interpolate import griddata
from scipy.optimize import brentq

import sys
sys.path.insert(0, 'scripts')
from cavity_taper import layout   # noqa: E402

N = 2.41


def slab_Lz(lam, t, n=N):
    """TE0 slab (E in-plane) of thickness t (nm) in air: L_z = int eps|E|^2 dz / (eps |E(0)|^2), and n_eff."""
    k0 = 2 * np.pi / lam
    f = lambda b: np.sqrt(n ** 2 * k0 ** 2 - b ** 2) * np.tan(np.sqrt(n ** 2 * k0 ** 2 - b ** 2) * t / 2) - np.sqrt(b ** 2 - k0 ** 2)
    b = brentq(f, k0 * 1.0001, k0 * n * 0.9999)
    kx, g = np.sqrt(n ** 2 * k0 ** 2 - b ** 2), np.sqrt(b ** 2 - k0 ** 2)
    inside = n ** 2 * (t / 2 + np.sin(kx * t) / (2 * kx))                 # int cos^2 over the core
    outside = 2 * np.cos(kx * t / 2) ** 2 / (2 * g)                       # two evanescent tails, eps = 1
    return (inside + outside) / n ** 2, b / k0


def device(mf):
    F = json.load(open(f'runs/cavity_619_final/data/final_{mf}.json'))
    c = F['cell']; z = np.load(Path(F['run_dir']) / 'data' / 'fields_final.npz')
    cfg = json.loads(str(z['cfg']))
    lam = 299792.458 / (float(z['f_opt']) / 1e12); Q = float(z['Q_opt'])
    lay = layout(cfg['a_m'], cfg['hx_m'], cfg['hy_m'], cfg['M'], cfg['n_mirror'], cfg['d'], cfg['eta'], cfg['xi'], cfg['chi'])
    x, y = z['opt_xyz'][:, 0], z['opt_xyz'][:, 1]; E = z['opt_val'][:, 1]                  # normE
    gx = np.linspace(0, x.max(), 1600); gy = np.linspace(0, y.max(), 360)
    GX, GY = np.meshgrid(gx, gy)
    G = griddata((x, y), E, (GX, GY), method='linear'); G = np.nan_to_num(G)
    eps = np.where(GY <= c['w'] / 2, N ** 2, 1.0)
    for xc, hx, hy in zip(lay['x'], lay['hx'], lay['hy']):
        eps[((GX - xc) / (hx / 2)) ** 2 + (GY / (hy / 2)) ** 2 < 1] = 1.0
    W = eps * G ** 2
    A_xy = 4 * np.trapezoid(np.trapezoid(W, gx, axis=1), gy) / W.max()                           # nm^2
    Lz, neff = slab_Lz(lam, c['t'])
    V = A_xy * Lz                                                                        # nm^3
    Vn = V / (lam / N) ** 3
    i_pk = np.unravel_index(W.argmax(), W.shape)
    pk_in_diamond = eps[i_pk] > 1
    slug = f"{mf}_w{c['w']}_d{F['d']:.2f}_xi{F['xi']:g}_chi{F['chi']:g}"
    od = Path('best_devices') / slug
    lumQ = None
    lm = od / 'lumerical_verification.md'
    if lm.exists():
        for line in lm.read_text().splitlines():
            if line.startswith('| optical Q'):
                lumQ = float(line.split('|')[3].split()[0])
    md = f"""# Optical mode volume and Q/V: {slug}

Estimated from SAVED field data (no new simulation): COMSOL midplane cut of the cavity mode (`{F['run_dir']}/data/fields_final.npz`).

| | |
|---|---|
| resonance | {lam:.2f} nm |
| in-plane area A_xy = ∫ε\\|E\\|² dxdy / max(ε\\|E\\|²) (z = 0 plane, whole beam + air) | {A_xy / 1e6:.4f} µm² |
| vertical length L_z (TE0 mode of a {c['t']} nm diamond slab, n_eff {neff:.3f}) | {Lz:.1f} nm |
| **mode volume V = A_xy · L_z** | **{V / 1e9:.4f} µm³ = {Vn:.2f} (λ/n)³**, n = {N} |
| peak of ε\\|E\\|² | {'in the diamond' if pk_in_diamond else 'in air (hole edge)'} at x = {GX[i_pk]:.0f} nm, y = {GY[i_pk]:.0f} nm |
| Q (COMSOL) | {Q:.2e} → **Q/V = {Q / Vn:.2e} per (λ/n)³** |
""" + (f"| Q (Lumerical, lower bound) | {lumQ:.2e} → Q/V = {lumQ / Vn:.2e} per (λ/n)³ |\n" if lumQ else "") + f"""
Purcell factor for an ideally placed and oriented dipole, F_P = (3/4π²)(λ/n)³ Q/V = {3 / (4 * np.pi ** 2) * Q / Vn:.2e} (COMSOL Q).

**Accuracy (~20–30 %):** assumes the field separates into the midplane pattern times the vertical profile of a uniform
120 nm slab (the real beam is patterned and 650–700 nm wide, so the vertical tail differs somewhat), and that the 3D
maximum of ε|E|² lies on the midplane. The exact V needs one evaluation of the saved `final_{F['label']}.mph` solution
on the COMSOL machine (no re-solve).
"""
    (od / 'mode_volume.md').write_text(md)
    print(f'{mf}: A_xy {A_xy/1e6:.4f} um2, Lz {Lz:.1f} nm, V {V/1e9:.4f} um3 = {Vn:.2f} (l/n)^3, Q/V {Q/Vn:.2e}, peak in diamond {pk_in_diamond}')
    return slug, Vn, Q / Vn


if __name__ == '__main__':
    res = [device(mf) for mf in ('60nm', '80nm')]
    rd = Path('best_devices/README.md'); s = rd.read_text()
    if 'mode volume' not in s:
        s += '\n**Optical mode volume (estimate from saved midplane fields, see each `mode_volume.md`):**\n\n| device | V ((λ/n)³) | Q/V (COMSOL Q) |\n|---|---|---|\n'
        s += ''.join(f'| {slug} | {vn:.2f} | {qv:.2e} |\n' for slug, vn, qv in res)
        rd.write_text(s)
