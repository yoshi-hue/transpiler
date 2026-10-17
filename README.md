# Multi-Language Legacy Code Modernizer

A compiler-design prototype for:

**subset front ends → normalized representation → deterministic code generation → empirical I/O validation**

The prototype supports documented subsets of COBOL, FORTRAN, Pascal, BASIC, and the earlier Python-like language. JavaScript and Python are available as targets for the implemented subset. When configured, the LLM fallback produces a complete target-program candidate for inputs with unsupported constructs. The candidate is shown as target output, the deterministic partial output is retained separately for review, and the candidate is not automatically accepted.

## Project objectives and evidence status

The project objectives are to survey translation approaches, identify evidence-backed research gaps, build a multi-language front end and shared representation, investigate a constrained hybrid backend, validate behavior by execution, and document contributions and limitations. Their current implementation status and the presentation's candidate gap claims are tracked in [`data/PROJECT_OBJECTIVES_AND_GAPS.md`](./data/PROJECT_OBJECTIVES_AND_GAPS.md).

A course-specific DOCX report may contain personal identifiers and is maintained separately from the public repository.

For the selected ICSE 2027 Tool Demonstration track, see the [submission draft](./ICSE_2027_TOOL_DEMO.tex) and [submission checklist](./CONFERENCE_DEMO_SUBMISSION.md). The track requires a four-page IEEE paper, author identities, a public tool with usage instructions, and a public three-to-five-minute video; the draft still needs verified author details and that video.

The main implementation/evaluation boundaries are:

- Front ends, normalized representation, deterministic generation, and finite execution checks are implemented for the subsets in [`data/supported_subset.json`](./data/supported_subset.json).
- A scoped primary-source audit and related-work reading list are documented in [`data/PROJECT_OBJECTIVES_AND_GAPS.md`](./data/PROJECT_OBJECTIVES_AND_GAPS.md). They partially address the survey/gap objectives; they are not an exhaustive or systematic review.
- The LLM fallback can request a complete-program candidate for unsupported input and displays it separately from acceptance while retaining deterministic partial output. JavaScript candidates run in Node's permission mode; Python candidates receive syntax checks only. Candidates are never automatically accepted. Prompt v3 was confirmed in a fresh server from commit `ade68dc`; the refreshed paired run produced no candidate after three provider request attempts for the unsupported COBOL case per target. See [`data/EVIDENCE_V3_REFRESH.md`](./data/EVIDENCE_V3_REFRESH.md).
- Contracts, risk assessments, failure fingerprints, learned-rule records, and the descriptive mapping catalogue are metadata/diagnostic features. They do not currently control acceptance or demonstrate improved correctness.
- Metadata mechanisms (contracts, risk scores, failure records, learned-rule examples) are prototype diagnostics only; no causal benefit is claimed or measured.
- Scalability and multilingual-bias experiments were not conducted and are not claimed contributions or findings. The unidentified “Xu et al. 2026” citation was removed from the paper framing.

## Why this project matters

The project addresses a practical and intellectually meaningful challenge: modernizing code written in legacy imperative languages without losing trust in the result.

Many real-world migration tasks are dominated by highly structured, deterministic constructs such as arithmetic, assignment, branching, and simple loops. Those patterns are well suited to compiler rules, while unusual or unsupported forms still benefit from external model assistance. The design therefore treats the LLM as a focused fallback rather than the primary translator.

This motivates a testable research question: can a validation-gated, scoped model fallback correctly handle some constructs that deterministic rules do not cover? The current prototype has not established that result.

## Research framing and academic contribution

The project is a prototype at the intersection of compiler construction and AI-assisted software maintenance. Its hypothesis is that a rule-first pipeline with scoped model suggestions can keep translation behavior inspectable and, if candidates are integrated behind an independent validation gate, improve results on constructs outside deterministic coverage. The current small benchmark does not establish statistical generality or superiority over alternative systems.

The implemented prototype provides:

- subset front ends and a normalized representation for multiple legacy languages
- rule-first deterministic translation for common constructs
- optional complete-program LLM candidate generation for unsupported constructs, with candidate display separated from semantic acceptance
- executable I/O validation on the documented subset
- provenance-aware evaluation workflow and diagnostic metadata

The supported-subset path is:

```text
supported source → parse/normalize → deterministic target generation → finite I/O check
```

## Research positioning

