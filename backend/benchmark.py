"""Inspectable local and task-derived benchmark cases.
Every case has an explicit source snippet and expected pipeline outcome rather than a
hidden score; task-derived examples retain provenance and adaptation notes.

This module also supports a controlled rule-only vs hybrid evaluation with
per-language and per-construct breakdowns, fallback frequency, latency, and
validation-failure tracking for research reporting.
"""
import json
import statistics
from pathlib import Path

from .transpiler import transpile

CASES = [
    ('COBOL', 'arithmetic', '''IDENTIFICATION DIVISION.\nPROGRAM-ID. B1.\nDATA DIVISION.\nWORKING-STORAGE SECTION.\n01 A PIC 999 VALUE 7.\n01 B PIC 999 VALUE 5.\nPROCEDURE DIVISION.\nCOMPUTE SUM = A + B.\nDISPLAY SUM.\nSTOP RUN.'''),
    ('COBOL', 'conditional', '''IDENTIFICATION DIVISION.\nPROGRAM-ID. B2.\nDATA DIVISION.\nWORKING-STORAGE SECTION.\n01 A PIC 999 VALUE 7.\nPROCEDURE DIVISION.\nIF A > 5\n DISPLAY "HIGH"\nELSE\n DISPLAY "LOW"\nEND-IF.\nSTOP RUN.'''),
    ('COBOL', 'comparison', '''IDENTIFICATION DIVISION.\nPROGRAM-ID. B2B.\nDATA DIVISION.\nWORKING-STORAGE SECTION.\n01 A PIC 999 VALUE 9.\nPROCEDURE DIVISION.\nIF A = 9\n DISPLAY "OK"\nELSE\n DISPLAY "BAD"\nEND-IF.\nSTOP RUN.'''),
    ('FORTRAN', 'loop', '''PROGRAM B3\nINTEGER :: I\nDO I = 1, 3\nPRINT *, I\nEND DO\nEND PROGRAM B3'''),
    ('FORTRAN', 'conditional', '''PROGRAM B4\nINTEGER :: A\nA = 4\nIF (A < 5) THEN\nPRINT *, "LOW"\nELSE\nPRINT *, "HIGH"\nEND IF\nEND PROGRAM B4'''),
    ('FORTRAN', 'comparison', '''PROGRAM B4B\nINTEGER :: A\nA = 10\nIF (A >= 10) THEN\nPRINT *, "OK"\nEND IF\nEND PROGRAM B4B'''),
    ('Pascal', 'arithmetic', '''program b5;\nvar a, b, s: integer;\nbegin\na := 4; b := 6; s := a + b; writeln(s);\nend.'''),
    ('Pascal', 'loop', '''program b6;\nvar i: integer;\nbegin\nfor i := 1 to 3 do writeln(i);\nend.'''),
    ('Pascal', 'conditional', '''program b7;\nvar a: integer;\nbegin\na := 0;\nif a = 0 then writeln("ok") else writeln("bad");\nend.'''),
    ('BASIC', 'arithmetic', '''10 LET A = 4\n20 LET B = 6\n30 PRINT A + B\n40 END'''),
    ('BASIC', 'loop', '''10 FOR I = 1 TO 3\n20 PRINT I\n30 NEXT I\n40 END'''),
    ('BASIC', 'comparison', '''10 LET A = 8\n20 LET B = 2\n30 IF A <> B THEN PRINT "NE"\n40 IF A <= B THEN PRINT "LE"\n50 IF A >= B THEN PRINT "GE"\n60 END'''),
]

