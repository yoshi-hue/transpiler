"""Explicit, hash-bound lifecycle for model-generated translation candidates.

This module is deliberately independent of a provider and of the UI.  It makes
the distinction between finite validation and human approval machine-readable.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib

STATES = {
    'generated', 'syntax_failed', 'runtime_failed', 'validation_failed',
    'validated_for_tested_inputs', 'review_required', 'approved', 'rejected',
}


def candidate_hash(candidate: str) -> str:
    return hashlib.sha256(candidate.encode('utf-8')).hexdigest()


def evidence_hash(evidence: dict) -> str:
    import json
    material = json.dumps(evidence, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(material.encode('utf-8')).hexdigest()


def bound_validation_evidence(evidence: dict) -> dict:
    """Return the fresh execution evidence used for approval binding.

    Human review records may contain additional fixture, security, and
    regression attestations.  Only the machine-produced current execution
    evidence is bound to the candidate approval; replay recomputes it.
    """
    nested = evidence.get('current_validation_evidence') if isinstance(evidence, dict) else None
    return nested if isinstance(nested, dict) else (evidence or {})


def classify_candidate(*, syntax_valid=None, runtime_valid=None, validation_status='not_run',
                       review_required=False, generated=True) -> str:
    if not generated:
        return 'rejected'
    if syntax_valid is False:
        return 'syntax_failed'
    if runtime_valid is False:
        return 'runtime_failed'
    if validation_status in {'failed', 'mismatch'}:
        return 'validation_failed'
    if validation_status == 'passed':
        return 'review_required' if review_required else 'validated_for_tested_inputs'
    return 'generated'


def review_candidate(*, source: str, candidate: str, validation_evidence: dict,
                     reviewer: str, decision: str, reason: str,
                     prior: dict | None = None, now: datetime | None = None,
                     target_reviewer: str | None = None) -> dict:
    """Record a review bound to the exact candidate and evidence.

    A later candidate or changed evidence cannot reuse this record because both
    hashes are included in the approval binding.
    """
    reviewer = (reviewer or '').strip()
    reason = (reason or '').strip()
    decision = (decision or '').strip().lower()
    if not reviewer:
        raise ValueError('reviewer identity is required; it is never inferred.')
    if target_reviewer is not None:
        target_reviewer = target_reviewer.strip()
        if not target_reviewer:
            raise ValueError('target-language reviewer identity is required when supplied.')
        if target_reviewer.lower() == reviewer.lower():
            raise ValueError('source-language and target-language reviewers must be independent.')
    lowered_reviewer = reviewer.lower()
    if any(token in lowered_reviewer for token in ('your name', 'you@example.com', 'example.com', '<reviewer')):
        raise ValueError('replace the example reviewer identity with a real reviewer identity.')
    if decision not in {'approved', 'rejected'}:
        raise ValueError("decision must be 'approved' or 'rejected'.")
    if not reason:
        raise ValueError('a review reason is required.')
    if reason in {'...', 'TBD', 'TODO'} or any(value in {'...', 'TBD', 'TODO'}
                                               for value in _evidence_values(validation_evidence)):
        raise ValueError('replace placeholder review evidence with actual evidence.')
    source_sha = hashlib.sha256(source.encode('utf-8')).hexdigest()
    candidate_sha = candidate_hash(candidate)
    validation_sha = evidence_hash(bound_validation_evidence(validation_evidence))
    prior_valid = bool(prior and prior.get('candidate_sha256') == candidate_sha
                       and prior.get('validation_evidence_sha256') == validation_sha
                       and prior.get('source_sha256') == source_sha)
    timestamp = (now or datetime.now(timezone.utc)).isoformat().replace('+00:00', 'Z')
    return {
        'status': decision,
        'reviewer': reviewer,
        'source_reviewer': reviewer,
        'target_reviewer': target_reviewer,
        'validation_evidence': validation_evidence,
        'reason': reason,
        'reviewed_at_utc': timestamp,
        'source_sha256': source_sha,
        'candidate_sha256': candidate_sha,
        'validation_evidence_sha256': validation_sha,
        'approval_binding': f'{source_sha}:{candidate_sha}:{validation_sha}',
        'prior_approval_reused': prior_valid,
        'state': 'approved' if decision == 'approved' else 'rejected',
    }


def _evidence_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _evidence_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _evidence_values(item)
    elif isinstance(value, str):
        yield value.strip()


def approval_is_current(review: dict | None, *, source: str, candidate: str,
                        validation_evidence: dict) -> bool:
    if not review or review.get('status') != 'approved':
        return False
    return (review.get('source_sha256') == hashlib.sha256(source.encode('utf-8')).hexdigest()
            and review.get('candidate_sha256') == candidate_hash(candidate)
            and review.get('validation_evidence_sha256') == evidence_hash(bound_validation_evidence(validation_evidence)))
