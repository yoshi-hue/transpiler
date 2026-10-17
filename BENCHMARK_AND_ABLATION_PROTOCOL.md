# Benchmark, sample-size, and ablation protocol

## Current corpus

`data/corpus_manifest.jsonl` contains 36 records: 16 development records (12 local
smoke cases and four A+B task adaptations) and 20 held-out records. The held-out records
are grouped into two task families: Maximum of two numbers and Loops/For. The runner
evaluates only `split=test`; the manifest validator rejects a `split_group` appearing in
more than one split. The test set includes equal-operand maxima, singleton and expanded
loop ranges, and three COBOL `PERFORM` variants expected to be unsupported.

The examples are project-authored from task descriptions. Their outputs are separately
derived from fixed constants and inclusive loop ranges and checked by the separate
reference evaluator in `tools/check_benchmark_oracles.py` (20/20). That checker does not
import the transpiler or its source interpreter. It is not a native source compiler or a
second human review, and the corpus is not an independent or representative benchmark. The repository's legacy source subset
does not implement stdin input; the multiple test inputs here are distinct source
programs within the same task group, not multiple runtime stdin values for one program.

The deterministic results are archived with case-level raw output in
[`data/benchmark_v2_javascript.json`](./data/benchmark_v2_javascript.json) and
[`data/benchmark_v2_python.json`](./data/benchmark_v2_python.json). Reproduce them with:

```powershell
python tools\run_test_benchmark.py --target JavaScript --output data\benchmark_v2_javascript.json
python tools\run_test_benchmark.py --target Python --output data\benchmark_v2_python.json
```

Both runs report 17/20 end-to-end passes, 20/20 expected outcomes correctly handled,
17/17 separately authored target-output matches, and 3/3 expected-unsupported cases
recognized. The 17/20 denominator treats the three expected-unsupported cases as
non-translation passes. This is deterministic-only evidence; it contains no LLM or
metadata-effect comparison.

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

The present 20-case set has only two task groups and cannot assess this effect. Do not
use its confidence interval or the earlier 24-case pilot to claim a general improvement.

## Metadata mechanisms

Contracts, risk scores, failure records, and learned-rule examples are reporting or
prototype features. The current application has no toggles that make them alter the
translation or acceptance decision. Therefore this project makes **no effectiveness
claim** about those features and reports no causal ablation. A future ablation must
change one mechanism at a time, keep task groups/model/prompt/review process fixed, and
measure accepted correctness and reviewer time (including errors introduced by the
mechanism).
