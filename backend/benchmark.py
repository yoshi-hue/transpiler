"""Small hand-curated in-project benchmark.
The benchmark is intentionally inspectable: every case is a source snippet and an
expected pipeline outcome, rather than a hidden score.

This module also supports a controlled rule-only vs hybrid evaluation with
per-language and per-construct breakdowns, fallback frequency, latency, and
validation-failure tracking for research reporting.
"""
import os
import statistics

from .transpiler import transpile

CASES = [
    ('COBOL', 'arithmetic', '''IDENTIFICATION DIVISION.\nPROGRAM-ID. B1.\nDATA DIVISION.\nWORKING-STORAGE SECTION.\n01 A PIC 999 VALUE 7.\n01 B PIC 999 VALUE 5.\nPROCEDURE DIVISION.\nCOMPUTE SUM = A + B.\nDISPLAY SUM.\nSTOP RUN.'''),
    ('COBOL', 'conditional', '''IDENTIFICATION DIVISION.\nPROGRAM-ID. B2.\nDATA DIVISION.\nWORKING-STORAGE SECTION.\n01 A PIC 999 VALUE 7.\nPROCEDURE DIVISION.\nIF A > 5\n DISPLAY "HIGH"\nELSE\n DISPLAY "LOW"\nEND-IF.\nSTOP RUN.'''),
    ('FORTRAN', 'loop', '''PROGRAM B3\nINTEGER :: I\nDO I = 1, 3\nPRINT *, I\nEND DO\nEND PROGRAM B3'''),
    ('FORTRAN', 'conditional', '''PROGRAM B4\nINTEGER :: A\nA = 4\nIF (A < 5) THEN\nPRINT *, "LOW"\nELSE\nPRINT *, "HIGH"\nEND IF\nEND PROGRAM B4'''),
    ('Pascal', 'arithmetic', '''program b5;\nvar a, b, s: integer;\nbegin\na := 4; b := 6; s := a + b; writeln(s);\nend.'''),
    ('Pascal', 'loop', '''program b6;\nvar i: integer;\nbegin\nfor i := 1 to 3 do writeln(i);\nend.'''),
    ('BASIC', 'arithmetic', '''10 LET A = 4\n20 LET B = 6\n30 PRINT A + B\n40 END'''),
    ('BASIC', 'loop', '''10 FOR I = 1 TO 3\n20 PRINT I\n30 NEXT I\n40 END'''),
]

LLM_ENV_KEYS = ('LLM_API_URL', 'LLM_API_MODE', 'LLM_MODEL', 'LLM_API_KEY', 'LLM_PROVIDER')


def _temporary_llm_state(enable_llm):
    original = {key: os.environ.get(key) for key in LLM_ENV_KEYS}

    def restore():
        for key in LLM_ENV_KEYS:
            value = original.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    if enable_llm:
        return restore

    for key in LLM_ENV_KEYS:
        os.environ.pop(key, None)
    return restore


def _case_result(language, case_name, source, target, *, enable_llm):
    restore = _temporary_llm_state(enable_llm)
    try:
        result = transpile(source, language, target)
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
            'llm_cost_usd': 0.0,
            'validation_failures': 1,
        }
    finally:
        restore()

    validation = result.get('validation', {})
    logs = result.get('fallback_log', [])
    llm_calls = 0
    llm_latencies = []
    for entry in logs:
        if isinstance(entry.get('latency_ms'), (int, float)):
            llm_calls += 1
            llm_latencies.append(float(entry['latency_ms']))

    return {
        'language': language,
        'case': case_name,
        'status': validation.get('status', 'not_run'),
        'failure_class': validation.get('failure_class'),
        'unsupported': len(result.get('unsupported', [])),
        'unsupported_constructs': result.get('unsupported', []),
        'rule_coverage': result.get('rule_coverage', {}).get('coverage_percent'),
        'generated_lines': result.get('generated_lines', 0),
        'llm_calls': llm_calls,
        'llm_latency_ms': llm_latencies,
        'llm_cost_usd': 0.0,
        'validation_failures': 1 if validation.get('status') in ('failed', 'not_run', 'error') else 0,
    }


