import ast
import hashlib
import re

from .legacy import legacy_transpile, LANGUAGES, SUBSETS
from .validator import run_javascript, run_python, run_python_isolated, compare
from .corpus import save_validated_example
from .llm_fallback import create_fallback_log, fallback_status, translate_construct
from .learned_rules import (
    apply_generalized_rule,
    find_generalized_rule,
    learn_generalized_rule,
)
from .rules import RULE_TABLE_VERSION

TARGETS = {
    'JavaScript': 'Executable with Node.js',
    'Python': 'Executable with Python 3',
}

def _extract_api_hints(source):
    lowered = source.lower()
    hints = []
    if 'print' in lowered or 'display' in lowered:
        hints.append('output')
    if 'if' in lowered or 'else' in lowered:
        hints.append('conditional')
    if 'for' in lowered or 'while' in lowered or 'do' in lowered:
        hints.append('loop')
    if 'goto' in lowered or 'call' in lowered:
        hints.append('control-flow')
    if any(token in lowered for token in ('+', '-', '*', '/', '%')):
        hints.append('arithmetic')
    return hints or ['program']


def _translation_contract(source, source_language, target_language, target_code, validation):
    output_hint = 'number|string'
    if any(token in source for token in ('print', 'DISPLAY', 'PRINT', 'WRITE')):
        output_hint = 'number|string'
    if 'array' in source.lower() or 'list' in source.lower():
        output_hint = 'list'
    if 'input' in source.lower() or 'read' in source.lower():
        output_hint = 'input stream'
    check_details = validation.get('checks', [])
    checks = [
        {'name': 'complete_source_coverage', 'passed': validation.get('status') != 'not_run'},
        {
            'name': 'target_execution_succeeded',
            'passed': validation.get('status') in ('passed', 'failed')
            and validation.get('failure_class') not in ('target_runtime_error', 'runtime_unavailable'),
        },
        {
            'name': 'finite_stdout_matches_source_oracle',
            'passed': validation.get('status') == 'passed',
            'source_output': validation.get('source_output'),
            'target_output': validation.get('target_output'),
        },
        *check_details,
    ]
    checks_passed = sum(check.get('passed') is True for check in checks)
    checks_failed = sum(check.get('passed') is False for check in checks)
    review_required = bool(validation.get('manual_review_required'))
    if validation.get('status') == 'not_run':
        status = 'pending'
    elif validation.get('status') != 'passed' or checks_failed:
        status = 'failed'
    elif review_required:
        status = 'review_required'
    else:
        status = 'satisfied_for_tested_inputs'
    source_hash = hashlib.sha256(source.encode('utf-8')).hexdigest()
    contract = {
        'contract_id': hashlib.sha256(f'{source_language}\0{target_language}\0{source_hash}'.encode()).hexdigest()[:20],
        'source_sha256': source_hash,
        'function': 'program',
        'inputs': ['source fragment'],
        'output': output_hint,
        'side_effects': ['stdout'] if 'print' in source.lower() or 'display' in source.lower() else [],
        'raises': ['unsupported construct'] if 'goto' in source.lower() else [],
        'source_api': _extract_api_hints(source),
        'target_api': ['console.log', 'let', 'if', 'function', 'return'] if target_language == 'JavaScript' else ['print', 'assignment', 'if', 'def', 'return'],
        'tests_passed': checks_passed,
        'tests_failed': checks_failed,
        'checks': checks,
        'translation_status': status,
        'confidence': None,
        'confidence_basis': 'not calibrated',
        'target_code_preview': (target_code[:180] + '…') if target_code and len(target_code) > 180 else target_code,
    }
    return contract


