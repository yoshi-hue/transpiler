# Multi-Language Legacy Code Modernizer

A compiler-design prototype for:

**subset front ends → normalized representation → deterministic code generation → empirical I/O validation**

The prototype supports documented subsets of COBOL, FORTRAN, Pascal, BASIC, and the earlier Python-like language. JavaScript and Python are available as targets for the implemented subset. When configured, the LLM fallback produces a complete target-program candidate for inputs with unsupported constructs. The candidate is shown as target output, the deterministic partial output is retained separately for review, and the candidate is not automatically accepted.

The FORTRAN subset accepts scalar list-directed input (`READ(*,*)`) and scalar
`WRITE(*, '(format)')` output; the format descriptor itself is not reproduced. Integer
division over declared integer variables truncates toward zero. For programs that read stdin, enter
whitespace-separated values in **Program input (stdin)** before translating; without
input, code is generated but execution validation remains pending. This adds a path for
simple CodeNet-style input/output tasks, not general CodeNet compatibility. The CodeNet
audit still requires fixtures and independent oracles before a sample can be counted as
a successful case.

## Project objectives and evidence status

The project objectives are to survey translation approaches, identify evidence-backed research gaps, build a multi-language front end and shared representation, investigate a constrained hybrid backend, validate behavior by execution, and document contributions and limitations. Their current implementation status and the presentation's candidate gap claims are tracked in [`documentation/PROJECT_OBJECTIVES_AND_GAPS.md`](./documentation/PROJECT_OBJECTIVES_AND_GAPS.md).

A course-specific DOCX report may contain personal identifiers and is maintained separately from the public repository.

The project report and paper draft are maintained separately from the runnable prototype. The implementation and evaluation scope are summarized below; the paper draft is supporting documentation rather than a claim of conference readiness.

The main implementation/evaluation boundaries are:

- Front ends, normalized representation, deterministic generation, and finite execution checks are implemented for the subsets in [`data/supported_subset.json`](./data/supported_subset.json).
- A scoped primary-source audit and related-work reading list are documented in [`documentation/PROJECT_OBJECTIVES_AND_GAPS.md`](./documentation/PROJECT_OBJECTIVES_AND_GAPS.md). They partially address the survey/gap objectives; they are not an exhaustive or systematic review.
- The LLM fallback can request a complete-program candidate for unsupported input and displays it separately from acceptance while retaining deterministic partial output. JavaScript candidates run in Node's permission mode; Python candidates can run in an isolated Docker container. The fixed COBOL `PERFORM` provider trial generated both target candidates; each passed its recorded runtime check and matched one predeclared expected output. The Python review report also records three fixture-variant matches. Both candidates remain unaccepted because human review and some other acceptance gates are pending. The earlier paired 24-case v3 benchmark produced no candidate after three provider attempts per target; it remains a historical result, not a contradiction. See the [provider trial](./data/provider_trial_latest.json), [Python trial](./data/provider_trial_latest_python.json), and [acceptance review](./data/provider_trial_python_acceptance_review.json).
- Contracts gate local rule storage, risk profiles select repeatability checks and high-risk review, and learned statement templates can generate matching restricted programs. These safeguards and transformations have not yet shown a causal correctness improvement.
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

## Rule-first, contracts, risk, and rule memory

- **Rule-first generation:** the documented deterministic front ends and code generators run before any optional LLM fallback. Unsupported syntax is reported; an LLM result remains a separate candidate.
- **Executable contract checks:** each result includes a source hash and checks for complete supported-source coverage, target execution, finite output agreement, and risk-selected repeatability. Any unsupported source, non-passing validation, failed contract check, or contract state other than `satisfied_for_tested_inputs` blocks the API's `acceptance_policy.eligible_for_use`; the same conditions block learned-rule storage. A pass means eligible for use after finite checks only, not human approval or equivalence proof. The source-side oracle is the project interpreter, not a native compiler.
- **Risk-aware validation:** low risk runs source and target once, medium risk runs each twice, and high risk runs each three times. Repeatability failures block eligibility. High risk additionally requires human review and blocks learned-rule storage. The API exposes risk level, run count, review requirement, storage decision, and blocking reasons; the UI shows the decision. Repeated runs are a determinism check, not additional input coverage.
- **Learned-rule memory:** a successful low/medium-risk deterministic example can be stored as a local exact-schema template for flat assignment/print IR. Reuse requires the same ordered statement kinds, scalar atom kinds, and identifier dependency shape, plus matching source/target, learner-schema version, and deterministic rule-table version. Variable spellings and literal values are slots; this is bounded template substitution, not inference of a source-language rule from one example. Unsupported or ambiguous IR is rejected. Every reuse is revalidated; a cache miss/rejection leaves deterministic generation in place. Loops, branches, compound expressions, and LLM candidates are not learned.

