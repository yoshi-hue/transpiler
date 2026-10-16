"""Corpus-manifest validation and conservative IBM Project CodeNet audit tools."""
import argparse
import csv
import hashlib
import heapq
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.benchmark import (  # noqa: E402
    CASES,
    EXTERNAL_CASES,
    LOCAL_EXPECTED_OUTPUTS,
    _EXTERNAL_CASE_METADATA,
)
from backend.legacy import LANGUAGES, SUBSETS, UnsupportedSyntax, legacy_transpile, run_nodes  # noqa: E402
from backend.validator import compare, run_javascript  # noqa: E402

MANIFEST_PATH = ROOT / 'data' / 'corpus_manifest.jsonl'
CODE_NET_REPOSITORY = 'https://github.com/IBM/Project_CodeNet'
CODE_NET_README = f'{CODE_NET_REPOSITORY}/blob/main/README.md'
LANGUAGE_ALIASES = {
    'cobol': 'COBOL',
    'fortran': 'FORTRAN',
    'fortran 77': 'FORTRAN',
    'fortran 90': 'FORTRAN',
    'pascal': 'Pascal',
    'basic': 'BASIC',
}


def _sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _group_split(group, seed):
    value = int(hashlib.sha256(f'{seed}:{group}'.encode('utf-8')).hexdigest()[:8], 16) % 100
    if value < 70:
        return 'train'
    if value < 85:
        return 'development'
    return 'test'


def _required_constructs(language, construct):
    if construct == 'arithmetic':
        return ['assignment', 'arithmetic', 'output']
    if construct == 'conditional':
        return ['conditional', 'comparison', 'output']
    if construct == 'loop':
        return ['loop', 'output']
    if language == 'Python-like':
        return ['assignment', 'output']
    return []


def _manifest_record(language, case_id, construct, source, *, origin, group, split, external=None):
    external = external or {}
    expected_output = external.get('expected_output')
    if expected_output is None:
        expected_output = LOCAL_EXPECTED_OUTPUTS.get((language, construct))
    expected_outcome = external.get('expected_outcome', 'translated')
    if expected_outcome == 'unsupported':
        expected_output = None

    provenance = external.get('provenance', {})
    source_uri = external.get('source_uri')
    if source_uri is None and origin == 'task-derived':
        source_uri = f'data/external_task_cases.jsonl#{case_id}'
    return {
        'schema_version': '1.0',
        'case_id': case_id,
        'origin': origin,
        'language': language,
        'dialect': LANGUAGES.get(language, 'unknown'),
        'task': provenance.get('task', construct),
        'category': external.get('construct', construct),
        'split_group': group,
        'split': split,
        'source': source,
        'source_sha256': _sha256(source),
        'source_url': provenance.get('url'),
        'source_repository': provenance.get('repository'),
        'source_commit': provenance.get('commit'),
        'original_status': external.get(
            'original_status',
            'not_applicable_adapted' if origin == 'task-derived' else 'not_applicable_project-authored',
        ),
        'license': external.get(
            'license',
            'project-authored; Rosetta Code task prompt attributed; upstream source implementation not copied'
            if origin == 'task-derived'
            else 'project-authored; review repository license before redistribution',
        ),
        'license_status': external.get(
            'license_status',
            'review_task_terms_before_redistribution' if origin == 'task-derived' else 'project_source',
        ),
        'required_constructs': external.get('required_constructs', _required_constructs(language, construct)),
        'input_fixtures': external.get('input_fixtures', []),
        'expected_outcome': expected_outcome,
        'expected_output': expected_output,
        'oracle_status': 'separately_authored_expected_output' if expected_output is not None else 'unsupported_expected',
        'source_uri': source_uri or f'embedded:backend/benchmark.py#{language}:{construct}',
        'adaptation_notes': provenance.get('adaptation', 'Project-authored local benchmark case.'),
    }


def build_manifest_records():
    records = []
    for language, construct, source in CASES:
        records.append(_manifest_record(
            language,
            f'local-{language.lower()}-{construct}',
            construct,
            source,
            origin='project-authored',
            group=f'local:{language}:{construct}',
            split='development',
        ))

    for language, case_id, source in EXTERNAL_CASES:
        external = _EXTERNAL_CASE_METADATA[(language, case_id)]
        task = external['provenance']['task']
        split = 'development' if task == 'A+B' else 'test'
        records.append(_manifest_record(
            language,
            case_id,
            external['construct'],
            source,
            origin='task-derived',
            group=f'rosettacode:{task}',
            split=split,
            external=external,
        ))
    return records


