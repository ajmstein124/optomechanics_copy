"""
fsp_best60.py  (remote)  -- runs/cavity_619_width
BUILD-ONLY .fsp (no FDTD run; user 2026-10-15) of the current best 60 nm device:
  w 650, t 120, hx/a 0.53, hy/w 0.77, d 0.10, a 190.3, xi 6, chi 4.0
  COMSOL (w650_mf60/data/best1_w650_mf60.npz): 619.5 nm, Q 1.8e7, breathing 9.67 GHz (loc 0.95, sidewall ratio 1.0),
  min feature 64 nm. (Replaces d 0.13 / a 194: its 9.82 GHz mode is a hybrid, sidewall ratio 0.35.)
Same generator as the sweep replicas (make_lsf.write_lsf), executed with do_run = 0.
Output: C:\\Users\\abby\\lumerical\\lum_w650_mf60_best_check.fsp (+ .lsf)
"""
import os
import sys
from pathlib import Path

sys.path.append(r"C:\Program Files\ANSYS Inc\v252\Lumerical\api\python")
os.environ["PATH"] += r";C:\Program Files\ANSYS Inc\v252\Lumerical\bin"
os.environ.setdefault("ANSYSLMD_LICENSE_FILE", "<PORT>@<LICENSE_SERVER>")   # TEMP-profile workaround
import lumapi                                    # noqa: E402
import make_lsf                                  # noqa: E402

make_lsf.OUT = Path(r'C:\Users\abby\lumerical')
name = 'lum_w650_mf60_best'
cell = dict(w=650, t=120, hx_a=0.53, hy_w=0.77)
lsf = make_lsf.write_lsf(name, cell, [dict(a=190.3, d=0.10, xi=6.0, chi=4.0)], 1,
                         'Best 60 nm device so far (w 650). COMSOL: 619.5 nm, Q 1.8e7, breathing 9.67 GHz.')
with lumapi.FDTD(hide=True) as fdtd:
    fdtd.cd(str(make_lsf.OUT)); fdtd.feval(str(lsf))
fsp = make_lsf.OUT / f'{name}_check.fsp'
print(f'built {fsp} exists={fsp.exists()}')
