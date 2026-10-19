"""
nbcell.py  (Mac, pccsim venv: ~/Documents/pccsim/.venv/bin/python)  -- runs/legume_proxy
Optical unit cell of the diamond nanobeam with legume GME, following pccsim's nanobeam() (stanfordnqp/pccsim
src/pccsim/nanobeam/simulation.py): beam of width w along x, one elliptical hole per period, tall air supercell in y.
Units: lengths in nm internally, normalized to a (legume works in units of the lattice constant).
band_X(w, a, hx, hy) -> guided TE-like frequencies at X (THz), y-parity of each (+1 / -1 for Ey even/odd about y=0).
"""
import numpy as np
if not hasattr(np, 'complex256'):
    np.complex256 = np.complex128
import legume  # noqa: E402

C_NM_THZ = 299792.458   # c in nm*THz


def cell(w, a, hx, hy, t=120.0, n=2.41, Ly=4.0):
    """legume PhotCryst in units of a. Ly = supercell height in units of a... given in multiples of w? -> absolute a units."""
    lat = legume.Lattice([1.0, 0], [0, Ly])
    pc = legume.PhotCryst(lat, eps_l=1.0, eps_u=1.0)
    pc.add_layer(d=t / a, eps_b=n ** 2)
    W = w / a
    pc.add_shape(legume.Ellipse(x_cent=0, y_cent=0, rx=hx / (2 * a), ry=hy / (2 * a), eps=1.0))
    pc.add_shape(legume.Poly(eps=1.0, x_edges=[-0.5, 0.5, 0.5, -0.5], y_edges=[W / 2, W / 2, Ly / 2, Ly / 2]))
    pc.add_shape(legume.Poly(eps=1.0, x_edges=[-0.5, -0.5, 0.5, 0.5], y_edges=[-W / 2, -Ly / 2, -Ly / 2, -W / 2]))
    return pc


def band_X(w, a, hx, hy, t=120.0, gmax=4.0, numeig=12, Ly=None, parity=True):
    Ly = Ly if Ly is not None else max(4.0, (w / a) + 3.0)
    pc = cell(w, a, hx, hy, t=t, Ly=Ly)
    gme = legume.GuidedModeExp(pc, gmax=gmax, truncate_g='abs')
    gme.run(kpoints=np.array([[np.pi], [0.0]]), numeig=numeig, verbose=False, gmode_inds=[0], compute_im=False)
    f = gme.freqs[0] * C_NM_THZ / a                  # normalized freq * c / a -> THz
    par = np.zeros(len(f))
    if parity:
        for i in range(len(f)):
            E = gme.get_field_xy('E', kind=0, mind=i, z=0.0, component='y', Nx=8, Ny=60)[0]['y']
            ys = np.linspace(-Ly / 2, Ly / 2, E.shape[0])
            col = E[:, 0]
            sym = np.abs(col + col[::-1]).sum(); asym = np.abs(col - col[::-1]).sum()
            par[i] = 1 if sym > asym else -1
    light = C_NM_THZ / (2 * a)                         # light line at X: f = c k / 2pi = c / (2a)
    return f, par, light