def _risk_assessment(source, source_language, target_language, validation=None):
    lowered = source.lower()
    features = {
        'loop': bool(re.search(r'\b(for|while|do|perform)\b', lowered)),
        'branch': bool(re.search(r'\b(if|else|case|switch)\b', lowered)),
        'unstructured_control': bool(re.search(r'\b(goto|call)\b', lowered)),
        'external_or_file_io': bool(re.search(r'\b(open|read|write|file|call)\b', lowered)),
        'cross_language': source_language != 'Python-like',
    }
    weights = {'loop': 0.2, 'branch': 0.15, 'unstructured_control': 0.55,
               'external_or_file_io': 0.3, 'cross_language': 0.1}
    score = min(1.0, sum(weights[name] for name, active in features.items() if active))
    level = 'high' if score >= 0.6 else 'medium' if score >= 0.2 else 'low'
    repeats = {'low': 1, 'medium': 2, 'high': 3}[level]
    review_required = level == 'high'
    reasons = [name.replace('_', ' ') for name, active in features.items() if active]
    return {
        'score': round(score, 2),
        'level': level,
        'features': features,
        'reasons': reasons or ['straight-line subset program'],
        'validation_profile': {
            'runtime_runs': repeats,
            'check_determinism': repeats > 1,
            'manual_review_required': review_required,
        },
        'validation_policy': (
            f'Run target and source oracle {repeats} times; '
            + ('require human review before acceptance.' if review_required else 'compare finite I/O outputs.')
        ),
    }


def _validate_with_risk(source_output, target_run, source_runner, target_runner, risk, target_language):
    """Compare outputs and apply the risk-selected repeatability checks."""
    profile = risk['validation_profile']
    expected_runs = profile['runtime_runs']
    source_outputs = [source_output]
    target_outputs = [target_run.get('output', '')]
    checks = []
    if target_run.get('available') and target_run.get('ok'):
        for _ in range(expected_runs - 1):
            source_outputs.append(source_runner())
            repeated = target_runner()
            if not repeated.get('available') or not repeated.get('ok'):
                checks.append({'name': 'repeat_target_execution', 'passed': False,
                               'error': repeated.get('error') or 'Target runtime unavailable.'})
                break
            target_outputs.append(repeated.get('output', ''))
    deterministic = len(set(source_outputs)) == 1 and len(set(target_outputs)) == 1
    checks.append({
        'name': 'runtime_determinism',
        'runs_requested': expected_runs,
        'source_runs_completed': len(source_outputs),
        'target_runs_completed': len(target_outputs),
        'passed': deterministic and len(source_outputs) == expected_runs and len(target_outputs) == expected_runs,
    })
    validation = compare(source_output, target_run, target_language)
    if validation['status'] == 'passed' and not checks[-1]['passed']:
        validation.update({
            'status': 'failed',
            'failure_class': 'nondeterministic_runtime',
            'message': 'Risk-selected repeatability check failed or could not complete.',
        })
    validation['risk_level'] = risk['level']
    validation['checks'] = checks
    validation['manual_review_required'] = profile['manual_review_required']
    return validation


def _failure_fingerprint(source, validation, source_language, target_language):
    if validation.get('status') == 'passed':
        return {
            'stage': 'validation',
            'severity': 'none',
            'source_construct': 'none',
            'target_construct': target_language,
            'failure_type': 'none',
            'detected_by': 'finite I/O comparison',
            'suggested_fix': 'No failure detected.',
        }

    failure_class = validation.get('failure_class', 'unknown')
    lowered = source.lower()
    if validation.get('status') == 'not_run' or 'unsupported' in failure_class or 'syntax' in failure_class or 'goto' in lowered:
        stage = 'syntax'
        failure_type = 'unsupported_construct'
        severity = 'high'
        suggested_fix = 'Add a deterministic rule or validate an LLM fallback candidate before accepting the fragment.'
        source_construct = 'unsupported syntax' if 'goto' not in lowered else 'unstructured control flow'
    elif failure_class == 'output_mismatch':
        stage = 'semantic'
        failure_type = 'output_mismatch'
        severity = 'high'
        suggested_fix = 'Compare data-flow and API semantics; regenerate the fragment with the corrected operator or boundary condition.'
        source_construct = 'expression or loop semantics'
    elif failure_class == 'target_runtime_error':
        stage = 'runtime'
        failure_type = 'runtime_exception'
        severity = 'high'
        suggested_fix = 'Check target-language runtime differences, imports, and exception behavior.'
        source_construct = 'runtime behavior'
    else:
        stage = 'validation'
        failure_type = failure_class
        severity = 'medium'
        suggested_fix = 'Inspect the validation log and confirm target-language semantics.'
        source_construct = 'unknown'

    return {
        'stage': stage,
        'severity': severity,
        'source_construct': source_construct,
        'target_construct': target_language,
        'failure_type': failure_type,
        'detected_by': 'execution + validation',
        'suggested_fix': suggested_fix,
    }


