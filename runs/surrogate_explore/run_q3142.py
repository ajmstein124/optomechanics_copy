"""run_q3142.py (remote): wait for batch 32 to finish (memory: at most 2 full-thickness models at a time), then batches 31 and 42."""
import subprocess, sys, time
from pathlib import Path
log = Path(r'C:\Users\abby\comsol\job_log_surrogate_explore__run_s32.txt')
t0 = time.time()
while 'batch 32 done' not in (log.read_text(errors='ignore') if log.exists() else ''):
    if time.time() - t0 > 10 * 3600:
        break
    time.sleep(60)
subprocess.run([sys.executable, '-u', 'surrogate_explore__eval_batch.py', '31', '42'], check=False)
