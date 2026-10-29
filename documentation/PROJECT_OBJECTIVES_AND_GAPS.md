# Project Objectives, Candidate Gaps, and Contribution Status

## Purpose and evidence boundary

This document aligns the project objectives and literature-gap slides with the current
prototype. It distinguishes implemented behavior from reporting-only mechanisms and
proposed research. Selected primary sources have been verified, but the presentation itself is unavailable
and its Xu et al. shorthand remains unidentified. The false-failure claim is now linked
to a fully specified publication, though it cannot be matched to the missing slide. This
is a scoped source audit, not a systematic literature review; do not generalize its
papers into field-wide findings.

[`project_report_evidence.json`](./project_report_evidence.json) is a historical
2026-10-17 evidence snapshot (24-case benchmark); it is not the current result source.
Current corpus counts and held-out scores are summarized below and archived in
[`codenet_integrated_evaluation_javascript.json`](./codenet_integrated_evaluation_javascript.json)
and [`codenet_integrated_evaluation_python.json`](./codenet_integrated_evaluation_python.json).
The executable source subset is specified in [`supported_subset.json`](./supported_subset.json).

## Six project objectives and implementation status

| # | Objective | Status in current project | Evidence and boundary |
|---|---|---|---|
| 1 | Survey established rule-based, compiler, transpiler, and learning-based translation approaches. | **Partially addressed: selected primary sources and official tool documentation checked; survey is not exhaustive.** | Verified studies and tool examples are summarized below with source links and bounded claims. The list is not a systematic review, common benchmark, or controlled baseline comparison. |
| 2 | Identify specific gaps supported by published evidence rather than assumed limitations. | **Partially addressed: selected studies are cited with bounded claims; the original slide deck was unavailable for complete citation reconciliation.** | The source audit supports scoped questions about feature mapping, evaluation false negatives, and repository-level evaluation. It does not establish field-wide gaps. The unidentified Xu et al. 2026 citation is excluded from the conference paper; the 2026 false-failure study is cited by its verified publication details below. The prototype does not measure scalability, benchmark reliability across systems, corpus scarcity, or model bias. |
| 3 | Build a multi-language front end with lexing/parsing and a shared representation. | **Implemented for documented subsets.** | Custom front ends produce normalized nodes/IR for the supported COBOL, FORTRAN, Pascal, BASIC and Python-like subsets. The FORTRAN subset now includes scalar list-directed stdin and scalar formatted stdout; users must provide input fixtures for runtime validation. This is not full-language support and should not be described as an ANTLR implementation. See `backend/legacy.py`, `backend/lexer.py`, `backend/parser.py`, `backend/ir.py`, and `data/supported_subset.json`. |
| 4 | Design a hybrid back end that constrains model assistance with explicit mappings. | **Partially implemented; complete-program fallback prototype present.** | For unsupported syntax, the model receives the complete source and may return a complete target-program candidate. JavaScript candidates are syntax-checked and executed by Node's permission-restricted mode; Python candidates are syntax-checked and executed in an isolated Docker container when available. In five live repeats over three held-out COBOL loop variants, each target generated 15/15 candidates that passed syntax, target execution, and expected-output comparison. None was accepted; human source/target reviews remain pending. This supports candidate behavior only, not a benefit in accepted translation. The descriptive `backend/rules.py` catalogue is not itself an executable rule-coverage table. |
| 5 | Validate behavior with execution-based checks rather than surface-level similarity metrics alone. | **Partially implemented.** | Deterministic supported-subset translations are executed and compared with the internal source interpreter. In the live fallback pilot, 30 target candidates (15 per target) matched predeclared outputs under restricted/isolated execution. These are repeated trials on three project-authored loop variants from one task group, not 30 independent programs; independent native-source oracles and human review are incomplete. Do not describe internal interpreter agreement as an independent oracle or finite I/O checks as formal equivalence proofs. |
| 6 | Document precisely what the project contributes relative to surveyed work, including what it does not contribute. | **Substantially addressed as a living documentation objective; final report still requires alignment and author review.** | This matrix, corpus protocol, benchmark/ablation protocol, and revised report prompt define implementation boundaries and evidence limits. The prototype does not establish research novelty, generalization, or causal improvement. Keep report claims synchronized with current code and archived artifacts; this audit does not complete the final course report or author review. |

## Candidate literature-gap claims from the presentation

The presentation proposes five gap areas. The audit below has checked selected primary
sources and corrected likely miscitation, but two slide references remain incomplete or
ambiguous. Treat the bounded study findings as setting-specific, not as consensus or
field-wide gaps.