The arithmetic “property validation” field is currently marked `not_run`; the prototype does not invent property-test expectations from source text.

## Research positioning

The paper is framed as an early tool demonstration: a prototype that exposes its declared language subset, deterministic output, unsupported syntax, candidate status, and finite execution checks. The project has not established that the fallback improves translation, that learned rules improve later results, or that the system outperforms other tools.

## What makes the LLM integration meaningful

When configured, the prototype requests a complete target-program candidate when the parser reports unsupported constructs. It sends the full source program so the model can preserve ordering and combine supported and unsupported statements. This is more than a fragment suggestion but remains probabilistic output.

The candidate becomes the displayed/downloadable target output, but the translator does not mark it accepted. JavaScript candidates receive a syntax check and are executed in Node's permission-restricted mode with secrets removed from the child environment. Python candidates receive syntax validation and, when Docker is available, run in a no-network, read-only, resource-limited container. A runtime pass establishes behavior only on the recorded inputs; acceptance still requires source review, independent fixtures, security review, regression checks, and human review. The LLM fallback is not a general-purpose migration path.

## Research-grade translation safeguards

The translator emits a machine-readable semantic-contract record and diagnostic metadata, including a risk assessment, failure fingerprint, and learned-rule record.

The risk profile selects repeatability runs, and the acceptance policy gates eligibility and learned-rule/example storage. These controls do not trigger generated tests, integrate model candidates, or establish improved reliability; treat them as prototype safeguards rather than evidence of a causal benefit.

## Evaluation strategy and benchmark design

The manifest has 42 records: 16 development cases and 26 held-out cases across eight task groups. The held-out split has 22 supported translations and four expected-unsupported cases. Six CodeNet Fortran cases cover p02600, p02606, p02607, p03997 (Trapezoids), p02724 (Golden Coins), and p03238 (Programming Education); each source has a recorded native GNU Fortran 14.3.0 build. The separate oracle checker matches 25 expected-output cases and 38 declared fixtures. The independent owner review of CodeNet terms and task/oracle behavior is still pending. The frozen review packet is [`data/independent_oracle_review_queue_v2.json`](./data/independent_oracle_review_queue_v2.json); it is not a completed review. Adding three CodeNet task groups increased the test split from five to eight groups, but this remains a small pilot, not a representative corpus.

Reproduce the held-out benchmark and its separate expected-output check with:

```powershell
python tools\check_benchmark_oracles.py --output data\oracle_current_check.json
python tools\run_test_benchmark.py --target JavaScript --output data\reproduced_test_26_javascript.json
python tools\run_test_benchmark.py --target Python --output data\reproduced_test_26_python.json
```

Candidate review requirements are in [documentation/CANDIDATE_ACCEPTANCE.md](./documentation/CANDIDATE_ACCEPTANCE.md), and the sample-size and metadata ablation decision are in [documentation/BENCHMARK_AND_ABLATION_PROTOCOL.md](./documentation/BENCHMARK_AND_ABLATION_PROTOCOL.md).

See [documentation/LLM_EVALUATION.md](./documentation/LLM_EVALUATION.md) for the recommended protocol.

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

To record a reproducible translation smoke trial (fixed source, expected output,
prompt/model/request metadata, candidate hash, and runtime/oracle result), configure the
same environment variables and run:

```powershell
python tools\run_llm_provider_trial.py --target JavaScript --output data\provider_trial_latest.json
```

The report explicitly says `not_configured` if endpoint/model credentials are missing.
The fixed trial is a provider smoke check, not evidence of effectiveness or acceptance.

## Run with Docker

The prototype walkthrough uses the included container, which provides Python and Node.js
for both target paths. From the repository root:

```bash
docker compose up --build
```

Open <http://127.0.0.1:8000>. Press Ctrl+C to stop. The first run builds the image and
installs dependencies. The default Compose service does not load `.env`, so the demo
cannot make external model requests. To explicitly enable the optional fallback, set
`LLM_API_KEY` in a local `.env` file and start with
`docker compose -f compose.yaml -f compose.llm.yaml up --build`. Never commit `.env`.
The container stores learned-rule and validated-example records under `/tmp`; those
local demo records last only for the lifetime of the container.