The paper is framed as an early tool demonstration: a prototype that exposes its declared language subset, deterministic output, unsupported syntax, candidate status, and finite execution checks. The project has not established that the fallback improves translation, that learned rules improve later results, or that the system outperforms other tools.

## What makes the LLM integration meaningful

When configured, the prototype requests a complete target-program candidate when the parser reports unsupported constructs. It sends the full source program so the model can preserve ordering and combine supported and unsupported statements. This is more than a fragment suggestion but remains probabilistic output.

The candidate becomes the displayed/downloadable target output, but the translator does not mark it accepted. JavaScript candidates receive a syntax check and are executed in Node's permission-restricted mode with secrets removed from the child environment. Python candidates receive a syntax check only and are not executed. Even a successful run establishes only behavior on tested inputs. The LLM fallback is therefore not yet a general-purpose or production-ready migration path.

## Research-grade translation safeguards

The translator emits a machine-readable semantic-contract record and diagnostic metadata, including a risk assessment, failure fingerprint, and learned-rule record.

These records do not currently select additional validation, trigger generated tests, change acceptance decisions, integrate candidates, or alter later code generation. Treat them as reporting/diagnostic mechanisms, not evidence of improved reliability.

## Evaluation strategy and benchmark design

The benchmark has 16 development examples and a 20-case held-out set grouped by whole task. It adds tie, singleton-range, and expanded-range cases; three COBOL `PERFORM` variants remain expected-unsupported. Expected outputs are separately authored from fixed constants and loop semantics and checked by a separate reference evaluator (20/20); they have not been checked against native source compilers. This remains a small task-derived benchmark, not a representative corpus. The refreshed v3 paired run is a historical 24-case baseline from the pushed commit; fallback requests failed, so it provides no candidate effectiveness result.

Reproduce the held-out benchmark and its separate expected-output check with:

```powershell
python tools\check_benchmark_oracles.py --output data\oracle_v2_check.json
python tools\run_test_benchmark.py --target JavaScript --output data\benchmark_v2_javascript.json
python tools\run_test_benchmark.py --target Python --output data\benchmark_v2_python.json
```

Candidate review requirements are in [CANDIDATE_ACCEPTANCE.md](./CANDIDATE_ACCEPTANCE.md), and the sample-size and metadata ablation decision are in [BENCHMARK_AND_ABLATION_PROTOCOL.md](./BENCHMARK_AND_ABLATION_PROTOCOL.md).

See [LLM_EVALUATION.md](./LLM_EVALUATION.md) for the recommended protocol.

## Scope

This is a research/course prototype, not a full implementation of COBOL, FORTRAN, Pascal, BASIC, or any other language. Results only apply to the documented subsets and tested constructs. Execution-based validation is empirical I/O validation over the supplied test cases; it is not a formal proof of program equivalence.

## Configure a real external model

Copy `.env.example` to `.env` and replace `LLM_API_KEY` with your Gemini API key. Do **not** commit the API key.

The default configuration uses Google's OpenAI-compatible Gemini endpoint:

```text
LLM_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
LLM_API_MODE=chat
LLM_PROVIDER=Google Gemini
LLM_MODEL=gemini-3.1-flash-lite
LLM_API_KEY=<your Gemini API key>
```

OpenAI-compatible endpoints are also supported. The server accepts OpenAI Responses endpoints by setting `LLM_API_MODE=responses` and using the provider's `/v1/responses` URL.

If your provider requires extra headers, set `LLM_EXTRA_HEADERS` as JSON, for example:

```text
LLM_EXTRA_HEADERS={"HTTP-Referer":"https://localhost:8000","X-Title":"Mini Transpiler"}
```

The UI's **Test LLM connection** button makes a real request to the configured endpoint. It reports the model, request ID and latency without exposing the secret key.

## Run

```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`.

Useful paper/demo API endpoints:

- `GET /rules` returns the JSON rules dataset with coverage counts, family breakdowns, and rule metadata.
- `GET /benchmark?target=JavaScript` runs the curated benchmark.
- `GET /experiment?target=JavaScript&repeats=1` runs the rule-only vs hybrid ablation.

Node.js is required for JavaScript target execution; Python 3 is required for the Python target.

## Deploy as a live website with GitHub Pages

The repository includes a GitHub Actions workflow that publishes the static frontend from `frontend/` whenever you push to `main` or `master`. In the repository's **Settings → Pages**, set the build and deployment source to **GitHub Actions**. After the workflow succeeds, the site will be available at `https://yoshi-hue.github.io/transpiler/`.

