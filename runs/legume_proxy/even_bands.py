"""even_bands.py: y-even (cavity-family) guided bands of a mirror cell along Gamma->X with legume -- does a higher-order
y-even band cross 484 THz (619 nm) at wide w (in-plane leak channel through the mirror)?"""
import sys
import numpy as np
from pccsim.layer import PCLayer
from pccsim.nanobeam.simulation import NanobeamHoleParams, nanobeam
import legume

C = 299792.458


def even_bands(w, a, hx, hy, t=120.0, n=2.41, nk=9, numeig=10):
    Ly = w / a + 3.0
    pc = nanobeam([PCLayer(eps=n ** 2, d=t / a, p=1.0)], NanobeamHoleParams(a=1.0, w=w / a, Ly=Ly, rx=hx / (2 * a), ry=hy / (2 * a)))
    ks = np.linspace(0.35, 1.0, nk) * np.pi
    gme = legume.GuidedModeExp(pc, gmax=4.01, truncate_g='abs')
    gme.run(kpoints=np.vstack([ks, np.zeros(nk)]), numeig=numeig, verbose=False, gmode_inds=[0], compute_im=False)
    out = []
    for ik, k in enumerate(ks):
        light = C * k / (2 * np.pi * a)
        row = []
        for i in range(numeig):
            f = gme.freqs[ik, i] * C / a
            if f >= light:
                break
            fld = gme.get_field_xy('E', kind=ik, mind=i, z=0.0, component='y', Nx=5, Ny=81)[0]['y']
            col = fld[:, fld.shape[1] // 2]
            if np.abs(col + col[::-1]).sum() > np.abs(col - col[::-1]).sum():
                row.append(f / 1.03)        # rough legume -> COMSOL scaling
        out.append((k * a / np.pi, row))
    return out


for w in map(float, sys.argv[1:]):
    a = 189.0
    print(f'w {w:.0f}:')
    for kk, row in even_bands(w, a, 0.49 * a, 0.75 * w):
        print(f'   k {kk:.2f} pi/a: even guided ' + ', '.join(f'{f:.0f}' for f in row[:4]))