def write_manifest(output=MANIFEST_PATH):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    records = build_manifest_records()
    with output.open('w', encoding='utf-8', newline='\n') as manifest:
        for record in records:
            manifest.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')
    return output, records


def validate_manifest(path=MANIFEST_PATH):
    path = Path(path)
    errors = []
    records = []
    ids = set()
    hashes = {}
    group_splits = {}
    with path.open(encoding='utf-8') as manifest:
        for line_number, line in enumerate(manifest, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f'line {line_number}: invalid JSON: {exc}')
                continue
            required = (
                'case_id', 'origin', 'language', 'dialect', 'split_group', 'split',
                'source', 'source_sha256', 'source_url', 'source_repository', 'source_commit',
                'original_status', 'license', 'license_status', 'task',
                'category', 'source_uri', 'required_constructs', 'input_fixtures',
                'expected_outcome', 'expected_output',
                'oracle_status', 'adaptation_notes',
            )
            missing = [field for field in required if field not in record]
            if missing:
                errors.append(f'line {line_number}: missing fields: {", ".join(missing)}')
                continue
            case_id = record['case_id']
            source_hash = _sha256(record['source'])
            if case_id in ids:
                errors.append(f'line {line_number}: duplicate case_id {case_id}')
            ids.add(case_id)
            if source_hash != record['source_sha256']:
                errors.append(f'line {line_number}: source hash mismatch for {case_id}')
            previous = hashes.get(source_hash)
            if previous:
                errors.append(f'line {line_number}: exact duplicate source {case_id} duplicates {previous}')
            else:
                hashes[source_hash] = case_id
            if record['split'] not in ('train', 'development', 'test', 'challenge'):
                errors.append(f'line {line_number}: invalid split {record["split"]!r}')
            group = record['split_group']
            previous_split = group_splits.setdefault(group, record['split'])
            if previous_split != record['split']:
                errors.append(f'line {line_number}: split leakage for group {group}')
            if record['expected_outcome'] == 'translated' and record['expected_output'] is None:
                errors.append(f'line {line_number}: translated case {case_id} lacks expected_output')
            if record['expected_outcome'] == 'translated' and record['oracle_status'] == 'unavailable':
                errors.append(f'line {line_number}: translated case {case_id} lacks an independent oracle')
            if record['origin'] == 'codenet' and record['license_status'] != 'reviewed':
                errors.append(f'line {line_number}: CodeNet case {case_id} has no reviewed license status')
            records.append(record)

    counts = Counter((record['split'], record['split_group']) for record in records)
    split_counts = Counter(record['split'] for record in records)
    if path.resolve() == MANIFEST_PATH.resolve():
        expected = {record['case_id']: record['source_sha256'] for record in build_manifest_records()}
        actual = {record['case_id']: record['source_sha256'] for record in records}
        if expected != actual:
            errors.append('manifest is stale relative to the benchmark source; run tools\\corpus.py write-manifest')
    return {
        'ok': not errors,
        'records': len(records),
        'split_counts': dict(sorted(split_counts.items())),
        'split_groups': len(counts),
        'errors': errors,
    }


def _resolve_codenet_source(root, row):
    problem_id = row.get('problem_id', '').strip()
    submission_id = row.get('submission_id', '').strip()
    language = row.get('language', '').strip()
    extension = row.get('filename_ext', '').strip().lstrip('.')
    if (
        not re.fullmatch(r'p\d{5}', problem_id)
        or not re.fullmatch(r's\d{9}', submission_id)
        or not re.fullmatch(r'[A-Za-z0-9_+. -]+', language)
        or (extension and not re.fullmatch(r'[A-Za-z0-9]+', extension))
    ):
        return None
    filename = f'{submission_id}.{extension}' if extension else submission_id
    source_path = (root / 'data' / problem_id / language / filename).resolve()
    if not source_path.is_relative_to(root.resolve()):
        return None
    return source_path


