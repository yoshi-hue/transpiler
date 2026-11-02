"""Run the versioned four-arm evaluation and archive native/safeguard status."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.benchmark import DEFAULT_CASES, _case_metadata, _oracle_match, run_benchmark, run_experiment
from backend.evidence import write_evidence
from backend.native_adapters import compile_and_run_native, native_tool_status
from backend.safeguards import evaluate_mutations
from backend.llm_fallback import translate_construct
from backend.validator import check_javascript_syntax, check_python_syntax, run_javascript, run_python_isolated
from backend.transpiler import transpile
from dotenv import load_dotenv


def native_oracle_match(output, expected):
    """Compare native output while allowing compiler-specific numeric padding."""
    if _oracle_match(output, expected):
        return True
    actual_text = str(output).strip()
    expected_text = str(expected).strip()
    try:
        return len(actual_text.splitlines()) == 1 and int(actual_text) == int(expected_text)
    except (TypeError, ValueError):
        return False


def review_queue_metrics():
    """Summarize review completeness without treating pending records as approval."""
    queue_path = ROOT / 'data' / 'independent_oracle_review_queue_v2.json'
    if not queue_path.exists():
        return {'status': 'not_available', 'total': 0}
    payload = json.loads(queue_path.read_text(encoding='utf-8'))
    cases = payload.get('cases', [])
    def complete(case):
        review = case.get('review', {})
        if review.get('status') not in {'approved', 'rejected'}:
            return False
        if not isinstance(review.get('reviewer_name'), str) or not review['reviewer_name'].strip():
            return False
        if not isinstance(review.get('review_minutes'), (int, float)) or review['review_minutes'] <= 0:
            return False
        if not isinstance(review.get('notes'), str) or not review['notes'].strip():
            return False
        allowed = {'approved', 'rejected', 'verified', 'not_applicable',
                   'not_applicable_project_authored'}
        return all(str(review.get(field, '')).strip().lower() in allowed for field in (
            'source_and_task_semantics', 'fixture_expected_outputs',
            'reuse_terms_and_attribution'))

    reviewed = [case for case in cases if complete(case)]
    status_decided = [case for case in cases if case.get('review', {}).get('status') in {'approved', 'rejected'}]
    return {
        'status': 'complete' if cases and len(reviewed) == len(cases) else 'pending',
        'total': len(cases),
        'reviewed': len(reviewed),
        'decided_but_incomplete': len(status_decided) - len(reviewed),
        'pending': len(cases) - len(reviewed),
        'decisions': {decision: sum(case.get('review', {}).get('status') == decision for case in cases)
                      for decision in ('approved', 'rejected')},
        'reviewer_identities_present': sum(bool(case.get('review', {}).get('reviewer_name')) for case in reviewed),
        'review_minutes_recorded': sum(bool(case.get('review', {}).get('review_minutes')) for case in reviewed),
    }


def candidate_gate_metrics(report):
    """Measure rejection/acceptance gates from recorded candidate evidence."""
    rows = report.get('cases', [])
    candidates = [artifact for row in rows for artifact in row.get('candidate_artifacts', [])]
    correct = [item for item in candidates if item.get('oracle_match') is True]
    incorrect = [item for item in candidates if item.get('oracle_match') is False]
    return {
        'candidates': len(candidates),
        'correct_candidates': len(correct),
        'incorrect_candidates': len(incorrect),
        'correct_candidate_rejections': sum(not item.get('accepted', False) for item in correct),
        'incorrect_candidate_rejections': sum(not item.get('accepted', False) for item in incorrect),
        'accepted_candidates': sum(bool(item.get('accepted')) for item in candidates),
        'interpretation': 'Rejection counts are evidence for this run only; they do not establish universal safeguard performance.',
    }


def repair_metrics(hybrid, repaired):
    base_rows = hybrid.get('cases', [])
    fixed_rows = repaired.get('cases', [])
    # Some legacy summaries store only a case count.  Keep the metric explicit
    # rather than failing the entire evidence run when detailed rows are absent.
    if not isinstance(base_rows, list) or not isinstance(fixed_rows, list):
        return {'comparable_cases': 0, 'hybrid_failures': None, 'repair_failures': None,
                'recovered_cases': None, 'regressions': None, 'max_repairs': 2,
                'status': 'detail_rows_unavailable'}
    base = {(row.get('language'), row.get('case')): row for row in base_rows}
    fixed = {(row.get('language'), row.get('case')): row for row in fixed_rows}
    comparable = [key for key in base if key in fixed]
    return {
        'comparable_cases': len(comparable),
        'hybrid_failures': sum(base[key].get('status') != 'passed' for key in comparable),
        'repair_failures': sum(fixed[key].get('status') != 'passed' for key in comparable),
        'recovered_cases': sum(base[key].get('status') != 'passed' and fixed[key].get('status') == 'passed' for key in comparable),
        'regressions': sum(base[key].get('status') == 'passed' and fixed[key].get('status') != 'passed' for key in comparable),
        'max_repairs': 2,
    }


def version(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def run_llm_only(target, cases):
    """Generate complete candidates without deterministic output selection."""
    if not __import__('backend.llm_fallback', fromlist=['fallback_status']).fallback_status().get('configured'):
        return {'status': 'not_run', 'reason': 'Provider is not configured.', 'cases': len(cases)}
    rows = []
    for language, case_name, source in cases:
        metadata = _case_metadata(language, case_name, source)
        if metadata.get('origin') == 'codenet':
            rows.append({'language': language, 'case': case_name, 'status': 'not_run',
                         'reason': 'External-source provider policy blocked this request.'})
            continue
        try:
            suggestion = translate_construct(language, target, source, source[:5000], complete_program=True)
            candidate = suggestion.get('candidate', '')
            syntax = (check_javascript_syntax(candidate) if target == 'JavaScript'
                      else check_python_syntax(candidate))
            runtime = ({'available': False, 'ok': None, 'output': '', 'error': 'syntax failed'}
                       if not syntax.get('ok') else
                       (run_javascript(candidate, restricted=True) if target == 'JavaScript'
                        else run_python_isolated(candidate)))
            expected = metadata.get('expected_output')
            match = bool(runtime.get('ok') and _oracle_match(runtime.get('output'), expected)) if expected is not None else None
            rows.append({'language': language, 'case': case_name,
                         'status': 'passed' if match else 'failed',
                         'candidate_generated': bool(candidate),
                         'syntax_valid': syntax.get('ok'), 'runtime_valid': runtime.get('ok'),
                         'oracle_match': match, 'candidate_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
                         'provider': suggestion.get('provider'), 'model': suggestion.get('model'),
                         'latency_ms': suggestion.get('latency_ms'), 'error': runtime.get('error', '')})
        except Exception as exc:
            rows.append({'language': language, 'case': case_name, 'status': 'error', 'error': str(exc)})
    return {'status': 'completed', 'cases': len(rows), 'passed': sum(row.get('status') == 'passed' for row in rows), 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('JavaScript', 'Python'), required=True)
    parser.add_argument('--output-dir', default='data/evidence')
    parser.add_argument('--enable-llm', action='store_true')
    parser.add_argument('--enable-repair', action='store_true')
    parser.add_argument('--project-only', action='store_true',
                        help='Exclude CodeNet-origin cases from live provider requests.')
    parser.add_argument('--max-cases', type=int, default=0,
                        help='Optional cap after filtering; 0 means all selected cases.')
    args = parser.parse_args()
    if args.enable_llm:
        load_dotenv(ROOT / '.env', override=False)
    selected_cases = list(DEFAULT_CASES)
    if args.project_only:
        selected_cases = [case for case in selected_cases
                          if _case_metadata(*case).get('origin') != 'codenet']
    if args.max_cases:
        selected_cases = selected_cases[:max(1, args.max_cases)]

    # Rule-only is always offline. The existing hybrid arm is paired on the same cases.
    rule_only = run_benchmark(args.target, cases=selected_cases)
    experiment = run_experiment(args.target, cases=selected_cases, repeats=1,
                                enable_llm=args.enable_llm, enable_repair=args.enable_repair)
    hybrid = experiment.get('hybrid', {})
    llm_only = run_llm_only(args.target, selected_cases) if args.enable_llm else {
        'status': 'not_run', 'reason': 'Use --enable-llm for an explicitly authorized live run.', 'cases': len(selected_cases)}
    if args.enable_llm and args.enable_repair:
        hybrid_repair = {'status': 'completed', **experiment.get('hybrid_repair', {})}
    else:
        hybrid_repair = {'status': 'not_run',
                         'reason': 'Use --enable-llm --enable-repair for an explicitly authorized live run.',
                         'cases': len(selected_cases)}
    native = {language: native_tool_status(language) for language in ('COBOL', 'FORTRAN', 'Pascal', 'BASIC')}
    native_pilots = {}
    for language in ('COBOL', 'FORTRAN', 'Pascal', 'BASIC'):
        native_pilot = {'status': 'not_run', 'reason': f'No {language} case selected.'}
        for case_language, case_name, source in selected_cases:
            if case_language == language:
                native_pilot = compile_and_run_native(language, source)
                native_pilot.update({'language': language, 'case': case_name,
                                     'expected_output': _case_metadata(language, case_name, source).get('expected_output')})
                if native_pilot.get('stdout') is not None and native_pilot.get('expected_output') is not None:
                    native_pilot['oracle_match'] = native_oracle_match(
                        native_pilot['stdout'], native_pilot['expected_output'])
                break
        native_pilots[language] = native_pilot
    mutation = evaluate_mutations('for (let i = 0; i < 3; i++) { console.log("STEP"); }',
                                  lambda code: run_javascript(code, restricted=True))
    repair_summary = repair_metrics(hybrid, hybrid_repair)
    gate_summary = candidate_gate_metrics(hybrid)
    outcomes = {
        'benchmark_version': 'four-arm-pilot-v1',
        'arms': {'rule_only': rule_only, 'llm_only': llm_only,
                 'rule_first_llm': hybrid, 'rule_first_llm_repair': hybrid_repair},
        'native_adapters': native,
        'native_pilots': native_pilots,
        'safeguards': {
            'mutation_sensitivity': mutation,
            'candidate_gates': gate_summary,
            'unsupported_input_recognition': {
                'cases': hybrid.get('unsupported_cases_expected', 0),
                'recognized': hybrid.get('unsupported_cases_recognized', 0),
                'rate_percent': hybrid.get('unsupported_recognition_rate_percent'),
            },
            'learned_rule_hits': hybrid.get('learned_rule_reuses', 0),
            'learned_rule_misses': max(0, hybrid.get('total', 0) - hybrid.get('learned_rule_reuses', 0)),
        },
        'repair_metrics': repair_summary,
        'human_review': review_queue_metrics(),
        'limitations': ['LLM-only and repair arms are not silently treated as passes when not explicitly run.',
                        'Native status is tool discovery only until a language-specific compile/run harness is supplied.'],
    }
    files = [ROOT / 'data' / 'external_task_cases.jsonl', ROOT / 'data' / 'supported_subset.json']
    path, record = write_evidence(
        output_dir=ROOT / args.output_dir,
        command=' '.join(sys.argv),
        settings={'target': args.target, 'llm_enabled': args.enable_llm,
                  'repair_enabled': args.enable_repair, 'project_only': args.project_only,
                  'selected_case_count': len(selected_cases), 'split': 'test'},
        outcomes=outcomes, files=files,
        runtime={'python': platform.python_version(), 'node': version(['node', '--version'])},
    )
    print(json.dumps({'output': str(path), 'run_id': record['run_id'],
                      'arms': list(outcomes['arms']), 'native': native}, indent=2))


if __name__ == '__main__':
    main()
