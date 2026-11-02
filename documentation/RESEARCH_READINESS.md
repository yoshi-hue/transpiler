# Research readiness

## Implemented and tested

- Deterministic subset translation, source/target finite I/O checks, explicit
  unsupported diagnostics, and fail-closed isolated Python candidate execution.
- Optional whole-program LLM fallback with bounded provider retries and response
  limits.
- Hash-bound candidate lifecycle/review records and a bounded repair helper.
- Immutable, content-addressed offline evidence files.
- A four-arm evaluation runner, mutation-sensitivity report, and native adapter
  interface with compile/run support when a compiler is installed.
- Evaluation records now include per-language, per-construct, and per-task-group
  breakdowns; bounded-repair recovery/regression counters; candidate-gate
  rejection metrics; unsupported-input recognition; learned-rule hits/misses;
  and an explicit independent-review queue status.

## Live-evaluated

Historical provider smoke and benchmark artifacts remain in `data/` and are not
relabeled by this change. The new lifecycle and repair paths have local
deterministic tests; no new live provider campaign was run.

The reproducible four-arm runner is:

```powershell
python tools\run_research_evaluation.py --target JavaScript --output-dir data\evidence
```

For an explicitly authorized provider run, add `--enable-llm`; add
`--enable-repair` to activate the bounded repair arm. Offline runs leave those
provider-dependent arms as `not_run`.

The live JavaScript run `20261102T081606Z-728da45c` completed with the following
verified pilot results: rule-only 22/26 (84.6%); rule-first plus LLM 22/26
(84.6%), with 3 candidates generated and 3/3 fixed-oracle matches; and the
repair arm also 22/26 (84.6%) with no additional recovery. LLM-only produced
18/26 recorded passes, but two Pascal requests failed with provider HTTP 429
quota errors and six CodeNet cases were correctly blocked by source policy, so
this is not a clean comparable success rate. The run demonstrates provider
connectivity and candidate generation, not an LLM improvement over rules.

A follow-up controlled run `20261102T082356Z-69caaf0f` used 20 project-authored
held-out cases, excluded CodeNet-origin sources, and set provider retries to zero
to avoid retry amplification. Rule-only passed 17/20 (85.0%). All 20 LLM-only
requests failed because the Gemini quota remained exhausted, and the hybrid arm
generated no candidates. This is a blocked live attempt, not evidence of LLM
failure or success. Native discovery still reports COBOL, Fortran, Pascal, and
BASIC compilers as unavailable at that time.

The later evidence run `20261102T091657Z-b844c52d` verified a containerized
GNU Fortran 14.3.0 native pilot: the `rosetta-maximum-fortran` case compiled,
ran with exit status 0, and matched the independent expected output `25`.

Evidence run `20261102T092706Z-aa1f75f4` now detects GnuCOBOL 3.1.2, GNU
Fortran 14.3.0, Free Pascal 3.2.2, and FreeBASIC 1.10.1 in Docker images. The
host PATH still does not contain these executables; the evidence records
containerized availability explicitly.

## Awaiting independent review

Human review of model candidates, external corpus licensing/oracles, and any
claim that the LLM improves over rule-only translation. The current queue has
6 pending CodeNet records, 20 completed project-authored decisions, and 20
recorded 45-minute review attestations; the evidence runner reports the six
provenance/licensing cases as pending rather than counting them as approved.

The audit packet also identified a COBOL presentation-format distinction: native
`PIC 999` DISPLAY can emit zero-padded values such as `025`, while the benchmark
oracle uses numeric equivalence for `25`. This is not byte-for-byte stdout
equivalence and remains documented for sign-off. Queue amendment
`audit-20261102-001` corrected two reviewer-facing fixture notes without changing
source text, inputs, or expected outputs.

## Blocked

Native-source validation is available through Docker for GNU Fortran, GnuCOBOL,
Free Pascal, and FreeBASIC. Host-local discovery remains unavailable, so runs
must use the Docker adapters and preserve their image/compiler metadata.
The latest provider-enabled project-only run `20261102T095152Z-aaf898e3`
completed and archived all four arms. It used 20 held-out cases: rule-only
passed 17/20, rule-first plus LLM passed 17/20, and rule-first plus bounded
repair passed 17/20 with zero recoveries and zero regressions. LLM-only recorded
18 passes, but provider failures and arm-specific denominators still require
inspection before treating that as a clean comparison. This run therefore does
not demonstrate an LLM improvement.

Offline runs also produce the complete reporting schema, but their
provider-dependent arms remain `not_run` and cannot establish LLM improvement.

## Proposed future work

Run the live four-arm evaluation on a frozen, independently reviewed benchmark
with exact request/token budgets. Native adapters are implemented and can now
record containerized compiler results for all four toolchains.