After publishing a version tag and making the GitHub Container Registry package public,
users can run the prebuilt image without building source:

```bash
docker compose -f compose.image.yaml up
```

The `v*` tag workflow publishes the versioned and `latest` images. The repository owner
must publish a release tag and set the GHCR package visibility to public before this
pull-based path is available.

For the first release, after reviewing the final source and passing CI:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Wait for **Publish demo container** to pass in GitHub Actions, make the generated
`ghcr.io/yoshi-hue/transpiler` package public in the repository's Packages settings, and
verify the `compose.image.yaml` pull path from a clean machine.

The guided demo sequence is in [`documentation/DEMO_WALKTHROUGH.md`](./documentation/DEMO_WALKTHROUGH.md).

## Run locally

### Prerequisites
- **Python**: 3.10+ (tested with Python 3.13.1)
- **Node.js**: Node 18+ (tested with Node.js v24.20.0, required for JavaScript target execution)

### 1. Setup Virtual Environment & Dependencies

**Windows PowerShell:**
`powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
`

**macOS / Linux:**
`ash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
`

### 2. Start the Application Server

Run the FastAPI backend with hot reloading enabled:
`powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
`

Once started, open your browser and navigate to:
**http://127.0.0.1:8000**

The web UI allows you to select a source language (COBOL, FORTRAN, Pascal, BASIC, or Python-like), enter code or select a preloaded sample, choose a target (JavaScript or Python), run transpilation, view AST/IR representations, inspect rule diagnostics, and verify execution output.

### 3. Run Automated Tests & Reproducible Benchmarks

To verify the installation and run the full test suite locally:
`powershell
# Run all unit and integration tests (58 passing tests)
python -m pytest

# Run the deterministic held-out benchmark (26 cases across 8 task groups)
python tools\run_test_benchmark.py --target JavaScript --output data\reproduced_test_26_javascript.json
python tools\run_test_benchmark.py --target Python --output data\reproduced_test_26_python.json

# Verify independent expected-output oracles and input fixtures
python tools\check_benchmark_oracles.py --output data\oracle_current_check.json
`


Useful paper/demo API endpoints:

- `GET /rules` returns the JSON rules dataset with coverage counts, family breakdowns, and rule metadata.
- `GET /benchmark?target=JavaScript` runs the curated benchmark.
- `GET /experiment?target=JavaScript&repeats=1` runs the offline three-arm ablation. Add `&enable_llm=true` only to allow live model requests.

Node.js is required for JavaScript target execution; Python 3 is required for the Python target.

## Deploy as a live website with GitHub Pages

The repository includes a GitHub Actions workflow that publishes the static frontend from `frontend/` whenever you push to `main` or `master`. In the repository's **Settings → Pages**, set the build and deployment source to **GitHub Actions**. After the workflow succeeds, the site will be available at `https://yoshi-hue.github.io/transpiler/`.

GitHub Pages only hosts static files; it cannot run this project's Python/FastAPI backend. To enable translation, benchmarks, experiments, and LLM checks on the published site:

1. Deploy the FastAPI app (`backend.main:app`) to a Python-capable host.
2. Set `LLM_API_KEY` and any other LLM settings as environment variables on that host if you want LLM fallback. Never put the key in the frontend or GitHub Pages.
3. Set `CORS_ALLOWED_ORIGINS` on the backend to a comma-separated list of exact frontend origins (for example, `https://yoshi-hue.github.io`). Same-origin deployments do not need CORS. The API does not enable credentialed cross-origin requests.
4. Set `window.TRANSPILER_API_BASE_URL` in [`frontend/config.js`](./frontend/config.js) to the backend's public origin (for example, `https://your-backend.example.com`), then push the change. Do not include an API path or trailing slash.

The frontend and backend can still be run together locally using the instructions above; leave the API URL empty in `frontend/config.js` in that case.

## Evaluation

The checked environment uses Python 3.13.1 and Node.js 24.20.0. Runtime and development
requirements are pinned, so a clean environment resolves the same package versions. Install
development dependencies and run the project suite with:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The release workflow runs this suite before publishing a container tag.
The current clean-environment commands, exact tool versions, test result, Docker
startup check, benchmark reports, and remaining review gates are archived in
[`data/reproducibility_current.json`](./data/reproducibility_current.json).

Run the benchmark from the UI or:

```text
GET /benchmark?target=JavaScript
```

