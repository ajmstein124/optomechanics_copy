"""
lum_run.py  (old PC DESKTOP-BBQLCD3, Lumerical v211, py -3.8; copied from optomechanics run_sweeps.py)
Runs generated .lsf sweeps in one FDTD session from this folder (outputs prefixed <name>_), ONE POINT PER CALL:
  - resumable: a point whose <name>_pt<i>.mat already exists is skipped (delete the .mat to redo it)
  - a point that errors (e.g. Qanalysis finds no resonance -> "Can not find result 'Q'") is logged to
    <name>_failed.txt and the sweep moves on; haveresult() does NOT catch that case in v211 (10/16 crash)
  py -3.8 -u lum_run.py name[:first:last] [name ...]     run (do_run = 1)
  py -3.8 -u lum_run.py --check name [name ...]          build check_point only -> <name>_check.fsp
Same file is used for the optomechanics queue (copied into its lumerical folder). ASCII-only prints (cp1252 console).
"""
import os, re, sys, time
sys.path.append(r"C:\Program Files\Lumerical\v211\api\python")
os.environ["PATH"] += r";C:\Program Files\Lumerical\v211\bin"
import lumapi
WD = os.path.dirname(os.path.abspath(__file__))
check = sys.argv[1] == '--check'
args = sys.argv[2:] if check else sys.argv[1:]
t0 = time.time()


def log(msg):
    print('%s (%.0f s)' % (msg, time.time() - t0)); sys.stdout.flush()


def write_run(name, s, first, last, do_run):
    s = re.sub(r'^do_run\s*=\s*\d;', 'do_run       = %d;' % do_run, s, flags=re.M)
    s = re.sub(r'^first_point\s*=\s*\d+;', 'first_point  = %d;' % first, s, flags=re.M)
    s = re.sub(r'^last_point\s*=\s*\d+;', 'last_point   = %d;' % last, s, flags=re.M)
    run = os.path.join(WD, name + '_run.lsf')
    open(run, 'w').write(s)
    return run


with lumapi.FDTD(hide=True) as fdtd:
    fdtd.cd(WD)
    for arg in args:
        name, *rng = arg.split(':')
        s = open(os.path.join(WD, name + '.lsf')).read()
        if check:
            fdtd.feval(write_run(name, s, 1, 1, 0)); log('--- %s check built' % name); continue
        npts = int(re.search(r'^npts\s*=\s*(\d+);', s, flags=re.M).group(1))
        first, last = (int(rng[0]), int(rng[1])) if rng else (1, npts)
        log('--- %s points %d-%d start' % (name, first, last))
        for ip in range(first, last + 1):
            if os.path.exists(os.path.join(WD, '%s_pt%d.mat' % (name, ip))):
                continue
            try:
                fdtd.feval(write_run(name, s, ip, ip, 1))
                log('%s point %d done' % (name, ip))
            except Exception as e:
                msg = str(e).encode('ascii', 'replace').decode()
                open(os.path.join(WD, name + '_failed.txt'), 'a').write('%d %s\n' % (ip, msg))
                log('%s point %d FAILED: %s' % (name, ip, msg))
                try:
                    fdtd.switchtolayout()
                except Exception:
                    pass
        log('--- %s done' % name)
log('lum_run done.')
