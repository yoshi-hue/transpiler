"""Recheck the fixed Python provider-trial candidate and apply a conservative AST screen."""
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.validator import run_python_isolated


QUEUE = ROOT / 'data' / 'llm_candidate_review_queue_v4.json'
TRIAL = ROOT / 'data' / 'provider_trial_latest_python.json'
OUTPUT = ROOT / 'data' / 'llm_candidate_regression_v4.json'


def main():
    queue = json.loads(QUEUE.read_text(encoding='utf-8'))
    trial = json.loads(TRIAL.read_text(encoding='utf-8'))
    candidate = queue['candidates'][0]
    code = candidate['candidate_code']
    digest = hashlib.sha256(code.encode('utf-8')).hexdigest()
    if digest != candidate['candidate_sha256'] or digest != trial['candidate_sha256']:
        raise SystemExit('Candidate hash does not match its review record/provider trial.')

    allowed = {ast.Module, ast.For, ast.Name, ast.Call, ast.Constant, ast.Expr, ast.Load, ast.Store}
    tree = ast.parse(code, mode='exec')
    disallowed = sorted({type(node).__name__ for node in ast.walk(tree) if type(node) not in allowed})
    names = sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name)})
    calls = sorted({node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)})
    static_screen = not disallowed and set(names) <= {'_', 'range', 'print'} and set(calls) <= {'range', 'print'}

    runtime = run_python_isolated(code, timeout=20)
    expected = trial['expected_output']
    observed = runtime.get('output')
    output_match = bool(runtime.get('available') and runtime.get('ok') and observed == expected.strip())
    record = {
        'schema_version': '1.0',
        'candidate_sha256': digest,
        'source_sha256': candidate['source_sha256'],
        'candidate_trial': candidate['trial_id'],
        'target': 'Python',
        'ast_static_screen': {
            'status': 'passed' if static_screen else 'failed',
            'disallowed_node_types': disallowed,
            'names': names,
            'calls': calls,
            'scope': 'Conservative syntax screen only; not a security approval.'
        },
        'isolated_runtime': runtime,
        'expected_output': expected,
        'observed_output': observed,
        'oracle_match': output_match,
        'regression_gate': 'passed_for_fixed_candidate_fixture' if output_match and static_screen else 'failed',
        'limitations': [
            'One fixed-output fixture only; independent fixture gate remains pending.',
            'Human source, target, and security reviews remain pending.',
            'This report does not accept or integrate the candidate.'
        ],
    }
    OUTPUT.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({
        'output': str(OUTPUT),
        'candidate_sha256': digest,
        'static_screen': record['ast_static_screen']['status'],
        'runtime_ok': runtime.get('ok'),
        'oracle_match': output_match,
        'regression_gate': record['regression_gate'],
    }, indent=2))
    return 0 if record['regression_gate'] == 'passed_for_fixed_candidate_fixture' else 1


if __name__ == '__main__':
    raise SystemExit(main())
