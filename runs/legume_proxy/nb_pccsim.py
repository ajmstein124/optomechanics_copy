"""
nb_pccsim.py  (Mac; run with ~/Documents/pccsim_main/.venv/bin/python)  -- runs/legume_proxy
Diamond nanobeam optical unit cell via pccsim's nanobeam() + legume GME (stanfordnqp/pccsim origin/main worktree at
~/Documents/pccsim_main). Returns the cavity-family (Ey even about y = 0, = COMSOL y0 PEC) guided bands at X in THz.
Units: everything normalized to a (pccsim convention a = 1).
"""
import numpy as np
from pccsim.layer import PCLayer
from pccsim.nanobeam.simulation import NanobeamHoleParams, nanobeam
import legume

C = 299792.458   # nm THz


def bands_X(w, a, hx, hy, t=120.0, n=2.41, gmax=5.0, gmode_inds=(0,), numeig=14, Ly_extra=3.0, keep='even'):
    Ly = w / a + Ly_extra
    pc = nanobeam([PCLayer(eps=n ** 2, d=t / a, p=1.0)], NanobeamHoleParams(a=1.0, w=w / a, Ly=Ly, rx=hx / (2 * a), ry=hy / (2 * a)))
    gme = legume.GuidedModeExp(pc, gmax=gmax, truncate_g='abs')
    gme.run(kpoints=np.array([[np.pi], [0.0]]), numeig=numeig, verbose=False, gmode_inds=list(gmode_inds), compute_im=False)
    f = gme.freqs[0] * C / a
    light = C / (2 * a)
    out = []
    for i in range(len(f)):
        if f[i] >= light:
            break
        fld = gme.get_field_xy('E', kind=0, mind=i, z=0.0, component='y', Nx=5, Ny=81)[0]['y']
        col = fld[:, fld.shape[1] // 2]
        even = np.abs(col + col[::-1]).sum() > np.abs(col - col[::-1]).sum()
        if (keep == 'even') == even:
            out.append(f[i])
    return np.array(out), light
