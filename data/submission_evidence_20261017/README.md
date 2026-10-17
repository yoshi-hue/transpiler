# Submission evidence snapshot (2026-10-17)

## Revision and corpus provenance

- Current repository `HEAD` when fresh exports were generated: `a06e15eaf2a5f0d584b6aa417c1ff5710298d4c9` (`master`).
- The 36-record manifest and held-out benchmark runner were introduced/refreshed in commit `5669bc22c76a8335194c608df4f231cb1213f519` (2026-10-17 18:17:45 +05:30). Benchmark-related source files and the manifest are unchanged from that commit through current `HEAD`.
- Manifest: 36 records (16 development, 20 held-out); SHA-256 `2f0cb646571589af20601873ca0c79e67cb945aa87363121ab379b3acdf1dfd8`.
- The older tracked `data/benchmark_v2_javascript.json` and `data/benchmark_v2_python.json` identify commit `ade68dc44200b043e77617857717d8da687b6699` and `worktree_modified=true`; they predate the 36-record manifest. Treat those as historical. The JSON files in this folder are the fresh exports for the current `HEAD` and manifest.
- When generated, the only pre-existing modified tracked file was `PROJECT_REPORT_PROMPT.md`. Benchmark/evaluation code and corpus inputs matched `HEAD`. The JSON exports indicate a modified worktree because of that prompt edit and these newly generated evidence files; see the recorded commit plus this note together.

## Fresh benchmark exports

- **JavaScript:** 17/20 end-to-end passes; 17/17 separate expected-output matches; 3/3 expected-unsupported cases recognized. Export time `2026-10-17T14:17:16.111767+00:00`; recorded commit `a06e15eaf2a5f0d584b6aa417c1ff5710298d4c9`; `worktree_modified=True`.
- **Python:** 17/20 end-to-end passes; 17/17 separate expected-output matches; 3/3 expected-unsupported cases recognized. Export time `2026-10-17T14:17:19.651430+00:00`; recorded commit `a06e15eaf2a5f0d584b6aa417c1ff5710298d4c9`; `worktree_modified=True`.

- Separate expected-output oracle check: 20/20 matches. This checks project-authored expected outputs with a separate evaluator; it is not a native source compiler or second-human review.
- Environment: Python `3.13.1`; `Windows-10-10.0.19045-SP0`. Node version and exact timestamps/commands are in each JSON export.

## Pytest output

- Command: `python -m pytest --basetemp <fresh workspace temp directory>`.
- Result: **41 passed**, exit code 0. The actual captured console output is in [`pytest_output.txt`](./pytest_output.txt), with the process code in [`pytest_exit_code.txt`](./pytest_exit_code.txt).
- The workspace-local temporary directory avoids a Windows permission error that occurred when pytest used the default user Temp directory.

## Evidence files and SHA-256

- [`benchmark_javascript.json`](./benchmark_javascript.json) ? `50631ed88afc0eaa36d8380c7dcf728a01ca2ef078c44ae2af1d7e71ef3ad026`
- [`benchmark_python.json`](./benchmark_python.json) ? `fa68d998a5e00a0e1f6abde7fbe6bbf40607319e2f9207d609a3c41fb31fd433`
- [`oracle_check.json`](./oracle_check.json) ? `8e30027dde1be5c3bf8fb70eaf82af998262615d343d08310f6ed8f4c9345ad9`
- [`pytest_output.txt`](./pytest_output.txt) ? `ceaaec1bf16741d22bc1ec49a99ebc9fdf3067b2f2d5a9ad7013f020bff1d1e7`