EXTERNAL_DATASET_ID = 'rosettacode-task-adaptations-v1'
EXTERNAL_CASES = []
_EXTERNAL_CASE_METADATA = {}
_external_cases_path = Path(__file__).resolve().parent.parent / 'data' / 'external_task_cases.jsonl'
with _external_cases_path.open(encoding='utf-8') as _dataset_file:
    for _line_number, _line in enumerate(_dataset_file, 1):
        if not _line.strip():
            continue
        _case = json.loads(_line)
        for _field in ('id', 'language', 'construct', 'source', 'required_constructs', 'provenance'):
            if _field not in _case:
                raise ValueError(f'Invalid external benchmark record on line {_line_number}: missing {_field}.')
        if _case.get('expected_outcome', 'translated') == 'translated' and 'expected_output' not in _case:
            raise ValueError(f'Invalid external benchmark record on line {_line_number}: missing expected_output.')
        _case_key = (_case['language'], _case['id'])
        if _case_key in _EXTERNAL_CASE_METADATA:
            raise ValueError(f'Duplicate external benchmark case id on line {_line_number}: {_case["id"]}.')
        _EXTERNAL_CASE_METADATA[_case_key] = _case
        EXTERNAL_CASES.append((_case['language'], _case['id'], _case['source']))

DEFAULT_CASES = CASES + EXTERNAL_CASES

LOCAL_EXPECTED_OUTPUTS = {
    ('COBOL', 'arithmetic'): '12',
    ('COBOL', 'conditional'): 'HIGH',
    ('COBOL', 'comparison'): 'OK',
    ('FORTRAN', 'loop'): '1\n2\n3',
    ('FORTRAN', 'conditional'): 'LOW',
    ('FORTRAN', 'comparison'): 'OK',
    ('Pascal', 'arithmetic'): '10',
    ('Pascal', 'loop'): '1\n2\n3',
    ('Pascal', 'conditional'): 'ok',
    ('BASIC', 'arithmetic'): '10',
    ('BASIC', 'loop'): '1\n2\n3',
    ('BASIC', 'comparison'): 'NE\nGE',
}
_LOCAL_CASE_SOURCES = {(language, name): source for language, name, source in CASES}

def _case_metadata(language, case_name, source=None):
    external = _EXTERNAL_CASE_METADATA.get((language, case_name))
    if external is not None:
        if source is not None and external['source'] != source:
            return {}
        return external
    expected_output = LOCAL_EXPECTED_OUTPUTS.get((language, case_name))
    if source is not None and _LOCAL_CASE_SOURCES.get((language, case_name)) != source:
        return {}
    return {'expected_output': expected_output} if expected_output is not None else {}


def _oracle_match(actual_output, expected_output):
    if expected_output is None or actual_output is None:
        return None
    normalize = lambda value: str(value).replace('\r\n', '\n').strip()
    return normalize(actual_output) == normalize(expected_output)


def _wilson_interval(successes, total, z=1.96):
    if total == 0:
        return None
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = z * ((proportion * (1 - proportion) / total + z * z / (4 * total * total)) ** 0.5) / denominator
    return [round(max(0.0, center - margin) * 100, 1), round(min(1.0, center + margin) * 100, 1)]


def _rule_categories(rules_used):
    categories = set()
    for rule in rules_used:
        prefix = rule.split('→', 1)[0].strip().lower()
        if prefix in ('assignment', 'output', 'conditional', 'loop'):
            categories.add(prefix)
        elif prefix == 'arithmetic':
            categories.add('arithmetic')
        elif prefix == 'comparison':
            categories.add('comparison')
        elif prefix == 'arithmetic/comparison expression':
            categories.add('arithmetic')
            categories.add('comparison')
        elif prefix == 'comparison expression':
            categories.add('comparison')
    return categories


def _required_construct_coverage(language, case_name, rules_used, source=None):
    metadata = _case_metadata(language, case_name, source)
    required = metadata.get('required_constructs', [])
    covered = sorted(set(required) & _rule_categories(rules_used))
    return {
        'required': required,
        'covered': covered,
        'total': len(required),
        'covered_count': len(covered),
        'coverage_percent': round((len(covered) / len(required)) * 100.0, 1) if required else None,
    }


