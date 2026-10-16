"""
run_sweeps.py  (old PC DESKTOP-BBQLCD3, Lumerical v211; user 2026-10-15: run the optics replicas here, not on
the COMSOL machine). Runs the generated .lsf sweeps in one FDTD session: copies <name>.lsf -> <name>_run.lsf
with do_run = 1 (and optional first/last point), executes it in this folder (outputs prefixed <name>_).
Usage:  py -3.8 -u run_sweeps.py name[:first:last] [name ...]
"""
import os, re, sys, time
sys.path.append(r"C:\Program Files\Lumerical\v211\api\python")
os.environ["PATH"] += r";C:\Program Files\Lumerical\v211\bin"
import lumapi
WD = os.path.dirname(os.path.abspath(__file__))
t0 = time.time()
with lumapi.FDTD(hide=True) as fdtd:
    fdtd.cd(WD)
    for arg in sys.argv[1:]:
        name, *rng = arg.split(':')
        s = open(os.path.join(WD, name + '.lsf')).read()
        s = re.sub(r'^do_run\s*=\s*\d;', 'do_run       = 1;', s, flags=re.M)
        if rng:
            s = re.sub(r'^first_point\s*=\s*\d+;', f'first_point  = {rng[0]};', s, flags=re.M)
            s = re.sub(r'^last_point\s*=\s*\d+;', f'last_point   = {rng[1]};', s, flags=re.M)
        summ = os.path.join(WD, name + '_summary.txt')
        if (not rng or rng[0] == '1') and os.path.exists(summ):   # fresh sweep (the .lsf cannot rm in safe mode)
            os.remove(summ)
        run = os.path.join(WD, name + '_run.lsf')
        open(run, 'w').write(s)
        print(f'--- {arg} start ({time.time()-t0:.0f} s)'); sys.stdout.flush()
        fdtd.feval(run)
        print(f'--- {arg} done ({time.time()-t0:.0f} s)'); sys.stdout.flush()
print('sweeps done.')
