"""Run the deterministic held-out test split and archive case-level provenance."""
import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
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


parser = argparse.ArgumentParser()
parser.add_argument('--target', required=True, choices=['JavaScript', 'Python'])
parser.add_argument('--output', required=True)
args = parser.parse_args()

record = {
    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    'command': f'python tools/run_test_benchmark.py --target {args.target} --output {args.output}',
    'python_version': sys.version,
    'platform': platform.platform(),
    'node_version': _version(['node', '--version']),
    'target': args.target,
    'git_commit': _version(['git', 'rev-parse', 'HEAD']),
    'worktree_modified': bool(_version(['git', 'status', '--porcelain'])),
    'llm_enabled': False,
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
