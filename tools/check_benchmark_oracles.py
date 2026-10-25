"""Check fixed expected outputs with a small evaluator separate from the transpiler.

This is not a native compiler or a human review. It independently extracts the
benchmark's deliberately small arithmetic/loop inputs and applies their stated
mathematical semantics; unsupported COBOL PERFORM examples use count-by-repetition.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = ROOT / 'data' / 'external_task_cases.jsonl'
TEST_TASKS = {
    'Maximum of two numbers', 'Loops/For', 'Kyu in AtCoder',
    'AIsing Programming Contest 2020 - A: Number of Multiples',
    'AIsing Programming Contest 2020 - B: An Odd Problem',
    'Trapezoids', 'Golden Coins', 'Programming Education',
}


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
    if task == 'Kyu in AtCoder':
        rating = int(case['input_fixtures'][0]['stdin'].strip())
        return str(8 - ((rating - 400) // 200))
    if task == 'AIsing Programming Contest 2020 - A: Number of Multiples':
        l, r, divisor = map(int, case['input_fixtures'][0]['stdin'].split())
        return str(r // divisor - (l - 1) // divisor)
    if task == 'Trapezoids':
        a, b, h = map(int, case['input_fixtures'][0]['stdin'].split())
        return str((a + b) * h // 2)
    if task == 'Golden Coins':
        x = int(case['input_fixtures'][0]['stdin'])
        return str((x // 500) * 1000 + ((x % 500) // 5) * 5)
    if task == 'Programming Education':
        values = [int(token) for token in case['input_fixtures'][0]['stdin'].split()]
        return 'Hello World' if values == [1] else str(values[1] + values[2])
    if task.endswith('An Odd Problem'):
        return None
    if task == 'Maximum of two numbers':
        return str(max(_assigned_integer(source, language, 'A'),
                       _assigned_integer(source, language, 'B')))
    if task == 'Loops/For':
        if language == 'COBOL':
            count = re.search(r'\bPERFORM\s+(\d+)\s+TIMES\b', source, re.IGNORECASE)
            literal = re.search(r'\bDISPLAY\s+["\']([^"\']*)["\']', source, re.IGNORECASE)
            if not count or not literal:
                raise ValueError('Could not independently read COBOL PERFORM fixture.')
            return '\n'.join([literal.group(1)] * int(count.group(1)))
        if language == 'FORTRAN':
            match = re.search(r'\bDO\s+\w+\s*=\s*(-?\d+)\s*,\s*(-?\d+)', source, re.IGNORECASE)
        elif language == 'Pascal':
            match = re.search(r'\bFOR\s+\w+\s*:=\s*(-?\d+)\s+TO\s+(-?\d+)', source, re.IGNORECASE)
        elif language == 'BASIC':
            match = re.search(r'\bFOR\s+\w+\s*=\s*(-?\d+)\s+TO\s+(-?\d+)', source, re.IGNORECASE)
        else:
            raise ValueError(f'Unsupported language in loop reference evaluator: {language!r}.')
        if not match:
            raise ValueError(f'Could not independently read {language} loop bounds.')
        start, stop = map(int, match.groups())
        return '\n'.join(str(value) for value in range(start, stop + 1))
    raise ValueError(f'No separate reference evaluator for task {task!r}.')


def _fixture_reference(task, stdin):
    values = [int(token) for token in stdin.split()]
    if task == 'Kyu in AtCoder':
        if len(values) != 1 or not 400 <= values[0] <= 1999:
            raise ValueError('Kyu in AtCoder fixture must contain one in-range rating.')
        return str(8 - ((values[0] - 400) // 200))
    if task == 'AIsing Programming Contest 2020 - A: Number of Multiples':
        if len(values) != 3 or values[2] <= 0 or values[0] > values[1]:
            raise ValueError('Number of Multiples fixture must contain valid L, R, d values.')
        return str(values[1] // values[2] - (values[0] - 1) // values[2])
    if task == 'Trapezoids':
        if len(values) != 3 or min(values) < 1:
            raise ValueError('Trapezoids fixture must contain three positive integers.')
        return str((values[0] + values[1]) * values[2] // 2)
    if task == 'Golden Coins':
        if len(values) != 1 or not 0 <= values[0] <= 1_000_000_000:
            raise ValueError('Golden Coins fixture must contain one in-range amount.')
        x = values[0]
        return str((x // 500) * 1000 + ((x % 500) // 5) * 5)
    if task == 'Programming Education':
        if not values or values[0] not in (1, 2):
            raise ValueError('Programming Education fixture must start with N=1 or N=2.')
        if values[0] == 1 and len(values) == 1:
            return 'Hello World'
        if values[0] == 2 and len(values) == 3:
            return str(values[1] + values[2])
        raise ValueError('Programming Education fixture does not match N=1/N=2 input shape.')
    if task.endswith('An Odd Problem'):
        if not values or len(values) != values[0] + 1:
            raise ValueError('An Odd Problem fixture must contain N followed by N integers.')
        return str(sum(value % 2 for index, value in enumerate(values[1:], 1) if index % 2 == 1))
    return None

parser = argparse.ArgumentParser()
parser.add_argument('--output', default='data/oracle_current_check.json')
args = parser.parse_args()

cases = [json.loads(line) for line in CASES_PATH.read_text(encoding='utf-8').splitlines() if line.strip()]
cases = [
    case for case in cases
    if case.get('split', 'test' if case['provenance']['task'] in {'Maximum of two numbers', 'Loops/For'} else 'development') == 'test'
    and case['provenance']['task'] in TEST_TASKS
]
case_output_cases = [case for case in cases if case.get('expected_output') is not None]
results = []
for case in case_output_cases:
    derived = _reference_output(case)
    normalize = lambda value: str(value).replace('\r\n', '\n').strip()
    match = None if derived is None else normalize(derived) == normalize(case.get('expected_output'))
    results.append({
        'case': case['id'],
        'task_group': case['provenance']['task'],
        'language': case['language'],
        'expected_output': case.get('expected_output'),
        'reference_output': derived,
        'match': match,
    })

fixture_results = []
for case in cases:
    for fixture in case.get('input_fixtures', []):
        derived = _fixture_reference(case['provenance']['task'], fixture['stdin'])
        normalize = lambda value: str(value).replace('\r\n', '\n').strip()
        fixture_results.append({
            'case': case['id'],
            'task_group': case['provenance']['task'],
            'fixture_id': fixture['fixture_id'],
            'oracle_status': fixture.get('oracle_status'),
            'expected_output': fixture['expected_output'],
            'reference_output': derived,
            'match': derived is not None and normalize(derived) == normalize(fixture['expected_output']),
        })

record = {
    'schema_version': '2.0',
    'method': 'separate regex input extraction plus direct max/range/repetition calculation; no transpiler or source interpreter imports',
    'limitation': 'Not an independently executed native compiler and not an independent human review.',
    'benchmark_sha256': hashlib.sha256(CASES_PATH.read_bytes()).hexdigest(),
    'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'cases': len(results),
    'case_output_matches': sum(row['match'] is True for row in results),
    'fixture_count': len(fixture_results),
    'fixture_matches': sum(row['match'] for row in fixture_results),
    'matches': sum(row['match'] is True for row in results),
    'results': results,
    'fixture_results': fixture_results,
}
output = Path(args.output)
if not output.is_absolute():
    output = ROOT / output
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({'output': str(output), 'cases': record['cases'], 'matches': record['matches'], 'fixtures': record['fixture_count'], 'fixture_matches': record['fixture_matches']}, indent=2))
if record['matches'] != record['cases'] or record['fixture_matches'] != record['fixture_count']:
    raise SystemExit(1)
