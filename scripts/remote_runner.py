"""
remote_runner.py

SSH runner for executing Python scripts on the Windows COMSOL machine.
Supports two modes:

  DETACH mode (default for overnight runs):
    python scripts/remote_runner.py scripts/some_script.py
    -- Copies script, launches it detached on Windows (survives SSH disconnect),
       returns immediately. Safe to close your Mac.

  BLOCKING mode (for short interactive runs):
    python scripts/remote_runner.py --block scripts/some_script.py
    -- Keeps SSH open, streams output, pulls results on finish.

  Status / result pull:
    python scripts/remote_runner.py --status
    -- Shows last detached job status (running/done), tails log, pulls results.

  Result pull only:
    python scripts/remote_runner.py --pull
    -- Just pulls results, no job check.

  Scripts under runs/<name>/ (2026-10-14):
    -- uploaded as <name>__<script>.py (no collisions between runs' sweep.py),
       sibling *.json files uploaded as <name>__<file>.json (e.g. <name>__plan.json),
       comsol_utils.py + plan_runner.py always uploaded,
       log at job_log_<name>__<stem>.txt (previous runs' logs are kept),
       --status / --pull fetch new files from runs/<name>/data/ (incl. subfolders)
       into the local runs/<name>/data/.

  Copy large model file (one-time):
    python scripts/remote_runner.py --copy-model scripts/unit_cell_3.mph

  Verify SSH is working:
    python scripts/remote_runner.py --check
"""

import subprocess
import sys
import os
import argparse
import base64
import json
import threading
import time
from pathlib import Path

# =============================================================================
# SSH / REMOTE CONFIG
# =============================================================================

REMOTE_HOST = '<USER>@<COMSOL_HOST>'
SSH_KEY     = os.path.expanduser('~/.ssh/id_ed25519')
REMOTE_DIR  = r'C:\Users\abby\comsol'
PYTHON_EXE  = r'C:\Program Files\ANSYS Inc\v252\Lumerical\python-3.13.1\python.exe'

# For blocking mode (legacy / short runs)
PYTHON_CMD  = r'"C:\Program Files\ANSYS Inc\v252\Lumerical\python-3.13.1\python.exe" -u'
POLL_INTERVAL = 90

# =============================================================================

LOCAL_RESULTS = Path(__file__).parent.parent / 'results'
JOB_FILE      = Path(__file__).parent.parent / '.last_job.json'


def _ssh(cmd, capture=False):
    full = ['ssh', '-i', SSH_KEY, '-o', 'StrictHostKeyChecking=no',
            '-o', 'ServerAliveInterval=60', REMOTE_HOST, cmd]
    if capture:
        r = subprocess.run(full, capture_output=True, text=True)
        return r.stdout, r.stderr, r.returncode
    else:
        r = subprocess.run(full)
        return r.returncode


def _ssh_ps(ps_script, capture=True):
    """Run a PowerShell script on the remote machine via EncodedCommand (no quoting issues)."""
    encoded = base64.b64encode(ps_script.encode('utf-16-le')).decode('ascii')
    return _ssh(f'powershell -EncodedCommand {encoded}', capture=capture)


def _scp_to(local_path, remote_path):
    cmd = ['scp', '-i', SSH_KEY, '-o', 'StrictHostKeyChecking=no',
           str(local_path), f'{REMOTE_HOST}:{remote_path}']
    subprocess.run(cmd, check=True)


def _scp_from(remote_glob, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    cmd = ['scp', '-i', SSH_KEY, '-o', 'StrictHostKeyChecking=no',
           f'{REMOTE_HOST}:{remote_glob}', str(local_dir)]
    subprocess.run(cmd, capture_output=True)


def _run_name(script_path: Path):
    """'diamond_a_sweep' for runs/diamond_a_sweep/sweep.py, else None."""
    parts = Path(script_path).resolve().parts
    if 'runs' in parts:
        i = parts.index('runs')
        if i + 2 < len(parts):
            return parts[i + 1]
    return None


def _pull_run_data(run_name):
    """Copy files in remote runs/<run>/data/ (recursive) that are missing locally."""
    remote_rel = f'runs\\{run_name}\\data'
    out, _, rc = _ssh_ps(
        f'$b = "{REMOTE_DIR}\\{remote_rel}"; '
        f'if (Test-Path $b) {{ Get-ChildItem $b -Recurse -File | '
        f'ForEach-Object {{ $_.FullName.Substring($b.Length + 1) }} }}')
    if rc != 0:
        print('  (could not list remote data folder)')
        return 0
    local_base = Path(__file__).parent.parent / 'runs' / run_name / 'data'
    remote_fwd = REMOTE_DIR.replace('\\', '/') + f'/runs/{run_name}/data'
    n_new = 0
    for rel in out.strip().splitlines():
        rel = rel.strip().replace('\\', '/')
        if not rel:
            continue
        dest = local_base / rel
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['scp', '-q', '-i', SSH_KEY, '-o', 'StrictHostKeyChecking=no',
                        f'{REMOTE_HOST}:{remote_fwd}/{rel}', str(dest)], capture_output=True)
        n_new += 1
    print(f'  pulled {n_new} new file(s) into {local_base}')
    return n_new


