import subprocess, sys
subprocess.run([sys.executable, '-u', 'surrogate_explore__eval_batch.py', '42'], check=False)
