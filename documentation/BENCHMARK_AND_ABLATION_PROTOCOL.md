# Benchmark, sample-size, and ablation protocol

## Current corpus

`data/corpus_manifest.jsonl` contains 42 records: 16 development records (12 local
smoke cases and four A+B task adaptations) and 26 held-out records across eight task
groups: Maximum of two numbers, Loops/For, and six CodeNet AtCoder tasks. The formerly
local-only p02606 challenge is now in the scored split.
The runner
evaluates only `split=test`; the manifest validator rejects a `split_group` appearing in
more than one split. The test set includes equal-operand maxima, singleton and expanded
loop ranges, three COBOL `PERFORM` variants and one CodeNet array-input program expected
to be unsupported.

The Rosetta Code adaptations are project-authored from task descriptions. Their outputs
are separately derived from fixed constants and inclusive loop ranges and checked by the
separate reference evaluator in `tools/check_benchmark_oracles.py` (20/20). CodeNet
p02600 adds two official samples and 15 task-derived rating fixtures; p02606 has three
official samples and two derived fixtures; p02607 has four fixtures. The checker does not
import the transpiler or its source interpreter. It is not
a native source compiler or a second human review, and the corpus is not an independent
or representative benchmark. The repository's legacy source subset
does not implement stdin input; the multiple test inputs here are distinct source
programs within the same task group, not multiple runtime stdin values for one program.

The frozen 20-case baseline is archived in
[`data/benchmark_v2_javascript.json`](./data/benchmark_v2_javascript.json) and
[`data/benchmark_v2_python.json`](./data/benchmark_v2_python.json). Current 26-case
reports are [`data/reproduced_test_26_javascript.json`](./data/reproduced_test_26_javascript.json)
and [`data/reproduced_test_26_python.json`](./data/reproduced_test_26_python.json).
Reproduce the current deterministic test split with:

```powershell
python tools\run_test_benchmark.py --target JavaScript --output data\reproduced_test_26_javascript.json
python tools\run_test_benchmark.py --target Python --output data\reproduced_test_26_python.json
```

These current runner reports are stable JSON for a fixed toolchain and source tree: they
record dataset, subset, backend, and runner hashes, and omit timestamps and local worktree
state. Recreate the oracle check and fixed offline ablation with:

```powershell
python tools\check_benchmark_oracles.py --output data\oracle_current_check.json
python tools\run_ablation.py --target JavaScript --output data\reproduced_ablation_26_javascript.json
python tools\run_ablation.py --target Python --output data\reproduced_ablation_26_python.json
```

The ablation runner does not load `.env`; LLM calls require an explicit `--enable-llm` flag.
Provider-enabled runs are not deterministic, even when model and prompt are fixed. They
record source/candidate hashes, provider/model/prompt metadata, and request IDs for audit.

The frozen 20-case baseline reports 17/20 end-to-end passes, 20/20 expected outcomes
correctly handled, 17/17 separately authored target-output matches, and 3/3
expected-unsupported cases recognized. The expanded deterministic reports are archived in
[`data/reproduced_test_26_javascript.json`](./data/reproduced_test_26_javascript.json)
and [`data/reproduced_test_26_python.json`](./data/reproduced_test_26_python.json).
Both targets report 22/22 supported-case output matches, 34/34 supported input-fixture
matches, and 4/4 expected-unsupported cases recognized. The six CodeNet cases now cover
six task groups. These results describe this fixed pilot and do not establish broad
generalization.

## Primary outcome and meaningful improvement

For a future fallback-effectiveness study, define a case as successful only if a
complete candidate is generated, target compilation and resource-limited execution
succeed, every predeclared independent fixture matches, and both required human
reviewers approve it. Candidate generation failure, syntax/runtime error, any fixture
mismatch, or rejection counts as not successful. Report deterministic parser coverage
and expected-unsupported recognition separately.

The smallest practically meaningful improvement is **20 percentage points** in this
case-level acceptance outcome over rule-only translation. Smaller changes do not justify
the additional model/runtime/review cost for this prototype.

## Sample size and repeats

Use at least **100 independent held-out task/source groups**, not 100 near-duplicate
programs. With paired binary outcomes, a two-sided 5% significance level, 80% power,
20-point improvement, and conservative 50% discordant-pair rate, the normal approximation
for McNemar's test requires about 98 independent pairs; round up to 100. The calculation
is an approximation and must be rechecked using the final planned analysis and observed
discordance before collection.

Run **five independent generation trials per task group and target**, with prompt,
provider/model snapshot, temperature, timeout, and source fixed. Treat the five outputs
as repeated observations nested within task group; they do not turn 100 groups into 500
independent samples. Report per-trial outcomes and use task-clustered bootstrap
confidence intervals or a mixed-effects analysis. Pair each hybrid result with the same
source's rule-only result. Register the set, split, outcomes, exclusions, and analysis
before querying the model; no development task may cross into test by task/source group.

