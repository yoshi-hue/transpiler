from backend.benchmark import render_experiment_report, run_experiment
from backend.transpiler import transpile
from backend.main import experiment, rules_report
from backend.validator import compare


def test_basic_translation():
    result = transpile('x = 10\nprint(x)\n')
    assert 'let x = 10;' in result['javascript']
    assert 'console.log(x);' in result['javascript']
    assert result['validation']['status'] in ('passed', 'not_run')


def test_validation_accepts_equivalent_numeric_and_boolean_output():
    target = {'available': True, 'ok': True, 'output': '4', 'error': ''}
    assert compare('4.0', target)['status'] == 'passed'
    assert compare('4.1', target)['status'] == 'failed'
    assert compare('value 4.0', target)['status'] == 'failed'
    assert compare('True', {**target, 'output': 'true'})['status'] == 'passed'
    assert compare('False', {**target, 'output': 'true'})['status'] == 'failed'


def test_shared_ir_exposes_graph_metadata_and_expression_rules():
    result = transpile('x = 2\nprint(x + 1)\n')
    ir = result['ir']
    assert ir['representation'] == 'SharedIR'
    assert ir['node_count'] == len(ir['nodes'])
    assert ir['edge_count'] == len(ir['edges'])
    assert ir['scopes'] == ['global']
    assert 'arithmetic/comparison expression -> JavaScript operator' in result['rules_used']
    assert result['rule_coverage']['source_units'] == 2
    assert result['rule_coverage']['translated_units'] == 2
    assert result['rule_coverage']['coverage_percent'] == 100.0
    assert 'coverage_breakdown' in result['rule_coverage']


def test_control_flow():
    result = transpile('x = 2\nif x > 1:\n    print("yes")\nelse:\n    print("no")\n')
    assert 'if ((x > 1)) {' in result['javascript']
    assert 'console.log("yes");' in result['javascript']


def test_function():
    result = transpile('def add(a, b):\n    return a + b\n\nprint(add(2, 3))\n')
    assert 'function add(a, b)' in result['javascript']
    assert 'return (a + b);' in result['javascript']


def test_python_like_reassignment_in_control_flow_and_function_parameters():
    loop_result = transpile('i = 0\nwhile i < 2:\n    print(i)\n    i = i + 1\n')
    assert loop_result['validation']['status'] == 'passed'
    assert loop_result['javascript'].count('let i =') == 1

    branch_result = transpile('if True:\n    x = 1\nprint(x)\n')
    assert branch_result['validation']['status'] == 'passed'
    assert 'var x = 1;' in branch_result['javascript']

    parameter_result = transpile('def increment(value):\n    value = value + 1\n    return value\n\nprint(increment(1))\n')
    assert parameter_result['validation']['status'] == 'passed'
    assert 'let value =' not in parameter_result['javascript']


def test_legacy_language_validation():
    examples = {
        'COBOL': '''IDENTIFICATION DIVISION.\nPROGRAM-ID. DEMO.\nDATA DIVISION.\nWORKING-STORAGE SECTION.\n01 A PIC 999 VALUE 10.\n01 B PIC 999 VALUE 20.\nPROCEDURE DIVISION.\nCOMPUTE SUM = A + B.\nDISPLAY SUM.\nSTOP RUN.''',
        'FORTRAN': '''PROGRAM DEMO\nINTEGER :: A, B\nA = 10\nB = 20\nPRINT *, A + B\nEND PROGRAM DEMO''',
        'Pascal': '''program demo;\nvar a, b, sum: integer;\nbegin\na := 10; b := 20; sum := a + b; writeln(sum);\nend.''',
        'BASIC': '''10 LET A = 10\n20 LET B = 20\n30 PRINT A + B\n40 END''',
    }
    for language, source in examples.items():
        result = transpile(source, language, 'JavaScript')
        assert result['validation']['status'] == 'passed'
        stages = [item['stage'] for item in result['pipeline_trace']]
        assert 'validation' in stages
        assert stages[-1] == 'learned_rule'
        assert result['unsupported'] == []


def test_legacy_python_target():
    result = transpile('10 LET A = 2\n20 FOR I = 1 TO 3\n30 PRINT I\n40 NEXT I\n50 END', 'BASIC', 'Python')
    assert 'for I in range(1, (3 + 1)):' in result['javascript']
    assert result['validation']['status'] == 'passed'


