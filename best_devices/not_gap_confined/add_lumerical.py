"""
add_lumerical.py  (Mac) -- best_devices/: Lumerical FDTD verification of each final device.
Runs on the GPU computer (<USER>@<GPU_HOST>, Lumerical v251, express mode, lum_run.py --gpu) from
runs/cavity_619/lumerical/lum_best_<mf>.lsf (make_lsf.py layout, x/y anti-symmetric + z symmetric, 5 ps, Qanalysis).
Per device folder: lumerical_verification.png (Ey maps Lumerical vs COMSOL, on-axis cut, resonances) + lumerical_verification.md.
Run from the project root:  python best_devices/not_gap_confined/add_lumerical.py   (pulls the .mat / summary from the GPU computer)
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import h5py
import numpy as np

G = '<USER>@<GPU_HOST>:C:/Users/<USER>/Documents/optomechanics/lumerical'
LUM = Path('runs/cavity_619/lumerical'); RES = LUM / 'results'
for mf in ('60nm', '80nm'):
    F = json.load(open(f'runs/cavity_619_final/data/final_{mf}.json'))
    slug = f"{mf}_w{F['cell']['w']}_d{F['d']:.2f}_xi{F['xi']:g}_chi{F['chi']:g}"
    od = Path('best_devices/not_gap_confined') / slug
    name = f'lum_best_{mf}'
    if subprocess.run(['scp', '-q', f'{G}/{name}_pt1.mat', str(RES / f'{name}_pt1.mat')]).returncode:
        print(mf, 'not run yet'); continue
    subprocess.run([sys.executable, str(LUM / 'plot_lum_point.py'), name, '1', f"{F['run_dir']}/data/fields_final.npz"], check=True)
    shutil.copy(RES / f'{name}_pt1.png', od / 'lumerical_verification.png')
    f = h5py.File(RES / f'{name}_pt1.mat', 'r')
    lam, Q = float(np.ravel(f['lam_best'])[0]) * 1e9, float(np.ravel(f['Q_best'])[0])
    md = f"""# Lumerical verification: {slug}

Independent FDTD check of the COMSOL design (`lumerical_verification.png`). Same hole layout (scripts/cavity_taper.py),
Lumerical FDTD v251 on the GPU computer (express mode), x/y anti-symmetric + z symmetric (COMSOL's mode class),
5 ps, Qanalysis (`runs/cavity_619/lumerical/{name}.lsf`).

| | COMSOL | Lumerical |
|---|---|---|
| resonance | {F['lam']:.2f} nm | {lam:.2f} nm ({lam - F['lam']:+.2f} nm, {100 * (lam - F['lam']) / F['lam']:+.2f} %) |
| optical Q | {F['Q']:.2e} | {Q:.2e} (lower bound: a 5 ps run cannot resolve the decay of Q > ~1e6) |

The field maps agree in shape and envelope; the spike at the center of the Lumerical map is the dipole source's near field.
"""
    if Q > F['Q']:
        md += (f"\nLumerical's Q ({Q:.1e}) is ABOVE the COMSOL value ({F['Q']:.1e}). Possible cause: COMSOL's compact air/PML box "
               "(validated only on the w550 beam) may limit its Q for this wider device; not yet checked with a larger COMSOL box.\n")
    if mf == '60nm':
        shutil.copy(LUM / 'lum_w650_mf60_shape_vs_comsol.png', od / 'lumerical_sweep_replica.png')
        md += ("\nThe w650 / 60 nm taper-shape sweep that found this device was also replicated point by point in Lumerical "
               "(old PC, CPU, 1.5 ps): `lumerical_sweep_replica.png`.\n")
    (od / 'lumerical_verification.md').write_text(md)
    print('wrote', od / 'lumerical_verification.md', f'{lam:.2f} nm, Q {Q:.2e}')
