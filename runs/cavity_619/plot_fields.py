"""
plot_fields.py  (Mac)  -- runs/cavity_619
Mode profiles overlaid on the device (hole outlines from cavity_taper.layout, same as COMSOL) for the
w550 / 60 nm candidates exported by export_fields.py. The 1/8 model is unfolded to the full top view:
  optics (x0 PEC, y0 PEC): Ey odd in x, even in y         -> real(Ey) on the z = 0 midplane
  mechanics (x0, y0 Symmetry): u odd in x / even in y, v even in x / odd in y, w even
                                                          -> breathing mode on the DEFORMED top face
                                                             (peak drawn as AMP nm), color = |u|,
                                                             undeformed outline in grey (Oh Fig. 1c view)
Usage:  python runs/cavity_619/plot_fields.py [data_dir out.png dev=title ...]
        (default: runs/cavity_619/data -> runs/cavity_619/mode_profiles.png, ad + shape)
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
from matplotlib.patches import Ellipse
from scipy.interpolate import griddata

sys.path.insert(0, 'scripts')
from cavity_taper import layout   # noqa: E402

D = Path(sys.argv[1]) if len(sys.argv) > 2 else Path('runs/cavity_619/data')
OUT_PNG = sys.argv[2] if len(sys.argv) > 2 else 'runs/cavity_619/mode_profiles.png'
XL, AMP = 3000.0, 50.0
DEVS = [tuple(a.split('=', 1)) for a in sys.argv[3:]] or [('ad', '(a, d) design'), ('shape', 'shape-sweep pick')]


def unfold(xyz, val, sx, sy):
    x, y = xyz[:, 0], xyz[:, 1]
    X = np.concatenate([x, -x, x, -x]); Y = np.concatenate([y, y, -y, -y])
    V = np.concatenate([val, sx * val, sy * val, sx * sy * val])
    return X, Y, V


def grid(X, Y, V, ymax, n=(900, 260)):
    gx = np.linspace(-XL, XL, n[0]); gy = np.linspace(-ymax, ymax, n[1])
    GX, GY = np.meshgrid(gx, gy)
    sel = np.abs(X) <= XL + 100
    return gx, gy, griddata((X[sel], Y[sel]), V[sel], (GX, GY), method='linear')


def holes(ax, lay, w, color='k', lw=0.6, fill=True):
    """Beam edges + holes, in um."""
    xl, w = XL / 1e3, w / 1e3
    ax.plot([-xl, xl], [w / 2, w / 2], color=color, lw=lw); ax.plot([-xl, xl], [-w / 2, -w / 2], color=color, lw=lw)
    for xc, hx, hy in zip(lay['x'] / 1e3, lay['hx'] / 1e3, lay['hy'] / 1e3):
        for s in ((1, -1) if xc > 0 else (1,)):
            if abs(xc) <= xl:
                ax.add_patch(Ellipse((s * xc, 0), hx, hy, fill=fill, fc='w', ec=color, lw=lw))


def in_hole(x, y, lay):
    h = np.zeros_like(x, bool)
    for xc, hx, hy in zip(lay['x'], lay['hx'], lay['hy']):
        for s in (1, -1):
            h |= ((x - s * xc) / (hx / 2)) ** 2 + (y / (hy / 2)) ** 2 < 1
    return h


def deformed(ax, z, lay, w):
    """Breathing mode on the deformed top face (um axes); returns the tripcolor handle."""
    x, y = z['mech_xyz'][:, 0], z['mech_xyz'][:, 1]
    u, v, wz = z['mech_val'].T
    X = np.concatenate([x, -x, x, -x]); Y = np.concatenate([y, y, -y, -y])
    U = np.concatenate([u, -u, u, -u]); V = np.concatenate([v, v, -v, -v]); M = np.sqrt(np.tile(u**2 + v**2 + wz**2, 4))
    sel = np.abs(X) <= XL + 200
    X, Y, U, V, M = X[sel], Y[sel], U[sel], V[sel], M[sel]
    sc = AMP / M.max()
    GX, GY = np.meshgrid(np.linspace(-XL, XL, 1500), np.linspace(-w / 2, w / 2, 140))
    G = []
    for q in (U, V, M):
        g = griddata((X, Y), q, (GX, GY), method='linear'); bad = ~np.isfinite(g)
        g[bad] = griddata((X, Y), q, (GX[bad], GY[bad]), method='nearest'); G.append(g)
    GU, GV, GM = G
    t0 = mtri.Triangulation(GX.ravel(), GY.ravel())
    tri = mtri.Triangulation((GX + sc * GU).ravel() / 1e3, (GY + sc * GV).ravel() / 1e3, t0.triangles)
    tri.set_mask(in_hole(GX.ravel()[t0.triangles].mean(1), GY.ravel()[t0.triangles].mean(1), lay))
    tp = ax.tripcolor(tri, (GM / GM.max()).ravel(), cmap='inferno', shading='gouraud', vmin=0, vmax=1)
    holes(ax, lay, w, color='0.6', lw=0.5, fill=False)
    return tp


fig, axes = plt.subplots(len(DEVS), 2, figsize=(15, 2.6 * len(DEVS) + 0.6))
for r, (dev, title) in enumerate(DEVS):
    fn = D / f'fields_{dev}.npz'
    if not fn.exists():
        for ax in axes[r]:
            ax.text(0.5, 0.5, f'{dev}: pending', ha='center', transform=ax.transAxes); ax.axis('off')
        continue
    z = np.load(fn)
    c = json.loads(str(z['cfg']))
    lay = layout(c['a_m'], c['hx_m'], c['hy_m'], c['M'], c['n_mirror'], c['d'], c['eta'], c['xi'], c['chi'])
    w = c['w']
    lam = 299792.458 / (float(z['f_opt']) / 1e12)
    head = f"{title}: w {c['w']:g}, a {c['a_m']:.1f}, d {c['d']}, ξ {c['xi']:g}, χ {c['chi']:g}"

    # optics: real(Ey), odd in x, even in y
    X, Y, V = unfold(z['opt_xyz'], z['opt_val'][:, 0], -1, 1)
    gx, gy, G = grid(X, Y, V, w / 2 + 400)
    G /= np.nanmax(np.abs(G))
    ax = axes[r, 0]
    ax.pcolormesh(gx / 1e3, gy / 1e3, G, cmap='RdBu_r', vmin=-1, vmax=1, shading='auto')
    holes(ax, lay, w)
    ax.set_title(f"{head}\noptical Ey: {lam:.2f} nm, Q {float(z['Q_opt']):.2g}", fontsize=9)

    # mechanics: deformed top face
    ax = axes[r, 1]
    tp = deformed(ax, z, lay, w)
    ax.set_title(f"{head}\nbreathing: {float(z['f_breath'])/1e9:.2f} GHz, localization {float(z['loc_breath']):.2f}",
                 fontsize=9)
    plt.colorbar(tp, ax=ax, label='|u| (norm.)', fraction=0.015, pad=0.01)
    for ax in axes[r]:
        ax.set_aspect('equal'); ax.set_xlim(-XL / 1e3, XL / 1e3)
        ax.set_xlabel('x (µm)'); ax.set_ylabel('y (µm)')
    axes[r, 1].set_ylim(-w / 2e3 - 1.6 * AMP / 1e3, w / 2e3 + 1.6 * AMP / 1e3)
fig.tight_layout()
fig.savefig(OUT_PNG, dpi=170)
print(f'wrote {OUT_PNG}')
