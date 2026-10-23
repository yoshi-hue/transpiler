"""Run and archive the three-arm held-out ablation without implicit dotenv loading.

LLM requests are disabled unless --enable-llm is explicitly passed. The default
report is deterministic for a fixed source tree and target toolchain.
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.benchmark import run_experiment


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _implementation_sha256():
    digest = hashlib.sha256()
    paths = sorted((ROOT / 'backend').glob('*.py'))
    paths.extend([Path(__file__), ROOT / 'data' / 'external_task_cases.jsonl'])
    for path in sorted(set(paths)):
        digest.update(path.relative_to(ROOT).as_posix().encode('utf-8'))
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


def _version(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--target', required=True, choices=['JavaScript', 'Python'])
parser.add_argument('--output', required=True)
parser.add_argument('--repeats', type=int, default=1)
parser.add_argument('--enable-llm', action='store_true', help='Allow live provider requests using process environment variables.')
args = parser.parse_args()
if not 1 <= args.repeats <= 10:
    parser.error('--repeats must be between 1 and 10')

report = run_experiment(
    target=args.target,
    repeats=args.repeats,
    enable_llm=args.enable_llm,
)
record = {
    'schema_version': '1.0',
    'runner': 'tools/run_ablation.py',
    'runtime': {
        'python': platform.python_version(),
        'node': _version(['node', '--version']),
    },
    'inputs': {
        'task_cases_sha256': _sha256(ROOT / 'data' / 'external_task_cases.jsonl'),
        'supported_subset_sha256': _sha256(ROOT / 'data' / 'supported_subset.json'),
        'implementation_sha256': _implementation_sha256(),
    },
    'settings': {
        'target': args.target,
        'repeats': args.repeats,
        'llm_enabled': args.enable_llm,
        'split': 'test',
        'dotenv_autoload': False,
    },
    'ablation': report,
}
output = Path(args.output)
if not output.is_absolute():
    output = ROOT / output
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({
    'output': str(output),
    'target': args.target,
    'repeats': args.repeats,
    'llm_enabled': args.enable_llm,
    'rule_only_passes': report['rule_only']['passed'],
    'hybrid_passes': report['hybrid']['passed'],
    'safeguards_passes': report['contracts_risk_learned_rules']['passed'],
    'learned_rule_reuses': report['contracts_risk_learned_rules']['learned_rule_reuses'],
}, indent=2))