def _summarize_variant(results, variant_name):
    total = len(results)
    passed = sum(1 for item in results if item.get('status') == 'passed')
    failed = total - passed
    llm_calls = sum(item.get('llm_calls', 0) for item in results)
    llm_latencies = [value for item in results for value in item.get('llm_latency_ms', [])]
    fallback_frequency = round((llm_calls / total) * 100.0, 1) if total else 0.0
    validation_failures = sum(item.get('validation_failures', 0) for item in results)
    unsupported = sum(item.get('unsupported', 0) for item in results)

    by_language = {}
    for item in results:
        entry = by_language.setdefault(item['language'], {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'unsupported_constructs': 0,
            'validation_failures': 0,
            'llm_calls': 0,
            'llm_latency_ms': [],
        })
        entry['total'] += 1
        entry['passed'] += int(item.get('status') == 'passed')
        entry['failed'] += int(item.get('status') != 'passed')
        entry['unsupported_constructs'] += item.get('unsupported', 0)
        entry['validation_failures'] += item.get('validation_failures', 0)
        entry['llm_calls'] += item.get('llm_calls', 0)
        entry['llm_latency_ms'].extend(item.get('llm_latency_ms', []))

    for payload in by_language.values():
        payload['success_rate_percent'] = round((payload['passed'] / payload['total']) * 100.0, 1) if payload['total'] else 0.0
        payload['fallback_frequency_percent'] = round((payload['llm_calls'] / payload['total']) * 100.0, 1) if payload['total'] else 0.0
        payload['median_llm_latency_ms'] = round(statistics.median(payload['llm_latency_ms']), 1) if payload['llm_latency_ms'] else None
        payload['mean_llm_latency_ms'] = round(sum(payload['llm_latency_ms']) / len(payload['llm_latency_ms']), 1) if payload['llm_latency_ms'] else None
        payload['llm_cost_usd'] = 0.0

    by_construct = {}
    for item in results:
        by_construct[item['case']] = {
            'language': item['language'],
            'status': item.get('status'),
            'failure_class': item.get('failure_class'),
            'unsupported': item.get('unsupported', 0),
            'llm_calls': item.get('llm_calls', 0),
            'llm_latency_ms': item.get('llm_latency_ms', []),
            'validation_failures': item.get('validation_failures', 0),
        }

    return {
        'target': variant_name,
        'total': total,
        'passed': passed,
        'failed': failed,
        'success_rate_percent': round((passed / total) * 100.0, 1) if total else 0.0,
        'unsupported_constructs': unsupported,
        'validation_failures': validation_failures,
        'fallback_frequency_percent': fallback_frequency,
        'metrics': {
            'llm_calls': llm_calls,
            'llm_latency_ms': llm_latencies,
            'median_llm_latency_ms': round(statistics.median(llm_latencies), 1) if llm_latencies else None,
            'mean_llm_latency_ms': round(sum(llm_latencies) / len(llm_latencies), 1) if llm_latencies else None,
            'llm_cost_usd': 0.0,
            'fallback_frequency_percent': fallback_frequency,
            'validation_failures': validation_failures,
        },
        'by_language': by_language,
        'by_construct': by_construct,
        'cases': results,
    }


def run_benchmark(target='JavaScript', cases=None):
    run_cases = list(cases or CASES)
    results = []
    for language, case_name, source in run_cases:
        try:
            r = transpile(source, language, target)
            results.append({
                'language': language,
                'case': case_name,
                'status': r['validation']['status'],
                'failure_class': r['validation'].get('failure_class'),
                'unsupported': len(r.get('unsupported', [])),
                'rule_coverage': r['rule_coverage'].get('coverage_percent'),
                'generated_lines': r.get('generated_lines', 0),
            })
        except Exception as exc:
            results.append({'language': language, 'case': case_name, 'status': 'error', 'failure_class': 'pipeline_error', 'error': str(exc)})
    passed = sum(x['status'] == 'passed' for x in results)
    return {'target': target, 'total': len(results), 'passed': passed, 'failed': len(results) - passed, 'success_rate_percent': round(passed / len(results) * 100, 1), 'cases': results}


def run_experiment(target='JavaScript', cases=None, repeats=1):
    run_cases = list(cases or CASES)
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
    for _, case_name, _ in run_cases:
        summary_by_construct[case_name] = {
            'rule_only': rule_only['by_construct'].get(case_name, {}),
            'hybrid': hybrid['by_construct'].get(case_name, {}),
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

    return {'target': target, 'repeats': repeats, 'rule_only': rule_only, 'hybrid': hybrid, 'summary': summary}


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
        '',
        'Rule-only',
        '---------',
        f"Success rate: {rule_only.get('success_rate_percent', 0)}%",
        f"Fallback frequency: {rule_only.get('fallback_frequency_percent', 0)}%",
        f"Validation failures: {rule_only.get('validation_failures', 0)}",
        '',
        'Hybrid',
        '------',
        f"Success rate: {hybrid.get('success_rate_percent', 0)}%",
        f"Fallback frequency: {hybrid.get('fallback_frequency_percent', 0)}%",
        f"Validation failures: {hybrid.get('validation_failures', 0)}",
        f"Median LLM latency: {hybrid.get('metrics', {}).get('median_llm_latency_ms')} ms",
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