GitHub Pages only hosts static files; it cannot run this project's Python/FastAPI backend. To enable translation, benchmarks, experiments, and LLM checks on the published site:

1. Deploy the FastAPI app (`backend.main:app`) to a Python-capable host.
2. Set `LLM_API_KEY` and any other LLM settings as environment variables on that host if you want LLM fallback. Never put the key in the frontend or GitHub Pages.
3. Set `window.TRANSPILER_API_BASE_URL` in [`frontend/config.js`](./frontend/config.js) to the backend's public origin (for example, `https://your-backend.example.com`), then push the change. Do not include an API path or trailing slash.

The frontend and backend can still be run together locally using the instructions above; leave the API URL empty in `frontend/config.js` in that case.

## Evaluation

Run the benchmark from the UI or:

```text
GET /benchmark?target=JavaScript
```

The benchmark combines 12 transparent local cases with 12 task-derived cases based on
independently published Rosetta Code prompts. The adapted source, task URLs, expected
unsupported outcomes, independently authored expected outputs, and required construct labels are in
[`data/external_task_cases.jsonl`](./data/external_task_cases.jsonl). These are
task-derived adaptations, not independently collected legacy source programs. Reported
correctness includes executable source/target I/O agreement and comparison against
separately specified expected outputs on supported cases, plus expected unsupported-syntax
recognition; it is not evidence of full-language coverage. Required
construct coverage matches declared per-case requirements to emitted rule categories.
Per-input source-unit coverage counts parsed IR statement nodes plus parser-reported
unsupported constructs.

The `/rules` endpoint is a descriptive mapping catalogue, not an executable rule-coverage
measure. Do not use its entry count or status labels as evidence of language support.

## Corpus collection and provenance

The implemented subset is enumerated in [`data/supported_subset.json`](./data/supported_subset.json);
screening and oracle policy are in [`data/CORPUS_PROTOCOL.md`](./data/CORPUS_PROTOCOL.md).
[`data/corpus_manifest.jsonl`](./data/corpus_manifest.jsonl) records the current 24 cases,
source hashes, provenance, expected output/outcome, license status, and task-group split.
The current set is a pilot, not an independent corpus.

Validate the committed manifest:

```powershell
python tools\corpus.py validate-manifest
```

For a CodeNet audit, first obtain and extract the official archive yourself; the
documented full archive is 7.8 GB. Then run:

```powershell
python tools\corpus.py audit-codenet --root C:\datasets\Project_CodeNet `
  --output data\codenet_audit.json `
  --candidate-manifest data\codenet_candidate_manifest.jsonl `
  --screen-per-language 100
```

The audit counts metadata submissions and accepted submissions with source files by
language, then deterministically samples up to 100 per matching legacy language for a
conservative parser/translation screen. It does not download or copy source files.
CodeNet repository licensing does not settle rights to every third-party submission;
the audit marks licensing as review-required. A screened candidate is not publication-
ready until its source-site terms, original build status, input fixtures, and independent
oracle have been checked.

IBM's published statistics workbook reports 15,059 Fortran submissions (8,018 accepted),
8,727 Pascal (4,820 accepted), and 1,277 COBOL (727 accepted). It reports Visual Basic
separately (2,116; 1,087 accepted), with no plain BASIC row. These are metadata totals,
not source-present or supported-subset sample counts; details and limitations are in
[`data/CORPUS_PROTOCOL.md`](./data/CORPUS_PROTOCOL.md).

For a future research evaluation, the desired ablation chain is:
1. rule-only baseline
2. rule-first + configured LLM fallback
3. rule-first + contracts + risk-aware validation + learned rules

The third variant is a future experiment, not a currently implemented ablation. The
current experiment only causally compares rule-only behavior with optional LLM
candidate generation. LLM candidates replace deterministic partial output in configured
hybrid runs, and
contracts, risk scores, and learned-rule metadata do not currently change generation or
acceptance. They must not be presented as ablated effectiveness improvements. The 95%
Wilson interval is reported because this benchmark is small; larger independent
collections are needed before making general claims.

Keep the model, prompt version, temperature, benchmark, runtime, and rule table fixed. See `LLM_EVALUATION.md` for the recommended protocol.

## Scope

This is a research/course prototype, not a full implementation of COBOL, FORTRAN, Pascal, BASIC, or any other language. Results only apply to the documented subsets and tested constructs. Execution-based validation is empirical I/O validation over the supplied test cases; it is not a formal proof of program equivalence.
