# LLM fallback evaluation protocol

The LLM component is an experimental translation assistant, not an oracle. A conference-quality evaluation must distinguish deterministic translation, LLM-assisted candidates, target compilation, and semantic validation.

## 1. Configure one fixed model

Set `LLM_API_URL`, `LLM_API_MODE`, `LLM_MODEL`, and `LLM_API_KEY` in the server environment. Do not put the key in HTML, JavaScript, Git, or screenshots.

For Google Gemini, use its OpenAI-compatible chat endpoint:

```text
LLM_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
LLM_API_MODE=chat
LLM_PROVIDER=Google Gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=<your Gemini API key>
```

For an OpenAI Responses API deployment, use an endpoint ending in `/v1/responses` and `LLM_API_MODE=responses`.

## 2. Establish a deterministic baseline

Run the benchmark with the LLM disabled. Report:
- number of programs
- deterministic rule coverage
- unsupported constructs
- target runtime failures
- output mismatches
- end-to-end validation pass rate
- 95% Wilson interval for the pass rate
- required-construct coverage based on emitted rule categories

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

| Metric | Rule-only | Hybrid | Full stack |
|---|---:|---:|---:|
| Programs | | | |
| Deterministic rule coverage | | | |
| Unsupported constructs | | | |
| LLM calls | 0 | | |
| Target execution success | | | |
| Semantic validation success | | | |
| Output mismatches | | | |
| Median LLM latency (ms) | — | | |
| LLM requests rejected | — | | |
| Delta vs baseline | — | | |

The desired full conference-style ablation chain is:

- Rule-only baseline
- Rule-first + LLM fallback
- Rule-first + contracts + risk-aware validation + learned rules (not yet implemented as a toggled ablation)

**Current implementation limitation:** only rule-only versus optional LLM candidate
generation is measured. Fallback candidates are not inserted into generated code, so
their acceptance count is zero and they cannot currently improve end-to-end correctness.
Contracts, risk assessments, and learned-rule metadata do not change translation or
acceptance decisions; do not report them as causal ablations until switches and
independent outcome measures are implemented.

The current benchmark includes 12 local cases and 12 source-attributed adaptations of
Rosetta Code task prompts (A+B, Maximum of two numbers, and Loops/For). These are task-derived
challenge cases, not a representative corpus of independently collected legacy
programs. Each translatable case has an expected-output oracle authored separately from
the source interpreter. See [`data/external_task_cases.jsonl`](./data/external_task_cases.jsonl)
for per-case expected output, URLs, and adaptation notes.

This makes the experiment immediately interpretable: if the full stack improves correctness without harming determinism, its value is clearer than a single opaque end-to-end number.

## 6. Minimum evidence for publication-quality reporting

For a workshop or demo-style venue, the project should include at least:

- a benchmark table with per-language results
- a construct-level breakdown for arithmetic, branching, loops, and unsupported constructs
- median and tail latency for LLM requests
- failure taxonomy counts (unsupported syntax, runtime error, output mismatch, rejected candidate)
- a statement of the exact evaluation protocol and a fixed model snapshot

## 7. Reproducibility

Archive the exact benchmark source files, model identifier, prompt version, rule-table version, target runtime version, and aggregate results. API keys and private source code must not be archived.

## 8. Suggested reporting template

```text
Model: gemini-2.5-flash
Prompt version: v3.1
Target runtime: Node.js 20 / Python 3.12
Benchmark: legacy subset benchmark (N cases)

Rule-only baseline:
- success: X%
- unsupported: Y
- mismatches: Z

Hybrid:
- success: X%
- LLM calls: N
- median latency: M ms
- rejected candidates: K

Full stack:
- success: X%
- validation failures: Y
- learned rules added: Z
```

Do not claim that hybrid translation is superior unless the benchmark and evaluation protocol support that conclusion. Report per-language and per-construct breakdowns as well as aggregate numbers.

The `/rules` endpoint returns a descriptive mapping catalogue, not executable rule
coverage. Its entry count and status labels must not be used as a coverage or correctness
metric.