The held-out benchmark evaluates 26 cases across eight task groups: 20 project-authored
adaptations of independently published Rosetta Code prompts and six CodeNet Fortran
submissions from six task groups. The complete manifest also retains 12 local smoke cases
and four development task adaptations, all excluded from held-out scoring. The adapted sources, task URLs, expected outcomes, expected outputs, and
required construct labels are in [`data/external_task_cases.jsonl`](./data/external_task_cases.jsonl).
The Rosetta Code examples are task-derived adaptations, not independently collected
legacy source programs. Reported correctness includes executable source/target I/O
agreement and separately specified expected outputs for supported cases, plus expected
unsupported-syntax recognition; it is not evidence of full-language coverage. Required
construct coverage matches declared per-case requirements to emitted rule categories.
Per-input source-unit coverage counts parsed IR statement nodes plus parser-reported
unsupported constructs. The CodeNet native builds and fixtures are documented in
[`data/codenet_case_review_p02600.json`](./data/codenet_case_review_p02600.json),
[`data/codenet_case_review.json`](./data/codenet_case_review.json) for p02606,
[`data/codenet_case_review_p02607.json`](./data/codenet_case_review_p02607.json), and the
new hash-bound reviews for [p03997](./data/codenet_case_review_p03997.json),
[p02724](./data/codenet_case_review_p02724.json), and
[p03238](./data/codenet_case_review_p03238.json).

The `/rules` endpoint is a descriptive mapping catalogue, not an executable rule-coverage
measure. Do not use its entry count or status labels as evidence of language support.

## Corpus collection and provenance

The implemented subset is enumerated in [`data/supported_subset.json`](./data/supported_subset.json);
screening and oracle policy are in [`documentation/CORPUS_PROTOCOL.md`](./documentation/CORPUS_PROTOCOL.md).
[`data/corpus_manifest.jsonl`](./data/corpus_manifest.jsonl) records 42 entries: 16
development and 26 held-out records across eight task groups, with source hashes,
provenance, expected outcomes/outputs, license status, and task-group splits. The
current set is a pilot, not an independent corpus.

Validate the committed manifest:

```powershell
python tools\corpus.py validate-manifest
```

Recreate stable benchmark reports (no timestamps, secrets, or local worktree state are
written into the JSON):

```powershell
python tools\check_benchmark_oracles.py --output data\oracle_current_check.json
python tools\run_test_benchmark.py --target JavaScript --output data\reproduced_test_26_javascript.json
python tools\run_test_benchmark.py --target Python --output data\reproduced_test_26_python.json
python tools\run_ablation.py --target JavaScript --output data\reproduced_ablation_26_javascript.json
python tools\run_ablation.py --target Python --output data\reproduced_ablation_26_python.json
```

The ablation command disables LLM requests unless `--enable-llm` is explicitly supplied.
The offline report is reproducible for the same source hashes and Python/Node versions.
Live provider results can vary and must be treated as separate trials. Docker Compose setup
also has a local capture/profile exclusion in `.dockerignore`; do not commit `.env`, browser
profiles, screenshots, or local debug logs.

For an explicit live provider ablation from the local `.env`, opt in to both the request
and dotenv loading:

```powershell
python tools\run_ablation.py --target JavaScript --output data\my_live_ablation_javascript.json --repeats 5 --enable-llm --load-dotenv
python tools\run_ablation.py --target Python --output data\my_live_ablation_python.json --repeats 5 --enable-llm --load-dotenv
```

The latest live ablation uses the frozen 26-case, eight-group test split and five repeats per arm. With provider network access enabled, both targets generated 15 candidates for the three project-authored COBOL loop variants; all 15 per target passed syntax, target runtime, and predeclared output checks. No candidate was accepted. Each arm had 110/130 supported validation passes (22/22 supported cases per repeat), while expected-unsupported recognition was 20/20. Learned-rule reuse was zero, and the third arm matched the rule-only and hybrid pass counts. This does not establish an improvement. See [the protocol and latest results](./documentation/BENCHMARK_AND_ABLATION_PROTOCOL.md), [JavaScript](./data/controlled_ablation_live_v9_javascript.json), and [Python](./data/controlled_ablation_live_v8_python.json).

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
Project CodeNet's full dataset is distributed under CDLA-Permissive-2.0; the CDLA FAQ
says the agreement is intended to cover both datasets and their individual contents.
Redistribution requires making the agreement text available with the data. The
repository's Apache license covers repository code, not the dataset. Source-site
provenance, build status, fixtures, and oracle evidence still need case-level review.

