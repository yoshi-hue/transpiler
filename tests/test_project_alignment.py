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
    assert 'candidate claims' in alignment
    assert 'primary-source verification' in alignment
    assert '23/24 end-to-end passes' in alignment
    assert 'zero configured cases and zero calls' in alignment


def test_frontend_exposes_objective_status_and_does_not_claim_fallback_improvement():
    frontend = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
    assert 'Project objectives and implementation status' in frontend
    assert 'not demonstrated by the current run' in frontend
    assert 'suggestion may be generated, but it is not integrated into target output' in frontend
    assert 'Finite I/O checks' in frontend