def _screen_candidate(candidate):
    canonical = LANGUAGE_ALIASES.get(candidate['language'].strip().lower())
    if canonical not in SUBSETS:
        return {'screen_status': 'not_supported_language'}
    try:
        source = candidate['source_path'].read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return {'screen_status': 'source_encoding_error'}
    except OSError as exc:
        return {'screen_status': 'source_read_error', 'screen_error': str(exc)[:300]}
    try:
        result = legacy_transpile(canonical, source, 'JavaScript')
    except (UnsupportedSyntax, ValueError, SyntaxError) as exc:
        return {'screen_status': 'parser_or_pipeline_error', 'screen_error': str(exc)[:300]}
    if result.unsupported:
        return {
            'screen_status': 'unsupported_syntax',
            'unsupported_constructs': len(result.unsupported),
        }
    source_output = []
    try:
        run_nodes(result.source_program, {}, source_output)
    except UnsupportedSyntax as exc:
        return {'screen_status': 'source_interpreter_error', 'screen_error': str(exc)[:300]}
    target_result = run_javascript(result.javascript)
    validation = compare('\n'.join(map(str, source_output)), target_result, 'JavaScript')
    if validation['status'] == 'not_run' and validation.get('failure_class') == 'runtime_unavailable':
        return {
            'screen_status': 'target_runtime_unavailable',
            'validation_status': validation['status'],
        }
    if validation['status'] != 'passed':
        return {
            'screen_status': 'not_independently_executable',
            'validation_status': validation['status'],
            'failure_class': validation.get('failure_class'),
        }
    return {
        'screen_status': 'subset_screen_pass',
        'validation_status': validation.get('status'),
        'validation_note': 'Prototype interpreter/target agreement only; not an independent oracle.',
    }