def _pull_results(sweep_name=None, run_name=None):
    """
    Pull results from remote, mirroring the remote simu_data/<subfolder> structure.
    If sweep_name is given, pull only that subfolder into results/<sweep_name>/.
    Otherwise pull all simu_data subfolders, each into its own local subfolder.
    """
    import re
    remote_fwd = REMOTE_DIR.replace('\\', '/')

    if run_name:
        _pull_run_data(run_name)
        return
    if sweep_name:
        local_dir = LOCAL_RESULTS / sweep_name
        local_dir.mkdir(parents=True, exist_ok=True)
        for ext in ('*.mat', '*.jpg', '*.npz', '*.png'):
            _scp_from(f'{remote_fwd}/simu_data/{sweep_name}/{ext}', local_dir)
    else:
        # Discover all simu_data subfolders on remote
        out, _, rc = _ssh(f'dir /b "{REMOTE_DIR}\\simu_data"', capture=True)
        if rc == 0:
            for subfolder in out.strip().splitlines():
                subfolder = subfolder.strip()
                if not subfolder:
                    continue
                local_dir = LOCAL_RESULTS / subfolder
                local_dir.mkdir(parents=True, exist_ok=True)
                for ext in ('*.mat', '*.jpg', '*.npz', '*.png'):
                    _scp_from(f'{remote_fwd}/simu_data/{subfolder}/{ext}', local_dir)
        # Pull loose CSV files from simu_data/ root (Python sweep outputs)
        local_simu = LOCAL_RESULTS.parent / 'simu_data'
        local_simu.mkdir(parents=True, exist_ok=True)
        _scp_from(f'{remote_fwd}/simu_data/*.csv', local_simu)
        # Also pull any loose files in REMOTE_DIR root
        for ext in ('*.mat', '*.jpg', '*.csv', '*.npz', '*.png'):
            _scp_from(f'{remote_fwd}/{ext}', LOCAL_RESULTS)


def _remote_name(script_path: Path):
    run = _run_name(script_path)
    return f'{run}__{script_path.name}' if run else script_path.name


def _copy_script(script_path: Path):
    """Copy script (as <run>__<name>.py for runs/<run>/ scripts), sibling *.json,
    and comsol_utils.py to remote."""
    remote_script = REMOTE_DIR + '\\' + _remote_name(script_path)
    _ssh(f'if not exist "{REMOTE_DIR}" mkdir "{REMOTE_DIR}"')
    print(f'  Copying {script_path.name} -> {_remote_name(script_path)}...')
    _scp_to(script_path, remote_script)
    if _run_name(script_path):
        run = _run_name(script_path)
        for js in sorted(script_path.parent.glob('*.json')):
            print(f'  Copying {js.name} -> {run}__{js.name}...')
            _scp_to(js, REMOTE_DIR + '\\' + f'{run}__{js.name}')
    for util in ('comsol_utils.py', 'plan_runner.py', 'build_nanobeam_model.py', 'build_cavity_model.py', 'cavity_taper.py', 'cavity_eval.py', 'cavity_pipeline.py', 'cavity_fields.py', 'cavity_designs.py'):
        up = Path(__file__).parent / util
        if up.exists():
            _scp_to(up, REMOTE_DIR + '\\' + util)


# ---------------------------------------------------------------------------
# DETACH MODE  (default, safe for overnight runs)
# ---------------------------------------------------------------------------

