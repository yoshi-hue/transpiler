# Multi-Language Legacy Code Modernizer

A compiler-design prototype for:

**subset front ends → normalized representation → deterministic code generation → empirical I/O validation**

The prototype supports documented subsets of COBOL, FORTRAN, Pascal, BASIC, and the earlier Python-like language. JavaScript and Python are available as targets for the implemented subset. The optional LLM path can produce suggestions for unsupported constructs when configured, but those candidates are not integrated into target code or automatically accepted.

## Project objectives and evidence status

The project objectives are to survey translation approaches, identify evidence-backed research gaps, build a multi-language front end and shared representation, investigate a constrained hybrid backend, validate behavior by execution, and document contributions and limitations. Their current implementation status and the presentation's candidate gap claims are tracked in [`data/PROJECT_OBJECTIVES_AND_GAPS.md`](./data/PROJECT_OBJECTIVES_AND_GAPS.md).

A course-specific DOCX report may contain personal identifiers and is maintained separately from the public repository.

The main implementation/evaluation boundaries are:

- Front ends, normalized representation, deterministic generation, and finite execution checks are implemented for the subsets in [`data/supported_subset.json`](./data/supported_subset.json).
- The LLM-fallback improvement is a research objective, not an established result. Current evidence records zero configured LLM cases and zero model calls; generated candidates are not integrated into output.
- Contracts, risk assessments, failure fingerprints, learned-rule records, and the descriptive mapping catalogue are metadata/diagnostic features. They do not currently control acceptance or demonstrate improved correctness.
- The candidate literature gaps are not presented as verified findings until their primary sources and exact citations are checked.

## Why this project matters

The project addresses a practical and intellectually meaningful challenge: modernizing code written in legacy imperative languages without losing trust in the result.

Many real-world migration tasks are dominated by highly structured, deterministic constructs such as arithmetic, assignment, branching, and simple loops. Those patterns are well suited to compiler rules, while unusual or unsupported forms still benefit from external model assistance. The design therefore treats the LLM as a focused fallback rather than the primary translator.

This motivates a testable research question: can a validation-gated, scoped model fallback correctly handle some constructs that deterministic rules do not cover? The current prototype has not established that result.

## Research framing and academic contribution

The project is a prototype at the intersection of compiler construction and AI-assisted software maintenance. Its hypothesis is that a rule-first pipeline with scoped model suggestions can keep translation behavior inspectable and, if candidates are integrated behind an independent validation gate, improve results on constructs outside deterministic coverage. The current small benchmark does not establish statistical generality or superiority over alternative systems.

The project contributes:

- subset front ends and a normalized representation for multiple legacy languages
- rule-first deterministic translation for common constructs
- optional LLM candidate generation for unsupported constructs; candidate integration is not implemented
- executable I/O validation on the documented subset
- provenance-aware evaluation workflow and diagnostic metadata

The current implemented path can be summarized as:

```text
supported source → parse/normalize → deterministic target generation → finite I/O check
```

## Research positioning

This project is best framed as a hybrid compiler + AI systems paper centered on reliable translation under uncertainty.

Research hypotheses to test (not findings established by the current benchmark):

- “We show that deterministic compiler rules can capture the majority of legacy-language behavior while an LLM handles only unsupported fragments.”
- “Translation correctness is treated as a validation problem, not merely a code-generation problem.”
- “Verified fallback patterns are accumulated into the rule set, lowering future dependence on external model calls.”

These are hypotheses, not findings. The LLM-improvement question requires a configured model, candidate integration behind validation, independent test oracles, and paired evaluation. Any effectiveness claim still requires larger independent evaluation.

## What makes the LLM integration meaningful

When configured, the prototype may request suggestions for parser-reported unsupported constructs after deterministic generation. The request includes source context; it is not currently restricted to a small IR subtree. The model path is optional and has not been exercised by the current benchmark evidence.

The LLM output remains a **candidate** and is not integrated into generated target code or automatically accepted. Consequently, current validation results measure deterministic translation, not end-to-end LLM fallback effectiveness.

## Research-grade translation safeguards

The translator emits a machine-readable semantic-contract record and diagnostic metadata, including a risk assessment, failure fingerprint, and learned-rule record.

These records do not currently select additional validation, trigger generated tests, change acceptance decisions, integrate candidates, or alter later code generation. Treat them as reporting/diagnostic mechanisms, not evidence of improved reliability.

## Evaluation strategy and benchmark design

The project includes a small benchmark and a rule-only versus optional-LLM-candidate experiment. A full metadata/validation ablation is future work, not an implemented comparison. A future conference-style evaluation should compare:

1. Rule-only baseline
2. Hybrid rule-first + LLM fallback
3. Full system with contracts, risk-aware validation, and learned rules

Only the first two variants are represented by the current experiment harness, and the latest run configured no LLM cases. The benchmark should report per-language and per-construct success, unsupported-syntax recognition, fallback frequency, validation failures, and latency when those measures are actually available.

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
LLM_MODEL=gemini-2.5-flash
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
candidate generation. LLM candidates are not inserted into generated target code, and
contracts, risk scores, and learned-rule metadata do not currently change generation or
acceptance. They must not be presented as ablated effectiveness improvements. The 95%
Wilson interval is reported because this benchmark is small; larger independent
collections are needed before making general claims.

Keep the model, prompt version, temperature, benchmark, runtime, and rule table fixed. See `LLM_EVALUATION.md` for the recommended protocol.

## Scope

This is a research/course prototype, not a full implementation of COBOL, FORTRAN, Pascal, BASIC, or any other language. Results only apply to the documented subsets and tested constructs. Execution-based validation is empirical I/O validation over the supplied test cases; it is not a formal proof of program equivalence.
