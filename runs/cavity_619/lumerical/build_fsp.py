"""
build_fsp.py  (remote, Lumerical FDTD v252 via lumapi)  -- runs/cavity_619/lumerical
Independent optical check of the 619 nm cavity in FDTD. Builds and SAVES (does not run) an .fsp for
GUI inspection: C:\\Users\\abby\\lumerical\\cavity_619_a220_d18.fsp

Device = the COMSOL template (runs/cavity_619/build.py): mirror a 220, w 550, t 120, hx/a 0.53,
hy/w 0.77, taper d 0.18, M 10, eta 1, xi 6, chi 3.5, 10 mirror cells per side (41 holes), n = 2.41.
Hole layout from the SAME scripts/cavity_taper.py as COMSOL.

FDTD setup (full beam, no symmetry BCs -> independent of the COMSOL symmetry choices):
  source   Ey dipole, 570-680 nm, at x = +90 nm (dielectric between center hole and hole 1, where Ey
           peaks; the cavity mode is odd in x so x = 0 is a node), y = 0, z = 0
  monitors 4 point time monitors near the center (ring-down -> resonance + Q), and a 2D z-normal
           frequency-domain profile at z = 0 (mode profile)
  region   x +/- 5.0 um, y +/- 1.175 um, z +/- 0.96 um (>= 1.5 lambda of air around the beam), PML all
           sides; beam extends through the x PML (as in COMSOL: light leaving through the mirrors is
           absorbed); auto non-uniform mesh accuracy 3 + 10 nm override over the beam
  time     3 ps (Q ~ 1e5 -> photon lifetime ~ 33 ps; Q from the ring-down fit, extend if needed)
Order of creation follows the global Lumerical notes: source -> monitors -> FDTD -> structures;
save before any run (headless "save as" dialog hangs otherwise).

Run via:
    python scripts/remote_runner.py --block runs/cavity_619/lumerical/build_fsp.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.append(r"C:\Program Files\ANSYS Inc\v252\Lumerical\api\python")
os.environ["PATH"] += r";C:\Program Files\ANSYS Inc\v252\Lumerical\bin"
# SSH sessions land in the TEMP profile (abby profile-path bug), which has no Lumerical license config.
# Process-only setting of the lab license server (from the working config in C:\Users\hopel\AppData\
# Roaming\Lumerical\License.ini); nothing persistent is changed on the machine.
os.environ.setdefault("ANSYSLMD_LICENSE_FILE", "<PORT>@<LICENSE_SERVER>")
import lumapi                                    # noqa: E402
from cavity_taper import layout                  # noqa: E402

NM = 1e-9
A, W, T, N_D = 220.0, 550.0, 120.0, 2.41
CFG = dict(a_m=A, hx_m=0.53 * A, hy_m=0.77 * W, M=10, n_mirror=10, d=0.18, eta=1.0, xi=6.0, chi=3.5)
LAY = layout(CFG['a_m'], CFG['hx_m'], CFG['hy_m'], CFG['M'], CFG['n_mirror'], CFG['d'],
             CFG['eta'], CFG['xi'], CFG['chi'])
OUTDIR = Path(r'C:\Users\abby\lumerical'); OUTDIR.mkdir(parents=True, exist_ok=True)
FSP = str(OUTDIR / 'cavity_619_a220_d18.fsp')
X_REG, Y_REG, Z_REG = 5000.0, W / 2 + 900.0, T / 2 + 900.0
X_DIP = 90.0
T_PTS = [(90, 0, 0), (270, 40, 0), (450, 80, 20), (630, 120, 30)]


def p(*a):
    print(*a); sys.stdout.flush()


with lumapi.FDTD(hide=True) as fdtd:
    # source
    fdtd.adddipole(); fdtd.set('name', 'dipole')
    # monitors
    for i, _ in enumerate(T_PTS, 1):
        fdtd.addtime(); fdtd.set('name', f'time{i}')
    fdtd.addprofile(); fdtd.set('name', 'profile_z0')
    # FDTD region + mesh override
    fdtd.addfdtd()
    fdtd.addmesh(); fdtd.set('name', 'mesh_beam')
    # structures: beam, then holes (higher priority = lower mesh order)
    fdtd.addrect(); fdtd.set('name', 'beam')
    fdtd.set('material', '<Object defined dielectric>'); fdtd.set('index', N_D)
    holes = []
    for j, (xj, hx, hy) in enumerate(zip(LAY['x'], LAY['hx'], LAY['hy'])):
        for side in ((1,) if j == 0 else (1, -1)):
            name = f'hole_{j}{"R" if side > 0 else "L"}' if j else 'hole_0'
            fdtd.addcircle(); fdtd.set('name', name)
            fdtd.set('material', '<Object defined dielectric>'); fdtd.set('index', 1.0)
            holes.append((name, side * xj, hx, hy))

    # geometry / settings
    fdtd.setnamed('dipole', 'x', X_DIP * NM); fdtd.setnamed('dipole', 'y', 0.0); fdtd.setnamed('dipole', 'z', 0.0)
    fdtd.setnamed('dipole', 'theta', 90.0); fdtd.setnamed('dipole', 'phi', 90.0)      # Ey
    fdtd.setnamed('dipole', 'wavelength start', 570 * NM); fdtd.setnamed('dipole', 'wavelength stop', 680 * NM)
    for i, (x, y, z) in enumerate(T_PTS, 1):
        for k, v in (('x', x), ('y', y), ('z', z)):
            fdtd.setnamed(f'time{i}', k, v * NM)
    fdtd.setnamed('profile_z0', 'monitor type', '2D Z-normal')
    for k, v in (('x', 0.0), ('x span', 6000 * NM), ('y', 0.0), ('y span', 1600 * NM), ('z', 0.0)):
        fdtd.setnamed('profile_z0', k, v)
    fdtd.setnamed('profile_z0', 'override global monitor settings', 1)
    fdtd.setnamed('profile_z0', 'use source limits', 1)
    fdtd.setnamed('profile_z0', 'frequency points', 11)

    for k, v in (('x', 0.0), ('x span', 2 * X_REG * NM), ('y', 0.0), ('y span', 2 * Y_REG * NM),
                 ('z', 0.0), ('z span', 2 * Z_REG * NM)):
        fdtd.setnamed('FDTD', k, v)
    fdtd.setnamed('FDTD', 'mesh type', 'auto non-uniform'); fdtd.setnamed('FDTD', 'mesh accuracy', 3)
    fdtd.setnamed('FDTD', 'dt stability factor', 0.95)
    fdtd.setnamed('FDTD', 'simulation time', 3e-12)
    for b in ('x min bc', 'x max bc', 'y min bc', 'y max bc', 'z min bc', 'z max bc'):
        fdtd.setnamed('FDTD', b, 'PML')
    for k, v in (('x', 0.0), ('x span', 2 * (X_REG - 200) * NM), ('y', 0.0), ('y span', (W + 60) * NM),
                 ('z', 0.0), ('z span', (T + 40) * NM)):
        fdtd.setnamed('mesh_beam', k, v)
    for k in ('dx', 'dy', 'dz'):
        fdtd.setnamed('mesh_beam', k, 10 * NM)

    for k, v in (('x', 0.0), ('x span', 2 * (X_REG + 2000) * NM), ('y', 0.0), ('y span', W * NM),
                 ('z', 0.0), ('z span', T * NM)):
        fdtd.setnamed('beam', k, v)
    fdtd.setnamed('beam', 'override mesh order from material database', 1); fdtd.setnamed('beam', 'mesh order', 2)
    for name, x, hx, hy in holes:
        fdtd.setnamed(name, 'make ellipsoid', 1)
        fdtd.setnamed(name, 'radius', hx / 2 * NM); fdtd.setnamed(name, 'radius 2', hy / 2 * NM)
        fdtd.setnamed(name, 'x', x * NM); fdtd.setnamed(name, 'y', 0.0)
        fdtd.setnamed(name, 'z', 0.0); fdtd.setnamed(name, 'z span', (T + 40) * NM)
        fdtd.setnamed(name, 'override mesh order from material database', 1); fdtd.setnamed(name, 'mesh order', 1)

    fdtd.save(FSP)
    p(f'Saved {FSP}: {len(holes)} holes, region x +/-{X_REG:.0f} nm, y +/-{Y_REG:.0f}, z +/-{Z_REG:.0f}')

info = dict(fsp=FSP, cfg=CFG, w=W, t=T, n=N_D, dipole_x_nm=X_DIP, time_monitors_nm=T_PTS,
            layout={k: [float(v) for v in LAY[k]] for k in ('x', 'a', 'hx', 'hy')})
Path('runs/cavity_619/lumerical').mkdir(parents=True, exist_ok=True)
json.dump(info, open('runs/cavity_619/lumerical/fsp_info.json', 'w'), indent=1)
p('done')