def launch_detached(script_path: Path):
    """
    Copy script to remote and launch it detached via a cmd.exe bat wrapper.
    cmd.exe handles > redirection natively (Start-Process -Redirect is unreliable).
    The job survives SSH disconnection -- safe to close the Mac.
    Returns immediately after launch.
    """
    import tempfile

    _copy_script(script_path)

    remote_name = _remote_name(script_path)
    stem     = Path(remote_name).stem
    log_file = REMOTE_DIR + f'\\job_log_{stem}.txt'
    bat_file = REMOTE_DIR + f'\\run_job_{stem}.bat'

    # Write a bat wrapper locally and SCP it over.
    # cmd.exe /c runs the bat and waits, so PID tracking works.
    bat_content = (
        f'@echo off\r\n'
        f'cd /d "{REMOTE_DIR}"\r\n'
        f'"{PYTHON_EXE}" -u "{remote_name}" > "{log_file}" 2>&1\r\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False, encoding='ascii') as f:
        f.write(bat_content)
        tmp_bat = f.name
    try:
        _scp_to(tmp_bat, bat_file)
    finally:
        Path(tmp_bat).unlink(missing_ok=True)

    # Clear previous log of THIS script only (other runs' logs are kept)
    _ssh_ps(f'Remove-Item -Path "{log_file}" -ErrorAction SilentlyContinue')

    # Invoke-CimMethod Win32_Process::Create creates a process that is completely
    # detached from the calling session (no job-object inheritance). This is the
    # reliable Windows equivalent of nohup -- survives SSH disconnect.
    ps = (
        f'$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create '
        f'-Arguments @{{CommandLine="cmd.exe /c {bat_file}"; '
        f'CurrentDirectory="{REMOTE_DIR}"}}; '
        f'Write-Output $r.ProcessId'
    )
    out, err, rc = _ssh_ps(ps)
    pid_str = out.strip()

    if rc != 0 or not pid_str.isdigit():
        print(f'ERROR launching job (rc={rc})')
        print(f'stdout: {out.strip()[:300]}')
        print(f'stderr: {err.strip()[:300]}')
        sys.exit(1)

    pid = int(pid_str)
    # Infer sweep name from SAVE_FOLDER in the script (grep for simu_data/...)
    sweep_name = None
    try:
        txt = script_path.read_text(encoding='utf-8', errors='ignore')
        import re
        m = re.search(r"simu_data[/\\\\]+([^'\")\s]+)", txt)
        if m:
            sweep_name = m.group(1).split('/')[0].split('\\')[0]
    except Exception:
        pass

    job = {
        'pid':        pid,
        'script':     remote_name,
        'run_name':   _run_name(script_path),
        'launched':   time.strftime('%Y-%m-%d %H:%M:%S'),
        'log_out':    log_file,
        'log_err':    '',
        'sweep_name': sweep_name,
    }
    JOB_FILE.write_text(json.dumps(job, indent=2))

    print(f'\nJob launched on remote machine.')
    print(f'  Script : {script_path.name}')
    print(f'  PID    : {pid}  (cmd.exe wrapper)')
    print(f'  Log    : {log_file}')
    print(f'\nSafe to close your Mac. Check back with:')
    print(f'  python scripts/remote_runner.py --status')


# ---------------------------------------------------------------------------
# STATUS CHECK
# ---------------------------------------------------------------------------

def check_status():
    """Check last detached job, tail log, pull results."""
    if not JOB_FILE.exists():
        print('No detached job found. Launch one with:')
        print('  python scripts/remote_runner.py scripts/your_script.py')
        return

    job = json.loads(JOB_FILE.read_text())
    pid     = job['pid']
    script  = job['script']
    started = job['launched']
    log_out = job['log_out']
    log_err = job.get('log_err', '')

    # Check if still running
    ps_check = (
        f'$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue; '
        f'if ($p) {{ "running" }} else {{ "done" }}'
    )
    out, _, _ = _ssh_ps(ps_check)
    status = out.strip()

    print(f'Script  : {script}')
    print(f'Started : {started}')
    print(f'Status  : {status}')

    # Tail stdout log
    print('\n--- Log (last 40 lines) ---')
    ps_tail = f'Get-Content "{log_out}" -Tail 40 -ErrorAction SilentlyContinue'
    out, _, _ = _ssh_ps(ps_tail)
    print(out.strip() or '(empty)')

    # Tail stderr if there's anything
    if log_err:
        ps_err = (
            f'$e = Get-Content "{log_err}" -ErrorAction SilentlyContinue; '
            f'if ($e) {{ Write-Output "--- Errors ---"; $e }}'
        )
        out, _, _ = _ssh_ps(ps_err)
        if out.strip():
            print(out.strip())

    # Pull results into sweep-specific subfolder if known
    sweep_name = job.get('sweep_name')
    run_name   = job.get('run_name')
    print('\nPulling results...')
    _pull_results(sweep_name, run_name)
    if not run_name:
        dest = LOCAL_RESULTS / sweep_name if sweep_name else LOCAL_RESULTS
        print(f'Results in: {dest}')


# ---------------------------------------------------------------------------
# BLOCKING MODE  (for short / interactive runs)
# ---------------------------------------------------------------------------

def _poll_loop(stop_event: threading.Event, run_name=None):
    while not stop_event.wait(POLL_INTERVAL):
        ts = time.strftime('%H:%M:%S')
        print(f'\n  [{ts}] pulling intermediate results...')
        _pull_results(run_name=run_name)


def run_blocking(script_path: Path):
    """Keep SSH open, stream output, poll results. Closes if Mac disconnects."""
    _copy_script(script_path)

    run_cmd = f'cd /d "{REMOTE_DIR}" && {PYTHON_CMD} "{_remote_name(script_path)}"'
    run_name = _run_name(script_path)
    print(f'Running (blocking)... (results polled every {POLL_INTERVAL}s)')

    ssh_proc = subprocess.Popen(
        ['ssh', '-i', SSH_KEY, '-o', 'StrictHostKeyChecking=no', REMOTE_HOST, run_cmd]
    )

    stop_event = threading.Event()
    poll_thread = threading.Thread(target=_poll_loop, args=(stop_event, run_name), daemon=True)
    poll_thread.start()

    rc = ssh_proc.wait()
    stop_event.set()
    poll_thread.join()

    if rc != 0:
        print(f'WARNING: remote script exited with code {rc}')

    print('Pulling final results...')
    _pull_results(run_name=run_name)


# ---------------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------------

def copy_model(local_model_path: str):
    p = Path(local_model_path)
    if not p.exists():
        print(f'ERROR: model file not found: {p}')
        sys.exit(1)
    remote_path = REMOTE_DIR + '\\' + p.name
    _ssh(f'if not exist "{REMOTE_DIR}" mkdir "{REMOTE_DIR}"')
    print(f'Copying {p.name} ({p.stat().st_size / 1e6:.0f} MB) -- this will take a while...')
    _scp_to(p, remote_path)
    print(f'Model copied to {remote_path}')


def check_remote():
    print('Checking SSH connection...')
    rc = _ssh('echo SSH OK')
    if rc != 0:
        print('ERROR: SSH connection failed.')
        return
    print('SSH: OK')

    print('Checking Python...')
    out, err, rc = _ssh(f'"{PYTHON_EXE}" --version', capture=True)
    if rc == 0:
        print(f'  Python OK: {out.strip() or err.strip()}')
    else:
        print(f'  WARNING: Python check failed (rc={rc}): {err.strip()[:200]}')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run scripts remotely on the COMSOL Windows machine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('script', nargs='?',
                        help='Path to .py script to run (launches detached by default)')
    parser.add_argument('--block', action='store_true',
                        help='Blocking mode: keep SSH open (use for short test runs)')
    parser.add_argument('--status', action='store_true',
                        help='Check last detached job status and pull results')
    parser.add_argument('--pull', action='store_true',
                        help='Pull results without checking job status')
    parser.add_argument('--copy-model', metavar='MODEL_FILE',
                        help='Copy a large .mph model file to the remote machine')
    parser.add_argument('--check', action='store_true',
                        help='Verify SSH and Python are working')
    args = parser.parse_args()

    if args.check:
        check_remote()
    elif args.copy_model:
        copy_model(args.copy_model)
    elif args.status:
        check_status()
    elif args.pull:
        print('Pulling results...')
        job = json.loads(JOB_FILE.read_text()) if JOB_FILE.exists() else {}
        _pull_results(job.get('sweep_name'), job.get('run_name'))
    elif args.script:
        p = Path(args.script)
        if not p.exists():
            print(f'ERROR: script not found: {p}')
            sys.exit(1)
        if args.block:
            run_blocking(p)
        else:
            launch_detached(p)
    else:
        parser.print_help()
