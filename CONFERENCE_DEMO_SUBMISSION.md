# Conference Demo Submission Draft

**Track fit:** student research, poster, or system-demonstration track
**Status:** venue-neutral draft; adapt to the selected conference's call for
participation, page limit, anonymity rules, and required demo format.
**Artifact:** this repository and the reproducibility record in
[`data/project_report_evidence.json`](./data/project_report_evidence.json).

## Title

**A Transparent Rule-First Modernizer for Small Legacy-Language Subsets**

## Abstract

Legacy-code migration is difficult to audit when generated code is plausible but its
behavior is uncertain. We present a compiler-design prototype that translates documented
subsets of COBOL, FORTRAN, Pascal, BASIC, and a project-specific Python-like language
to JavaScript or Python. Its deterministic path parses supported constructs, normalizes
them to an inspectable representation, emits target code, and checks finite input/output
behavior. For parser-reported unsupported source, an optional large-language-model
(LLM) path can produce a complete target-program candidate. The interface labels that
candidate unvalidated; syntax/runtime checks and fixed-case oracle comparisons do not
cause the translator to accept it.

The demonstration exposes intermediate artifacts, unsupported syntax, candidate
provenance, and validation status rather than presenting generated text as verified
translation. In a 24-case, project-authored and task-derived pilot, 23 cases passed
end-to-end checks and one deliberately unsupported COBOL loop was recognized as
unsupported. In a paired JavaScript run, one candidate for that loop passed restricted
execution and matched its separately authored expected output; the source case remained
`not_run`, so this did not increase the end-to-end pass rate. The pilot is illustrative,
not a representative corpus or evidence of general LLM effectiveness. We offer the
prototype as a reproducible system demonstration of inspectable translation boundaries
and explicit uncertainty reporting.

## Demonstration contribution

This submission is a **system demonstration**, not a claim of a new translation
algorithm or statistically established improvement. The contribution is an executable,
inspectable prototype and an evaluation workflow that makes four different outcomes
visible:

1. deterministic translation of a declared source subset;
2. explicit reporting of constructs outside that subset;
3. optional generation and separate display of a full-program LLM candidate; and
4. finite syntax, runtime, and expected-output evidence without conflating those checks
   with translator acceptance.

The implementation supports custom subset front ends, normalized nodes, JavaScript and
Python target generation, a FastAPI service, a browser UI, provenance records, a small
paired evaluation harness, and tests. The LLM path does not silently convert
unsupported-source recognition into a successful end-to-end translation. Diagnostic
contract, risk, failure-fingerprint, and learned-rule fields are metadata; they are not
active control mechanisms or demonstrated causal contributions.

## Live demonstration plan (approximately 7 minutes)

1. **State the scope (45 seconds).** Show the supported-subset table and clarify that
   this is not a complete COBOL/FORTRAN/Pascal/BASIC compiler.
2. **Translate a supported example (90 seconds).** Use the COBOL arithmetic example.
   Show deterministic output and the finite I/O validation status. Explain that the
   source interpreter is limited and is not an independent compiler oracle.
3. **Inspect the pipeline (90 seconds).** Expand tokens, normalized representation,
   emitted rules, coverage basis, and pipeline trace. Clarify that the descriptive
   mapping catalogue is not the executable code-generation engine.
4. **Exercise unsupported syntax (2 minutes).** Use the benchmark's COBOL
   `PERFORM 3 TIMES` example with the configured model. Show unsupported-construct
   reporting, the complete candidate, syntax/runtime checks, the expected-output
   comparison, and the persistent `not_run`/unaccepted status.
5. **Show the paired measurement (90 seconds).** Display rule-only and hybrid counts
   with denominators, then explain why a one-case candidate match is not a pass-rate
   improvement or general correctness result.
6. **Close with failure boundaries (45 seconds).** Explain what happens when the model
   is unavailable and why candidates must be reviewed before use.

If the live provider is unavailable, use a previously captured, clearly labeled
**historical** interaction or a deterministic fake-response test. Never imply that a
recorded candidate is a fresh live result.

## Evaluation snapshot

Recorded paired evaluations used `gemini-3.1-flash-lite`,
`legacy-modernizer-llm-v2`, Python 3.13.1, Node.js v24.20.0, and rule table version
1.3. Forty automated tests passed after the COBOL parser regressions were added. The
24 cases include 12 local examples and 12 project-authored adaptations of
published Rosetta Code task prompts. They are not independently collected legacy
programs.