| Candidate gap | Claim shown in presentation | Audit result and limitation |
|---|---|---|
| Scalability | Translation success may fall on programs above roughly 100 lines. | **Qualified evidence:** Zhang et al. (PLDI 2025) discuss prior size-related limitations and evaluate a Go-to-Rust project translator. Their study is not proof of a universal 100-line threshold. The current project has no >100-line scalability study. |
| Evaluation and benchmark reliability | A benchmark analysis reportedly found correct translations graded as failures. | **Verified source used for the bounded statement:** Rabbi et al. (AIware 2026) report evaluation-pipeline false negatives in tested setups. The original slide shorthand cannot be reconciled without the slide deck; no broader prevalence claim is made. |
| Feature/API mapping | Cross-language feature/API mapping can produce subtle semantic divergence. | **Qualified evidence:** Zhang et al. (PLDI 2025) address unmapped Go-language features in Go-to-Rust translation using explicit feature mapping and type-compatibility checks. This is not a general API-mapping result. |
| Repository-level corpus scarcity | Available data may be function-level while tasks require project/repository context. | **Correct likely source/venue:** RepoTransBench (TSE 2026) describes prior snippet/function/file-level benchmarks and contributes repository-level data. This does not prove repository-level data is absent or required for every task. The slide's EMNLP 2025 attribution is not verified. |
| Multilingual bias and cross-paradigm transfer | Translation quality may track language representation in training data. | **Unverified and omitted from the submission framing:** the supplied Xu et al. 2026 shorthand did not identify a matching primary source. This prototype has no model-level bias experiment. |

## Primary-source audit and bounded related work