def _rule_evolution(rule, reused=False, generalized=False):
    return {
        'learned_rule': rule,
        'reused': reused,
        'generalizes': generalized,
        'description': ('A bounded statement-pattern rule.' if generalized
                        else 'No generalized rule matched or was learned for this program.'),
    }


def _infer_identifier_types(source):
    mapping = {}
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$', stripped)
        if not match:
            continue
        name, value = match.groups()
        literal = value.strip().strip('"\'')
        if re.fullmatch(r'-?\d+', literal):
            mapping[name] = 'int'
        elif re.fullmatch(r'-?\d+\.\d+', literal):
            mapping[name] = 'float'
        elif re.fullmatch(r'".*"|\'.*\'', value.strip()):
            mapping[name] = 'string'
        else:
            mapping[name] = 'unknown'
    return mapping


def _type_map_for_pair(source_language, target_language, source):
    inferred = _infer_identifier_types(source)
    translated = {}
    for name, kind in inferred.items():
        if kind in {'int', 'float'}:
            translated[name] = 'number'
        elif kind == 'string':
            translated[name] = 'string'
        else:
            translated[name] = 'unknown'
    return {source_language: {target_language: translated}}


def _invariants_for_contract(source):
    invariants = []
    if re.search(r'\bif\b|\bfor\b|\bwhile\b', source, re.I):
        invariants.append('branch and loop conditions are preserved')
    if re.search(r'\bprint\b|\bDISPLAY\b|\bPRINT\b', source, re.I):
        invariants.append('output side effects remain observable in target runtime')
    if re.search(r'\b[A-Za-z_][A-Za-z0-9_]*\s*=\s*-?\d', source):
        invariants.append('numeric assignments remain numerically stable')
    return invariants or ['translation preserves source program behavior under tested inputs']


def _dependency_order(source):
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    seen = set()
    ordered = []
    names = set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', source))
    for line in lines:
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*=', line):
            ordered.append(line)
            seen.add(line)
    for line in lines:
        if line not in seen:
            ordered.append(line)
    return {
        'ordered_lines': ordered,
        'dependency_notes': [
            'Assignments are ordered before dependent output statements when a variable is reused.',
            f'Candidate symbols considered: {sorted(names)[:10]}',
        ],
    }


def _safe_eval_expression(expression, variables):
    try:
        parsed = ast.parse(expression, mode='eval')
        code = compile(parsed, '<expr>', 'eval')
        env = {'__builtins__': {}}
        env.update(variables)
        return eval(code, env, variables)
    except Exception:
        return None


def _property_validation(source, target_language):
    return {
        'status': 'not_run',
        'method': 'No source-input model is available to derive sound property cases.',
        'target_language': target_language,
        'generated_cases': [],
    }


def _idiomatic_refactor(target_code, target_language):
    if target_language == 'JavaScript':
        summary = 'Kept direct assignment + console output patterns because they match JavaScript idioms without unnecessary abstraction.'
    elif target_language == 'Python':
        summary = 'Kept simple assignment + print semantics because they preserve Python readability and avoid unnecessary refactoring.'
    else:
        summary = 'No forced refactor required for this target language.'
    return {
        'target_language': target_language,
        'summary': summary,
        'applied': False,
        'refactor_notes': ['This stage is intentionally conservative; it preserves correctness before styling.'],
    }


def _contract_with_metadata(source, source_language, target_language, target_code, validation):
    contract = _translation_contract(source, source_language, target_language, target_code, validation)
    contract['invariants'] = _invariants_for_contract(source)
    return contract