The earlier 20-case ablation set had only two task groups and cannot assess this effect.
The expanded deterministic corpus has 26 cases across eight task groups. The five-repeat
live comparison below generated candidates after provider network access was explicitly
enabled. The small corpus still cannot establish broad effectiveness; do not use its
confidence interval to claim a general improvement.

## Live provider pilot (2026-10-25)

The predeclared 20 held-out cases were run with the same source tree, split, provider
(Google Gemini `gemini-3.1-flash-lite`), prompt version (`legacy-modernizer-llm-v3`),
temperature 0, and one or five repeats. Reports are
[`data/controlled_ablation_live_v2_javascript.json`](data/controlled_ablation_live_v2_javascript.json),
[`data/controlled_ablation_live_v2_python.json`](data/controlled_ablation_live_v2_python.json),
and the five-repeat results in
[`data/controlled_ablation_live_v3_javascript.json`](data/controlled_ablation_live_v3_javascript.json)
and [`data/controlled_ablation_live_v3_python.json`](data/controlled_ablation_live_v3_python.json).
The runner explicitly loads `.env` only with `--load-dotenv`; the reports do not contain
credentials. The five-repeat reports include the generated candidate text, hashes, and
observed outputs for review.

In each target, each arm is 85/100 passes across five repeats of the 20 cases (17/20 per
repeat). The LLM arm generated 15/15 candidates for the three expected-unsupported
COBOL loop cases; all 15 passed target syntax, restricted/isolated runtime, and the
predeclared expected-output check (JavaScript 15/15; Python 15/15). Zero candidates were
accepted, so supported end-to-end success did not improve over rule-only. The three
source cases are repeated observations from one task group; they are not 15 independent
test programs. Human review effort remains unmeasured. Contracts/risk are shared by the
arms, and learned-rule reuse remained zero; this run does not estimate their individual
effects or establish a reliability benefit.

The historical review package is
[`data/live_ablation_human_review_queue_v1.json`](data/live_ablation_human_review_queue_v1.json).
The provider-trial candidate and its pending gates are in
[`data/llm_candidate_review_queue_v4.json`](data/llm_candidate_review_queue_v4.json).
The project owner agreed to perform the independent review; named decisions and actual
elapsed minutes remain pending. No candidate is accepted.

## Expanded live ablation v9/v8 (2026-10-25)

The JavaScript and Python target reports are
[`data/controlled_ablation_live_v9_javascript.json`](data/controlled_ablation_live_v9_javascript.json)
and [`data/controlled_ablation_live_v8_python.json`](data/controlled_ablation_live_v8_python.json).
Both use the same 26-case test corpus (SHA-256
`832607a99c5ff81f32deaa86fd967fad337f671594a6fbae6edc2d305af608b2`), eight task
groups, five repeats per arm, temperature 0, and the configured Google Gemini
`gemini-3.1-flash-lite` provider. Provider network access was explicitly enabled for both
runs; CodeNet sources remained blocked from provider requests.

Each arm has 130 observations: 22 supported cases and four expected-unsupported cases,
each repeated five times. Rule-only, hybrid, and contracts/risk/learned-rule arms all had
110/110 supported-case passes, all 170 supported fixture executions matched, and the
expected-unsupported cases were recognized in 20/20 observations. The hybrid arm generated
15 candidates per target (three project-authored COBOL loop programs, five repeats each).
All 15 per target passed syntax, isolated/restricted execution, and fixed expected-output
checks. Zero candidates were accepted; candidate acceptance requires outstanding source,
fixture, security, regression, and human review gates. Learned-rule reuse was zero. The
third arm had the same pass counts as both baselines, and contracts/risk checks remain
shared across arms. Thus this run demonstrates working provider connectivity and candidate
validation on a narrow repeated pilot, but no improvement in accepted translations.
Median provider latency was 1,130.8 ms for JavaScript and 1,067.7 ms for Python. Reviewer
effort remains null because no human review time was recorded.

The three distinct candidate hashes per target are tied to three separate COBOL loop
sources; each hash was generated five times. The reports preserve candidate code/hash,
request IDs, target validation, and blockers. No CodeNet source was submitted to the model.
The JavaScript run without network permission is archived as v8 and had only connection
errors; it is not the connectivity result used above. Historical v4 reports retain the
previously documented uncertainty about CodeNet payload receipt before the source guard.

## Metadata mechanisms

Contracts and risk are implemented policy mechanisms: they gate finite-check
eligibility and learned-rule storage, choose repeatability checks, and require human
review at high risk. The three-arm runner cannot safely disable these shared translator
policies, so its third arm does **not** isolate their causal effect. It only enables
learned-rule memory seeded from development cases; the historical live run had zero
learned-rule reuse. No effectiveness claim is supported for contracts/risk/learned rules.
A future experiment must isolate each mechanism where safe, keep task groups/model/
prompt/review process fixed, and measure accepted correctness, failure types, and actual
reviewer time.