def _case_result(language, case_name, source, target, *, enable_llm):
    metadata = _case_metadata(language, case_name, source)
    try:
        result = transpile(source, language, target, enable_llm=enable_llm)
    except Exception as exc:
        return {
            'language': language,
            'case': case_name,
            'status': 'error',
            'failure_class': 'pipeline_error',
            'error': str(exc),
            'unsupported': 0,
            'unsupported_constructs': [],
            'llm_calls': 0,
            'llm_latency_ms': [],
            'llm_cost_usd': None,
            'validation_failures': 1,
            'source_reference': metadata.get('provenance'),
            'required_construct_coverage': _required_construct_coverage(language, case_name, [], source),
            'candidate_generated': 0,
            'accepted_llm_candidates': 0,
            'llm_configured': False,
            'gold_output_match': None,
        }
    validation = result.get('validation', {})
    logs = result.get('fallback_log', [])
    llm_calls = sum(
        1 for entry in logs
        if entry.get('action') in ('LLM produced a complete-program candidate; validation required', 'LLM fallback failed')
    )
    llm_latencies = []
    llm_attempts = 0
    for entry in logs:
        if isinstance(entry.get('latency_ms'), (int, float)):
            llm_latencies.append(float(entry['latency_ms']))
        if isinstance(entry.get('attempts'), int):
            llm_attempts += entry['attempts']
    rules_used = result.get('rules_used', [])
    suggestions = result.get('fallback_suggestions', [])
    target_runtime = result.get('target_runtime', {})
    gold_output_match = None
    if (
        not result.get('unsupported')
        and target_runtime.get('available')
        and target_runtime.get('ok')
    ):
        gold_output_match = _oracle_match(target_runtime.get('output'), metadata.get('expected_output'))
    candidate_oracle_match = None
    if (
        suggestions
        and metadata.get('expected_output') is not None
        and target == 'JavaScript'
        and target_runtime.get('available')
    ):
        candidate_oracle_match = bool(
            target_runtime.get('ok')
            and _oracle_match(target_runtime.get('output'), metadata['expected_output'])
        )

    return {
        'language': language,
        'case': case_name,
        'status': validation.get('status', 'not_run'),
        'failure_class': validation.get('failure_class'),
        'unsupported': len(result.get('unsupported', [])),
        'unsupported_constructs': result.get('unsupported', []),
        'source_construct_coverage_percent': result.get('rule_coverage', {}).get('coverage_percent'),
        'required_construct_coverage': _required_construct_coverage(language, case_name, rules_used, source),
        'llm_configured': result.get('fallback_status', {}).get('configured', False),
        'generated_lines': result.get('generated_lines', 0),
        'llm_calls': llm_calls,
        'llm_attempts': llm_attempts,
        'llm_latency_ms': llm_latencies,
        'llm_cost_usd': None,
        'candidate_generated': sum(suggestion.get('candidate_status') == 'candidate_generated' for suggestion in suggestions),
        'candidate_syntax_valid': sum(bool(suggestion.get('target_syntax_valid')) for suggestion in suggestions),
        'candidate_runtime_valid': sum(bool(suggestion.get('target_runtime_valid')) for suggestion in suggestions),
        'candidate_runtime_checked': sum(suggestion.get('target_runtime_valid') is not None for suggestion in suggestions),
        'candidate_runtime_not_run': sum(suggestion.get('target_runtime_valid') is None for suggestion in suggestions),
        'candidate_oracle_match': candidate_oracle_match,
        'accepted_llm_candidates': 0,
        'source_reference': metadata.get('provenance'),
        'expected_outcome': metadata.get('expected_outcome', 'translated'),
        'gold_output_match': gold_output_match,
        'outcome_correct': (
            validation.get('status') == 'passed'
            if metadata.get('expected_outcome', 'translated') == 'translated'
            else bool(result.get('unsupported')) and validation.get('status') == 'not_run'
        ),
        'validation_failures': 1 if validation.get('status') in ('failed', 'not_run', 'error') else 0,
    }


