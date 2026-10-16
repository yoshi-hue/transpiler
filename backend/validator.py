from decimal import Decimal, InvalidOperation
import subprocess
import tempfile
from pathlib import Path


def _run(command, filename, code, timeout=5):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / filename
        path.write_text(code, encoding='utf-8')
        try:
            p = subprocess.run(command + [str(path)], capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            return {'available': False, 'ok': None, 'output': '', 'error': f'{command[0]} is not installed.'}
        except subprocess.TimeoutExpired:
            return {'available': True, 'ok': False, 'output': '', 'error': 'Target execution timed out.'}
        return {'available': True, 'ok': p.returncode == 0, 'output': p.stdout.strip(), 'error': p.stderr.strip()}


def run_javascript(code):
    return _run(['node'], 'translated.js', code)


def run_python(code):
    return _run(['python'], 'translated.py', code)


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
        message = 'Input/output equivalence check passed.'
    else:
        failure = 'output_mismatch'
        message = 'Source and target outputs differ.'
    return {
        'status': 'passed' if same else 'failed', 'message': message,
        'source_output': source_output, 'target_output': target['output'],
        'error': target['error'], 'target_runtime': target_language,
        'failure_class': failure
    }
