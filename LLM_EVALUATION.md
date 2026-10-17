# LLM fallback evaluation protocol

The LLM component is an experimental translation assistant, not an oracle. A conference-quality evaluation must distinguish deterministic translation, LLM-assisted candidates, target compilation, and semantic validation.

## 1. Configure one fixed model

Set `LLM_API_URL`, `LLM_API_MODE`, `LLM_MODEL`, and `LLM_API_KEY` in the server environment. Do not put the key in HTML, JavaScript, Git, or screenshots.

For Google Gemini, use its OpenAI-compatible chat endpoint:

```text
LLM_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
LLM_API_MODE=chat
LLM_PROVIDER=Google Gemini
LLM_MODEL=gemini-3.1-flash-lite
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

For parser-reported unsupported syntax, the application sends the complete source
program once and asks for one complete target program. This preserves statement order
better than requesting and concatenating unrelated fragments. For a returned candidate,
the application records a request ID, model, prompt version/hash, attempt count, HTTP
status, latency, and candidate output. On failure, it records request ID, attempts,
latency, and a failure message; the benchmark keeps a redacted failure category and
HTTP status, when available.

The current implementation uses prompt version `legacy-modernizer-llm-v3`. Source and
context are JSON-quoted as untrusted text, and model instructions explicitly say not
to follow instructions embedded in code comments or literals. The older v2 result in
[`data/project_report_evidence.json`](./data/project_report_evidence.json) is historical
and must not be presented as an evaluation of v3. Retry settings
are bounded at startup; transient HTTP errors are retried, permanent client errors are
reported immediately, and a provider `Retry-After` value is respected up to 30 seconds.

## 4. Acceptance policy

An LLM candidate is **not** automatically accepted.

A candidate can be classified as:
- `candidate_generated`: model produced target code
- `target_syntax_valid`: candidate parses as the target language
- `target_runtime_valid`: JavaScript candidate executes under Node's permission-restricted mode; Python candidates are syntax-checked but not executed and must be counted as runtime-not-run, not runtime failures
- `validation_status`: `runtime_valid_unverified`, `syntax_valid_runtime_not_run`, `rejected_syntax`, `rejected_runtime`, `runtime_unavailable`, or `syntax_check_unavailable`
- `candidate_oracle_match`: candidate output matches a separately authored expected output for a fixed benchmark input
- `semantically_validated`: source and target behavior agree over the defined independent test inputs
- `rejected`: candidate cannot be compiled/executed or disagrees with the source

An oracle match is evidence for that tested input only, not a proof of equivalence or
general correctness. The translator does not automatically accept model candidates.

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
| Median LLM latency (ms) | -- | |
| LLM requests rejected | -- | |
| Delta vs baseline | -- | |

Metadata features are excluded from the causal comparison: contracts, risk assessments,
failure fingerprints, and learned-rule records do not alter code generation, validation,
or acceptance. Describe them as prototype diagnostics. The only implemented paired
comparison is rule-only versus hybrid candidate generation; it does not isolate or test
the metadata features.

The strengthened benchmark now contains 36 manifest records: 16 development examples
(local smoke tests plus the A+B task family) and 20 test examples from two held-out task
families (Maximum of two numbers and Loops/For). The test set adds equal-value maxima,
singleton and expanded ranges, and three expected-unsupported COBOL PERFORM variants.
The benchmark runner scores only the test split. Expected outputs are separately authored
from constants and loop semantics and match the separate reference evaluator (20/20),
but have not been executed in native source compilers or checked by a second human; this
remains a small task-derived pilot. The test set is not large enough to support a
broad effectiveness claim. See [`BENCHMARK_AND_ABLATION_PROTOCOL.md`](./BENCHMARK_AND_ABLATION_PROTOCOL.md)
for task grouping and the sample-size design.

## 6. Minimum evidence for publication-quality reporting

For a future effectiveness paper, the project should include at least:

- a benchmark table with per-language results
- a construct-level breakdown for arithmetic, branching, loops, and unsupported constructs
- median and tail latency for LLM requests
- failure taxonomy counts (unsupported syntax, runtime error, output mismatch, rejected candidate)
- a statement of the exact evaluation protocol and a fixed model snapshot

## 7. Reproducibility

The CLI loads project-local `.env` settings for reproducible experiments. Run the same
paired benchmark against each target with:

```powershell
python evaluate.py --target JavaScript --output evaluation_result.json
python evaluate.py --target Python --output evaluation_result.json
```

The JSON output is local/ignored and is overwritten by the second command. Record the
aggregate measures and exact environment in the evidence record before rerunning for
another target. Archive the exact benchmark source files, model identifier, prompt
version, rule-table version, target runtime version, and aggregate results. API keys
and private source code must not be archived.

## 8. Suggested reporting template

```text
Model: gemini-3.1-flash-lite
Prompt version: legacy-modernizer-llm-v3
Target runtime: record exact Node.js and Python versions from the run
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

```

Do not claim that hybrid translation is superior unless the benchmark and evaluation protocol support that conclusion. Report per-language and per-construct breakdowns as well as aggregate numbers.

The `/rules` endpoint returns a descriptive mapping catalogue, not executable rule
coverage. Its entry count and status labels must not be used as a coverage or correctness
metric. Candidate acceptance requirements are specified in [`CANDIDATE_ACCEPTANCE.md`](./CANDIDATE_ACCEPTANCE.md).
