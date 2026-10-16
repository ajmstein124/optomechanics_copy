"""probe_qanalysis.py (remote, read-only probe): can 'Qanalysis' be added by script, and what are its properties?"""
import os, sys
sys.path.append(r"C:\Program Files\ANSYS Inc\v252\Lumerical\api\python")
os.environ["PATH"] += r";C:\Program Files\ANSYS Inc\v252\Lumerical\bin"
os.environ.setdefault("ANSYSLMD_LICENSE_FILE", "<PORT>@<LICENSE_SERVER>")
import lumapi
def p(*a): print(*a); sys.stdout.flush()
with lumapi.FDTD(hide=True) as fdtd:
    for name in ('Qanalysis', 'high_Q_analysis', 'Q analysis'):
        try:
            fdtd.addobject(name); fdtd.set('name', 'qa_test')
            p('addobject OK:', name)
            props = fdtd.eval('?getdata;') if False else None
            p(fdtd.eval('s = splitstring(get("qa_test")," "); ?get;') if False else '')
            break
        except Exception as e:
            p('addobject failed:', name, str(e)[:120])
    fdtd.eval('select("qa_test"); ?getnamed("qa_test","type"); props = getpropertylist; ?props;') if False else None
    try:
        fdtd.select('qa_test')
        p(fdtd.eval('out = "";') or '')
        fdtd.eval('pl = splitstring(get(""),""); ')
    except Exception as e:
        p('list err', str(e)[:100])
    for prop in ('t start', 'f min', 'f max', 'lambda min', 'lambda max', 'nx', 'ny', 'nz', 'x span', 'y span', 'z span',
                 'use relative coordinates', 'make plots', 'number of resonances', 'resonance threshold'):
        try:
            p(f'  {prop!r} = {fdtd.getnamed("qa_test", prop)}')
        except Exception as e:
            p(f'  {prop!r}: n/a')
