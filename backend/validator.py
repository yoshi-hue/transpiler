from decimal import Decimal, InvalidOperation
import ast
import base64
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def _run(command, filename, code, timeout=5, env=None, stdin_data=None):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / filename
        path.write_text(code, encoding='utf-8')
        try:
            p = subprocess.run(command + [str(path)], capture_output=True, text=True, timeout=timeout, env=env, input=stdin_data)
        except FileNotFoundError:
            return {'available': False, 'ok': None, 'output': '', 'error': f'{command[0]} is not installed.'}
        except subprocess.TimeoutExpired:
            return {'available': True, 'ok': False, 'output': '', 'error': 'Target execution timed out.'}
        return {'available': True, 'ok': p.returncode == 0, 'output': p.stdout.strip(), 'error': p.stderr.strip()}


def run_javascript(code, *, restricted=False, stdin_data=None):
    command = ['node']
    env = None
    if restricted:
        command.extend(['--permission', '--max-old-space-size=128'])
        env = {
            key: os.environ[key]
            for key in ('PATH', 'SystemRoot', 'WINDIR', 'TEMP', 'TMP')
            if os.environ.get(key)
        }
    return _run(command, 'translated.js', code, env=env, stdin_data=stdin_data)


def run_python(code, *, stdin_data=None):
    return _run(['python'], 'translated.py', code, stdin_data=stdin_data)


def run_python_isolated(code, *, timeout=5):
    """Run generated Python in a networkless, read-only Docker container.

    No host paths are mounted. The candidate is passed as base64 in a container-only
    environment variable so the Docker CLI does not need to keep an interactive stdin
    pipe open on Windows. If Docker is unavailable, execution fails closed rather than
    running candidate code on the host.
    """
    docker = shutil.which('docker')
    if not docker:
        return {'available': False, 'ok': None, 'output': '',
                'error': 'Docker is required for isolated Python candidate execution.'}
    image = os.getenv('PYTHON_SANDBOX_IMAGE', 'python:3.13-slim')
    candidate_b64 = base64.b64encode(code.encode('utf-8')).decode('ascii')
    # Windows limits process command lines to 32,767 characters. Keep ample room
    # for the Docker flags and command while bounding candidate payload size.
    if len(candidate_b64) > 24000:
        return {'available': True, 'ok': False, 'output': '',
                'error': 'Candidate is too large for isolated execution (24,000-byte encoded limit).'}
    command = [
        docker, 'run', '--rm', '--network', 'none', '--read-only',
        '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m', '--memory', '128m',
        '--cpus', '0.5', '--pids-limit', '32', '--user', '65534:65534',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--env', 'PYTHONDONTWRITEBYTECODE=1',
        '--env', f'CANDIDATE_B64={candidate_b64}', image, 'python', '-I', '-u', '-c',
        'import base64, os; exec(compile(base64.b64decode(os.environ["CANDIDATE_B64"]), "<candidate>", "exec"))',
    ]
    try:
        process = subprocess.run(command, capture_output=True, text=True,
                                 timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        # Keep Docker's partial output: it distinguishes an image/startup failure
        # from a candidate that ran but did not exit before the deadline.
        stdout = exc.stdout or ''
        stderr = exc.stderr or ''
        if isinstance(stdout, bytes):
            stdout = stdout.decode('utf-8', errors='replace')
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', errors='replace')
        details = '\n'.join(part.strip() for part in (stderr, stdout) if part.strip())
        error = 'Isolated Python candidate timed out.'
        if details:
            error = f'{error} Partial Docker output: {details}'
        return {'available': True, 'ok': False, 'output': stdout.strip(),
                'error': error}
    except OSError as exc:
        return {'available': False, 'ok': None, 'output': '',
                'error': f'Could not start Docker: {exc}'}
    return {
        'available': True,
        'ok': process.returncode == 0,
        'output': process.stdout.strip(),
        'error': process.stderr.strip(),
        'sandbox': {
            'image': image, 'network': 'none', 'filesystem': 'read-only',
            'memory_limit': '128m', 'cpu_limit': '0.5', 'pids_limit': 32,
            'host_mounts': [],
        },
    }


def check_python_syntax(code):
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return {'available': True, 'ok': False, 'error': f'{exc.msg} at line {exc.lineno}.'}
    return {'available': True, 'ok': True, 'error': ''}


def check_javascript_syntax(code):
    return _run(['node', '--check'], 'translated.js', code)


def _outputs_equivalent(source_output, target_output):
    if source_output == target_output:
        return True
    source_lines = source_output.splitlines()
    target_lines = target_output.splitlines()
    if len(source_lines) != len(target_lines):
        return False
    for source_line, target_line in zip(source_lines, target_lines):
        if source_line == target_line:
            continue
        if source_line.lower() in ('true', 'false') and source_line.lower() == target_line.lower():
            continue
        try:
            source_number = Decimal(source_line)
            target_number = Decimal(target_line)
        except InvalidOperation:
            return False
        if not source_number.is_finite() or not target_number.is_finite() or source_number != target_number:
            return False
    return True


def compare(source_output, target, target_language='JavaScript'):
    if not target['available']:
        runtime = 'Node.js' if target_language == 'JavaScript' else 'Python'
        return {
            'status': 'not_run', 'message': f'Install {runtime} to run the target-side equivalence check.',
            'source_output': source_output, 'target_output': None, 'target_runtime': runtime,
            'failure_class': 'runtime_unavailable'
        }
    same = target['ok'] and _outputs_equivalent(source_output, target['output'])
    if not target['ok']:
        failure = 'target_runtime_error'
        message = 'Generated target program failed during execution.'
    elif same:
        failure = None
        message = 'Finite input/output comparison passed for this run.'
    else:
        failure = 'output_mismatch'
        message = 'Source and target outputs differ.'
    return {
        'status': 'passed' if same else 'failed', 'message': message,
        'source_output': source_output, 'target_output': target['output'],
        'error': target['error'], 'target_runtime': target_language,
        'failure_class': failure
    }