def _acceptance_policy(contract, risk, validation, *, unsupported=False, llm_candidate=False):
    """Apply the local output-use and learned-memory gates; not human approval."""
    failed_checks = [check['name'] for check in contract.get('checks', []) if check.get('passed') is False]
    reasons = []
    if unsupported:
        reasons.append('unsupported_source_constructs')
    if llm_candidate:
        reasons.append('model_candidate_requires_separate_review')
    if contract.get('translation_status') != 'satisfied_for_tested_inputs':
        reasons.extend(f'contract:{name}' for name in failed_checks)
        if not failed_checks:
            reasons.append(f"contract_status:{contract.get('translation_status')}")
    if validation.get('status') != 'passed':
        reasons.append(f"validation_status:{validation.get('status')}")
    if risk.get('level') == 'high':
        reasons.append('high_risk_human_review_required')
    can_use = not reasons
    can_learn = can_use and not unsupported and not llm_candidate
    return {
        'status': 'eligible_for_use_after_finite_checks' if can_use else 'blocked',
        'eligible_for_use': can_use,
        'learned_rule_storage_allowed': can_learn,
        'reasons': list(dict.fromkeys(reasons)),
        'policy_version': '1',
        'note': 'Eligibility applies only to tested inputs; it is not proof of equivalence or human approval.',
    }


def _candidate_acceptance_record(candidate, target_language, suggestion, *, source_sha256):
    """Build a fail-closed candidate acceptance record; runtime checks alone never accept."""
    syntax_ok = suggestion.get('target_syntax_valid') is True
    runtime_ok = suggestion.get('target_runtime_valid') is True
    toolchain_ok = syntax_ok and runtime_ok
    requirements = {
        'source_review': {'status': 'pending', 'evidence': None},
        'target_toolchain': {
            'status': 'passed' if toolchain_ok else 'failed' if suggestion.get('target_syntax_valid') is False or suggestion.get('target_runtime_valid') is False else 'pending',
            'target': target_language,
            'syntax_check': suggestion.get('target_syntax_valid'),
            'restricted_runtime_check': suggestion.get('target_runtime_valid') if target_language == 'JavaScript' else 'not_applicable',
            'isolated_runtime_check': suggestion.get('target_runtime_valid') if target_language == 'Python' else 'not_applicable',
            'sandbox': suggestion.get('target_runtime_sandbox'),
        },
        'independent_fixtures': {'status': 'pending', 'fixture_set_id': None, 'cases_passed': 0, 'cases_total': 0},
        'security_review': {'status': 'pending', 'reviewer': None, 'evidence': None},
        'regression_checks': {'status': 'pending', 'suite_id': None, 'passed': None},
        'human_review': {
            'status': 'pending',
            'source_reviewer': None,
            'target_reviewer': None,
            'decision': None,
        },
    }
    ready = all(item.get('status') == 'passed' for item in requirements.values())
    return {
        'accepted': False,
        'status': 'eligible_for_review' if ready else 'unaccepted_candidate',
        'source_sha256': source_sha256,
        'candidate_sha256': hashlib.sha256(candidate.encode('utf-8')).hexdigest(),
        'model': suggestion.get('model'),
        'prompt_version': suggestion.get('prompt_version'),
        'prompt_hash': suggestion.get('prompt_hash'),
        'request_id': suggestion.get('request_id'),
        'requirements': requirements,
        'blockers': [name for name, item in requirements.items() if item.get('status') != 'passed'],
        'policy': 'Acceptance requires every listed gate to pass and documented reviewer decisions; automated checks never accept a candidate.',
    }


def _is_unsupported_candidate(candidate):
    for line in (candidate or '').splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r'^(?://|#|/\*+|\*|--)\s*', '', line)
        return bool(re.match(r'UNSUPPORTED\b', line, re.IGNORECASE))
    return False


