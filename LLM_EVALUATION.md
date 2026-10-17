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
better than requesting and concatenating unrelated fragments. The application records
a request ID, model, prompt version/hash, attempt count, HTTP status, latency, and
candidate output for each fallback request.

The current implementation uses prompt version `legacy-modernizer-llm-v3`. Source and
context are JSON-quoted as untrusted text, and model instructions explicitly say not
to follow instructions embedded in code comments or literals. The recorded v2 pilot
below is historical and should not be presented as an evaluation of v3. Retry settings
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

**Current implementation boundary:** rule-only output is compared with a complete
LLM-generated program for parser-reported unsupported cases. The model candidate is
shown as the target output and the deterministic partial output is retained separately
for review; the candidate is not automatically accepted. JavaScript syntax is checked and the complete candidate is run
with Node's permission model and a scrubbed environment. Python candidates receive
syntax checking only. A benchmark candidate is counted as oracle-matching only when
restricted execution succeeds and output equals that case's separate expected-output
oracle. This benchmark-only score does not change translator acceptance or establish
general semantic equivalence.
Contracts, risk assessments, and learned-rule metadata do not change translation or
acceptance decisions; do not report them as causal ablations until switches and
independent outcome measures are implemented.

The current benchmark includes 12 local cases and 12 source-attributed adaptations of
Rosetta Code task prompts (A+B, Maximum of two numbers, and Loops/For). These are task-derived
challenge cases, not a representative corpus of independently collected legacy
programs. The COBOL `PERFORM 3 TIMES` challenge remains outside deterministic parser
coverage, but now has a separately authored expected output so model candidate
generation, restricted runtime execution, and oracle matching can be measured without
relabeling parser coverage. See [`data/external_task_cases.jsonl`](./data/external_task_cases.jsonl)
for per-case expected output, URLs, and adaptation notes.

This makes the experiment immediately interpretable: if the full stack improves correctness without harming determinism, its value is clearer than a single opaque end-to-end number.

### Recorded live pilot

The latest single-repeat paired run, rerun after the COBOL parser safety regression
fixes, is recorded in
[`data/project_report_evidence.json`](./data/project_report_evidence.json). On
2026-10-17, both target runs reported 23/24 end-to-end passes; the configured hybrid
made one fallback call for the unsupported COBOL loop using
`gemini-3.1-flash-lite` and prompt `legacy-modernizer-llm-v2`. With JavaScript, the
candidate was syntax-valid, ran in restricted Node, and matched its separately
authored three-line expected output (1/1); the one-call latency was 2249.3 ms and
translator acceptance stayed at zero. With Python, the candidate passed syntax
checking but execution was not run and no oracle match was claimed; one-call latency was
1735.5 ms. The unsupported case remains `not_run` in both runs. These single
fixed-input results do not show an end-to-end improvement or establish general
correctness.

## 6. Minimum evidence for publication-quality reporting

For a workshop or demo-style venue, the project should include at least:

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

Full stack:
- success: X%
- validation failures: Y
- learned rules added: Z
```

Do not claim that hybrid translation is superior unless the benchmark and evaluation protocol support that conclusion. Report per-language and per-construct breakdowns as well as aggregate numbers.

The `/rules` endpoint returns a descriptive mapping catalogue, not executable rule
coverage. Its entry count and status labels must not be used as a coverage or correctness
metric.