def test_pascal_and_basic_equality_conditions_translate_to_python():
    examples = {
        'Pascal': 'program demo;\nvar a: integer;\nbegin\na := 0;\nif a = 0 then writeln("ok") else writeln("bad");\nend.',
        'BASIC': '10 LET A = 0\n20 IF A = 0 THEN PRINT "ok"\n30 END',
    }
    for language, source in examples.items():
        for target in ('JavaScript', 'Python'):
            result = transpile(source, language, target)
            assert result['validation']['status'] == 'passed'
            assert result['unsupported'] == []


def test_legacy_not_equal_and_ordered_comparisons():
    source = '10 LET A = 8\n20 LET B = 2\n30 IF A <> B THEN PRINT "NE"\n40 IF A <= B THEN PRINT "LE"\n50 IF A >= B THEN PRINT "GE"\n60 END'
    for target in ('JavaScript', 'Python'):
        result = transpile(source, 'BASIC', target)
        assert result['validation']['status'] == 'passed'
        assert result['unsupported'] == []


def test_unsupported_legacy_syntax_is_reported_for_fallback():
    result = transpile('10 GOTO 100\n100 END', 'BASIC', 'JavaScript')
    assert result['unsupported']
    assert result['fallback_log']
    assert result['validation']['status'] == 'not_run'
    assert result['validation']['failure_class'] == 'unsupported_source_syntax'


def test_cobol_single_line_program_is_split_into_sentences_and_translated():
    source = (
        'IDENTIFICATION DIVISION. PROGRAM-ID. DEMO. DATA DIVISION. '
        'WORKING-STORAGE SECTION. 01 A PIC 999 VALUE 10. '
        'PROCEDURE DIVISION. DISPLAY "VERSION 1.2". STOP RUN.'
    )

    result = transpile(source, 'COBOL', 'JavaScript')

    assert result['unsupported'] == []
    assert result['validation']['status'] == 'passed'
    assert result['validation']['target_output'] == 'VERSION 1.2'
    assert result['code_origin'] == 'deterministic'


def test_cobol_single_line_unsupported_statement_is_not_silently_accepted(monkeypatch):
    monkeypatch.setenv('LLM_API_URL', '')
    monkeypatch.setenv('LLM_MODEL', '')
    monkeypatch.setenv('LLM_API_KEY', '')
    source = 'IDENTIFICATION DIVISION. PROGRAM-ID. DEMO. PROCEDURE DIVISION. CALL "EXTERNAL-ROUTINE". STOP RUN.'

    result = transpile(source, 'COBOL', 'JavaScript')

    assert result['unsupported'] == ['CALL "EXTERNAL-ROUTINE"']
    assert result['validation']['status'] == 'not_run'
    assert result['validation']['failure_class'] == 'unsupported_source_syntax'
    assert result['code_origin'] == 'deterministic'


def test_cobol_unrecognized_data_division_line_is_reported_unsupported(monkeypatch):
    monkeypatch.setenv('LLM_API_URL', '')
    monkeypatch.setenv('LLM_MODEL', '')
    monkeypatch.setenv('LLM_API_KEY', '')
    source = '''IDENTIFICATION DIVISION.
PROGRAM-ID. DEMO.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 A PIC X(20).
PROCEDURE DIVISION.
STOP RUN.'''

    result = transpile(source, 'COBOL', 'JavaScript')

    assert result['unsupported'] == ['01 A PIC X(20)']
    assert result['validation']['status'] == 'not_run'


def test_llm_fallback_example_records_unaccepted_construct(monkeypatch):
    monkeypatch.setenv('LLM_API_URL', '')
    monkeypatch.setenv('LLM_MODEL', '')
    monkeypatch.setenv('LLM_API_KEY', '')
    result = transpile('10 GOTO 100\n20 PRINT "needs fallback"\n100 END', 'BASIC', 'JavaScript')
    assert result['unsupported']
    assert result['fallback_log'][0]['action'].startswith('LLM fallback')
    assert result['validation']['status'] == 'not_run'


