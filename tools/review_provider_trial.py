"""Record an explicit human review for a provider-trial candidate.

This command never invents reviewer identities or evidence. Approval requires
the reviewer to supply each acceptance-gate attestation explicitly; the review
is written separately so the original provider trial remains unchanged.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.candidate_lifecycle import review_candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', default='data/provider_trial_latest.json')
    parser.add_argument('--output', default='data/provider_trial_latest_review.json')
    parser.add_argument('--reviewer', required=True, help='Your real reviewer identity.')
    parser.add_argument('--target-reviewer', required=True, help='Reviewer identity for target/runtime review.')
    parser.add_argument('--decision', choices=('approved', 'rejected'), required=True)
    parser.add_argument('--reason', required=True)
    parser.add_argument('--source-review-evidence', required=True)
    parser.add_argument('--fixture-evidence', required=True,
                        help='Describe or reference independently authored fixtures; do not reuse the smoke oracle.')
    parser.add_argument('--security-evidence', required=True)
    parser.add_argument('--regression-evidence', required=True)
    args = parser.parse_args()

    if any(token in args.reviewer.lower() for token in ('your name', 'you@example.com', 'example.com', '<reviewer')):
        raise SystemExit('Replace the example reviewer identity with a real identity.')
    if any(token in args.target_reviewer.lower() for token in ('your name', 'you@example.com', 'example.com', '<reviewer')):
        raise SystemExit('Replace the example target reviewer identity with a real identity.')
    evidence_args = (args.reason, args.source_review_evidence, args.fixture_evidence,
                     args.security_evidence, args.regression_evidence)
    if any(value.strip() in {'...', 'TBD', 'TODO'} for value in evidence_args):
        raise SystemExit('Replace placeholder evidence with actual review evidence.')

    report = json.loads((ROOT / args.report).read_text(encoding='utf-8'))
    candidate = report.get('candidate_code')
    if not candidate or not report.get('candidate_generated'):
        raise SystemExit('The report has no generated candidate to review.')
    if report.get('syntax_valid') is not True or report.get('runtime_valid') is not True:
        raise SystemExit('Candidate must pass syntax and runtime checks before review.')
    evidence = {
        'source_review': {'reviewer': args.reviewer, 'evidence': args.source_review_evidence},
        'target_toolchain': report.get('runtime_validation', {}),
        'independent_fixtures': {'evidence': args.fixture_evidence},
        'security_review': {'reviewer': args.reviewer, 'evidence': args.security_evidence},
        'regression_checks': {'evidence': args.regression_evidence},
        'human_review': {'source_reviewer': args.reviewer, 'target_reviewer': args.target_reviewer,
                         'decision': args.decision},
        'trial_id': report.get('trial_id'),
        'observed_output': report.get('observed_output'),
        'oracle_match': report.get('independent_oracle_match'),
    }
    review = review_candidate(
        source='provider-trial:' + report['source_sha256'], candidate=candidate,
        validation_evidence=evidence, reviewer=args.reviewer,
        decision=args.decision, reason=args.reason,
    )
    result = {
        'schema_version': '1',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_report': args.report,
        'candidate_sha256': report.get('candidate_sha256'),
        'review': review,
        'gate_evidence': evidence,
        'candidate_accepted': args.decision == 'approved',
        'limitation': ('Approval records reviewer attestations; it is still not formal semantic equivalence.'
                       if args.decision == 'approved' else 'Candidate remains rejected.'),
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(output), 'decision': args.decision,
                      'candidate_accepted': result['candidate_accepted']}, indent=2))


if __name__ == '__main__':
    main()