def _summarize_variant(results, variant_name):
    total = len(results)
    passed = sum(1 for item in results if item.get('status') == 'passed')
    failed = total - passed
    llm_calls = sum(item.get('llm_calls', 0) for item in results)
    llm_attempts = sum(item.get('llm_attempts', 0) for item in results)
    llm_latencies = [value for item in results for value in item.get('llm_latency_ms', [])]
    fallback_frequency = round((llm_calls / total) * 100.0, 1) if total else 0.0
    validation_failures = sum(item.get('validation_failures', 0) for item in results)
    unsupported = sum(item.get('unsupported', 0) for item in results)
    required_constructs = sum(item.get('required_construct_coverage', {}).get('total', 0) for item in results)
    covered_constructs = sum(item.get('required_construct_coverage', {}).get('covered_count', 0) for item in results)
    candidate_generated = sum(item.get('candidate_generated', 0) for item in results)
    candidate_syntax_valid = sum(item.get('candidate_syntax_valid', 0) for item in results)
    candidate_runtime_valid = sum(item.get('candidate_runtime_valid', 0) for item in results)
    candidate_runtime_checked = sum(item.get('candidate_runtime_checked', 0) for item in results)
    candidate_runtime_not_run = sum(item.get('candidate_runtime_not_run', 0) for item in results)
    accepted_candidates = sum(item.get('accepted_llm_candidates', 0) for item in results)
    candidate_oracle_cases = sum(item.get('candidate_oracle_match') is not None for item in results)
    candidate_oracle_matches = sum(item.get('candidate_oracle_match') is True for item in results)
    configured_cases = sum(bool(item.get('llm_configured', False)) for item in results)
    expected_outcomes_matched = sum(bool(item.get('outcome_correct')) for item in results)
    expected_supported = sum(item.get('expected_outcome', 'translated') == 'translated' for item in results)
    expected_supported_passed = sum(
        item.get('expected_outcome', 'translated') == 'translated' and item.get('status') == 'passed'
        for item in results
    )
    expected_unsupported = sum(item.get('expected_outcome') == 'unsupported' for item in results)
    recognized_unsupported = sum(
        item.get('expected_outcome') == 'unsupported' and item.get('outcome_correct')
        for item in results
    )
    gold_output_cases = [item for item in results if item.get('gold_output_match') is not None]
    gold_output_matches = sum(bool(item.get('gold_output_match')) for item in gold_output_cases)

    by_language = {}
    for item in results:
        entry = by_language.setdefault(item['language'], {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'unsupported_constructs': 0,
            'validation_failures': 0,
            'llm_calls': 0,
            'llm_attempts': 0,
            'llm_latency_ms': [],
            'candidate_generated': 0,
            'candidate_syntax_valid': 0,
            'candidate_runtime_valid': 0,
            'candidate_runtime_checked': 0,
            'candidate_runtime_not_run': 0,
            'accepted_llm_candidates': 0,
            'llm_configured_cases': 0,
        })
        entry['total'] += 1
        entry['passed'] += int(item.get('status') == 'passed')
        entry['failed'] += int(item.get('status') != 'passed')
        entry['unsupported_constructs'] += item.get('unsupported', 0)
        entry['validation_failures'] += item.get('validation_failures', 0)
        entry['llm_calls'] += item.get('llm_calls', 0)
        entry['llm_attempts'] += item.get('llm_attempts', 0)
        entry['llm_latency_ms'].extend(item.get('llm_latency_ms', []))
        entry['candidate_generated'] += item.get('candidate_generated', 0)
        entry['candidate_syntax_valid'] += item.get('candidate_syntax_valid', 0)
        entry['candidate_runtime_valid'] += item.get('candidate_runtime_valid', 0)
        entry['candidate_runtime_checked'] += item.get('candidate_runtime_checked', 0)
        entry['candidate_runtime_not_run'] += item.get('candidate_runtime_not_run', 0)
        entry['accepted_llm_candidates'] += item.get('accepted_llm_candidates', 0)
        entry['llm_configured_cases'] += int(bool(item.get('llm_configured', False)))

    for payload in by_language.values():
        payload['success_rate_percent'] = round((payload['passed'] / payload['total']) * 100.0, 1) if payload['total'] else 0.0
        payload['fallback_frequency_percent'] = round((payload['llm_calls'] / payload['total']) * 100.0, 1) if payload['total'] else 0.0
        payload['median_llm_latency_ms'] = round(statistics.median(payload['llm_latency_ms']), 1) if payload['llm_latency_ms'] else None
        payload['mean_llm_latency_ms'] = round(sum(payload['llm_latency_ms']) / len(payload['llm_latency_ms']), 1) if payload['llm_latency_ms'] else None
        payload['llm_cost_usd'] = None
        payload['success_rate_95ci_percent'] = _wilson_interval(payload['passed'], payload['total'])

    by_construct = {}
    for item in results:
        by_construct[f"{item['language']}:{item['case']}"] = {
            'language': item['language'],
            'status': item.get('status'),
            'failure_class': item.get('failure_class'),
            'unsupported': item.get('unsupported', 0),
            'required_construct_coverage': item.get('required_construct_coverage'),
            'llm_calls': item.get('llm_calls', 0),
            'llm_attempts': item.get('llm_attempts', 0),
            'llm_latency_ms': item.get('llm_latency_ms', []),
            'candidate_syntax_valid': item.get('candidate_syntax_valid', 0),
            'candidate_runtime_valid': item.get('candidate_runtime_valid', 0),
            'candidate_runtime_checked': item.get('candidate_runtime_checked', 0),
            'candidate_runtime_not_run': item.get('candidate_runtime_not_run', 0),
            'candidate_oracle_match': item.get('candidate_oracle_match'),
            'validation_failures': item.get('validation_failures', 0),
        }

    return {
        'target': variant_name,
        'total': total,
        'passed': passed,
        'failed': failed,
        'success_rate_percent': round((passed / total) * 100.0, 1) if total else 0.0,
        'success_rate_95ci_percent': _wilson_interval(passed, total),
        'unsupported_constructs': unsupported,
        'validation_failures': validation_failures,
        'required_constructs': required_constructs,
        'covered_required_constructs': covered_constructs,
        'required_construct_coverage_percent': round((covered_constructs / required_constructs) * 100.0, 1) if required_constructs else None,
        'candidate_generated': candidate_generated,
        'candidate_syntax_valid': candidate_syntax_valid,
        'candidate_runtime_valid': candidate_runtime_valid,
        'candidate_runtime_checked': candidate_runtime_checked,
        'candidate_runtime_not_run': candidate_runtime_not_run,
        'accepted_llm_candidates': accepted_candidates,
        'candidate_oracle_cases': candidate_oracle_cases,
        'candidate_oracle_matches': candidate_oracle_matches,
        'candidate_oracle_match_percent': round((candidate_oracle_matches / candidate_oracle_cases) * 100.0, 1) if candidate_oracle_cases else None,
        'llm_configured_cases': configured_cases,
        'expected_outcomes_matched': expected_outcomes_matched,
        'expected_outcome_match_rate_percent': round((expected_outcomes_matched / total) * 100, 1) if total else 0.0,
        'supported_case_success_rate_percent': round((expected_supported_passed / expected_supported) * 100, 1) if expected_supported else None,
        'supported_case_success_rate_95ci_percent': _wilson_interval(expected_supported_passed, expected_supported),
        'unsupported_cases_expected': expected_unsupported,
        'unsupported_cases_recognized': recognized_unsupported,
        'unsupported_recognition_rate_percent': round((recognized_unsupported / expected_unsupported) * 100, 1) if expected_unsupported else None,
        'gold_output_cases': len(gold_output_cases),
        'gold_output_matches': gold_output_matches,
        'gold_output_accuracy_percent': round((gold_output_matches / len(gold_output_cases)) * 100, 1) if gold_output_cases else None,
        'fallback_frequency_percent': fallback_frequency,
        'metrics': {
            'llm_calls': llm_calls,
            'llm_attempts': llm_attempts,
            'llm_latency_ms': llm_latencies,
            'median_llm_latency_ms': round(statistics.median(llm_latencies), 1) if llm_latencies else None,
            'mean_llm_latency_ms': round(sum(llm_latencies) / len(llm_latencies), 1) if llm_latencies else None,
            'llm_cost_usd': None,
            'candidate_generated': candidate_generated,
            'candidate_syntax_valid': candidate_syntax_valid,
            'candidate_runtime_valid': candidate_runtime_valid,
            'accepted_llm_candidates': accepted_candidates,
            'candidate_oracle_cases': candidate_oracle_cases,
            'candidate_oracle_matches': candidate_oracle_matches,
            'llm_configured_cases': configured_cases,
            'fallback_frequency_percent': fallback_frequency,
            'validation_failures': validation_failures,
        },
        'by_language': by_language,
        'by_construct': by_construct,
        'cases': results,
    }