def test_llm_fallback_generates_and_restrictedly_runs_a_complete_program(monkeypatch):
    import backend.transpiler as transpiler_module

    source = '''IDENTIFICATION DIVISION.
PROGRAM-ID. EXT-LOOP.
PROCEDURE DIVISION.
PERFORM 3 TIMES
 DISPLAY "STEP"
END-PERFORM.
STOP RUN.'''
    candidate = 'for (let i = 0; i < 3; i++) { console.log("STEP"); }'
    called = {}

    def fake_translate(source_language, target_language, construct, context, *, complete_program=False):
        called.update({
            'source_language': source_language,
            'target_language': target_language,
            'construct': construct,
            'context': context,
            'complete_program': complete_program,
        })
        return {
            'candidate': candidate,
            'accepted': False,
            'validation_status': 'not_run',
            'request_id': 'test-request',
            'latency_ms': 1,
            'model': 'test-model',
            'prompt_version': 'test-prompt',
        }

    monkeypatch.setenv('LLM_API_URL', 'https://example.com/v1/chat/completions')
    monkeypatch.setenv('LLM_MODEL', 'test-model')
    monkeypatch.setattr(transpiler_module, 'translate_construct', fake_translate)

    result = transpiler_module.transpile(source, 'COBOL', 'JavaScript')

    assert result['javascript'] == candidate
    assert called['construct'] == source
    assert called['complete_program'] is True
    assert result['target_runtime']['ok'] is True
    assert result['target_runtime']['output'] == 'STEP\nSTEP\nSTEP'
    assert result['fallback_suggestions'][0]['target_runtime_valid'] is True
    assert result['fallback_suggestions'][0]['accepted'] is False
    assert result['validation']['status'] == 'not_run'
    assert result['candidate_acceptance']['accepted'] is False
    assert result['candidate_acceptance']['requirements']['target_toolchain']['status'] == 'passed'
    assert result['candidate_acceptance']['requirements']['independent_fixtures']['status'] == 'pending'


def test_python_llm_candidate_uses_isolated_runner_and_fails_closed_without_docker(monkeypatch):
    import backend.transpiler as transpiler_module

    monkeypatch.setenv('LLM_API_URL', 'https://example.com/v1/chat/completions')
    monkeypatch.setenv('LLM_MODEL', 'test-model')
    monkeypatch.setattr(
        transpiler_module,
        'run_python_isolated',
        lambda _code: {
            'available': False,
            'ok': None,
            'output': '',
            'error': 'Docker is required for isolated Python candidate execution.',
        },
    )
    monkeypatch.setattr(
        transpiler_module,
        'translate_construct',
        lambda *args, **kwargs: {
            'candidate': 'for i in range(3):\n    print("STEP")',
            'accepted': False,
            'validation_status': 'not_run',
        },
    )

    result = transpiler_module.transpile('10 GOTO 100\n100 END', 'BASIC', 'Python')

    suggestion = result['fallback_suggestions'][0]
    assert suggestion['target_syntax_valid'] is True
    assert suggestion['target_runtime_valid'] is None
    assert result['target_runtime']['available'] is False
    assert result['target_runtime']['ok'] is None
    assert 'Docker is required' in result['target_runtime']['error']
    assert result['candidate_acceptance']['accepted'] is False
    assert 'target_toolchain' in result['candidate_acceptance']['blockers']
    assert 'independent_fixtures' in result['candidate_acceptance']['blockers']
    assert 'security_review' in result['candidate_acceptance']['blockers']
    assert 'regression_checks' in result['candidate_acceptance']['blockers']
    assert 'human_review' in result['candidate_acceptance']['blockers']


def test_python_isolated_runner_does_not_fall_back_to_host(monkeypatch):
    from backend.validator import run_python_isolated
    monkeypatch.setattr('backend.validator.shutil.which', lambda _name: None)
    result = run_python_isolated('print("candidate")')
    assert result['available'] is False
    assert result['ok'] is None
    assert 'Docker is required' in result['error']


