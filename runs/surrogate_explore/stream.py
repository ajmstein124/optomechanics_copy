"""stream.py (Mac): launch a chain of BO batches as ONE remote job with its own log:
    python runs/surrogate_explore/stream.py <name> <batch> [<batch> ...]
Uploads batch_<n>.json for each, writes run_<name>.py (calls eval_batch.py for the batches in order)."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
name, batches = sys.argv[1], sys.argv[2:]
key = str(Path("~/.ssh/id_ed25519").expanduser())
for b in batches:
    subprocess.run(["scp", "-q", "-i", key, str(HERE / f"batch_{b}.json"),
                    f"<USER>@<COMSOL_HOST>:C:/Users/abby/comsol/surrogate_explore__batch_{b}.json"], check=True)
for mod in ("eval_batch.py",):           # the evaluator itself (2026-10-19 bug: a stale remote copy ran the old 1/8 model)
    subprocess.run(["scp", "-q", "-i", key, str(HERE / mod), f"<USER>@<COMSOL_HOST>:C:/Users/abby/comsol/surrogate_explore__{mod}"], check=True)
run = HERE / f"run_{name}.py"
run.write_text("import subprocess, sys\n"
               f"subprocess.run([sys.executable, '-u', 'surrogate_explore__eval_batch.py', {', '.join(repr(b) for b in batches)}], check=False)\n")
subprocess.run([sys.executable, str(HERE.parents[1] / "scripts" / "remote_runner.py"), str(run)], check=True)
