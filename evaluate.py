"""Reproducible benchmark runner for the legacy modernizer."""
import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')

from backend.benchmark import run_benchmark, run_experiment
from backend.llm_fallback import fallback_status
from backend.rules import RULE_TABLE_VERSION

parser = argparse.ArgumentParser()
parser.add_argument('--target', default='JavaScript', choices=['JavaScript', 'Python'])
parser.add_argument('--output', default='evaluation_result.json')
args = parser.parse_args()

benchmark = run_benchmark(args.target)
experiment = run_experiment(args.target)
record = {
    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    'python_version': sys.version,
    'platform': platform.platform(),
    'target': args.target,
    'rule_table_version': RULE_TABLE_VERSION,
    'llm_configuration': fallback_status(),
    'benchmark': benchmark,
    'experiment': experiment,
}
with open(args.output, 'w', encoding='utf-8') as f:
    json.dump(record, f, indent=2)
print(json.dumps(record, indent=2))
print(f'\nSaved: {args.output}')
