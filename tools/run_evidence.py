"""Run an offline deterministic evaluation and write a new immutable evidence file."""
import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.benchmark import run_benchmark
from backend.evidence import write_evidence


def version(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--target', choices=['JavaScript', 'Python'], required=True)
parser.add_argument('--output-dir', default='data/evidence')
args = parser.parse_args()
outcomes = run_benchmark(args.target)
path, record = write_evidence(
    output_dir=ROOT / args.output_dir,
    command=' '.join(sys.argv),
    settings={'target': args.target, 'llm_enabled': False, 'learned_rules_enabled': False,
              'split': 'test'},
    outcomes=outcomes,
    files=[ROOT / 'data' / 'external_task_cases.jsonl', ROOT / 'data' / 'supported_subset.json'],
    runtime={'python': platform.python_version(), 'node': version(['node', '--version'])},
)
print(json.dumps({'path': str(path), 'run_id': record['run_id'],
                  'total': outcomes.get('total'), 'passed': outcomes.get('passed')}, indent=2))
