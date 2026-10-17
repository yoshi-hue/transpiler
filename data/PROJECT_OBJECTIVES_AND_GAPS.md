# Project Objectives, Candidate Gaps, and Contribution Status

## Purpose and evidence boundary

This document aligns the project objectives and literature-gap slides with the current
prototype. It distinguishes implemented behavior from reporting-only mechanisms and
proposed research. Selected primary sources have been verified, but the presentation itself is unavailable
and its Xu et al. shorthand remains unidentified. The false-failure claim is now linked
to a fully specified publication, though it cannot be matched to the missing slide. This
is a scoped source audit, not a systematic literature review; do not generalize its
papers into field-wide findings.

The current evidence snapshot is [`project_report_evidence.json`](./project_report_evidence.json).
The executable source subset is specified in [`supported_subset.json`](./supported_subset.json).

## Six project objectives and implementation status

| # | Objective | Status in current project | Evidence and boundary |
|---|---|---|---|
| 1 | Survey established rule-based, compiler, transpiler, and learning-based translation approaches. | **Partially addressed: selected primary sources and official tool documentation checked; survey is not exhaustive.** | Verified studies and tool examples are summarized below with source links and bounded claims. The list is not a systematic review, common benchmark, or controlled baseline comparison. |
| 2 | Identify specific gaps supported by published evidence rather than assumed limitations. | **Partially addressed: selected studies are cited with bounded claims; the original slide deck was unavailable for complete citation reconciliation.** | The source audit supports scoped questions about feature mapping, evaluation false negatives, and repository-level evaluation. It does not establish field-wide gaps. The unidentified Xu et al. 2026 citation is excluded from the conference paper; the 2026 false-failure study is cited by its verified publication details below. The prototype does not measure scalability, benchmark reliability across systems, corpus scarcity, or model bias. |
| 3 | Build a multi-language front end with lexing/parsing and a shared representation. | **Implemented for documented subsets.** | Custom front ends produce normalized nodes/IR for the supported COBOL, FORTRAN, Pascal, BASIC and Python-like subsets. This is not full-language support and should not be described as an ANTLR implementation. See `backend/legacy.py`, `backend/lexer.py`, `backend/parser.py`, `backend/ir.py`, and `data/supported_subset.json`. |
| 4 | Design a hybrid back end that constrains model assistance with explicit mappings. | **Partially implemented; complete-program fallback prototype present.** | For unsupported syntax, the model receives the complete source and returns a complete target-program candidate shown as generated output. JavaScript candidates are syntax-checked and executed by Node's permission-restricted mode; Python candidates receive a syntax check only and are not executed. Candidates are never automatically marked semantically accepted. The descriptive `backend/rules.py` catalogue is not itself an executable rule-coverage table. |
| 5 | Validate behavior with execution-based checks rather than surface-level similarity metrics alone. | **Partially implemented.** | Deterministic supported-subset translations are executed and compared with the internal source interpreter. The fallback pilot separately executes JavaScript candidates in restricted Node mode and can compare known outputs with separately authored expected-output oracles. These are finite-case checks, not formal equivalence proofs; do not describe internal interpreter agreement as an independent oracle. |
| 6 | Document precisely what the project contributes relative to surveyed work, including what it does not contribute. | **Documentation objective; this status matrix and the report prompt support it.** | The prototype itself does not establish research novelty. The contribution must be framed as an implemented engineering prototype plus a reproducibility/evaluation workflow, with proposed capabilities clearly separated from measured results. |

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
  “Scalable, Validated Code Translation of Entire Projects using Large Language
  Models.” *Proceedings of the ACM on Programming Languages* 9, PLDI (2025), 1616–1641.
  [DOI: 10.1145/3729315](https://doi.org/10.1145/3729315);
  [arXiv:2412.08035](https://arxiv.org/abs/2412.08035). Use the published version's
  results; do not mix its reported 9,700-line/780-function result with earlier
  preprint figures. One study motivates specific size and unmapped-feature questions;
  it is not a general survey of all translators.
- Rabbi, Fazle, Soumit Kanti Saha, and Jinqiu Yang. “Beyond Translation Accuracy:
  Addressing False Failures in LLM-Based Code Translation.” ACM AIware ’26, 38–42.
  [DOI: 10.1145/3805760.3814890](https://doi.org/10.1145/3805760.3814890);
  [arXiv:2605.02195](https://arxiv.org/abs/2605.02195). Their tested study reports
  evaluation-pipeline false negatives associated with compilation flags, library
  links, and runtime configuration. Do not infer a field-wide prevalence from the
  abstract or this project.
- Wang, Yanli, et al. “RepoTransBench: A Real-World Multilingual Benchmark for
  Repository-Level Code Translation.” *IEEE Transactions on Software Engineering*
  52(2) (2026), 675–690.
  [DOI: 10.1109/TSE.2025.3645056](https://doi.org/10.1109/TSE.2025.3645056);
  [arXiv:2412.17744](https://arxiv.org/abs/2412.17744). This is TSE, not EMNLP;
  it presents a repository-level benchmark and characterizes the granularity of
  some prior datasets.
- He, Minghua, et al. “ExeCoder: Empowering Large Language Models with Executability
  Representation for Code Translation.” EMNLP 2025, 7110–7136.
  [ACL Anthology](https://aclanthology.org/2025.emnlp-main.362/);
  [DOI: 10.18653/v1/2025.emnlp-main.362](https://doi.org/10.18653/v1/2025.emnlp-main.362).
  This is a verified EMNLP translation paper about executability representations,
  not evidence for repository-level corpus scarcity.
- Yang, Zhen, et al. “Exploring and Unleashing the Power of Large Language Models in
  Automated Code Translation.” FSE 2024.
  [DOI: 10.1145/3660778](https://doi.org/10.1145/3660778);
  [arXiv:2404.14646](https://arxiv.org/abs/2404.14646). UniTrans studies tests,
  test-informed translation, execution, and iterative repair in its evaluated
  language settings.
- Yin, Xin, et al. “Rectifier: Code Translation with Corrector via LLMs.”
  [arXiv:2407.07472](https://arxiv.org/abs/2407.07472) (2024). A learned
  post-generation correction approach; it does not support a blanket claim that
  repair methods are unconstrained.
- Yuan, Zhiqiang, et al. “TransAgent: Enhancing LLM-Based Code Translation via
  Fine-Grained Execution Alignment.” FSE 2026.
  [DOI: 10.1145/3797099](https://doi.org/10.1145/3797099);
  [arXiv:2409.19894](https://arxiv.org/abs/2409.19894). The paper studies
  execution-aligned localization of translation errors; cite the peer-reviewed
  publication year as 2026.
- Rabbi, Fazle, et al. “BabelCoder: Agentic Code Translation with Specification
  Alignment.” [arXiv:2512.06902](https://arxiv.org/abs/2512.06902). Treat as an
  arXiv preprint unless a peer-reviewed publication record is confirmed.
- Bhattarai, Manish, et al. “Enhancing Code Translation in Language Models with
  Few-Shot Learning via Retrieval-Augmented Generation.”
  [arXiv:2407.19619](https://arxiv.org/abs/2407.19619). A specific retrieval-guided
  example, not a complete citation for a broad method family.
- Nitin, Vikram, Rahul Krishna, and Baishakhi Ray. “SpecTra: Enhancing the Code
  Translation Ability of Language Models by Generating Multi-Modal Specifications.”
  [arXiv:2405.18574](https://arxiv.org/abs/2405.18574). Its “multi-modal” label
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
| Evaluation reliability | Keep validation and benchmark reporting in the project, expose failure categories, and compare expected outputs separately where available. | Implemented as prototype I/O checks and a 20-case held-out pilot; the internal source interpreter is not independent. No compiler-flag or linker-configuration study has been performed. |
| Feature/API mapping | Maintain explicit documented source subsets and inspectable mapping descriptions. | Mapping catalogue exists, but it is descriptive and not the execution engine. Actual emission is performed by back-end code. No comprehensive semantic-divergence study exists. |
| Corpus scarcity | Record provenance, hashes, oracle status, grouping, and licensing review; define an external-corpus audit workflow. | Manifest contains 24 pilot cases. The full CodeNet archive is not present/audited; no claim of a curated repository-scale corpus is supported. |
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
   identical cases. The complete-program candidate path now supports restricted target
   execution for JavaScript and has three COBOL loop cases with separately authored
   expected outputs; benchmark-only oracle matches are counted separately from translator
   acceptance. Python fallback candidates are syntax-checked but not executed. Report
   calls, candidates, runtime-valid candidates, oracle matches, unsupported constructs,
   failures, and latency. The pilot is too small to establish general fallback
   improvement.
8. **Scalability, cross-language semantics, and bias:** require purpose-built
   benchmarks and controlled analyses; none are established by the current 20-case
   held-out pilot.

## Current evidence summary

The refreshed v3 paired run is recorded in [`EVIDENCE_V3_REFRESH.md`](./EVIDENCE_V3_REFRESH.md)
with raw JSON case records. It was run from pushed commit `ade68dc44200b043e77617857717d8da687b6699`,
using `gemini-3.1-flash-lite`, prompt `legacy-modernizer-llm-v3`, Python 3.13.1, and
Node.js v24.20.0. On the pre-split 24-case pilot, both targets had 23/24 end-to-end
passes and 23/23 target-output matches; the expected-unsupported COBOL PERFORM case
was recognized. In the hybrid variant the provider returned no candidate after three
request attempts for each target. The unchanged end-to-end rate is not an LLM improvement
result.

The strengthened held-out test split has 20 cases across two task groups (17 supported,
three expected-unsupported COBOL loops). The deterministic benchmark reports 17/17
separately authored expected-output matches for both JavaScript and Python and correctly
recognizes all three unsupported cases. These outputs were derived from fixed constants and loop semantics and match a separate
reference evaluator (20/20). They have not been independently executed in native
source-language compilers or reviewed by a second human; the set is exploratory and
cannot establish general semantic equivalence. See
[`../BENCHMARK_AND_ABLATION_PROTOCOL.md`](../BENCHMARK_AND_ABLATION_PROTOCOL.md).

Contracts, risk scores, failure fingerprints, and learned-rule examples remain prototype
diagnostics. No controlled ablation was performed and no benefit is claimed. Scalability
and multilingual bias are not contributions or findings. The target submission draft is
[`../ICSE_2027_TOOL_DEMO.tex`](../ICSE_2027_TOOL_DEMO.tex); verified author identities,
the public video, and compilation to the required PDF remain outstanding.