IBM's published statistics workbook reports 15,059 Fortran submissions (8,018 accepted),
8,727 Pascal (4,820 accepted), and 1,277 COBOL (727 accepted). It reports Visual Basic
separately (2,116; 1,087 accepted), with no plain BASIC row. These are metadata totals,
not source-present or supported-subset sample counts; details and limitations are in
[`documentation/CORPUS_PROTOCOL.md`](./documentation/CORPUS_PROTOCOL.md).

The local CodeNet audit has now scanned 4,053 metadata files (13,916,868 submissions;
7,460,588 marked accepted). It found source files for all accepted COBOL, Fortran, and
Pascal records in those metadata labels (13,565 total). A deterministic sample of 10
per language yielded 27 parser/pipeline errors and 3 unsupported-syntax results, with
zero prototype-screen passes at that time. A later rescreen of the same 30 archived
sources after scalar Fortran stdin/output support produced one fixture-backed prototype
pass on five fixtures (three official AtCoder examples and two derived boundary cases),
24 parser/pipeline errors, and five unsupported results. CodeNet metadata records GNU
Fortran 9.2.1 and Accepted status. A local GNU Fortran 14.3.0 build passed with
explicit free-form mode and all three official plus two derived fixtures. Project
CodeNet's dataset is released under CDLA-Permissive-2.0; the CDLA FAQ says the license
covers a dataset and its individual contents. AtCoder says authors retain copyright,
which does not itself negate a dataset license. No separate file-level license header
was found for this sample. A second submission, p02607/s779285219 ("B: An Odd Problem"),
is now in the held-out expected-unsupported set: its array input is outside the
documented subset, and it passed a local GNU Fortran 14.3.0 build against two official
samples and two derived fixtures. The CDLA agreement text is included at
[`data/licenses/CDLA-Permissive-2.0.txt`](./data/licenses/CDLA-Permissive-2.0.txt).
See the saved
[`audit report`](./data/codenet_audit.json) and
[`candidate metadata`](./data/codenet_candidate_manifest.jsonl), plus
[`local screening manifest`](./data/codenet_local_screening_manifest.jsonl), and
[`case build and rights review`](./data/codenet_case_review.json) and
[`second CodeNet case review`](./data/codenet_case_review_p02607.json).

The current deterministic outputs are archived for
[`JavaScript`](./data/reproduced_test_26_javascript.json) and
[`Python`](./data/reproduced_test_26_python.json): 22/22 supported cases passed, with all 34
fixtures matched, and 4/4 expected-unsupported cases were recognized. The test set has
eight task groups and remains too small for broad generalization claims.

The experiment endpoint reports three matched arms:
1. rule-only baseline
2. rule-first + configured LLM fallback
3. rule-first + development-seeded learned-rule memory (contracts/risk are shared)

The learned-rule arm seeds a temporary store from development cases and evaluates the
held-out cases without allowing test-to-test learning. Contracts and risk behavior are
shared across arms, so this experiment does not estimate their individual effects. LLM
candidates remain unaccepted. Reviewer effort is not collected and is reported as
unavailable. The following one-repeat reports are historical 20-case
baselines from before the CodeNet case was added; they are archived in
the historical ablation snapshots omitted from the final repository. Both used the same 20
held-out cases from two task groups; no LLM provider was configured and no learned-rule
reuse occurred. All arms had 17/20 overall passes, 17/17 supported-case passes, and
3/3 expected-unsupported cases recognized. These runs show no observed difference and
do not establish effectiveness. The 95% Wilson interval is reported because this
benchmark is small; larger independent collections are needed before general claims.

The latest five-repeat live ablations use the same 26 cases and eight groups for both
targets: [JavaScript v9](./data/controlled_ablation_live_v9_javascript.json) and
[Python v8](./data/controlled_ablation_live_v8_python.json). Each arm has 130 observations:
110 supported-case passes and 20 expected-unsupported recognitions. The hybrid arm
produced 15 candidates per target, all passing syntax/runtime and output checks, but none
were accepted. Learned-rule reuse was zero. Provider network access was explicitly enabled
and CodeNet sources were withheld from requests. Human review effort remains unmeasured.

Keep the model, prompt version, temperature, benchmark, runtime, and rule table fixed. See `documentation/LLM_EVALUATION.md` for the recommended protocol.

## Scope

This is a research/course prototype, not a full implementation of COBOL, FORTRAN, Pascal, BASIC, or any other language. Results only apply to the documented subsets and tested constructs. Execution-based validation is empirical I/O validation over the supplied test cases; it is not a formal proof of program equivalence.
