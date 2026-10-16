"""
fsp_builds.py  (remote)  -- runs/cavity_619_final
After the COMSOL chain (waits for 'Deliverables done.'): for each final device (final_<mf>.json) write a
single-point .lsf with the SAME generator as the sweep replicas (make_lsf.write_lsf) and execute it in
BUILD-ONLY mode (do_run = 0) -> <name>_check.fsp for GUI inspection. Per user 2026-10-14: Lumerical is
only used to build/save files here; NO FDTD simulation is run.
Output: C:\\Users\\abby\\lumerical\\lum_best_<mf>_check.fsp (+ the .lsf)
"""
import json
import os
import sys
import time
from pathlib import Path

LOGD = Path(r'C:\Users\abby\comsol\job_log_cavity_619_final__deliverables.txt')
t0 = time.time()
time.sleep(600)                                  # let the relaunched deliverables log start
while LOGD.exists() and 'Deliverables done.' not in LOGD.read_text(errors='ignore'):
    if time.time() - t0 > 40 * 3600:
        break
    time.sleep(120)

sys.path.append(r"C:\Program Files\ANSYS Inc\v252\Lumerical\api\python")
os.environ["PATH"] += r";C:\Program Files\ANSYS Inc\v252\Lumerical\bin"
os.environ.setdefault("ANSYSLMD_LICENSE_FILE", "<PORT>@<LICENSE_SERVER>")   # TEMP-profile workaround
import lumapi                                    # noqa: E402
import make_lsf                                  # noqa: E402  (uploaded next to this script)

make_lsf.OUT = Path(r'C:\Users\abby\lumerical')
for fn in sorted(Path('runs/cavity_619_final/data').glob('final_*.json')):
    b = json.load(open(fn)); mf = fn.stem.replace('final_', '')
    name = f'lum_best_{mf}'
    lsf = make_lsf.write_lsf(name, b['cell'], [dict(a=b['a'], d=b['d'], xi=b['xi'], chi=b['chi'])], 1,
                             f"Final {mf} device (COMSOL: {b})")
    with lumapi.FDTD(hide=True) as fdtd:
        fdtd.cd(str(make_lsf.OUT)); fdtd.feval(str(lsf))
    print(f'{mf}: built {make_lsf.OUT / (name + "_check.fsp")}'); sys.stdout.flush()
print('fsp builds done.')
