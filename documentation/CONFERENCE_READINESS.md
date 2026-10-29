# Project readiness and evidence status

## Current contribution

The project is an inspectable compiler-design prototype for documented subsets of
COBOL, FORTRAN, Pascal, BASIC, and a project-specific Python-like language. It has a
shared intermediate representation, deterministic rule-first translation, unsupported
syntax reporting, optional complete-program LLM proposals, finite validation, contracts
and risk-aware eligibility rules, and bounded exact-schema learned-rule memory.
This is an engineering prototype; it does not establish a new translation algorithm,
generalization, production readiness, or an accuracy improvement.

## Current evidence snapshot

- The corpus manifest has 42 records: 16 development and 26 held-out cases across eight task groups. The held-out split has 22 supported translations and four expected-unsupported programs.
- Deterministic JavaScript and Python runs each matched all 22 supported outputs and 34/34 supported fixtures, and recognized 4/4 unsupported cases. The separate task-formula checker matched 25 expected-output records and 38 fixtures. This small pilot is not a generalization estimate.
- Six CodeNet Fortran cases cover six task groups (p02600, p02606, p02607, p03997, p02724, p03238). Hash-bound records document GNU Fortran 14.3.0 source builds and fixture outputs. The dataset-level CDLA-Permissive-2.0 basis is included; owner review of task semantics, expected outputs, attribution, and reuse terms remains pending in `data/independent_oracle_review_queue_v2.json`.
- The latest live five-repeat comparison used the same 26-case hash and settings for both targets. Each arm had 110/130 observations: 22/22 supported passes per repeat and 20/20 expected-unsupported recognitions. The hybrid generated 15 candidates per target; all 15 per target passed syntax, isolated/restricted runtime, and fixed output checks. Zero candidates were accepted, learned-rule reuse was zero, and reviewer effort was not measured. Arms had identical outcomes, so no improvement is established. CodeNet inputs were excluded from provider requests.
- The clean setup record predates the current corpus/code changes. A fresh full-suite result is being recorded after these changes; the previous 57-test result is historical. Docker Compose startup was previously verified. See `data/reproducibility_current.json` for archived commands, versions, and reports.
- Candidate review gates remain pending. Contracts/risk are shared across arms, so their individual effects remain unestimated. The preserved v4 run attempted CodeNet requests before the source guard; payload receipt is unknown.
See [`PROJECT_OBJECTIVES_AND_GAPS.md`](PROJECT_OBJECTIVES_AND_GAPS.md),
[`BENCHMARK_AND_ABLATION_PROTOCOL.md`](BENCHMARK_AND_ABLATION_PROTOCOL.md), and
[`CORPUS_PROTOCOL.md`](CORPUS_PROTOCOL.md) for the objective matrix, current
protocol, provenance, and artifact links. Report exact denominators and distinguish
supported translation from unsupported recognition.

## Work remaining

1. Complete the independent held-out case review in `data/independent_oracle_review_queue_v2.json`.
2. Complete source/target, independent fixture, security, regression, and human review for the six unique LLM candidate programs, then record actual review effort.
3. Expand the group-held-out corpus toward the planned 100 groups; eight groups remain a small pilot.
4. Establish native or independently executed source oracles for project-authored task adaptations.
5. Isolate contract and risk mechanisms where safe, and rerun controlled comparisons on the expanded frozen corpus.
6. Reconcile and author-review the course report and demo. Paper/demo files remain drafts.

The status matrix describes the remaining research and engineering objectives. An ICSE
submission package is not currently being prepared; author identities, a public video,
PDF/page-count verification, and final author approval would be separate requirements if
that changes.
