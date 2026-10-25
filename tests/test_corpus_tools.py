import csv
import json
from pathlib import Path

from backend.legacy import LANGUAGES
from tools import corpus
from tools.corpus import audit_codenet, validate_manifest


def test_checked_in_corpus_manifest_has_hashes_and_task_isolated_splits():
    manifest = Path(__file__).resolve().parents[1] / 'data' / 'corpus_manifest.jsonl'
    report = validate_manifest(manifest)
    assert report['ok'] is True
    assert report['records'] == 42
    assert report['split_counts']['development'] == 16
    assert report['split_counts']['test'] == 26
    assert report['split_counts'].get('challenge', 0) == 0


def test_heldout_expected_outputs_match_separate_reference_evaluator():
    root = Path(__file__).resolve().parents[1]
    check = json.loads((root / 'data' / 'oracle_current_check.json').read_text(encoding='utf-8'))
    assert check['cases'] == 25
    assert check['matches'] == 25
    assert check['fixture_count'] == 38
    assert check['fixture_matches'] == 38
    assert all(row['match'] for row in check['results'])
    assert all(row['match'] for row in check['fixture_results'])
    assert 'Not an independently executed native compiler' in check['limitation']


def test_supported_subset_spec_lists_each_implemented_source_language():
    specification = Path(__file__).resolve().parents[1] / 'data' / 'supported_subset.json'
    payload = json.loads(specification.read_text(encoding='utf-8'))
    assert set(payload['languages']) == set(LANGUAGES)
    assert all(language['implemented_constructs'] for language in payload['languages'].values())
    assert all('not_claimed' in language for language in payload['languages'].values())


def test_codenet_audit_counts_accepted_source_files_and_screens_supported_subset(tmp_path):
    root = tmp_path / 'Project_CodeNet'
    metadata = root / 'metadata'
    source_dir = root / 'data' / 'p00001' / 'Fortran'
    metadata.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    (source_dir / 's000000001.f90').write_text(
        'PROGRAM TEST\nINTEGER :: A\nA = 4\nPRINT *, A\nEND PROGRAM TEST',
        encoding='utf-8',
    )
    (source_dir / 's000000002.f90').write_text(
        'PROGRAM TEST\nINTEGER :: A\nA = 7\nPRINT *, A\nEND PROGRAM TEST',
        encoding='utf-8',
    )
    with (metadata / 'p00001.csv').open('w', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                'submission_id', 'problem_id', 'user_id', 'date', 'language',
                'original_language', 'filename_ext', 'status', 'cpu_time',
                'memory', 'code_size', 'accuracy',
            ],
        )
        writer.writeheader()
        writer.writerow({
            'submission_id': 's000000001',
            'problem_id': 'p00001',
            'language': 'Fortran',
            'filename_ext': 'f90',
            'status': 'Accepted',
        })
        writer.writerow({
            'submission_id': 's000000002',
            'problem_id': 'p00001',
            'language': 'Fortran',
            'filename_ext': 'f90',
            'status': 'Accepted',
        })

    report = audit_codenet(root, screen_per_language=2)
    fortran = report['per_language']['Fortran']
    assert fortran['submissions'] == 2
    assert fortran['accepted'] == 2
    assert fortran['accepted_source_present'] == 2
    assert fortran['screened_sample_size'] == 2
    assert fortran['screen_results']['subset_screen_pass'] == 2
    assert report['licensing']['status'] == 'dataset_level_license_documented'
    candidates = report['screened_candidate_manifest']
    assert all(candidate['expected_outcome'] == 'screening_only' for candidate in candidates)
    assert all(candidate['split'] == candidates[0]['split'] for candidate in candidates)
    assert all(candidate['source_archive_path'].startswith('data/p00001/Fortran/') for candidate in candidates)


def test_codenet_screen_records_parser_crashes_as_candidate_failures(tmp_path, monkeypatch):
    source = tmp_path / 'sample.f90'
    source.write_text('PROGRAM BROKEN\nEND PROGRAM BROKEN', encoding='utf-8')

    def broken_parser(*_args, **_kwargs):
        raise IndexError('synthetic parser crash')

    monkeypatch.setattr(corpus, 'legacy_transpile', broken_parser)
    result = corpus._screen_candidate({'language': 'Fortran', 'source_path': source})

    assert result['screen_status'] == 'parser_or_pipeline_error'
    assert result['screen_error'] == 'synthetic parser crash'