| Measure | JavaScript target | Python target |
|---|---:|---:|
| End-to-end passes | 23/24 (95.8%) | 23/24 (95.8%) |
| 95% Wilson interval | 79.8–99.3% | 79.8–99.3% |
| Expected outcomes recognized | 24/24 | 24/24 |
| Supported-case expected-output matches | 23/23 | 23/23 |
| Expected-unsupported cases recognized | 1/1 | 1/1 |
| Hybrid candidates generated | 1 | 1 |
| Candidate syntax valid | 1/1 | 1/1 |
| Candidate runtime checked | 1/1 | 0/1 (not run) |
| Candidate expected-output matches | 1/1 | Not scored |
| Candidates accepted by translator | 0 | 0 |

The candidate in both hybrid runs corresponds to the unsupported COBOL loop. In the
JavaScript run, it executed under restricted Node permissions and matched the
separately authored `STEP`-three-times expected output. In the Python run, only syntax
was checked; execution and oracle comparison were not performed. The COBOL source
remained `not_run` in both cases. Accordingly, the headline end-to-end score stayed
23/24 in both rule-only and hybrid variants.

The 95% interval is wide because the sample is small. These pilot results demonstrate
that the system and reporting path execute; they do not show a statistically meaningful
improvement, broad semantic equivalence, or performance on production legacy systems.
See the evidence JSON for exact timestamps, per-case measures, commands, and
limitations.

## Safety and reproducibility

- A fresh app process loads `.env` at startup. Keep API credentials local and never
  include them in screenshots, evaluation artifacts, or source control.
- JavaScript candidate execution uses Node's permission-restricted mode and a scrubbed
  environment. This is a risk reduction, not a complete sandbox or a correctness proof.
- Python candidates are syntax-checked only and are not executed by the fallback
  evaluator.
- Reproduce tests with `python -m pytest -q`.
- Validate corpus metadata with `python tools\corpus.py validate-manifest`.
- Run paired evaluations with
  `python evaluate.py --target JavaScript --output evaluation_result.json` and
  `python evaluate.py --target Python --output evaluation_result.json`. The second
  command overwrites the local, ignored output; preserve reported aggregates in the
  evidence record before rerunning.
- The corpus manifest is provenance metadata, not permission to redistribute upstream
  source. Task-derived examples have licensing review caveats.

## Limitations and reviewer-facing claims

- The 24-case set is small, project-authored/task-derived, and not representative.
- The source interpreter and finite checks do not provide formal equivalence.
- There is one unsupported-construct pilot case; Python candidate runtime behavior is
  not evaluated.
- No candidate is automatically accepted. The system does not provide a general
  semantic acceptance gate for arbitrary user programs.
- Contracts, risk scores, failure fingerprints, and learned-rule records are not
  evaluated control mechanisms.
- Scalability, production readiness, full-language support, multilingual bias, and
  superiority to other translators have not been established.
- The literature review is scoped rather than systematic. The intended “Xu et al.
  2026” multilingual-bias reference remains unidentified; do not cite it as verified.

For a research-paper track, additional work is required before submission: a named
venue's scope and format, a larger license-cleared corpus with independent oracles,
multiple challenging unsupported constructs, repeated controlled model trials, and
comparisons against appropriate baselines. This demo draft deliberately makes none of
those results up.

## Submission checklist

- [ ] Choose a specific conference and confirm that its student demo/poster track accepts
  this project type.
- [ ] Replace this venue-neutral draft with the track's required format and word/page
  limits.
- [ ] Do not submit the existing course DOCX without revision: it predates the latest
  fallback implementation and contains statements that candidates are not integrated.
- [ ] Capture current UI screenshots or a live-demo recording; label model output as an
  unvalidated candidate and keep secrets out of view.
- [ ] Confirm the active server restarted from the current checkout and reports the
  expected model/prompt version.
- [ ] Run the test suite, corpus validation, and both target evaluations immediately
  before submission; update the evidence record if any code or results change.
- [ ] Add only verified author, affiliation, artifact URL, and bibliography details.
- [ ] Do not describe the pilot as proof of semantic equivalence or a demonstrated
  LLM-driven accuracy improvement.