- Zhang, Hanliang, Cristina David, Meng Wang, Brandon Paulsen, and Daniel Kroening.
  â€œScalable, Validated Code Translation of Entire Projects using Large Language
  Models.â€ *Proceedings of the ACM on Programming Languages* 9, PLDI (2025), 1616â€“1641.
  [DOI: 10.1145/3729315](https://doi.org/10.1145/3729315);
  [arXiv:2412.08035](https://arxiv.org/abs/2412.08035). Use the published version's
  results; do not mix its reported 9,700-line/780-function result with earlier
  preprint figures. One study motivates specific size and unmapped-feature questions;
  it is not a general survey of all translators.
- Rabbi, Fazle, Soumit Kanti Saha, and Jinqiu Yang. â€œBeyond Translation Accuracy:
  Addressing False Failures in LLM-Based Code Translation.â€ ACM AIware â€™26, 38â€“42.
  [DOI: 10.1145/3805760.3814890](https://doi.org/10.1145/3805760.3814890);
  [arXiv:2605.02195](https://arxiv.org/abs/2605.02195). Their tested study reports
  evaluation-pipeline false negatives associated with compilation flags, library
  links, and runtime configuration. Do not infer a field-wide prevalence from the
  abstract or this project.
- Wang, Yanli, et al. â€œRepoTransBench: A Real-World Multilingual Benchmark for
  Repository-Level Code Translation.â€ *IEEE Transactions on Software Engineering*
  52(2) (2026), 675â€“690.
  [DOI: 10.1109/TSE.2025.3645056](https://doi.org/10.1109/TSE.2025.3645056);
  [arXiv:2412.17744](https://arxiv.org/abs/2412.17744). This is TSE, not EMNLP;
  it presents a repository-level benchmark and characterizes the granularity of
  some prior datasets.
- He, Minghua, et al. â€œExeCoder: Empowering Large Language Models with Executability
  Representation for Code Translation.â€ EMNLP 2025, 7110â€“7136.
  [ACL Anthology](https://aclanthology.org/2025.emnlp-main.362/);
  [DOI: 10.18653/v1/2025.emnlp-main.362](https://doi.org/10.18653/v1/2025.emnlp-main.362).
  This is a verified EMNLP translation paper about executability representations,
  not evidence for repository-level corpus scarcity.
- Yang, Zhen, et al. â€œExploring and Unleashing the Power of Large Language Models in
  Automated Code Translation.â€ FSE 2024.
  [DOI: 10.1145/3660778](https://doi.org/10.1145/3660778);
  [arXiv:2404.14646](https://arxiv.org/abs/2404.14646). UniTrans studies tests,
  test-informed translation, execution, and iterative repair in its evaluated
  language settings.
- Yin, Xin, et al. â€œRectifier: Code Translation with Corrector via LLMs.â€
  [arXiv:2407.07472](https://arxiv.org/abs/2407.07472) (2024). A learned
  post-generation correction approach; it does not support a blanket claim that
  repair methods are unconstrained.
- Yuan, Zhiqiang, et al. â€œTransAgent: Enhancing LLM-Based Code Translation via
  Fine-Grained Execution Alignment.â€ FSE 2026.
  [DOI: 10.1145/3797099](https://doi.org/10.1145/3797099);
  [arXiv:2409.19894](https://arxiv.org/abs/2409.19894). The paper studies
  execution-aligned localization of translation errors; cite the peer-reviewed
  publication year as 2026.
- Rabbi, Fazle, et al. â€œBabelCoder: Agentic Code Translation with Specification
  Alignment.â€ [arXiv:2512.06902](https://arxiv.org/abs/2512.06902). Treat as an
  arXiv preprint unless a peer-reviewed publication record is confirmed.
- Bhattarai, Manish, et al. â€œEnhancing Code Translation in Language Models with
  Few-Shot Learning via Retrieval-Augmented Generation.â€
  [arXiv:2407.19619](https://arxiv.org/abs/2407.19619). A specific retrieval-guided
  example, not a complete citation for a broad method family.
- Nitin, Vikram, Rahul Krishna, and Baishakhi Ray. â€œSpecTra: Enhancing the Code
  Translation Ability of Language Models by Generating Multi-Modal Specifications.â€
  [arXiv:2405.18574](https://arxiv.org/abs/2405.18574). Its â€œmulti-modalâ€ label
  concerns generated specifications; do not imply image/video inputs without source
  evidence.

The primary source intended by the slide's Xu et al. 2026 claim remains unknown. The
slide deck was not in the repository, and the shorthand does not provide enough
information to identify it. It was removed from the target paper instead of being
replaced with a nearby citation. The paper makes no claim that depends on this source.

## Related-work taxonomy and LLM follow-up systems

The presentation suggests organizing the survey around parser-based tools, general
transpilers, domain-specific translators, intermediate-language compilers, and interface
generators. The following official project pages verify representative tool purposes;
they are descriptive primary documentation, not comparable empirical studies.

| Tool | Verified purpose | Source |
|---|---|---|
| ANTLR | Parser generator; not by itself a source-to-source translator. | [ANTLR](https://www.antlr.org/) |
| Babel | JavaScript compiler/toolchain for transforming JavaScript syntax. | [Babel](https://babeljs.io/) |
| Emscripten | LLVM/Clang-based toolchain targeting WebAssembly and JavaScript environments. | [Emscripten](https://emscripten.org/) |
| JSweet | Java-to-TypeScript/JavaScript transpiler. | [JSweet](https://www.jsweet.org/) |
| GWT | Java-to-JavaScript development toolkit/compiler. | [GWT](https://www.gwtproject.org/) |
| C2Rust | C-to-Rust translation tool, with documented limitations and manual follow-up. | [C2Rust](https://c2rust.com/) |
| Haxe | Cross-platform language/toolkit with multiple targets. | [Haxe](https://haxe.org/) |
| SWIG | Interface generator for connecting C/C++ code to other languages; not general program translation. | [SWIG](https://www.swig.org/) |

These systems do not all solve the same task and are not direct baselines by default.
Compare only verified capabilities and clearly state each system's purpose,
source/target languages, semantic guarantees, and evaluation method.

The presentation also names Rectifier, UniTrans, ExeCoder, TransAgent, BabelCoder, and
retrieval-augmented/multimodal methods as related LLM work. Treat this as a reading list,
not a verified claim that they share one limitation or that they are directly comparable.
Check primary sources and avoid the slide's generalization that repair necessarily leaves
translation unconstrained unless each cited paper supports that specific claim.

## Contribution-to-gap mapping, with honest status

| Candidate gap | Project response/design decision | Current status and evidence limit |
|---|---|---|
| Scalability | Normalize parsed programs into an intermediate representation instead of relying on arbitrary line-window fragmentation. | A normalized representation exists for prototype inputs, but the project has no large-program or >100-line scalability evaluation. Do not claim that it reduces cross-fragment errors. |
| Evaluation reliability | Keep validation and benchmark reporting in the project, expose failure categories, and compare expected outputs separately where available. | Implemented as prototype I/O checks and a 26-case held-out pilot across eight groups; its independent arithmetic/task oracle matches 25 expected-output records and 38 declared fixtures. Human second review is pending; this small pilot is not representative. No compiler-flag or linker-configuration study has been performed. |
| Feature/API mapping | Maintain explicit documented source subsets and inspectable mapping descriptions. | Mapping catalogue exists, but it is descriptive and not the execution engine. Actual emission is performed by back-end code. No comprehensive semantic-divergence study exists. |
| Corpus scarcity | Record provenance, hashes, oracle status, grouping, and licensing review; define an external-corpus audit workflow. | The main corpus manifest has 42 records: 16 development and 26 held out across eight task groups. A local audit scanned 4,053 CodeNet metadata files; 13,565 accepted COBOL, Fortran, and Pascal source files were present. Six CodeNet cases now represent six separate task groups: two earlier supported scalar-input cases, one expected-unsupported array-input case, and three newly supported Fortran task cases. All six have native builds and fixture checks. The dataset-level CDLA-Permissive-2.0 basis and agreement text are recorded. The independent human review of task semantics, fixtures, and reuse terms remains pending. See the hash-bound case review JSON files and `data/independent_oracle_review_queue_v2.json`. |
| Multilingual bias | Bound the intended translation scope by explicit language subsets and use a shared front-end/IR architecture where implemented. | No model training or multilingual-bias measurement has been done. The fallback receives source context and is not restricted to a small IR subtree; do not claim that it mitigates training-data bias. |

## Evaluation measures aligned with the objectives

Use the following measures only with their denominators and current implementation
limitations:

1. **End-to-end pass rate:** cases for which target execution and the implemented
   validation report `passed`, divided by all benchmark cases. Expected-unsupported
   cases are not translation passes.
2. **Supported-case translation success:** expected-translatable cases that pass divided
   by expected-translatable cases.
3. **Expected-unsupported recognition:** correctly identified expected-unsupported
   cases divided by expected-unsupported cases; keep it separate from translation
   success.
4. **Independent expected-output matches:** compare target output with the separately
   specified expected output where available. This does not turn source-interpreter
   agreement into an independent oracle.
5. **Failure-mode breakdown:** report exact available `failure_class` categories (for
   example unsupported syntax, target runtime error, and output mismatch). Do not report
   compile-error or linker-error counts unless the evaluation actually invokes and
   captures an original compiler/linker.
6. **Construct coverage:** describe the implementation's recognized-source-unit
   coverage and benchmark's required-construct coverage accurately. Do not equate
   either with the descriptive catalogue entry count.
7. **LLM fallback effect:** use a fixed model and paired rule-only/hybrid runs over
   identical cases. The candidate path supports restricted JavaScript execution and isolated Docker execution for Python when available. A fixed COBOL PERFORM smoke trial generated one candidate per target; each matched one predeclared output, and the Python candidate matched three recorded fixture variants. Both candidates remain unaccepted. The held-out deterministic benchmark separately contains three expected-unsupported COBOL loop cases and one CodeNet array-input case; it is not evidence of fallback behavior. Report calls, candidate generation, runtime validity, oracle matches, acceptance, failures, and latency. This single-case pilot does not establish fallback improvement.
8. **Scalability, cross-language semantics, and bias:** require purpose-built
   benchmarks and controlled analyses; none are established by the current 26-case,
   eight-group held-out pilot.

## Current evidence summary

The earlier paired run and five-repeat live comparison were historical pilots and are not included in the final evidence set. Current reproducibility and benchmark files are listed in the root README. These are finite pilot results, not general effectiveness evidence.

The current held-out split has 26 cases across eight task groups (22 supported and four
expected-unsupported: three COBOL loops and one CodeNet Fortran array-input program).
The deterministic benchmark reports 22/22 supported-case output matches, all 34 target
fixture checks matching, and all four unsupported cases recognized for both targets. The
separate oracle checker matches 25 expected-output records and 38 fixtures. CodeNet p02600,
p02606, p02607, p03997, p02724, and p03238 have source-hash-bound GNU Fortran 14.3.0
build records. Independent owner review of source/task behavior, expected outputs, and
reuse terms is still pending. The project-authored cases are not all independently
compiled in native source-language toolchains; this remains exploratory evidence, not
general semantic equivalence. See
[`./BENCHMARK_AND_ABLATION_PROTOCOL.md`](./BENCHMARK_AND_ABLATION_PROTOCOL.md).
Contracts and risk affect local eligibility and learned-rule storage, but their individual
effects are not isolated. The current 26-case/eight-group live ablations used five repeats
per target. With provider network access explicitly enabled, both target runs generated
15 candidates; all passed target syntax/runtime and predeclared output checks, but zero
were accepted. Each arm had 110/130 observations (22/22 supported translations per repeat)
and 20/20 expected-unsupported recognitions; learned-rule reuse was zero and reviewer
effort was not measured. These runs establish provider connectivity and bounded candidate
validation, not an improvement. Current deterministic reports are
[`../data/reproduced_test_26_javascript.json`](../data/reproduced_test_26_javascript.json)
and [`../data/reproduced_test_26_python.json`](../data/reproduced_test_26_python.json). Live
reports are [`../data/controlled_ablation_live_v9_javascript.json`](../data/controlled_ablation_live_v9_javascript.json)
and [`../data/controlled_ablation_live_v8_python.json`](../data/controlled_ablation_live_v8_python.json). Historical v4 reports attempted CodeNet requests before the guard; payload receipt is unknown. Scalability and multilingual bias are not contributions or findings.
