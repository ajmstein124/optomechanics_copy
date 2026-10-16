"""run_lsf_check.py (remote): execute a generated .lsf in build-only mode (do_run = 0) to produce its
<name>_check.fsp for GUI inspection. Usage: set LSF below; run via remote_runner --block."""
import os, sys
sys.path.append(r"C:\Program Files\ANSYS Inc\v252\Lumerical\api\python")
os.environ["PATH"] += r";C:\Program Files\ANSYS Inc\v252\Lumerical\bin"
os.environ.setdefault("ANSYSLMD_LICENSE_FILE", "<PORT>@<LICENSE_SERVER>")   # TEMP-profile workaround
import lumapi
LSFS = [r"C:\Users\abby\lumerical\lum_ad_mf60.lsf"]
def p(*a): print(*a); sys.stdout.flush()
for lsf in LSFS:
    with lumapi.FDTD(hide=True) as fdtd:
        fdtd.feval(lsf)
        p(f'{lsf}: build-only run OK')
