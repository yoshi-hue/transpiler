# Candidate acceptance and review policy

## Current rule

Model output is an unaccepted proposal. A successful syntax check or one successful
execution does not establish translation correctness. The application must not merge a
candidate into trusted output automatically. Python candidates are executed only by the
isolated Docker runner when Docker is available; they are never executed on the host.

Every generated candidate includes a machine-readable `candidate_acceptance` record.
It starts unaccepted and lists blockers for source review, target-toolchain checks,
predeclared independent fixtures, security review, regression checks, and two human
reviews. Syntax validity, restricted JavaScript execution, or isolated Python execution
can satisfy only the target-toolchain subcheck; they never satisfy the other gates. No
API path automatically changes `accepted` to true.

## Evidence required before a candidate can be accepted

1. **Source review:** confirm that every source construct is understood, identify
   unsupported language features and external dependencies, and record the source
   dialect and complete input program hash.
2. **Build and static checks:** parse/compile with the actual target toolchain and
   intended target version; reject syntax errors, unresolved placeholders, TODOs,
   invented APIs, and undeclared dependencies.
3. **Behavioral checks:** run every independently specified input fixture plus boundary
   cases (zero, negative and equal operands where legal; empty/singleton/multiple loop
   iterations; both branches; and error/termination cases that are in scope). Compare
   output, exit status, and specified side effects against an oracle independent of the
   transpiler's interpreter. Test the same source program against more than one input
   where the source dialect supports runtime input; otherwise use distinct source
   variants and label them as such.
4. **Regression checks:** run the entire relevant source-to-target suite and confirm
   that adding the candidate does not change unrelated translations.
5. **Security checks:** inspect filesystem, network, subprocess, environment, and
   dependency use. Restrict generated behavior to the declared program contract.
6. **Human review:** one reviewer with source-language knowledge and one reviewer with
   target/runtime knowledge inspect the source, candidate diff, fixtures, failures, and
   dependencies. Both record a decision; unresolved semantic questions mean reject or
   retain as a proposal.
7. **Acceptance record:** store source/candidate hashes, model and prompt versions,
   fixtures and oracle source, toolchain/runtime versions, test results, reviewer
   identities, date, and accept/reject decision.

## Safe execution

JavaScript candidates are syntax-checked and run with Node's permission mode, a short
timeout, and a scrubbed environment. This remains a prototype safeguard, not complete
proof of safety. Python candidates are syntax-checked and, when Docker is available,
run in a container with no network, a read-only filesystem, no host mounts, dropped
capabilities, and CPU, memory, process, and wall-clock limits. If Docker is missing,
execution reports unavailable and never falls back to the host. The sandbox is not an
acceptance policy; fixture, security, regression, and human-review gates still apply.

## Current status

No model candidate has passed the complete acceptance policy. The v3 paired benchmark
returned no candidate for either target. Fixed JavaScript and Python provider trials
have returned candidates and matched their predeclared stdout in restricted/isolated
runtimes. The Python candidate also passed three project-authored source-variant
fixtures, a static AST security review, and `tests/test_transpiler.py`. These checks do
not validate the COBOL source with a native compiler: its dialect and source format are
unspecified, and `cobc` was unavailable during review. Two human reviews (COBOL source
and Python target/runtime) remain outstanding. No candidate is accepted.

The Python trial's detailed evidence is in
[`data/provider_trial_python_acceptance_review.json`](data/provider_trial_python_acceptance_review.json);
the source variants and expected outputs are in
[`data/provider_trial_python_fixtures.json`](data/provider_trial_python_fixtures.json).
The expected outputs were authored from the fixed-count `PERFORM` and `DISPLAY`
semantics; they are not native compiler results. The review report preserves the source
review and two-person human-review gates as pending.

## Reproducible provider trial

Configure `LLM_API_URL`, `LLM_MODEL`, and (when required) `LLM_API_KEY` in the local
`.env` (the trial script loads it locally) or server environment; never paste credentials
into chat, commit them, or put them in the browser. Then run the fixed COBOL `PERFORM
3 TIMES` trial:

```powershell
python tools\run_llm_provider_trial.py --target JavaScript --output data\provider_trial_latest.json
python tools\run_llm_provider_trial.py --target Python --output data\provider_trial_latest_python.json
```

The JSON record includes the fixed source hash, expected output, provider/model,
prompt version/hash, request ID, attempts, latency, candidate hash and code, toolchain
status, sandbox details, observed output, and expected-output match when executable. It
never records the API key. The
expected output is a predeclared project fixture, not a native COBOL run; this is a
reproducibility smoke trial, not an effectiveness result. A provider run must return a
candidate before effectiveness evaluation can begin.

Latest JavaScript smoke-trial record: `data/provider_trial_latest.json`. It generated a
candidate, passed syntax and restricted runtime checks, and matched the fixed expected
stdout. The record is explicitly not accepted and does not establish effectiveness.

## Learned-rule behavior

The current implementation can induce an experimental statement-pattern rule from one
deterministic translation that passes the configured finite checks at low or medium
risk. The supported schema is limited to flat assignment/print programs whose
expressions are single literals or identifiers. Variable and literal values become
slots in the target template. The rule is keyed by source language, target language,
schema, and deterministic rule-table version; every match is revalidated. Loops,
branches, compound expressions, high-risk cases, and model candidates are not learned.
This restricted rule induction is not the human-reviewed candidate acceptance
workflow described above, and passing finite checks does not establish semantic
correctness for every program matched by the pattern.
