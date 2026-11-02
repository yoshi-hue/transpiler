"""Bounded validation-driven candidate repair.

Only diagnostics and explicitly permitted development examples are passed to the
repair callback. Hidden evaluation data is intentionally not part of this API.
"""
from __future__ import annotations

from .candidate_lifecycle import candidate_hash, classify_candidate


def generate_with_bounded_repair(generate, validate, *, max_repairs=2,
                                 development_diagnostics=None,
                                 development_examples=None):
    """Generate and revalidate from scratch, preserving every attempt.

    ``generate`` receives ``None`` for the first attempt, then a public failure
    packet. ``validate`` receives only the candidate. The callbacks are provider
    agnostic, which makes deterministic mock-provider tests straightforward.
    """
    budget = max(0, min(int(max_repairs), 2))
    diagnostics = list(development_diagnostics or [])
    examples = list(development_examples or [])
    attempts = []
    previous = None
    for number in range(budget + 1):
        candidate = generate(None if number == 0 else {
            'diagnostics': diagnostics,
            'development_examples': examples,
            'previous_candidate_sha256': candidate_hash(previous),
            'repair_attempt': number,
        })
        candidate = (candidate or '').strip()
        record = {'attempt': number, 'candidate': candidate,
                  'candidate_sha256': candidate_hash(candidate)}
        if not candidate:
            record.update({'state': 'validation_failed', 'validation': {'status': 'failed', 'error': 'empty candidate'}})
            attempts.append(record)
            break
        if previous is not None and candidate == previous:
            record.update({'state': 'validation_failed', 'validation': {'status': 'failed', 'error': 'identical candidate repeated'}})
            attempts.append(record)
            break
        validation = dict(validate(candidate) or {})
        record['validation'] = validation
        record['state'] = classify_candidate(
            syntax_valid=validation.get('syntax_valid'),
            runtime_valid=validation.get('runtime_valid'),
            validation_status=validation.get('status', 'not_run'),
            review_required=bool(validation.get('review_required')),
        )
        attempts.append(record)
        if validation.get('status') == 'passed':
            return {'selected': candidate, 'selected_attempt': number,
                    'state': record['state'], 'attempts': attempts,
                    'repair_budget': budget}
        previous = candidate
    return {'selected': None, 'selected_attempt': None,
            'state': attempts[-1]['state'] if attempts else 'validation_failed',
            'attempts': attempts, 'repair_budget': budget}
