# LLM fallback evaluation protocol

The LLM component is an experimental translation assistant, not an oracle. A conference-quality evaluation must distinguish deterministic translation, LLM-assisted candidates, target compilation, and semantic validation.

## 1. Configure one fixed model

Set `LLM_API_URL`, `LLM_API_MODE`, `LLM_MODEL`, and `LLM_API_KEY` in the server environment. Do not put the key in HTML, JavaScript, Git, or screenshots.

For an OpenAI Responses API deployment, use an endpoint ending in `/v1/responses` and `LLM_API_MODE=responses`.

## 2. Establish a deterministic baseline

Run the benchmark with the LLM disabled. Report:
- number of programs
- deterministic rule coverage
- unsupported constructs
- target runtime failures
- output mismatches
- end-to-end validation pass rate

## 3. Run the hybrid system

Enable the same model and rerun exactly the same benchmark. Keep fixed:
- model identifier
- prompt version
- temperature (0)
- benchmark programs
- target runtime
- timeout policy

The application records a request ID, model, prompt version/hash, attempt count, HTTP status, latency, and candidate output for each fallback request.

## 4. Acceptance policy

An LLM candidate is **not** automatically accepted.

A candidate can be classified as:
- `candidate_generated`: model produced target code
- `target_runtime_valid`: generated target fragment/program executes
- `semantically_validated`: source and target outputs agree under the project's executable test harness
- `rejected`: candidate cannot be compiled/executed or disagrees with the source

Only the last two categories support a correctness claim. A model response by itself is not evidence of semantic equivalence.

## 5. Reportable metrics

Recommended table columns:

| Metric | Rule-only | Hybrid |
|---|---:|---:|
| Programs | | |
| Deterministic rule coverage | | |
| Unsupported constructs | | |
| LLM calls | 0 | |
| Target execution success | | |
| Semantic validation success | | |
| Output mismatches | | |
| Median LLM latency (ms) | — | |
| LLM requests rejected | — | |

Do not claim that hybrid translation is superior unless the benchmark and evaluation protocol support that conclusion. Report per-language and per-construct breakdowns as well as aggregate numbers.

## 6. Reproducibility

Archive the exact benchmark source files, model identifier, prompt version, rule-table version, target runtime version, and aggregate results. API keys and private source code must not be archived.
