"""
plot_lum_point.py  (Mac)
One Lumerical sweep point vs COMSOL: Ey field map on the z = 0 midplane (Lumerical profile at the resonance,
phase-normalized to its peak; COMSOL cavity mode from fields_<dev>.npz), hole outlines from cavity_taper, an
on-axis |Ey| cut, and the Qanalysis resonances found (lambda vs Q) with the COMSOL mode marked.
Usage (from project root):
    python runs/cavity_619/lumerical/plot_lum_point.py <name> <point> <comsol fields npz> [--pull]
    e.g. lum_w650_mf60_shape 3 runs/cavity_619_width/w650_mf60/data/fields_shape.npz
Output: runs/cavity_619/lumerical/results/<name>_pt<point>.png
"""
import json
import subprocess
import sys
from pathlib import Path

import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse
from scipy.interpolate import griddata

sys.path.insert(0, 'scripts')
from cavity_taper import layout   # noqa: E402

HERE = Path('runs/cavity_619/lumerical'); RES = HERE / 'results'; RES.mkdir(exist_ok=True)
PULL_FROM = '<USER>@<LUMERICAL_HOST>:C:/Users/JVadmin/Documents/optomechanics/lumerical'
XL = 3.0   # um shown


def holes(ax, lay, w):
    ax.plot([-XL, XL], [w / 2, w / 2], 'k', lw=0.6); ax.plot([-XL, XL], [-w / 2, -w / 2], 'k', lw=0.6)
    for xc, hx, hy in zip(lay['x'] / 1e3, lay['hx'] / 1e3, lay['hy'] / 1e3):
        for s in ((1, -1) if xc > 0 else (1,)):
            if abs(xc) <= XL:
                ax.add_patch(Ellipse((s * xc, 0), hx, hy, fill=False, ec='k', lw=0.6))


name, pt, cfn = sys.argv[1], int(sys.argv[2]), sys.argv[3]
mat = RES / f'{name}_pt{pt}.mat'
if '--pull' in sys.argv or not mat.exists():
    subprocess.run(['scp', '-q', '-i', str(Path('~/.ssh/id_ed25519').expanduser()), f'{PULL_FROM}/{name}_pt{pt}.mat', str(mat)], check=True)
f = h5py.File(mat, 'r')
E = np.squeeze(np.array(f['Ey_res'])); E = E['real'] + 1j * E['imag']   # (ny, nx); v251 adds a singleton axis
xg, yg = np.array(f['xg']).ravel() * 1e6, np.array(f['yg']).ravel() * 1e6
lamr, Qv = np.array(f['lamr']).ravel() * 1e9, np.array(f['Qv']).ravel()
lam_b, Q_b = float(np.array(f['lam_best']).ravel()[0]) * 1e9, float(np.array(f['Q_best']).ravel()[0])
E = E * np.exp(-1j * np.angle(E.flat[np.argmax(np.abs(E))])); E = np.real(E) / np.abs(E).max()

pts = json.load(open(HERE / f'{name}_points.json'))['points']; P = pts[pt - 1]
cell = json.load(open(HERE / f'{name}_points.json'))['cell']
lay = layout(P['a'], cell['hx_a'] * P['a'], cell['hy_w'] * cell['w'], 10, 10, P['d'], 1.0, P['xi'], P['chi'])
w = cell['w'] / 1e3

z = np.load(cfn)
X, Y, V = z['opt_xyz'][:, 0], z['opt_xyz'][:, 1], z['opt_val'][:, 0]
X = np.r_[X, -X, X, -X]; Y = np.r_[Y, Y, -Y, -Y]; V = np.r_[V, -V, V, -V]       # Ey odd in x, even in y
gx = np.linspace(-XL * 1e3, XL * 1e3, 900); gy = np.linspace(-(w * 1e3 / 2 + 400), w * 1e3 / 2 + 400, 200)
C = griddata((X, Y), V, tuple(np.meshgrid(gx, gy)), method='linear'); C = C / np.nanmax(np.abs(C))
if np.nansum(C[:, len(gx) // 2:] * np.interp(gx[len(gx) // 2:], xg * 1e3, E[len(yg) // 2])) < 0:
    C = -C                                                                        # same overall sign as Lumerical
lam_c = 299792.458 / (float(z['f_opt']) / 1e12); Q_c = float(z['Q_opt'])

fig = plt.figure(figsize=(15, 9.5)); gs = fig.add_gridspec(3, 2, width_ratios=(2.3, 1), hspace=0.45)
for r, (img, gxx, gyy, title) in enumerate(((E, xg, yg, f'Lumerical E$_y$: {lam_b:.2f} nm, Q {Q_b:.2g} (lower bound)'),
                                            (C, gx / 1e3, gy / 1e3, f'COMSOL E$_y$: {lam_c:.2f} nm, Q {Q_c:.2g}'))):
    ax = fig.add_subplot(gs[r, 0])
    ax.pcolormesh(gxx, gyy, img, cmap='RdBu_r', vmin=-1, vmax=1, shading='auto')
    holes(ax, lay, w); ax.set_aspect('equal'); ax.set_xlim(-XL, XL); ax.set_ylim(-w / 2 - 0.35, w / 2 + 0.35)
    ax.set_xlabel('x (µm)'); ax.set_ylabel('y (µm)'); ax.set_title(title, fontsize=10, fontweight='bold')
ax = fig.add_subplot(gs[2, 0])
ax.plot(xg, np.abs(E[np.argmin(np.abs(yg))]), label='Lumerical')
ax.plot(gx / 1e3, np.abs(C[np.argmin(np.abs(gy))]), '--', label='COMSOL')
for xc in lay['x'] / 1e3:
    for s in (1, -1):
        if abs(xc) <= XL:
            ax.axvline(s * xc, color='0.85', lw=0.6, zorder=0)
ax.set_xlim(-XL, XL); ax.set_xlabel('x (µm)'); ax.set_ylabel('|E$_y$| on axis (norm.)'); ax.legend(fontsize=9)
ax = fig.add_subplot(gs[:, 1])
ax.scatter(lamr, Qv, s=60, edgecolor='k', label='Lumerical Qanalysis resonances')
ax.scatter([lam_c], [Q_c], marker='*', s=260, color='tab:red', edgecolor='k', label='COMSOL cavity mode')
ax.set_yscale('log'); ax.set_xlabel('wavelength (nm)'); ax.set_ylabel('Q'); ax.set_xlim(570, 680)
ax.axvline(619.4, color='0.6', ls=':'); ax.legend(fontsize=9, loc='lower left')
ax.set_title(f"Δλ = {lam_b - lam_c:+.2f} nm ({(lam_b - lam_c) / lam_c * 100:+.2f} %)", fontsize=10, fontweight='bold')
fig.suptitle(f"{name} point {pt}: w {cell['w']}, a {P['a']:.1f}, d {P['d']}, ξ {P['xi']:g}, χ {P['chi']:g}", fontsize=13, fontweight='bold')
out = RES / f'{name}_pt{pt}.png'
fig.savefig(out, dpi=140, facecolor='white', bbox_inches='tight'); print(f'wrote {out}')