def test_candidate_acceptance_record_fails_closed_even_after_runtime_pass():
    from backend.transpiler import _candidate_acceptance_record
    record = _candidate_acceptance_record(
        'console.log("ok");', 'JavaScript',
        {'target_syntax_valid': True, 'target_runtime_valid': True,
         'model': 'fixture-model', 'prompt_version': 'fixture-prompt'},
        source_sha256='source-hash',
    )
    assert record['accepted'] is False
    assert record['requirements']['target_toolchain']['status'] == 'passed'
    assert set(record['blockers']) == {'source_review', 'independent_fixtures', 'security_review', 'regression_checks', 'human_review'}


def test_provider_trial_is_reproducible_and_reports_missing_configuration(monkeypatch, tmp_path):
    from tools.run_llm_provider_trial import run_trial
    monkeypatch.setenv('LLM_API_URL', '')
    monkeypatch.setenv('LLM_MODEL', '')
    monkeypatch.setenv('LLM_API_KEY', '')
    report = run_trial('JavaScript')
    assert report['status'] == 'not_configured'
    assert report['trial_id'] == 'cobol-perform-three-times-v1'
    assert report['candidate_accepted'] is False
    assert len(report['source_sha256']) == 64


def test_restricted_llm_javascript_execution_hides_secrets_and_blocks_file_access(monkeypatch):
    from backend.validator import run_javascript

    monkeypatch.setenv('LLM_API_KEY', 'must-not-reach-generated-code')
    result = run_javascript(
        'console.log(process.env.LLM_API_KEY || "NO_SECRET");',
        restricted=True,
    )
    assert result['ok'] is True
    assert result['output'] == 'NO_SECRET'

    blocked = run_javascript(
        'require("fs").readFileSync(process.cwd() + "/.env", "utf8");',
        restricted=True,
    )
    assert blocked['ok'] is False
    assert 'permission' in blocked['error'].lower()


def test_experiment_summary_reports_rule_and_hybrid_breakdown():
    report = run_experiment(
        'JavaScript',
        cases=[('BASIC', 'arithmetic', '10 LET A = 4\n20 LET B = 6\n30 PRINT A + B\n40 END')],
    )
    assert report['rule_only']['total'] == 1
    assert report['hybrid']['total'] == 1
    assert 'summary' in report
    assert 'by_language' in report['summary']
    assert 'llm_latency_ms' in report['hybrid']['metrics']


def test_experiment_report_renders_publication_summary():
    report = run_experiment(
        'JavaScript',
        cases=[('BASIC', 'arithmetic', '10 LET A = 4\n20 LET B = 6\n30 PRINT A + B\n40 END')],
        repeats=1,
    )
    text = render_experiment_report(report)
    assert 'Rule-only' in text
    assert 'Hybrid' in text
    assert 'Fallback frequency' in text


def test_experiment_endpoint_exposes_controlled_ablation(monkeypatch):
    monkeypatch.setenv('LLM_API_URL', '')
    monkeypatch.setenv('LLM_MODEL', '')
    monkeypatch.setenv('LLM_API_KEY', '')
    response = experiment('JavaScript', repeats=1)
    assert response['ok'] is True
    assert response['rule_only']['total'] == response['hybrid']['total']
    assert response['rule_only']['total'] == response['contracts_risk_learned_rules']['total']
    assert response['summary']['overall']['delta_success_rate_percent'] >= 0
    assert 'LLM fallback' in response['ablation_scope']['compared_component']
    assert response['ablation_scope']['shared_mechanisms']
    assert response['hybrid']['accepted_llm_candidates'] == 0
    assert 'human reviewer effort' in response['ablation_scope']['candidate_acceptance']


