"""
pull.py  (runs locally on Mac)
Pull diamond_a_sweep .npz files from jv-adamantoise into runs/diamond_a_sweep/data/.
Lists the remote folder first (scp globs don't work against Windows OpenSSH),
then copies only files not already present locally. Also prints the job-log tail.

Usage (from project root):
    python runs/diamond_a_sweep/pull.py
"""

import subprocess
from pathlib import Path

HOST   = '<USER>@<COMSOL_HOST>'
KEY    = str(Path.home() / '.ssh' / 'id_ed25519')
REMOTE = 'C:/Users/abby/comsol/runs/diamond_a_sweep/data'
LOCAL  = Path('runs/diamond_a_sweep/data')
LOCAL.mkdir(parents=True, exist_ok=True)

ssh = ['ssh', '-i', KEY, '-o', 'ConnectTimeout=15', HOST]

out = subprocess.run(ssh + [f'powershell -Command "Get-ChildItem {REMOTE} -Name"'],
                     capture_output=True, text=True, check=True).stdout
remote_files = sorted(f.strip() for f in out.splitlines() if f.strip().endswith('.npz'))

new = [f for f in remote_files if not (LOCAL / f).exists()]
for f in new:
    subprocess.run(['scp', '-q', '-i', KEY, f'{HOST}:{REMOTE}/{f}', str(LOCAL)], check=True)

print(f'Remote: {len(remote_files)}/54 combos done.  Pulled {len(new)} new file(s).')

log = subprocess.run(ssh + ['powershell -Command "Get-Content C:/Users/abby/comsol/job_log.txt -Tail 4; '
                            'Select-String -Path C:/Users/abby/comsol/job_log.txt -Pattern FAILED,Traceback,Error '
                            '| Select-Object -Last 5 | ForEach-Object { $_.Line }"'],
                     capture_output=True, text=True).stdout
print('--- remote log tail / errors ---')
print(log.strip())