def run_benchmark(target='JavaScript', cases=None):
    run_cases = list(DEFAULT_CASES if cases is None else cases)
    results = []
    for language, case_name, source in run_cases:
        try:
            r = transpile(source, language, target, enable_llm=False)
            results.append({
                'language': language,
                'case': case_name,
                'status': r['validation']['status'],
                'failure_class': r['validation'].get('failure_class'),
                'unsupported': len(r.get('unsupported', [])),
                'source_construct_coverage_percent': r['rule_coverage'].get('coverage_percent'),
                'required_construct_coverage': _required_construct_coverage(language, case_name, r.get('rules_used', []), source),
                'source_reference': _case_metadata(language, case_name, source).get('provenance'),
                'gold_output_match': (
                    _oracle_match(
                        r.get('target_runtime', {}).get('output'),
                        _case_metadata(language, case_name, source).get('expected_output'),
                    )
                    if (
                        not r.get('unsupported')
                        and r.get('target_runtime', {}).get('available')
                        and r.get('target_runtime', {}).get('ok')
                    )
                    else None
                ),
                'expected_outcome': _case_metadata(language, case_name, source).get('expected_outcome', 'translated'),
                'outcome_correct': (
                    r['validation']['status'] == 'passed'
                    if _case_metadata(language, case_name, source).get('expected_outcome', 'translated') == 'translated'
                    else bool(r.get('unsupported')) and r['validation']['status'] == 'not_run'
                ),
                'generated_lines': r.get('generated_lines', 0),
            })
        except Exception as exc:
            results.append({'language': language, 'case': case_name, 'status': 'error', 'failure_class': 'pipeline_error', 'expected_outcome': _case_metadata(language, case_name, source).get('expected_outcome', 'translated'), 'outcome_correct': False, 'gold_output_match': None, 'error': str(exc)})
    passed = sum(x['status'] == 'passed' for x in results)
    required_total = sum(x.get('required_construct_coverage', {}).get('total', 0) for x in results)
    required_covered = sum(x.get('required_construct_coverage', {}).get('covered_count', 0) for x in results)
    expected_matches = sum(bool(x.get('outcome_correct')) for x in results)
    expected_supported = sum(x.get('expected_outcome', 'translated') == 'translated' for x in results)
    expected_supported_passed = sum(
        x.get('expected_outcome', 'translated') == 'translated' and x.get('status') == 'passed'
        for x in results
    )
    expected_unsupported = sum(x.get('expected_outcome') == 'unsupported' for x in results)
    recognized_unsupported = sum(
        x.get('expected_outcome') == 'unsupported' and x.get('outcome_correct')
        for x in results
    )
    gold_output_cases = [x for x in results if x.get('gold_output_match') is not None]
    gold_output_matches = sum(bool(x.get('gold_output_match')) for x in gold_output_cases)
    return {
        'target': target,
        'dataset_id': EXTERNAL_DATASET_ID,
        'external_task_derived_cases': len(EXTERNAL_CASES),
        'total': len(results),
        'passed': passed,
        'failed': len(results) - passed,
        'success_rate_percent': round(passed / len(results) * 100, 1) if results else 0.0,
        'required_constructs': required_total,
        'covered_required_constructs': required_covered,
        'required_construct_coverage_percent': round((required_covered / required_total) * 100.0, 1) if required_total else None,
        'success_rate_95ci_percent': _wilson_interval(passed, len(results)),
        'expected_outcomes_matched': expected_matches,
        'expected_outcome_match_rate_percent': round((expected_matches / len(results)) * 100, 1) if results else 0.0,
        'supported_case_success_rate_percent': round((expected_supported_passed / expected_supported) * 100.0, 1) if expected_supported else None,
        'supported_case_success_rate_95ci_percent': _wilson_interval(expected_supported_passed, expected_supported),
        'translation_success_rate_percent': round((expected_supported_passed / expected_supported) * 100.0, 1) if expected_supported else None,
        'unsupported_cases_expected': expected_unsupported,
        'unsupported_cases_recognized': recognized_unsupported,
        'unsupported_recognition_rate_percent': round((recognized_unsupported / expected_unsupported) * 100.0, 1) if expected_unsupported else None,
        'gold_output_cases': len(gold_output_cases),
        'gold_output_matches': gold_output_matches,
        'gold_output_accuracy_percent': round((gold_output_matches / len(gold_output_cases)) * 100.0, 1) if gold_output_cases else None,
        'cases': results,
    }