def test_experiment_counts_candidate_only_when_independent_oracle_matches(monkeypatch):
    import backend.benchmark as benchmark_module

    metadata = {
        'required_constructs': ['loop', 'output'],
        'expected_output': 'STEP\nSTEP\nSTEP',
        'expected_outcome': 'unsupported',
        'provenance': {'task': 'test oracle'},
    }
    result = {
        'validation': {'status': 'not_run', 'failure_class': 'unsupported_source_syntax'},
        'fallback_log': [{
            'action': 'LLM produced a complete-program candidate; validation required',
            'latency_ms': 12,
        }],
        'fallback_suggestions': [{'target_runtime_valid': True}],
        'fallback_status': {'configured': True},
        'target_runtime': {'available': True, 'ok': True, 'output': 'STEP\nSTEP\nSTEP'},
        'unsupported': ['PERFORM 3 TIMES'],
        'rule_coverage': {'coverage_percent': 0},
        'rules_used': [],
        'generated_lines': 3,
    }
    monkeypatch.setattr(benchmark_module, '_case_metadata', lambda *args: metadata)
    monkeypatch.setattr(benchmark_module, 'transpile', lambda *args, **kwargs: result)

    case = benchmark_module._case_result(
        'COBOL',
        'fallback-oracle-case',
        'source',
        'JavaScript',
        enable_llm=True,
    )

    assert case['candidate_oracle_match'] is True
    assert case['gold_output_match'] is None
    assert case['accepted_llm_candidates'] == 0
    assert case['status'] == 'not_run'

    result['target_runtime']['output'] = 'WRONG'
    failed_case = benchmark_module._case_result(
        'COBOL',
        'fallback-oracle-case',
        'source',
        'JavaScript',
        enable_llm=True,
    )
    assert failed_case['candidate_oracle_match'] is False
    assert failed_case['accepted_llm_candidates'] == 0


def test_experiment_summary_counts_python_candidate_runtime_as_not_run():
    from backend.benchmark import _summarize_variant

    summary = _summarize_variant([{
        'language': 'COBOL',
        'case': 'python-candidate',
        'status': 'not_run',
        'candidate_generated': 1,
        'candidate_syntax_valid': 1,
        'candidate_runtime_valid': 0,
        'candidate_runtime_checked': 0,
        'candidate_runtime_not_run': 1,
        'required_construct_coverage': {'total': 0, 'covered_count': 0},
    }], 'hybrid')

    assert summary['candidate_runtime_valid'] == 0
    assert summary['candidate_runtime_checked'] == 0
    assert summary['candidate_runtime_not_run'] == 1
    assert summary['by_language']['COBOL']['candidate_runtime_not_run'] == 1


def test_rules_endpoint_exposes_json_coverage_report():
    payload = rules_report()
    assert payload['ok'] is True
    assert payload['catalogue_entries'] >= 35
    assert payload['rule_table_version'] == '1.3'
    assert payload['is_executable_coverage_measure'] is False
    assert 'family_counts' in payload
    assert payload['rules'][0]['source']
    assert payload['status_counts']['unsupported'] == 1


def test_experiment_endpoint_rejects_invalid_repeat_count():
    response = experiment('JavaScript', repeats=11)
    assert response == {'ok': False, 'error': 'Repeats must be between 1 and 10.'}


def test_benchmark_covers_translation_and_expected_unsupported_outcomes():
    from backend.benchmark import run_benchmark
    report = run_benchmark('JavaScript')
    assert report['total'] == 20
    assert report['external_task_derived_cases'] == 20
    assert report['development_cases_excluded'] == 16
    assert report['passed'] == 17
    assert report['success_rate_percent'] < 100.0
    assert report['success_rate_95ci_percent'][0] < report['success_rate_percent']
    assert report['expected_outcome_match_rate_percent'] == 100.0
    assert report['gold_output_accuracy_percent'] == 100.0
    assert report['gold_output_cases'] == 17
    assert report['unsupported_cases_expected'] == 3
    assert report['unsupported_recognition_rate_percent'] == 100.0
    external = [case for case in report['cases'] if case.get('source_reference')]
    assert len(external) == 20
    assert all(case['source_reference']['url'].startswith('https://') for case in external)
    assert all(case['split'] == 'test' for case in report['cases'])
    assert len({case['split_group'] for case in report['cases']}) == 2


def test_translation_contract_is_generated_for_valid_translation():
    result = transpile('x = 2\nprint(x + 1)\n')
    contract = result['translation_contract']
    assert contract['function'] == 'program'
    assert contract['output'] == 'number|string'
    assert 'source_api' in contract
    assert contract['translation_status'] in ('satisfied_for_tested_inputs', 'pending', 'review_required')
    assert contract['confidence'] is None
    assert contract['confidence_basis'] == 'not calibrated'
    assert result['acceptance_policy']['eligible_for_use'] is True
    assert result['acceptance_policy']['learned_rule_storage_allowed'] is True


