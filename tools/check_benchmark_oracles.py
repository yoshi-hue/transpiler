"""Check fixed expected outputs with a small evaluator separate from the transpiler.

This is not a native compiler or a human review. It independently extracts the
benchmark's deliberately small arithmetic/loop inputs and applies their stated
mathematical semantics; unsupported COBOL PERFORM examples use count-by-repetition.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / 'data' / 'external_task_cases.jsonl'
TEST_TASKS = {'Maximum of two numbers', 'Loops/For'}


def _assigned_integer(source, language, name):
    patterns = {
        'COBOL': rf'\b01\s+{name}\s+PIC\s+\S+\s+VALUE\s+(-?\d+)\b',
        'FORTRAN': rf'\b{name}\s*=\s*(-?\d+)\b',
        'Pascal': rf'\b{name}\s*:=\s*(-?\d+)\b',
        'BASIC': rf'\b(?:LET\s+)?{name}\s*=\s*(-?\d+)\b',
    }
    match = re.search(patterns[language], source, re.IGNORECASE)
    if not match:
        raise ValueError(f'Could not independently read {name} from {language} source.')
    return int(match.group(1))


def _reference_output(case):
    source = case['source']
    language = case['language']
    task = case['provenance']['task']
    if task == 'Maximum of two numbers':
        return str(max(_assigned_integer(source, language, 'A'),
                       _assigned_integer(source, language, 'B')))
    if task != 'Loops/For':
        raise ValueError(f'No separate reference evaluator for task {task!r}.')

    if language == 'COBOL':
        count = re.search(r'\bPERFORM\s+(\d+)\s+TIMES\b', source, re.IGNORECASE)
        literal = re.search(r'\bDISPLAY\s+["\']([^"\']*)["\']', source, re.IGNORECASE)
        if not count or not literal:
            raise ValueError('Could not independently read COBOL PERFORM fixture.')
        return '\n'.join([literal.group(1)] * int(count.group(1)))

    if language == 'FORTRAN':
        match = re.search(r'\bDO\s+\w+\s*=\s*(-?\d+)\s*,\s*(-?\d+)', source, re.IGNORECASE)
        if not match:
            raise ValueError('Could not independently read FORTRAN DO range.')
        start, stop = map(int, match.groups())
    elif language == 'Pascal':
        match = re.search(r'\bFOR\s+\w+\s*:=\s*(-?\d+)\s+TO\s+(-?\d+)', source, re.IGNORECASE)
        if not match:
            raise ValueError('Could not independently read Pascal FOR range.')
        start, stop = map(int, match.groups())
    elif language == 'BASIC':
        match = re.search(r'\bFOR\s+\w+\s*=\s*(-?\d+)\s+TO\s+(-?\d+)', source, re.IGNORECASE)
        if not match:
            raise ValueError('Could not independently read BASIC FOR range.')
        start, stop = map(int, match.groups())
    else:
        raise ValueError(f'Unsupported language in reference evaluator: {language!r}.')
    return '\n'.join(str(value) for value in range(start, stop + 1))


parser = argparse.ArgumentParser()
parser.add_argument('--output', default='data/oracle_v2_check.json')
args = parser.parse_args()

cases = [json.loads(line) for line in CASES_PATH.read_text(encoding='utf-8').splitlines() if line.strip()]
cases = [case for case in cases if case['provenance']['task'] in TEST_TASKS]
results = []
for case in cases:
    derived = _reference_output(case)
    normalize = lambda value: str(value).replace('\r\n', '\n').strip()
    results.append({
        'case': case['id'],
        'task_group': case['provenance']['task'],
        'language': case['language'],
        'expected_output': case.get('expected_output'),
        'reference_output': derived,
        'match': normalize(derived) == normalize(case.get('expected_output')),
    })

record = {
    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    'method': 'separate regex input extraction plus direct max/range/repetition calculation; no transpiler or source interpreter imports',
    'limitation': 'Not an independently executed native compiler and not an independent human review.',
    'benchmark_sha256': hashlib.sha256(CASES_PATH.read_bytes()).hexdigest(),
    'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'cases': len(results),
    'matches': sum(row['match'] for row in results),
    'results': results,
}
output = Path(args.output)
if not output.is_absolute():
    output = ROOT / output
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({'output': str(output), 'cases': record['cases'], 'matches': record['matches']}, indent=2))
if record['matches'] != record['cases']:
    raise SystemExit(1)
