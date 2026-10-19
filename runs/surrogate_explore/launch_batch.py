"""launch_batch.py (Mac): upload batch_<n>.json and launch eval_batch.py for it via remote_runner (detached)."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
n = int(sys.argv[1])
(HERE / 'current_batch.txt').write_text(str(n))
# remote_runner uploads sibling *.json as surrogate_explore__<name>.json; the .txt goes via scp
subprocess.run(['scp', '-q', '-i', str(Path('~/.ssh/id_ed25519').expanduser()), str(HERE / 'current_batch.txt'),
                '<USER>@<COMSOL_HOST>:C:/Users/abby/comsol/surrogate_explore__current_batch.txt'], check=True)
subprocess.run([sys.executable, str(HERE.parents[1] / 'scripts' / 'remote_runner.py'), str(HERE / 'eval_batch.py')], check=True)
