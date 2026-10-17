# Report screenshots and evidence

Captured on 2026-10-17 from the project in this workspace. Application images use the real frontend and local backend. The capture-only backend disabled LLM fallback per request; no external LLM request was made.

| File | Evidence |
|---|---|
| `01_main_interface.png` | Main translator interface |
| `02_translation_result.png` | COBOL to JavaScript result and diagnostics |
| `03_language_examples.png` | Language selection and Load example control |
| `04_successful_translation.png` | BASIC to JavaScript sample with finite-I/O validation |
| `05_unsupported_input.png` | COBOL `PERFORM` unsupported-syntax handling; do not describe as a successful translation |
| `06_rules_catalogue.png` | Actual `/rules` response; descriptive catalogue, not executable coverage proof |
| `07_javascript_benchmark.png` | Live JavaScript benchmark API response |
| `08_python_benchmark.png` | Live Python benchmark API response |
| `09_rule_vs_hybrid.png` | Live experiment response, target JavaScript, one repeat; LLM calls disabled, so this does not measure fallback efficacy |
| `11_api_docs.png` | OpenAPI JSON response. Swagger `/docs` page did not render in the headless capture environment |
| `12_test_results.png` | Screenshot of the saved actual pytest stdout (`41 passed in 19.81s`, exit code 0); this is a browser rendering of the captured output, not a terminal window capture |

## Revision and benchmark provenance

The checked-out Git revision at capture time was `a06e15eaf2a5f0d584b6aa417c1ff5710298d4c9` (`Make conference demo walkthrough concrete`, 2026-10-17). The live benchmark endpoint responded with dataset ID `rosettacode-task-adaptations-v2` and `total: 20`; this is distinct from the previously referenced 36-record archived benchmark. These live screenshots must not be cited as the 36-record archived run.

`13_repository_commit.png` was not captured because GitHub was unreachable from this environment. `10_llm_fallback.png` was omitted: no live LLM request was made. The API responses and pytest stdout are retained in this folder's sibling evidence directory where available.
