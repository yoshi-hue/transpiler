from backend.benchmark import render_experiment_report, run_experiment
from backend.transpiler import transpile
from backend.main import experiment


def test_basic_translation():
    result = transpile('x = 10\nprint(x)\n')
    assert 'let x = 10;' in result['javascript']
    assert 'console.log(x);' in result['javascript']
    assert result['validation']['status'] in ('passed', 'not_run')


def test_shared_ir_exposes_graph_metadata_and_expression_rules():
    result = transpile('x = 2\nprint(x + 1)\n')
    ir = result['ir']
    assert ir['representation'] == 'SharedIR'
    assert ir['node_count'] == len(ir['nodes'])
    assert ir['edge_count'] == len(ir['edges'])
    assert ir['scopes'] == ['global']
    assert 'arithmetic/comparison expression -> JavaScript operator' in result['rules_used']
    assert result['rule_coverage']['rules_available'] >= 12


def test_control_flow():
    result = transpile('x = 2\nif x > 1:\n    print("yes")\nelse:\n    print("no")\n')
    assert 'if ((x > 1)) {' in result['javascript']
    assert 'console.log("yes");' in result['javascript']


def test_function():
    result = transpile('def add(a, b):\n    return a + b\n\nprint(add(2, 3))\n')
    assert 'function add(a, b)' in result['javascript']
    assert 'return (a + b);' in result['javascript']


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
        assert result['pipeline_trace'][-1]['stage'] == 'validation'
        assert result['unsupported'] == []


def test_legacy_python_target():
    result = transpile('10 LET A = 2\n20 FOR I = 1 TO 3\n30 PRINT I\n40 NEXT I\n50 END', 'BASIC', 'Python')
    assert 'for I in range(1, (3 + 1)):' in result['javascript']
    assert result['validation']['status'] == 'passed'


def test_unsupported_legacy_syntax_is_reported_for_fallback():
    result = transpile('10 GOTO 100\n100 END', 'BASIC', 'JavaScript')
    assert result['unsupported']
    assert result['fallback_log']
    assert result['validation']['status'] == 'not_run'
    assert result['validation']['failure_class'] == 'unsupported_source_syntax'


def test_llm_fallback_example_records_unaccepted_construct():
    result = transpile('10 GOTO 100\n20 PRINT "needs fallback"\n100 END', 'BASIC', 'JavaScript')
    assert result['unsupported']
    assert result['fallback_log'][0]['action'].startswith('LLM fallback')
    assert result['validation']['status'] == 'not_run'


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


def test_experiment_endpoint_exposes_controlled_ablation():
    response = experiment('JavaScript', repeats=1)
    assert response['ok'] is True
    assert response['rule_only']['total'] == response['hybrid']['total']
    assert response['summary']['overall']['delta_success_rate_percent'] >= 0


def test_experiment_endpoint_rejects_invalid_repeat_count():
    response = experiment('JavaScript', repeats=11)
    assert response == {'ok': False, 'error': 'Repeats must be between 1 and 10.'}


def test_benchmark_all_curated_cases_pass():
    from backend.benchmark import run_benchmark
    report = run_benchmark('JavaScript')
    assert report['total'] == 8
    assert report['passed'] == 8
    assert report['success_rate_percent'] == 100.0


def test_translation_contract_is_generated_for_valid_translation():
    result = transpile('x = 2\nprint(x + 1)\n')
    contract = result['translation_contract']
    assert contract['function'] == 'program'
    assert contract['output'] == 'number|string'
    assert 'source_api' in contract
    assert contract['translation_status'] in ('verified', 'pending')


def test_risk_assessment_and_failure_fingerprint_are_exposed():
    result = transpile('10 GOTO 100\n100 END', 'BASIC', 'JavaScript')
    risk = result['risk_assessment']
    assert risk['score'] >= 0
    assert risk['level'] in ('low', 'medium', 'high')
    assert result['failure_fingerprint']['stage'] in ('syntax', 'unsupported')


def test_rule_learning_tracks_verified_fallback_rules():
    result = transpile('x = 2\nprint(x + 1)\n')
    evolution = result['rule_evolution']
    assert 'learned_rules' in evolution
    assert 'rule_coverage_gain' in evolution


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
    assert 'generated_cases' in result['property_validation']


def test_llm_status_rejects_placeholder_credentials(monkeypatch):
    monkeypatch.setenv('LLM_API_URL', 'https://example.com/v1/chat/completions')
    monkeypatch.setenv('LLM_MODEL', 'gpt-4o-mini')
    monkeypatch.setenv('LLM_API_KEY', 'your_provider_api_key_here')
    from backend.llm_fallback import fallback_status

    status = fallback_status()
    assert status['configured'] is False
    assert status['key_set'] is False
