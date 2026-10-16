import csv
import json
from pathlib import Path

from backend.legacy import LANGUAGES
from tools.corpus import audit_codenet, validate_manifest


def test_checked_in_corpus_manifest_has_hashes_and_task_isolated_splits():
    manifest = Path(__file__).resolve().parents[1] / 'data' / 'corpus_manifest.jsonl'
    report = validate_manifest(manifest)
    assert report['ok'] is True
    assert report['records'] == 24
    assert report['split_counts']['test'] == 8


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
    assert report['licensing']['status'] == 'review_required'
    candidates = report['screened_candidate_manifest']
    assert all(candidate['expected_outcome'] == 'screening_only' for candidate in candidates)
    assert all(candidate['split'] == candidates[0]['split'] for candidate in candidates)
    assert all(candidate['source_archive_path'].startswith('data/p00001/Fortran/') for candidate in candidates)