def test_contract_failure_and_high_risk_block_eligibility_and_rule_storage():
    from backend.transpiler import _acceptance_policy
    valid_contract = {'translation_status': 'satisfied_for_tested_inputs', 'checks': []}
    passed = {'status': 'passed'}
    medium = {'level': 'medium'}
    failed_contract = {'translation_status': 'failed', 'checks': [{'name': 'finite_stdout_matches_source_oracle', 'passed': False}]}
    blocked = _acceptance_policy(failed_contract, medium, passed)
    assert blocked['eligible_for_use'] is False
    assert blocked['learned_rule_storage_allowed'] is False
    assert 'contract:finite_stdout_matches_source_oracle' in blocked['reasons']
    high = _acceptance_policy(valid_contract, {'level': 'high'}, passed)
    assert high['eligible_for_use'] is False
    assert high['learned_rule_storage_allowed'] is False
    assert 'high_risk_human_review_required' in high['reasons']
    unsupported = _acceptance_policy(valid_contract, medium, passed, unsupported=True)
    assert unsupported['learned_rule_storage_allowed'] is False


def test_risk_assessment_and_failure_fingerprint_are_exposed():
    result = transpile('10 GOTO 100\n100 END', 'BASIC', 'JavaScript')
    risk = result['risk_assessment']
    assert risk['score'] >= 0
    assert risk['level'] in ('low', 'medium', 'high')
    assert result['failure_fingerprint']['stage'] in ('syntax', 'unsupported')


def test_one_example_reuses_only_same_ordered_schema_not_arbitrary_program(monkeypatch, tmp_path):
    from backend import learned_rules
    monkeypatch.setattr(learned_rules, 'RULE_STORE', tmp_path / 'learned_rules.jsonl')
    first = transpile('10 LET A = 10\n20 PRINT A', 'BASIC', 'JavaScript')
    second = transpile('10 LET B = 27\n20 PRINT B', 'BASIC', 'JavaScript')
    assert first['validation']['status'] == 'passed'
    assert first['learned_rule']['generalizes'] is False
    assert first['learned_rule']['status'] == 'experimental_exact_schema'
    assert second['rule_evolution']['reused'] is True
    assert second['javascript'] == 'let B = 27;\nconsole.log(B);'
    assert second['validation']['status'] == 'passed'
    assert second['translation_contract']['checks']
    assert len(second['learned_rule']['examples']) == 2
    different_shape = transpile('10 LET C = 27\n20 LET D = 4\n30 PRINT C', 'BASIC', 'JavaScript')
    assert different_shape['rule_evolution']['reused'] is False
    assert different_shape['code_origin'] == 'deterministic'


def test_python_like_same_schema_template_is_revalidated(monkeypatch, tmp_path):
    from backend import learned_rules
    monkeypatch.setattr(learned_rules, 'RULE_STORE', tmp_path / 'learned_rules.jsonl')
    first = transpile('value = 3\nprint(value)\n')
    second = transpile('count = 8\nprint(count)\n')
    assert first['learned_rule']['generalizes'] is False
    assert second['rule_evolution']['reused'] is True
    assert second['javascript'] == 'let count = 8;\nconsole.log(count);'
    assert second['validation']['status'] == 'passed'


def test_learned_rule_rejects_schema_mismatch_and_stale_or_malformed_rule(monkeypatch, tmp_path):
    from backend import learned_rules
    monkeypatch.setattr(learned_rules, 'RULE_STORE', tmp_path / 'learned_rules.jsonl')
    first = transpile('10 LET A = 10\n20 PRINT A', 'BASIC', 'JavaScript')
    rule = first['learned_rule']
    parsed = __import__('backend.legacy', fromlist=['legacy_transpile']).legacy_transpile(
        'BASIC', '10 LET A = 10\n20 PRINT A\n30 PRINT A', 'JavaScript')
    assert learned_rules.apply_generalized_rule(rule, parsed.ir) is None
    stale = dict(rule, learner_schema_version=-1)
    assert learned_rules.apply_generalized_rule(stale, first['ir']) is None
    malformed = dict(rule, target_templates=['console.log({{expr}});'] * len(first['ir']))
    assert learned_rules.apply_generalized_rule(malformed, first['ir']) is None


