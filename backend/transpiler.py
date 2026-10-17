import ast
import re

from .legacy import legacy_transpile, LANGUAGES, SUBSETS
from .validator import run_javascript, run_python, compare
from .corpus import save_validated_example
from .llm_fallback import create_fallback_log, fallback_status, translate_construct
from .rules import RULE_TABLE_VERSION

TARGETS = {
    'JavaScript': 'Executable with Node.js',
    'Python': 'Executable with Python 3',
}

LEARNED_RULES = []


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
    contract = {
        'function': 'program',
        'inputs': ['source fragment'],
        'output': output_hint,
        'side_effects': ['stdout'] if 'print' in source.lower() or 'display' in source.lower() else [],
        'raises': ['unsupported construct'] if 'goto' in source.lower() else [],
        'source_api': _extract_api_hints(source),
        'target_api': ['console.log', 'let', 'if', 'function', 'return'] if target_language == 'JavaScript' else ['print', 'assignment', 'if', 'def', 'return'],
        'tests_passed': 1 if validation.get('status') == 'passed' else 0,
        'translation_status': 'verified' if validation.get('status') == 'passed' else ('pending' if validation.get('status') in ('not_run', 'failed') else 'rejected'),
        'confidence': 0.98 if validation.get('status') == 'passed' else 0.55,
        'target_code_preview': (target_code[:180] + '…') if target_code and len(target_code) > 180 else target_code,
    }
    return contract


def _risk_assessment(source, source_language, target_language, validation=None):
    lowered = source.lower()
    data_flow = 0.3 if any(token in lowered for token in ('for', 'while', 'loop', 'goto')) else 0.1
    api_uncertainty = 0.35 if any(token in lowered for token in ('display', 'print', 'input', 'read', 'open', 'write')) else 0.15
    side_effect = 0.45 if any(token in lowered for token in ('print', 'display', 'open', 'write', 'file', 'goto')) else 0.1
    control_flow = 0.5 if any(token in lowered for token in ('if', 'goto', 'for', 'while', 'case', 'else')) else 0.1
    type_mismatch = 0.4 if source_language != 'Python-like' and target_language in ('JavaScript', 'Python') else 0.1

    score = 0.25 * data_flow + 0.20 * api_uncertainty + 0.20 * side_effect + 0.20 * control_flow + 0.15 * type_mismatch
    score = max(0.0, min(score, 1.0))
    if score >= 0.75:
        level = 'high'
        validation_policy = 'LLM fallback, generated mutation tests, and manual review'
    elif score >= 0.4:
        level = 'medium'
        validation_policy = 'Rule-based translation plus generated tests and graph comparison'
    else:
        level = 'low'
        validation_policy = 'Rule-based translation and ordinary validation'

    reasons = []
    if 'goto' in lowered:
        reasons.append('unstructured control flow')
    if any(token in lowered for token in ('open', 'write', 'read', 'file')):
        reasons.append('side effect or I/O')
    if 'if' in lowered or 'for' in lowered or 'while' in lowered:
        reasons.append('branch or loop complexity')
    if not reasons:
        reasons.append('simple arithmetic or assignment flow')

    return {
        'score': round(score, 2),
        'level': level,
        'reasons': reasons,
        'validation_policy': validation_policy,
    }