def run_experiment(target='JavaScript', cases=None, repeats=1):
    run_cases = list(DEFAULT_CASES if cases is None else cases)
    rule_only_results = []
    hybrid_results = []

    for _ in range(repeats):
        for language, case_name, source in run_cases:
            rule_only_results.append(_case_result(language, case_name, source, target, enable_llm=False))
            hybrid_results.append(_case_result(language, case_name, source, target, enable_llm=True))

    rule_only = _summarize_variant(rule_only_results, 'rule_only')
    hybrid = _summarize_variant(hybrid_results, 'hybrid')

    summary_by_language = {}
    for language, _, _ in run_cases:
        if language not in summary_by_language:
            summary_by_language[language] = {
                'rule_only': rule_only['by_language'].get(language, {}),
                'hybrid': hybrid['by_language'].get(language, {}),
            }

    summary_by_construct = {}
    for language, case_name, _ in run_cases:
        key = f'{language}:{case_name}'
        summary_by_construct[key] = {
            'rule_only': rule_only['by_construct'].get(key, {}),
            'hybrid': hybrid['by_construct'].get(key, {}),
        }

    summary = {
        'by_language': summary_by_language,
        'by_construct': summary_by_construct,
        'overall': {
            'rule_only_success_rate_percent': rule_only['success_rate_percent'],
            'hybrid_success_rate_percent': hybrid['success_rate_percent'],
            'delta_success_rate_percent': round(hybrid['success_rate_percent'] - rule_only['success_rate_percent'], 1),
        },
    }

    return {
        'target': target,
        'dataset_id': EXTERNAL_DATASET_ID,
        'external_task_derived_cases': len(EXTERNAL_CASES),
        'repeats': repeats,
        'rule_only': rule_only,
        'hybrid': hybrid,
        'ablation_scope': {
            'compared_component': 'complete-program LLM fallback generation, restricted target execution, and independent expected-output matching',
            'candidate_acceptance': 'Candidate oracle matches are counted for benchmark cases only; the translator never marks model candidates accepted automatically.',
            'not_isolated': ['semantic contracts', 'risk assessment', 'learned-rule metadata do not currently alter code generation or acceptance decisions'],
        },
        'summary': summary,
    }


