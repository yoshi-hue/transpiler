# Refreshed v3 evidence (pushed baseline)

## Provenance

- **Commit:** `ade68dc44200b043e77617857717d8da687b6699` (`master`, pushed to `origin/master`)
- **Benchmark source at that commit:** 24 records; SHA-256
  `857a4f1089e73f197a03b11a94e3919fef540303522a85b3ec395d5db22939c9`
- **Prompt version:** `legacy-modernizer-llm-v3`
- **Prompt implementation SHA-256:**
  `e4b5e22702cf461671a01dcac308bac2395e419eea5f2b8eed1cd869ba72f1b4`
- **Fallback input:** COBOL `rosetta-loops-for-cobol`, complete-program prompt; the
  request payload hashes were `2b62b903e13ffdbe` for JavaScript and
  `a57f52f8661d058a` for Python.
- **Provider/model:** Google Gemini OpenAI-compatible chat endpoint,
  `gemini-3.1-flash-lite`; `/llm/status` reported configured, chat mode, 45-second
  timeout, and at most two retries. No credentials are recorded here.
- **Runtime:** Windows 10 build 19045; Python 3.13.1; Node.js v24.20.0.
- **Server restart:** fresh Uvicorn process from this checkout on
  `http://127.0.0.1:8765`; `/llm/status` confirmed the model and v3 prompt above.
- **Run times:** JavaScript `2026-10-17T12:32:28.928457+00:00`; Python
  `2026-10-17T12:32:43.602342+00:00`.

## Commands

The server was started from the workspace with:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
```

The model/prompt check was:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/llm/status
```

The paired benchmark commands were:

```powershell
python evaluate.py --target JavaScript --output data\evaluation_v3_javascript.json
python evaluate.py --target Python --output data\evaluation_v3_python.json
```

`evaluate.py` runs the deterministic benchmark and one paired rule-only/hybrid repeat.
The full unmodified command output is archived in the two JSON files below. The CSV
contains every case from both targets, benchmark phase, and both paired variants.
Those files are a frozen historical record. The current `evaluate.py` defaults to no
provider requests; `run_experiment` also defaults to offline mode. Pass `--enable-llm`
to `evaluate.py` or `tools/run_ablation.py`, or check the UI opt-in, to explicitly load
`.env` and run a live hybrid arm. That opt-in behavior applies to future runs and does
not rewrite this baseline.

## Results

Both targets' deterministic benchmark and rule-only/hybrid experiment reported 23/24
end-to-end passes (95.8%). The Wilson 95% interval for 23/24 is 79.8%–99.3%. All 24
predeclared outcomes were recognized; all 23 supported target outputs matched the
separately authored expected outputs. The single non-pass was the deliberately
unsupported COBOL `PERFORM 3 TIMES` case, recognized as unsupported.

| Target | Rule-only | Hybrid | Delta | Fallback request | Attempts | Candidate | Syntax/runtime/oracle | Translator accepted |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| JavaScript | 23/24 | 23/24 | 0.0 pp | 1 | 3 | 0 | not run | 0 |
| Python | 23/24 | 23/24 | 0.0 pp | 1 | 3 | 0 | not run | 0 |

The fallback was configured, but it returned no candidate for the unsupported COBOL
case in either target run. Thus the current-code v3 refresh does **not** reproduce the
older v2 candidate result and supports no claim of fallback effectiveness. The baseline
evaluator recorded request counts, attempts, and latency (JavaScript 1634.7 ms; Python
1592.5 ms), but did not preserve provider HTTP status or a failure category. The
benchmark logger has since been updated to retain a redacted failure category/status
for future runs; it never copies provider response bodies into case records.

## Raw case records

- [JavaScript raw evaluate output](./evaluation_v3_javascript.json) — 24 deterministic
  cases and 24 cases per paired variant.
- [Python raw evaluate output](./evaluation_v3_python.json) — same structure.
- [Flattened raw case CSV](./evaluation_v3_case_results.csv) — 144 rows, retaining target,
  phase, variant, case ID, expected outcome, status, unsupported count, attempts,
  latency, candidate checks, and oracle result.
- [Benchmark source records at the evaluated commit](https://github.com/yoshi-hue/transpiler/blob/ade68dc44200b043e77617857717d8da687b6699/data/external_task_cases.jsonl).

The 24-case run is retained as a frozen pushed-commit baseline. A later change separates
development data from held-out tests and expands edge cases; its results are reported
separately in the benchmark protocol and must not be substituted into this baseline.