def transpile(source, source_language='Python-like', target_language='JavaScript', *, enable_llm=None, enable_learned_rules=True, store_validated_example=True):
    if source_language != 'Python-like':
        if target_language not in TARGETS:
            raise ValueError('Unsupported target language. Choose JavaScript or Python.')
        result = legacy_transpile(source_language, source, target_language)
        risk_assessment = _risk_assessment(source, source_language, target_language)
        generalized_rule = find_generalized_rule(source_language, target_language, result.ir) if enable_learned_rules else None
        generalized_code = apply_generalized_rule(generalized_rule, result.ir) if generalized_rule else None
        learned_rule_reused = bool(generalized_code and not result.unsupported)
        learned_rule = generalized_rule
        rule_is_generalized = bool(learned_rule and learned_rule.get('generalizes'))
        if not result.unsupported:
            if generalized_code:
                result.javascript = generalized_code
        fallback = create_fallback_log()
        fallback_info = fallback_status(enabled=enable_llm)
        fallback_suggestions = []
        trace = [
            {'stage':'front_end', 'status':'completed', 'detail':f'{source_language} subset tokenized, parsed and normalized.'},
            {'stage':'shared_ir', 'status':'completed', 'detail':f'{len(result.ir)} normalized IR nodes constructed.'},
            {'stage':'rule_first', 'status':'completed', 'detail':f"{result.coverage['deterministic_rules']} deterministic rule mappings emitted."},
        ]

        if result.unsupported:
            context = source[:5000]
            trace.append({'stage':'llm_fallback', 'status':'requested', 'detail':f'{len(result.unsupported)} unsupported construct(s) require review.'})
            entry = fallback.record('; '.join(result.unsupported))
            if fallback_info['configured']:
                try:
                    suggestion = translate_construct(
                        source_language,
                        target_language,
                        source,
                        context,
                        complete_program=True,
                    )
                    suggestion['source_constructs'] = result.unsupported
                    fallback_suggestions.append(suggestion)
                    entry['action'] = 'LLM produced a complete-program candidate; validation required'
                    entry['result'] = 'candidate generated; target syntax/runtime checks are reported separately'
                    entry['request_id'] = suggestion.get('request_id')
                    entry['latency_ms'] = suggestion.get('latency_ms')
                    entry['attempts'] = suggestion.get('attempts')
                    entry['model'] = suggestion.get('model')
                    entry['prompt_version'] = suggestion.get('prompt_version')
                except Exception as exc:
                    entry['action'] = 'LLM fallback failed'
                    entry['result'] = str(exc)
                    if getattr(exc, 'request_id', None):
                        entry['request_id'] = exc.request_id
                    if isinstance(getattr(exc, 'attempts', None), int):
                        entry['attempts'] = exc.attempts
                    if isinstance(getattr(exc, 'latency_ms', None), (int, float)):
                        entry['latency_ms'] = exc.latency_ms
            else:
                entry['action'] = 'LLM fallback skipped; provider not configured'
                entry['result'] = 'Set LLM_API_URL and LLM_MODEL to enable it.'
            trace[-1]['status'] = 'completed' if fallback_suggestions else 'skipped'
        else:
            trace.append({'stage':'llm_fallback', 'status':'not_needed', 'detail':'All constructs covered by deterministic rules.'})

        llm_candidate = fallback_suggestions[0].get('candidate', '').strip() if fallback_suggestions else ''
        has_llm_candidate = bool(llm_candidate) and not _is_unsupported_candidate(llm_candidate)
        deterministic_code = result.javascript
        candidate_validation_status = 'not_run'
        candidate_acceptance = None
        if fallback_suggestions:
            fallback_suggestions[0]['candidate_status'] = 'candidate_generated' if has_llm_candidate else 'unsupported_or_refused'
        if has_llm_candidate:
            result.javascript = llm_candidate

        if result.unsupported:
            if has_llm_candidate and target_language == 'JavaScript':
                from .validator import check_javascript_syntax
                syntax_result = check_javascript_syntax(result.javascript)
                if not syntax_result.get('available'):
                    fallback_suggestions[0]['target_syntax_valid'] = None
                    fallback_suggestions[0]['target_runtime_valid'] = None
                    target_run = {
                        'available': False,
                        'ok': None,
                        'output': '',
                        'error': syntax_result.get('error') or 'JavaScript syntax checker is unavailable.',
                    }
                    candidate_validation_status = 'syntax_check_unavailable'
                elif syntax_result.get('ok'):
                    fallback_suggestions[0]['target_syntax_valid'] = True
                    target_run = run_javascript(result.javascript, restricted=True)
                    fallback_suggestions[0]['target_runtime_valid'] = bool(target_run.get('available') and target_run.get('ok'))
                    if not target_run.get('available'):
                        fallback_suggestions[0]['target_runtime_valid'] = None
                        candidate_validation_status = 'runtime_unavailable'
                    else:
                        candidate_validation_status = 'runtime_valid_unverified' if target_run.get('ok') else 'rejected_runtime'
                else:
                    fallback_suggestions[0]['target_syntax_valid'] = False
                    target_run = {
                        'available': True,
                        'ok': False,
                        'output': '',
                        'error': syntax_result.get('error') or 'Target syntax validation failed.',
                    }
                    fallback_suggestions[0]['target_runtime_valid'] = None
                    candidate_validation_status = 'rejected_syntax'
            elif has_llm_candidate and target_language == 'Python':
                from .validator import check_python_syntax
                syntax_result = check_python_syntax(result.javascript)
                fallback_suggestions[0]['target_syntax_valid'] = syntax_result['ok']
                if syntax_result['ok']:
                    target_run = run_python_isolated(result.javascript)
                    fallback_suggestions[0]['target_runtime_valid'] = bool(target_run.get('available') and target_run.get('ok')) if target_run.get('available') else None
                    candidate_validation_status = ('runtime_valid_unverified' if target_run.get('ok') else
                                                   'runtime_unavailable' if not target_run.get('available') else
                                                   'rejected_runtime')
                else:
                    target_run = {'available': True, 'ok': False, 'output': '',
                                  'error': syntax_result.get('error', 'Python syntax check failed.')}
                    candidate_validation_status = 'rejected_syntax'
                    fallback_suggestions[0]['target_runtime_valid'] = None
                target_run['syntax_valid'] = syntax_result['ok']
            else:
                target_run = {
                    'available': False,
                    'ok': None,
                    'output': '',
                    'error': 'Incomplete translation was not executed.',
                }
            if fallback_suggestions:
                fallback_suggestions[0]['target_runtime_error'] = target_run.get('error', '')
                fallback_suggestions[0]['target_runtime_sandbox'] = target_run.get('sandbox')
                candidate_acceptance = _candidate_acceptance_record(
                    llm_candidate, target_language, fallback_suggestions[0],
                    source_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
                ) if has_llm_candidate else None
                fallback_suggestions[0]['accepted'] = False
                fallback_suggestions[0]['validation_status'] = candidate_validation_status
                fallback_suggestions[0]['acceptance_record'] = candidate_acceptance
                trace.append({
                    'stage': 'candidate_validation',
                    'status': candidate_validation_status,
                    'detail': 'Candidate checks are reported separately; no LLM candidate is automatically accepted.',
                })
        elif target_language == 'JavaScript':
            target_run = run_javascript(result.javascript)
        else:
            target_run = run_python(result.javascript)

        validation = {
            'status':'not_run',
            'message':'Validation requires complete deterministic source coverage; unsupported constructs need review.',
            'source_output':'', 'target_output':'', 'target_runtime':target_language,
            'failure_class':'unsupported_source_syntax',
            'risk_level': risk_assessment['level'],
            'manual_review_required': risk_assessment['validation_profile']['manual_review_required'],
        }
        if not result.unsupported:
            source_runner = lambda: '\n'.join(_run_normalized(result.source_program))
            target_runner = (lambda: run_javascript(result.javascript)) if target_language == 'JavaScript' else (lambda: run_python(result.javascript))
            source_output = source_runner()
            validation = _validate_with_risk(
                source_output, target_run, source_runner, target_runner,
                risk_assessment, target_language,
            )
        trace.append({'stage':'validation', 'status':validation['status'], 'detail':validation['message']})

        failure_fingerprint = _failure_fingerprint(source, validation, source_language, target_language)
        type_map = _type_map_for_pair(source_language, target_language, source)
        dependency_order = _dependency_order(source)
        idiomatic_refactor = _idiomatic_refactor(result.javascript, target_language)
        property_validation = _property_validation(source, target_language)
        contract = _contract_with_metadata(source, source_language, target_language, result.javascript, validation)
        acceptance = _acceptance_policy(contract, risk_assessment, validation,
                                        unsupported=bool(result.unsupported), llm_candidate=has_llm_candidate)
        if acceptance['eligible_for_use'] and store_validated_example:
            save_validated_example(source,result.javascript,result.ir,validation)
        if enable_learned_rules and acceptance['learned_rule_storage_allowed']:
            learned_rule = learn_generalized_rule(
                source_language, target_language, source, result.ir, result.javascript, contract,
            )
            rule_is_generalized = bool(learned_rule and learned_rule.get('generalizes'))
        trace.append({
            'stage': 'learned_rule',
            'status': 'reused' if learned_rule_reused else 'recorded' if learned_rule else 'not_applicable',
            'detail': 'Learned target templates are revalidated; only flat assignment/print schemas are generalized.',
        })
        rule_evolution = _rule_evolution(learned_rule, learned_rule_reused, rule_is_generalized)

        return {
            'language_support':{'source':source_language,'target':target_language,'subset':SUBSETS[source_language]},
            'tokens':result.tokens,'ir':result.ir,'symbol_table':result.symbols,
            'javascript':result.javascript,'target_code':result.javascript,
            'deterministic_code':deterministic_code,'rules_used':result.rules_used,
            'code_origin':'llm_candidate' if has_llm_candidate else 'deterministic',
            'rule_table_version':RULE_TABLE_VERSION,'rule_coverage':result.coverage,
            'fallback_log':fallback.entries,'fallback_status':fallback_info,'fallback_suggestions':fallback_suggestions,
            'validation':validation,'unsupported':result.unsupported,'notes':result.notes,
            'pipeline_trace':trace,
            'target_runtime':target_run,
            'generated_lines':len([x for x in result.javascript.splitlines() if x.strip()]),
            'translation_contract': contract,
            'acceptance_policy': acceptance,
            'candidate_acceptance': candidate_acceptance,
            'risk_assessment': risk_assessment,
            'failure_fingerprint': failure_fingerprint,
            'rule_evolution': rule_evolution,
            'learned_rule': learned_rule,
            'type_map': type_map,
            'dependency_order': dependency_order,
            'idiomatic_refactor': idiomatic_refactor,
            'property_validation': property_validation,
        }

    # Existing Python-like pipeline retained and exposed through the same response schema.
    if target_language not in ('JavaScript',):
        raise ValueError('Python-like source currently targets JavaScript in this prototype.')
    from .lexer import Lexer
    from .parser import Parser
    from .semantic import SemanticAnalyzer
    from .ir import SharedIR
    from .codegen import CodeGenerator
    from .ast_nodes import ast_to_dict
    from .interpreter import run_source
    tokens=Lexer(source).tokenize(); ast=Parser(tokens).parse(); symbols=SemanticAnalyzer().analyze(ast); ir=SharedIR(ast)
    generator=CodeGenerator(); javascript=generator.generate(ast); fallback=create_fallback_log(); source_runner=lambda: run_source(ast)
    learning_ir = _python_ast_learning_ir(ast)
    learned_rule = find_generalized_rule('Python-like', target_language, learning_ir) if enable_learned_rules and learning_ir else None
    generalized_code = apply_generalized_rule(learned_rule, learning_ir) if learned_rule else None
    learned_rule_reused = bool(generalized_code)
    if generalized_code:
        javascript = generalized_code
    risk_assessment = _risk_assessment(source, 'Python-like', target_language)
    source_output=source_runner(); target_runner=lambda: run_javascript(javascript); target=target_runner()
    validation=_validate_with_risk(source_output,target,source_runner,target_runner,risk_assessment,'JavaScript')
    def count_statement_units(statements):
        count = 0
        for statement in statements:
            count += 1
            count += count_statement_units(getattr(statement, 'body', []))
            count += count_statement_units(getattr(statement, 'else_body', []))
            for _, branch in getattr(statement, 'elifs', []):
                count += count_statement_units(branch)
        return count

    source_units=count_statement_units(ast.statements)
    coverage={
        'coverage_basis':'Python AST statement nodes emitted by the deterministic backend',
        'source_units':source_units,
        'translated_units':source_units,
        'unsupported_units':0,
        'rules_used':len(set(generator.rules_used)),
        'coverage_percent':100.0,
        'coverage_breakdown':sorted(set(generator.rules_used)),
    }
    contract = _contract_with_metadata(source, 'Python-like', target_language, javascript, validation)
    acceptance = _acceptance_policy(contract, risk_assessment, validation)
    if acceptance['eligible_for_use']:
        save_validated_example(source,javascript,ir.to_dict(),validation)
    failure_fingerprint = _failure_fingerprint(source, validation, 'Python-like', target_language)
    type_map = _type_map_for_pair('Python-like', target_language, source)
    dependency_order = _dependency_order(source)
    idiomatic_refactor = _idiomatic_refactor(javascript, target_language)
    property_validation = _property_validation(source, target_language)
    if (enable_learned_rules and learning_ir and acceptance['learned_rule_storage_allowed']):
        learned_rule = learn_generalized_rule(
            'Python-like', target_language, source, learning_ir, javascript, contract,
        )
    rule_evolution = _rule_evolution(
        learned_rule, learned_rule_reused,
        bool(learned_rule and learned_rule.get('generalizes')),
    )
    return {'language_support':{'source':'Python-like','target':'JavaScript','subset':'Existing prototype subset'},'tokens':[{'type':t.type,'value':t.value,'line':t.line,'column':t.column} for t in tokens if t.type not in ('NEWLINE','INDENT','DEDENT','EOF')],'ast':ast_to_dict(ast),'ir':ir.to_dict(),'symbol_table':symbols.as_dict(),'javascript':javascript,'target_code':javascript,'deterministic_code':javascript,'rules_used':generator.rules_used,'rule_table_version':RULE_TABLE_VERSION,'rule_coverage':coverage,'fallback_log':fallback.entries,'fallback_status':fallback_status(enabled=enable_llm),'fallback_suggestions':[],'validation':validation,'unsupported':[],'notes':['Original Python-like demonstration pipeline retained.'],'pipeline_trace':[{'stage':'front_end','status':'completed','detail':'Python-like lexer/parser/semantic analysis completed.'},{'stage':'shared_ir','status':'completed','detail':'Shared IR constructed.'},{'stage':'rule_first','status':'completed','detail':'Deterministic JavaScript code generation completed.'},{'stage':'learned_rule','status':'reused' if learned_rule_reused else 'recorded' if learned_rule else 'not_applicable','detail':'Bounded assignment/print templates are recorded only when contract and risk gates allow; reused output is revalidated.'},{'stage':'llm_fallback','status':'not_needed','detail':'No unsupported constructs in the current subset.'},{'stage':'validation','status':validation['status'],'detail':validation['message']}],'target_runtime':target,'generated_lines':len([x for x in javascript.splitlines() if x.strip()]),'translation_contract':contract,'acceptance_policy':acceptance,'candidate_acceptance':None,'risk_assessment':risk_assessment,'failure_fingerprint':failure_fingerprint,'rule_evolution':rule_evolution,'learned_rule':learned_rule,'type_map':type_map,'dependency_order':dependency_order,'idiomatic_refactor':idiomatic_refactor,'property_validation':property_validation}


def _run_normalized(nodes):
    from .legacy import run_nodes
    out=[]; run_nodes(nodes,{},out); return out


def _python_ast_learning_ir(program):
    """Expose only flat scalar assignment/print statements to the pattern learner."""
    import json
    from .ast_nodes import Assignment, Boolean, Name, Number, PrintStatement, String

    def atom_text(node):
        if isinstance(node, Number):
            return str(node.value)
        if isinstance(node, String):
            return json.dumps(node.value)
        if isinstance(node, Boolean):
            return 'True' if node.value else 'False'
        if isinstance(node, Name):
            return node.value
        return None

    nodes = []
    for statement in program.statements:
        if isinstance(statement, Assignment):
            expression = atom_text(statement.value)
            kind = 'assign'
            attributes = {'kind': kind, 'name': statement.name, 'expr': expression}
        elif isinstance(statement, PrintStatement):
            expression = atom_text(statement.expression)
            kind = 'print'
            attributes = {'kind': kind, 'expr': expression}
        else:
            return None
        if expression is None:
            return None
        nodes.append({'kind': kind, 'parent': None, 'attributes': attributes})
    return nodes or None