def test_ambiguous_or_unsupported_schema_is_not_learned():
    from backend.learned_rules import _schema_from_ir
    assert _schema_from_ir([{'kind': 'assign', 'parent': None, 'attributes': {'name':'x', 'expr':'x'}}]) is None
    assert _schema_from_ir([{'kind': 'call', 'parent': None, 'attributes': {'expr':'1'}}]) is None


def test_pattern_learner_refuses_compound_expressions(monkeypatch, tmp_path):
    from backend import learned_rules
    monkeypatch.setattr(learned_rules, 'RULE_STORE', tmp_path / 'learned_rules.jsonl')
    result = transpile('10 LET A = 10 + 2\n20 PRINT A', 'BASIC', 'JavaScript')
    assert result['validation']['status'] == 'passed'
    assert result['learned_rule'] is None


def test_high_risk_profile_requires_review_and_selects_repeated_checks():
    result = transpile('10 GOTO 100\n100 END', 'BASIC', 'JavaScript')
    risk = result['risk_assessment']
    assert risk['level'] == 'high'
    assert risk['validation_profile']['runtime_runs'] == 3
    assert risk['validation_profile']['manual_review_required'] is True
    assert result['acceptance_policy']['eligible_for_use'] is False
    assert result['acceptance_policy']['learned_rule_storage_allowed'] is False


def test_medium_risk_validation_repeats_source_and_target():
    from backend.transpiler import _risk_assessment, _validate_with_risk
    risk = _risk_assessment('while x < 2', 'Python-like', 'JavaScript')
    calls = {'source': 0, 'target': 0}

    def source_runner():
        calls['source'] += 1
        return '2'

    def target_runner():
        calls['target'] += 1
        return {'available': True, 'ok': True, 'output': '2', 'error': ''}

    validation = _validate_with_risk(
        '2', {'available': True, 'ok': True, 'output': '2', 'error': ''},
        source_runner, target_runner, risk, 'JavaScript',
    )
    assert risk['level'] == 'medium'
    assert calls == {'source': 1, 'target': 1}
    assert validation['status'] == 'passed'
    assert validation['checks'][0]['target_runs_completed'] == 2


def test_low_medium_high_risk_selects_one_two_three_runs():
    from backend.transpiler import _risk_assessment
    low = _risk_assessment('x = 1', 'Python-like', 'JavaScript')
    medium = _risk_assessment('while x < 2', 'Python-like', 'JavaScript')
    high = _risk_assessment('goto 10 call foo open file', 'BASIC', 'JavaScript')
    assert [low['validation_profile']['runtime_runs'], medium['validation_profile']['runtime_runs'], high['validation_profile']['runtime_runs']] == [1, 2, 3]


def test_type_mapping_and_contract_propagation_are_exposed():
    result = transpile('x = 2\nprint(x + 1)\n')
    assert 'type_map' in result
    assert 'invariants' in result['translation_contract']
    assert result['type_map']['Python-like']['JavaScript']['x'] in {'int', 'number'}


def test_dependency_order_and_idiomatic_refactor_are_applied():
    result = transpile('x = 2\nprint(x + 1)\n')
    assert 'dependency_order' in result
    assert 'idiomatic_refactor' in result
    assert result['idiomatic_refactor']['target_language'] in {'JavaScript', 'Python'}


def test_property_based_validation_is_exposed_for_numeric_programs():
    result = transpile('x = 2\nprint(x + 1)\n')
    assert 'property_validation' in result
    assert result['property_validation']['status'] == 'not_run'
    assert result['property_validation']['generated_cases'] == []


def test_llm_status_rejects_placeholder_credentials(monkeypatch):
    monkeypatch.setenv('LLM_API_URL', 'https://example.com/v1/chat/completions')
    monkeypatch.setenv('LLM_MODEL', 'gpt-4o-mini')
    monkeypatch.setenv('LLM_API_KEY', 'your_provider_api_key_here')
    from backend.llm_fallback import fallback_status

    status = fallback_status()
    assert status['configured'] is False
    assert status['key_set'] is False


def test_llm_fallback_sends_configured_key_as_bearer_token(monkeypatch):
    monkeypatch.setenv('LLM_API_KEY', 'gemini-test-key')
    from backend.llm_fallback import _headers

    assert _headers()['Authorization'] == 'Bearer gemini-test-key'