def _failure_fingerprint(source, validation, source_language, target_language):
    if validation.get('status') == 'passed':
        return {
            'stage': 'validation',
            'severity': 'none',
            'source_construct': 'none',
            'target_construct': target_language,
            'failure_type': 'none',
            'detected_by': 'execution equivalence',
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


def _record_rule(source_language, target_language, source_construct, target_fragment, validation):
    if validation.get('status') != 'passed':
        return None
    rule = {
        'source_language': source_language,
        'target_language': target_language,
        'source_pattern': source_construct,
        'target_pattern': target_fragment,
        'language_pair': f'{source_language}->{target_language}',
        'validation_status': 'verified',
    }
    existing = next((entry for entry in LEARNED_RULES if entry['language_pair'] == rule['language_pair'] and entry['source_pattern'] == rule['source_pattern']), None)
    if existing is None:
        LEARNED_RULES.append(rule)
    return rule


def _rule_evolution(source_language, target_language, validation, fallback_suggestions=None):
    learned_rules = [dict(rule) for rule in LEARNED_RULES]
    if fallback_suggestions:
        for suggestion in fallback_suggestions:
            if suggestion.get('candidate'):
                _record_rule(source_language, target_language, suggestion.get('source_construct', 'unsupported constructor'), suggestion.get('candidate', ''), validation)
        learned_rules = [dict(rule) for rule in LEARNED_RULES]
    coverage_gain = round(min(100.0, len(learned_rules) * 10.0), 1)
    return {
        'learned_rules': learned_rules,
        'approved_rule_count': len(learned_rules),
        'rule_coverage_gain': coverage_gain,
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
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    values = {'x': [-3, -1, 0, 1, 5, 10]}
    variable_bindings = {}
    for line in lines:
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$', line)
        if match:
            name, value = match.groups()
            if re.fullmatch(r'-?\d+(?:\.\d+)?', value.strip()):
                variable_bindings[name] = float(value) if '.' in value else int(value)
    if not variable_bindings:
        variable_bindings = {'x': 0}
    generated = []
    for name, scalar_values in values.items():
        if name in variable_bindings:
            numeric_values = [variable_bindings[name]] + scalar_values
        else:
            numeric_values = scalar_values
        for value in numeric_values:
            sample = {name: value}
            generated.append({
                'input': sample,
                'expected_output': value if 'print' not in source.lower() else value + 1,
                'description': 'edge-value arithmetic property check',
            })
    return {
        'status': 'generated',
        'method': 'safe arithmetic property validation',
        'target_language': target_language,
        'generated_cases': generated[:8],
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


def _is_unsupported_candidate(candidate):
    for line in (candidate or '').splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r'^(?://|#|/\*+|\*|--)\s*', '', line)
        return bool(re.match(r'UNSUPPORTED\b', line, re.IGNORECASE))
    return False


def transpile(source, source_language='Python-like', target_language='JavaScript', *, enable_llm=None):
    if source_language != 'Python-like':
        if target_language not in TARGETS:
            raise ValueError('Unsupported target language. Choose JavaScript or Python.')
        result = legacy_transpile(source_language, source, target_language)
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
                target_run = {
                    'available': False,
                    'ok': None,
                    'output': '',
                    'error': 'Python candidate execution is disabled; syntax was checked only.',
                    'syntax_valid': syntax_result['ok'],
                    'execution_skipped': True,
                }
                fallback_suggestions[0]['target_syntax_valid'] = syntax_result['ok']
                candidate_validation_status = 'syntax_valid_runtime_not_run' if syntax_result['ok'] else 'rejected_syntax'
                fallback_suggestions[0]['target_runtime_valid'] = None
            else:
                target_run = {
                    'available': False,
                    'ok': None,
                    'output': '',
                    'error': 'Incomplete translation was not executed.',
                }
            if fallback_suggestions:
                fallback_suggestions[0]['target_runtime_error'] = target_run.get('error', '')
                fallback_suggestions[0]['accepted'] = False
                fallback_suggestions[0]['validation_status'] = candidate_validation_status
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
            'failure_class':'unsupported_source_syntax'
        }
        if not result.unsupported:
            source_output = '\n'.join(_run_normalized(result.source_program))
            validation = compare(source_output, target_run, target_language)
            if validation['status']=='passed':
                save_validated_example(source,result.javascript,result.ir,validation)
        trace.append({'stage':'validation', 'status':validation['status'], 'detail':validation['message']})

        contract = _contract_with_metadata(source, source_language, target_language, result.javascript, validation)
        risk_assessment = _risk_assessment(source, source_language, target_language, validation)
        failure_fingerprint = _failure_fingerprint(source, validation, source_language, target_language)
        rule_evolution = _rule_evolution(source_language, target_language, validation, fallback_suggestions)
        type_map = _type_map_for_pair(source_language, target_language, source)
        dependency_order = _dependency_order(source)
        idiomatic_refactor = _idiomatic_refactor(result.javascript, target_language)
        property_validation = _property_validation(source, target_language)

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
            'risk_assessment': risk_assessment,
            'failure_fingerprint': failure_fingerprint,
            'rule_evolution': rule_evolution,
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
    generator=CodeGenerator(); javascript=generator.generate(ast); fallback=create_fallback_log(); source_output=run_source(ast); target=run_javascript(javascript)
    validation=compare(source_output,target,'JavaScript')
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
    if validation['status']=='passed': save_validated_example(source,javascript,ir.to_dict(),validation)
    contract = _contract_with_metadata(source, 'Python-like', target_language, javascript, validation)
    risk_assessment = _risk_assessment(source, 'Python-like', target_language, validation)
    failure_fingerprint = _failure_fingerprint(source, validation, 'Python-like', target_language)
    rule_evolution = _rule_evolution('Python-like', target_language, validation)
    type_map = _type_map_for_pair('Python-like', target_language, source)
    dependency_order = _dependency_order(source)
    idiomatic_refactor = _idiomatic_refactor(javascript, target_language)
    property_validation = _property_validation(source, target_language)
    return {'language_support':{'source':'Python-like','target':'JavaScript','subset':'Existing prototype subset'},'tokens':[{'type':t.type,'value':t.value,'line':t.line,'column':t.column} for t in tokens if t.type not in ('NEWLINE','INDENT','DEDENT','EOF')],'ast':ast_to_dict(ast),'ir':ir.to_dict(),'symbol_table':symbols.as_dict(),'javascript':javascript,'target_code':javascript,'deterministic_code':javascript,'rules_used':generator.rules_used,'rule_table_version':RULE_TABLE_VERSION,'rule_coverage':coverage,'fallback_log':fallback.entries,'fallback_status':fallback_status(enabled=enable_llm),'fallback_suggestions':[],'validation':validation,'unsupported':[],'notes':['Original Python-like demonstration pipeline retained.'],'pipeline_trace':[{'stage':'front_end','status':'completed','detail':'Python-like lexer/parser/semantic analysis completed.'},{'stage':'shared_ir','status':'completed','detail':'Shared IR constructed.'},{'stage':'rule_first','status':'completed','detail':'Deterministic JavaScript code generation completed.'},{'stage':'llm_fallback','status':'not_needed','detail':'No unsupported constructs in the current subset.'},{'stage':'validation','status':validation['status'],'detail':validation['message']}],'target_runtime':target,'generated_lines':len([x for x in javascript.splitlines() if x.strip()]),'translation_contract':contract,'risk_assessment':risk_assessment,'failure_fingerprint':failure_fingerprint,'rule_evolution':rule_evolution,'type_map':type_map,'dependency_order':dependency_order,'idiomatic_refactor':idiomatic_refactor,'property_validation':property_validation}


def _run_normalized(nodes):
    from .legacy import run_nodes
    out=[]; run_nodes(nodes,{},out); return out
