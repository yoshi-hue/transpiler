"""Run and archive the three-arm held-out ablation.

LLM requests are disabled unless --enable-llm is explicitly passed. The default
report is deterministic for a fixed source tree and target toolchain. Live trials can
explicitly load the repository-local .env without ever writing its values to the report.
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
from backend.llm_fallback import fallback_status


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
parser.add_argument('--load-dotenv', action='store_true', help='Explicitly load repository .env for a live provider run; secrets are never included in output.')
args = parser.parse_args()
if args.load_dotenv:
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env', override=False)
if args.load_dotenv and not args.enable_llm:
    parser.error('--load-dotenv requires --enable-llm')
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
        'dotenv_explicitly_loaded': args.load_dotenv,
        'temperature': 0 if args.enable_llm else None,
    },
    'ablation': report,
        'provider': {
            'configured': report.get('hybrid', {}).get('llm_configured_cases', 0) > 0,
            'provider': next((case.get('provider') for case in report.get('hybrid', {}).get('cases', []) if case.get('provider')), None),
            'model': next((case.get('model') for case in report.get('hybrid', {}).get('cases', []) if case.get('model')), None),
            'prompt_version': next((case.get('prompt_version') for case in report.get('hybrid', {}).get('cases', []) if case.get('prompt_version')), None),
        } if args.enable_llm else {'configured': False},
    'provider_configuration': {
        **{
            key: fallback_status(enabled=True).get(key)
            for key in ('provider', 'model', 'api_mode', 'prompt_version', 'timeout_seconds', 'max_retries', 'enabled_for_request')
        },
        'temperature': 0,
    } if args.enable_llm else None,
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
