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

No model candidate has passed the complete acceptance policy. The archived provider
trial returned a Python candidate and matched its fixed expected stdout in an isolated
runtime. The current guarded v6 five-repeat ablation used the expanded corpus, but all
15 eligible project-authored fallback requests per target failed with connection
errors; it generated no candidates. The v6 run did not send CodeNet-origin sources to
the provider. The preserved v4 attempt has an unresolved payload-receipt status in the
CodeNet review record.
The archived Python candidate was re-run in Docker and passed a conservative AST
allowlist screen plus its one fixed-output regression fixture. This is not the independent
fixture-set gate or human security review. Source-semantic, target/runtime, and security
review decisions remain pending from the project owner. No candidate is accepted.

The latest candidate review packet is
[`data/llm_candidate_review_queue_v6.json`](data/llm_candidate_review_queue_v6.json);
its reproducible isolated runtime and AST screening report is
[`data/llm_candidate_regression_v4.json`](data/llm_candidate_regression_v4.json). The
expected output is from a fixed-count `PERFORM`/`DISPLAY` fixture, not a native COBOL
compiler result. The packet records the project owner as the assigned independent
reviewer and leaves decisions and actual review minutes pending.

The historical v3 live ablation did produce candidates, as recorded in
[`data/live_ablation_human_review_queue_v1.json`](data/live_ablation_human_review_queue_v1.json).
The current v6 ablation reports instead have zero candidate generation after 15
eligible connection failures per target. Actual reviewer minutes must be entered by the owner;
they are not estimated from automated execution time.

The CodeNet Fortran challenge review is in
[`data/codenet_case_review.json`](data/codenet_case_review.json). It built with GNU
Fortran 14.3.0 in explicit free-form mode and passed three official AtCoder samples and
two derived fixtures. Its dataset-level CDLA-Permissive-2.0 reuse basis, source
provenance, and redistribution condition are recorded; the complete agreement text is
included at [`data/licenses/CDLA-Permissive-2.0.txt`](data/licenses/CDLA-Permissive-2.0.txt).
The held-out case p02607/s779285219 is reviewed in
[`data/codenet_case_review_p02607.json`](data/codenet_case_review_p02607.json); it is
expected unsupported and its four fixtures passed the local GNU Fortran build. The
p02600/s098305279 case's 17 fixtures passed the same native Fortran toolchain and both
target translators; its independent owner review remains pending in
[`data/codenet_case_review_p02600.json`](data/codenet_case_review_p02600.json). These
are corpus rights/build reviews, not LLM-candidate acceptance reviews. The source code
remains copyrighted by its submitter, and no individual file license header was found;
the recorded reuse basis is the CodeNet dataset agreement and its terms.

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
