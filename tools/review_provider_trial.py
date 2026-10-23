"""Run bounded fixture, static security, and regression checks for a saved trial."""
import argparse
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.validator import run_python_isolated


def inspect_candidate(code):
    """Conservative static check for this tiny, fixed-output Python candidate."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {'passed': False, 'findings': [f'Syntax error: {exc.msg} at line {exc.lineno}.']}

    disallowed_nodes = (ast.Import, ast.ImportFrom, ast.Attribute, ast.Subscript,
                        ast.Lambda, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                        ast.With, ast.AsyncWith, ast.Try, ast.Raise, ast.Global,
                        ast.Nonlocal, ast.Await, ast.Yield, ast.YieldFrom)
    findings = [f'Disallowed syntax node: {type(node).__name__}.'
                for node in ast.walk(tree) if isinstance(node, disallowed_nodes)]
    calls = [node.func.id for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    other_calls = [node for node in ast.walk(tree)
                   if isinstance(node, ast.Call) and not isinstance(node.func, ast.Name)]
    if other_calls:
        findings.append('Call through a non-name expression is present.')
    if sorted(calls) != ['print', 'range']:
        findings.append(f'Expected only range and print calls; found {calls!r}.')

    expected = ast.parse('for _ in range(3):\n    print("STEP")')
    if ast.dump(tree, include_attributes=False) != ast.dump(expected, include_attributes=False):
        findings.append('Candidate does not match the reviewed fixed-loop/fixed-literal shape.')
    return {
        'passed': not findings,
        'findings': findings or [
            'Candidate contains one fixed range(3) loop and prints only the literal STEP; '
            'no imports, attribute access, filesystem, network, subprocess, environment, '
            'dynamic evaluation, or dependencies were found.'
        ],
    }


def run_regressions():
    basetemp = f".pytest-tmp-review-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"
    command = [sys.executable, '-m', 'pytest', 'tests/test_transpiler.py', '-q',
               f'--basetemp={basetemp}']
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                   timeout=180, check=False)
        return {
            'status': 'passed' if completed.returncode == 0 else 'failed',
            'command': command,
            'exit_code': completed.returncode,
            'stdout_tail': completed.stdout[-4000:],
            'stderr_tail': completed.stderr[-4000:],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'status': 'failed', 'command': command, 'error': str(exc)}


def review(trial_path, fixtures_path):
    trial = json.loads(trial_path.read_text(encoding='utf-8'))
    fixtures = json.loads(fixtures_path.read_text(encoding='utf-8'))
    candidate = trial.get('candidate_code') or ''
    candidate_hash = hashlib.sha256(candidate.encode('utf-8')).hexdigest() if candidate else None
    hash_matches = bool(candidate) and candidate_hash == trial.get('candidate_sha256')

    fixture_results = []
    for fixture in fixtures.get('cases', []):
        execution = run_python_isolated(candidate)
        passed = bool(execution.get('available') and execution.get('ok')
                      and execution.get('output') == fixture.get('expected_output'))
        fixture_results.append({
            'fixture_id': fixture.get('id'),
            'variant': fixture.get('variant'),
            'source_sha256': hashlib.sha256(fixture['source'].encode('utf-8')).hexdigest(),
            'expected_output': fixture.get('expected_output'),
            'observed_output': execution.get('output'),
            'match': passed,
            'runtime_error': execution.get('error', ''),
            'sandbox': execution.get('sandbox'),
        })

    security = inspect_candidate(candidate)
    regression = run_regressions()
    fixtures_passed = bool(fixture_results) and all(item['match'] for item in fixture_results)
    source_compiler = shutil.which('cobc')
    source_review = {
        'status': 'pending',
        'reviewer': None,
        'source_sha256': trial.get('source_sha256'),
        'dialect': 'unspecified',
        'source_format': 'unspecified',
        'native_compiler': source_compiler,
        'evidence': [
            'The visible constructs are a program header, fixed-count PERFORM, DISPLAY of a literal, END-PERFORM, and STOP RUN.',
            'No input statements or external dependencies are present in the supplied text.',
            'The source layout does not declare fixed or free format; native COBOL compilation is unavailable in this environment.',
        ],
    }
    human = {
        'status': 'pending',
        'source_reviewer': None,
        'target_reviewer': None,
        'source_decision': None,
        'target_decision': None,
        'evidence': 'Requires two human reviewers: one knowledgeable in the selected COBOL dialect and one in Python/runtime behavior.',
    }
    requirements = {
        'source_review': source_review,
        'target_toolchain': {
            'status': 'passed' if trial.get('syntax_valid') is True and trial.get('runtime_valid') is True else 'failed',
            'target': trial.get('target_language'),
            'python_version': sys.version.split()[0],
            'syntax_check': trial.get('syntax_valid'),
            'isolated_runtime_check': trial.get('runtime_valid'),
            'sandbox': trial.get('runtime_validation', {}).get('sandbox'),
        },
        'independent_fixtures': {
            'status': 'passed' if fixtures_passed and hash_matches else 'failed' if fixture_results else 'pending',
            'fixture_set_id': fixtures.get('fixture_set_id'),
            'oracle_method': fixtures.get('oracle_method'),
            'source_format_status': fixtures.get('source_format_status'),
            'cases_passed': sum(item['match'] for item in fixture_results),
            'cases_total': len(fixture_results),
            'case_results': fixture_results,
        },
        'security_review': {
            'status': 'passed' if security['passed'] else 'failed',
            'reviewer': 'Codex static AST review',
            'evidence': security['findings'],
        },
        'regression_checks': {
            'status': regression['status'],
            'suite_id': 'tests/test_transpiler.py',
            'result': regression,
        },
        'human_review': human,
    }
    blockers = [name for name, requirement in requirements.items()
                if requirement.get('status') != 'passed']
    accepted = not blockers and hash_matches
    return {
        'schema_version': '1',
        'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
        'trial_id': trial.get('trial_id'),
        'source_sha256': trial.get('source_sha256'),
        'candidate_sha256': candidate_hash,
        'candidate_hash_matches_trial': hash_matches,
        'fixture_manifest': str(fixtures_path.relative_to(ROOT)),
        'candidate_acceptance': {
            'accepted': accepted,
            'status': 'accepted' if accepted else 'unaccepted_candidate',
            'requirements': requirements,
            'blockers': blockers,
            'policy': 'Every review gate must pass; machine checks do not substitute for the two required human reviews.',
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial', default='data/provider_trial_latest_python.json')
    parser.add_argument('--fixtures', default='data/provider_trial_python_fixtures.json')
    parser.add_argument('--output', default='data/provider_trial_python_acceptance_review.json')
    args = parser.parse_args()
    trial_path = (ROOT / args.trial).resolve()
    fixtures_path = (ROOT / args.fixtures).resolve()
    output = (ROOT / args.output).resolve()
    report = review(trial_path, fixtures_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    acceptance = report['candidate_acceptance']
    print(json.dumps({'accepted': acceptance['accepted'], 'blockers': acceptance['blockers'],
                      'output': str(output.relative_to(ROOT))}, indent=2))


if __name__ == '__main__':
    main()
