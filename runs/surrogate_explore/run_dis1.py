"""run_dis1.py (remote): disorder sigma 1 nm (s_x 0.5 nm), 4 seeds, same three designs."""
import subprocess, sys
subprocess.run([sys.executable, '-u', 'surrogate_explore__disorder_sigma.py', '1.0', '4'], check=False)
