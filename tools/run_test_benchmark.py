"""Run the deterministic held-out test split and archive case-level provenance."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.benchmark import run_benchmark


def _version(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _implementation_sha256():
    digest = hashlib.sha256()
    for path in sorted((ROOT / 'backend').glob('*.py')):
        digest.update(path.relative_to(ROOT).as_posix().encode('utf-8'))
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--target', required=True, choices=['JavaScript', 'Python'])
parser.add_argument('--output', required=True)
args = parser.parse_args()

record = {
    'schema_version': '2.0',
    'runner': 'tools/run_test_benchmark.py',
    'runtime': {
        'python': sys.version.split()[0],
        'node': _version(['node', '--version']),
    },
    'target': args.target,
    'inputs': {
        'task_cases_sha256': _sha256(ROOT / 'data' / 'external_task_cases.jsonl'),
        'supported_subset_sha256': _sha256(ROOT / 'data' / 'supported_subset.json'),
        'backend_implementation_sha256': _implementation_sha256(),
        'runner_sha256': _sha256(__file__),
    },
    'settings': {'llm_enabled': False, 'learned_rules_enabled': False, 'split': 'test'},
    'benchmark': run_benchmark(args.target),
}
output = Path(args.output)
if not output.is_absolute():
    output = ROOT / output
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({
    'output': str(output),
    'target': args.target,
    'cases': record['benchmark']['total'],
    'passed': record['benchmark']['passed'],
    'unsupported_recognized': record['benchmark']['unsupported_cases_recognized'],
    'gold_matches': record['benchmark']['gold_output_matches'],
}, indent=2))
