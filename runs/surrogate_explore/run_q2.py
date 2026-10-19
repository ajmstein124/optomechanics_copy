"""run_q2.py (remote): after the SEQ stream (batch 42 done), run the next queue: batches listed in surrogate_explore__queue2.txt
(one per line, re-read after each batch so the Mac can append), one full-thickness model at a time."""
import subprocess, sys, time
from pathlib import Path
log = Path(r'C:\Users\abby\comsol\job_log_surrogate_explore__run_SEQ.txt')
q = Path('surrogate_explore__queue2.txt')
t0 = time.time()
while 'batch 42 done' not in (log.read_text(errors='ignore') if log.exists() else ''):
    if time.time() - t0 > 12 * 3600:
        break
    time.sleep(60)
done = set()
while True:
    todo = [l.strip() for l in q.read_text().splitlines() if l.strip()] if q.exists() else []
    todo = [b for b in todo if b not in done]
    if not todo:
        break
    b = todo[0]; done.add(b)
    subprocess.run([sys.executable, '-u', 'surrogate_explore__eval_batch.py', b], check=False)
print('queue2 done.', flush=True)
