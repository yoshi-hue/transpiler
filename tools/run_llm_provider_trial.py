"""Run one fixed, auditable LLM translation trial and write a redacted JSON record."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.llm_fallback import fallback_status
from backend.transpiler import transpile
from backend.benchmark import _fallback_failure_summary
from dotenv import load_dotenv

load_dotenv(ROOT / '.env', override=False)


SOURCE = '''IDENTIFICATION DIVISION.
PROGRAM-ID. PROVIDER-TRIAL.
PROCEDURE DIVISION.
PERFORM 3 TIMES
 DISPLAY "STEP"
END-PERFORM.
STOP RUN.'''
EXPECTED_OUTPUT = 'STEP\nSTEP\nSTEP'


def run_trial(target):
    source_hash = hashlib.sha256(SOURCE.encode('utf-8')).hexdigest()
    record = {
        'schema_version': '1',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'trial_id': 'cobol-perform-three-times-v1',
        'source_language': 'COBOL',
        'target_language': target,
        'source_sha256': source_hash,
        'expected_output': EXPECTED_OUTPUT,
        'oracle': 'predeclared fixed-count output expectation; not a native COBOL execution',
        'provider_status_before': fallback_status(),
    }
    if not record['provider_status_before']['configured']:
        record.update({'status': 'not_configured', 'candidate_generated': False,
                       'candidate_accepted': False,
                       'limitation': 'No provider endpoint/model/API key configured; no live request was made.'})
        return record

    result = transpile(SOURCE, 'COBOL', target, enable_llm=True, enable_learned_rules=False)
    suggestion = next((item for item in result.get('fallback_suggestions', []) if item.get('candidate')), None)
    candidate = suggestion.get('candidate') if suggestion else None
    runtime = result.get('target_runtime', {})
    runtime_succeeded = bool(runtime.get('available') and runtime.get('ok'))
    observed = runtime.get('output') if runtime_succeeded else None
    record.update({
        'status': 'completed' if suggestion else 'no_candidate',
        'candidate_generated': bool(candidate),
        'candidate_code': candidate,
        'candidate_sha256': hashlib.sha256(candidate.encode('utf-8')).hexdigest() if candidate else None,
        'request_id': suggestion.get('request_id') if suggestion else None,
        'provider': suggestion.get('provider') if suggestion else record['provider_status_before'].get('provider'),
        'model': suggestion.get('model') if suggestion else record['provider_status_before'].get('model'),
        'prompt_version': suggestion.get('prompt_version') if suggestion else record['provider_status_before'].get('prompt_version'),
        'prompt_hash': suggestion.get('prompt_hash') if suggestion else None,
        'attempts': suggestion.get('attempts') if suggestion else None,
        'latency_ms': suggestion.get('latency_ms') if suggestion else None,
        'syntax_valid': suggestion.get('target_syntax_valid') if suggestion else None,
        'runtime_valid': suggestion.get('target_runtime_valid') if suggestion else None,
        'runtime_validation': {
            'available': runtime.get('available'),
            'ok': runtime.get('ok'),
            'error': runtime.get('error', ''),
            'sandbox': runtime.get('sandbox'),
        },
        'observed_output': observed,
        'independent_oracle_match': observed == EXPECTED_OUTPUT if observed is not None else None,
        'candidate_acceptance': result.get('candidate_acceptance'),
        'candidate_accepted': False,
        'fallback_failures': [_fallback_failure_summary(entry) for entry in result.get('fallback_log', [])
                              if entry.get('action') == 'LLM fallback failed'],
    })
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('JavaScript', 'Python'), default='JavaScript')
    parser.add_argument('--output', default='data/provider_trial_latest.json')
    args = parser.parse_args()
    report = run_trial(args.target)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'candidate_generated': report['candidate_generated'],
                      'candidate_accepted': False, 'output': str(output)}, indent=2))


if __name__ == '__main__':
    main()