def audit_codenet(root, output=None, screen_per_language=100):
    root = Path(root).resolve()
    metadata_dir = root / 'metadata'
    if not metadata_dir.is_dir():
        raise FileNotFoundError(f'CodeNet metadata directory not found: {metadata_dir}')

    totals = Counter()
    by_language = defaultdict(Counter)
    candidate_heaps = defaultdict(list)
    metadata_files = sorted(
        path for path in metadata_dir.glob('p*.csv')
        if path.name != 'problem_list.csv'
    )

    for metadata_file in metadata_files:
        with metadata_file.open(encoding='utf-8-sig', newline='') as source:
            reader = csv.DictReader(source)
            expected = {'submission_id', 'problem_id', 'language', 'status'}
            if not reader.fieldnames or not expected.issubset(reader.fieldnames):
                continue
            for row in reader:
                language = row.get('language', '').strip() or 'unknown'
                status = row.get('status', '').strip()
                source_path = _resolve_codenet_source(root, row)
                exists = bool(source_path and source_path.is_file())
                totals['submissions'] += 1
                by_language[language]['submissions'] += 1
                if status.lower() == 'accepted':
                    totals['accepted'] += 1
                    by_language[language]['accepted'] += 1
                    if exists:
                        totals['accepted_source_present'] += 1
                        by_language[language]['accepted_source_present'] += 1
                        if language.lower() in LANGUAGE_ALIASES and screen_per_language > 0:
                            submission_id = row.get('submission_id', '')
                            rank = int(hashlib.sha256(submission_id.encode('utf-8')).hexdigest()[:16], 16)
                            candidate = {
                                'language': language,
                                'problem_id': row.get('problem_id', ''),
                                'submission_id': submission_id,
                                'source_path': source_path,
                                'source_hash': '',
                            }
                            heap = candidate_heaps[language]
                            item = (-rank, submission_id, candidate)
                            if len(heap) < screen_per_language:
                                heapq.heappush(heap, item)
                            elif item > heap[0]:
                                heapq.heapreplace(heap, item)
                    else:
                        by_language[language]['accepted_source_missing'] += 1
                else:
                    by_language[language]['not_accepted'] += 1

    if not metadata_files:
        raise FileNotFoundError(
            f'No per-problem metadata CSV files (p*.csv) found in {metadata_dir}. '
            'Extract the CodeNet archive before running this audit.'
        )

    screened = defaultdict(Counter)
    candidate_records = []
    for language, heap in candidate_heaps.items():
        for _, _, candidate in sorted(heap, key=lambda item: -item[0]):
            source_bytes = candidate['source_path'].read_bytes()
            candidate['source_hash'] = hashlib.sha256(source_bytes).hexdigest()
            outcome = _screen_candidate(candidate)
            screened[language][outcome['screen_status']] += 1
            canonical = LANGUAGE_ALIASES.get(language.lower())
            candidate_records.append({
                'schema_version': '1.0',
                'case_id': f'codenet-{candidate["problem_id"]}-{candidate["submission_id"]}',
                'origin': 'codenet',
                'dataset': 'IBM Project CodeNet',
                'dataset_version': '1.0.0',
                'language': canonical or language,
                'source_language_label': language,
                'dialect': candidate['language'],
                'task': candidate['problem_id'],
                'category': 'codenet_submission',
                'split_group': f'codenet:{candidate["problem_id"]}',
                'split': _group_split(f'codenet:{candidate["problem_id"]}', 2026),
                'source_uri': f'codenet-archive:{candidate["source_path"].relative_to(root).as_posix()}',
                'source_archive_path': candidate['source_path'].relative_to(root).as_posix(),
                'source_sha256': candidate['source_hash'],
                'source_url': CODE_NET_REPOSITORY,
                'source_repository': CODE_NET_REPOSITORY,
                'source_commit': None,
                'license': 'unknown; must be verified for the source submission and source-site terms',
                'license_status': 'review_required',
                'original_status': 'Accepted',
                'required_constructs': [],
                'input_fixtures': [],
                'expected_outcome': 'screening_only',
                'expected_output': None,
                'oracle_status': 'unavailable',
                'screen_result': outcome,
                'adaptation_notes': 'Source remains in the local CodeNet archive; no source text copied to the manifest. Acceptance status is inherited from CodeNet metadata; original toolchain was not rerun by this audit.',
            })

    report = {
        'dataset': 'IBM Project CodeNet',
        'dataset_version': '1.0.0',
        'dataset_repository': CODE_NET_REPOSITORY,
        'dataset_readme': CODE_NET_README,
        'audit_timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'metadata_files_scanned': len(metadata_files),
        'group_split_seed': 2026,
        'totals': dict(sorted(totals.items())),
        'per_language': {},
        'screened_candidate_manifest': candidate_records,
        'screening': {
            'policy': 'Deterministically hash-sampled accepted source-present submissions; transpile to JavaScript; require no unsupported constructs and prototype validation pass.',
            'sampled_per_language_max': screen_per_language,
            'oracle_independent': False,
            'note': 'Screen counts are candidate triage only. Source/target agreement uses this prototype interpreter and is not an independent correctness oracle or proof of original-language compilation.',
        },
        'licensing': {
            'status': 'review_required',
            'note': 'The repository LICENSE does not establish redistribution rights for each third-party online-judge submission. Review CodeNet, AIZU, AtCoder, and any applicable source-specific terms before using or redistributing samples.',
        },
        'supported_language_mapping': {
            'COBOL': ['COBOL'],
            'FORTRAN': ['Fortran', 'Fortran 77', 'Fortran 90'],
            'Pascal': ['Pascal'],
            'BASIC': ['BASIC'],
        },
    }
    for language in sorted(set(by_language) | set(screened)):
        counts = by_language[language]
        report['per_language'][language] = {
            **dict(sorted(counts.items())),
            'subset_language': LANGUAGE_ALIASES.get(language.lower()),
            'accepted_source_present_candidates': counts.get('accepted_source_present', 0),
            'screened_sample_size': sum(screened[language].values()),
            'screen_results': dict(sorted(screened[language].items())),
        }

    if output:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        public_report = {key: value for key, value in report.items() if key != 'screened_candidate_manifest'}
        output_path.write_text(json.dumps(public_report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        report['output_path'] = str(output_path)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)

    manifest_parser = subparsers.add_parser('write-manifest', help='Regenerate the manifest for repository benchmark cases')
    manifest_parser.add_argument('--output', default=str(MANIFEST_PATH))

    validate_parser = subparsers.add_parser('validate-manifest', help='Validate manifest hashes, fields, and group splits')
    validate_parser.add_argument('--manifest', default=str(MANIFEST_PATH))

    codenet_parser = subparsers.add_parser('audit-codenet', help='Count and conservatively screen local CodeNet metadata/source files')
    codenet_parser.add_argument('--root', required=True, help='Extracted CodeNet root containing metadata/ and data/')
    codenet_parser.add_argument('--output', default='data/codenet_audit.json')
    codenet_parser.add_argument('--screen-per-language', type=int, default=100)
    codenet_parser.add_argument('--candidate-manifest', default=None, help='Optional JSONL output for sampled candidate metadata (no source contents)')

    args = parser.parse_args()
    if args.command == 'write-manifest':
        output, records = write_manifest(args.output)
        print(json.dumps({'manifest': str(output), 'records': len(records)}, indent=2))
        return
    if args.command == 'validate-manifest':
        report = validate_manifest(args.manifest)
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report['ok'] else 1)
    if args.screen_per_language < 0:
        parser.error('--screen-per-language must be non-negative')
    report = audit_codenet(args.root, None, args.screen_per_language)
    candidate_manifest = report.pop('screened_candidate_manifest')
    if args.candidate_manifest:
        candidate_path = Path(args.candidate_manifest)
        if not candidate_path.is_absolute():
            candidate_path = ROOT / candidate_path
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        with candidate_path.open('w', encoding='utf-8', newline='\n') as manifest:
            for record in candidate_manifest:
                manifest.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')
        report['candidate_manifest_path'] = str(candidate_path)
        report['candidate_manifest_records'] = len(candidate_manifest)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report['output_path'] = str(output_path)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