def render_experiment_report(report):
    rule_only = report.get('rule_only', {})
    hybrid = report.get('hybrid', {})
    summary = report.get('summary', {})
    overall = summary.get('overall', {})

    lines = [
        'Rule-only vs Hybrid Experiment Summary',
        '====================================',
        f"Target: {report.get('target', 'JavaScript')}",
        f"Repeats: {report.get('repeats', 1)}",
        f"Dataset: {report.get('dataset_id', 'local')}",
        f"External task-derived cases: {report.get('external_task_derived_cases', 0)}",
        '',
        'Rule-only',
        '---------',
        f"Semantic-validation pass rate (all cases): {rule_only.get('success_rate_percent', 0)}%",
        f"Supported-case translation pass rate: {rule_only.get('supported_case_success_rate_percent')}%",
        f"95% Wilson interval: {rule_only.get('supported_case_success_rate_95ci_percent')}",
        f"Expected outcome agreement: {rule_only.get('expected_outcome_match_rate_percent')}%",
        f"Fallback frequency: {rule_only.get('fallback_frequency_percent', 0)}%",
        f"Validation failures: {rule_only.get('validation_failures', 0)}",
        f"Required-construct coverage: {rule_only.get('required_construct_coverage_percent')}%",
        '',
        'Hybrid',
        '------',
        f"Semantic-validation pass rate (all cases): {hybrid.get('success_rate_percent', 0)}%",
        f"Supported-case translation pass rate: {hybrid.get('supported_case_success_rate_percent')}%",
        f"95% Wilson interval: {hybrid.get('supported_case_success_rate_95ci_percent')}",
        f"Expected outcome agreement: {hybrid.get('expected_outcome_match_rate_percent')}%",
        f"Fallback frequency: {hybrid.get('fallback_frequency_percent', 0)}%",
        f"Validation failures: {hybrid.get('validation_failures', 0)}",
        f"Cases with LLM configured: {hybrid.get('llm_configured_cases', 0)}",
        f"Required-construct coverage: {hybrid.get('required_construct_coverage_percent')}%",
        f"LLM candidates generated: {hybrid.get('candidate_generated', 0)}",
        f"LLM candidates syntax-valid: {hybrid.get('candidate_syntax_valid', 0)}",
        f"LLM candidates runtime-valid: {hybrid.get('candidate_runtime_valid', 0)}",
        f"LLM candidate runtimes not run: {hybrid.get('candidate_runtime_not_run', 0)}",
        f"Candidate expected-output matches: {hybrid.get('candidate_oracle_matches', 0)}/{hybrid.get('candidate_oracle_cases', 0)}",
        f"LLM candidates accepted by translator: {hybrid.get('accepted_llm_candidates', 0)}",
        f"Median LLM latency: {hybrid.get('metrics', {}).get('median_llm_latency_ms')} ms",
        f"Ablation scope: {report.get('ablation_scope', {}).get('compared_component', 'not specified')}",
        '',
        'Overall',
        '-------',
        f"Rule-only success: {overall.get('rule_only_success_rate_percent', 0)}%",
        f"Hybrid success: {overall.get('hybrid_success_rate_percent', 0)}%",
        f"Delta: {overall.get('delta_success_rate_percent', 0)}%",
        '',
        'Per-language summary:',
    ]

    for language, payload in summary.get('by_language', {}).items():
        lines.append(f"- {language}: rule_only={payload.get('rule_only', {}).get('success_rate_percent', 0)}%, hybrid={payload.get('hybrid', {}).get('success_rate_percent', 0)}%")

    return '\n'.join(lines)
