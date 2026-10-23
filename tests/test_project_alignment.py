from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_objectives_and_candidate_gaps_are_documented_with_status_caveats():
    alignment = (ROOT / 'data' / 'PROJECT_OBJECTIVES_AND_GAPS.md').read_text(encoding='utf-8')
    for objective in (
        'Survey established',
        'Identify specific gaps',
        'Build a multi-language front end',
        'Design a hybrid back end',
        'Validate behavior',
        'Document precisely',
    ):
        assert objective in alignment
    assert 'scoped source audit' in alignment
    assert 'Primary-source audit' in alignment
    assert 'field-wide gaps' in alignment


def test_frontend_exposes_objective_status_and_does_not_claim_fallback_improvement():
    frontend = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
    assert 'Project objectives and implementation status' in frontend
    assert 'This prototype does not establish that outcome' in frontend
    assert 'suggestion may be generated and displayed separately' in frontend
    assert 'Finite I/O checks' in frontend
    assert 'Fallback events include skipped attempts' in frontend


def test_frontend_surfaces_llm_candidates_separately_from_validated_code():
    frontend = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
    assert '[hidden]{display:none!important}' in frontend
    assert 'LLM candidate (unvalidated)' in frontend
    assert 'Download LLM candidate' in frontend
    assert 'This model-generated program is not semantically validated' in frontend


def test_frontend_loads_a_supported_llm_example_for_python_like_selection():
    frontend = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
    assert "if(language==='Python-like')" in frontend
    assert "$('source').value='BASIC'" in frontend
    assert "$('sourceCode').value=llmExample.BASIC" in frontend
