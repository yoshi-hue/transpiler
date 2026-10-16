# Project Objectives, Candidate Gaps, and Contribution Status

## Purpose and evidence boundary

This document aligns the project objectives and literature-gap slides with the current
prototype. It distinguishes implemented behavior from reporting-only mechanisms and
proposed research. The gap names below are **candidate claims transcribed from the
project presentation**, not independently verified conclusions from a completed
systematic literature review. Do not call them literature-backed findings until each
claim has been checked against its primary source and complete bibliographic details.

The current evidence snapshot is [`project_report_evidence.json`](./project_report_evidence.json).
The executable source subset is specified in [`supported_subset.json`](./supported_subset.json).

## Six project objectives and implementation status

| # | Objective | Status in current project | Evidence and boundary |
|---|---|---|---|
| 1 | Survey established rule-based, compiler, transpiler, and learning-based translation approaches. | **Partially addressed in report materials; literature review requires source verification.** | The presentation lists parser-based tools, general transpilers, domain-specific translators, intermediate-language compilers, interface generators, and selected LLM translation follow-up systems. This is a taxonomy for structuring a review, not a validated exhaustive survey or a controlled baseline comparison. Verify primary sources, scope, and citations. |
| 2 | Identify specific gaps supported by published evidence rather than assumed limitations. | **Research objective; not established by the prototype.** | Candidate gaps are listed below. Their exact claims and citations need primary-source verification. The current benchmark cannot validate claims about field-wide scalability, benchmark reliability, corpus scarcity, or multilingual bias. |
| 3 | Build a multi-language front end with lexing/parsing and a shared representation. | **Implemented for documented subsets.** | Custom front ends produce normalized nodes/IR for the supported COBOL, FORTRAN, Pascal, BASIC and Python-like subsets. This is not full-language support and should not be described as an ANTLR implementation. See `backend/legacy.py`, `backend/lexer.py`, `backend/parser.py`, `backend/ir.py`, and `data/supported_subset.json`. |
| 4 | Design a hybrid back end that constrains model assistance with explicit mappings. | **Partially implemented.** | Deterministic code generation is used for supported constructs. For unsupported constructs, the optional model path can produce suggestions/candidates when configured. Candidates are not integrated into generated target code or automatically accepted. The descriptive `backend/rules.py` catalogue is not itself an executable rule-coverage table. |
| 5 | Validate behavior with execution-based checks rather than surface-level similarity metrics alone. | **Partially implemented.** | The program executes generated target code and compares output with the project's limited source interpreter; benchmark cases also compare target output to separately authored expected outputs. This is empirical finite-case checking, not a formal equivalence proof. Do not describe internal interpreter agreement as an independent oracle. |
| 6 | Document precisely what the project contributes relative to surveyed work, including what it does not contribute. | **Documentation objective; this status matrix and the report prompt support it.** | The prototype itself does not establish research novelty. The contribution must be framed as an implemented engineering prototype plus a reproducibility/evaluation workflow, with proposed capabilities clearly separated from measured results. |

## Candidate literature-gap claims from the presentation

The presentation proposes five gap areas. Retain them as **candidate review questions** until
the full cited work is located and checked. The short labels shown on the slides are
insufficient as complete citations.

| Candidate gap | Claim shown in presentation | Required verification before reporting it as established |
|---|---|---|
| Scalability | Translation success may fall on programs above roughly 100 lines. | Locate the cited PoPL/ACM PL 2025 source; verify the tested systems, benchmark, program-size measure, and whether the finding generalizes to source-to-source transpilation. The current project has no >100-line scalability study. |
| Evaluation and benchmark reliability | A benchmark analysis reportedly found correct translations graded as failures. | Locate the 2026 artifact-analysis source; inspect its examples, grading setup, and prevalence. The current project does not independently establish a field-wide benchmark reliability problem. |
| Feature/API mapping | Cross-language feature/API mapping can produce subtle semantic divergence. | Locate and read the cited PLDI 2025 source; extract the exact construct/API setting and evidence. The current rule catalogue does not by itself solve or measure this gap. |
| Repository-level corpus scarcity | Available data may be function-level while tasks require project/repository context. | Verify the cited EMNLP 2025 evidence, dataset units, and task definition. CodeNet totals in the repository are published metadata totals only; no full local archive audit has been completed. |
| Multilingual bias and cross-paradigm transfer | Translation quality may track language representation in training data. | Locate the cited Xu et al. 2026 work and verify language coverage, measures, and findings. This prototype has no model-level bias experiment. |

Do not invent author lists, titles, venues, page numbers, DOIs, or causal explanations for
these shorthand citations. If a cited source cannot be verified, omit or qualify the
claim and list it as a source requiring author follow-up.

## Related-work taxonomy and LLM follow-up systems

The presentation suggests organizing the survey around parser-based tools, general
transpilers, domain-specific translators, intermediate-language compilers, and interface
generators. Example names visible in the presentation include ANTLR; Babel, Emscripten,
JSweet and GWT; CxGo, C2Rust and JavaToCSharp; Haxe; and SWIG. These tools do not all
solve the same task and are not direct baselines by default. Compare only verified
capabilities and clearly state each system's purpose, source/target languages, semantic
guarantees, and evaluation method.

The presentation also names Rectifier, UniTrans, ExeCoder, TransAgent, BabelCoder, and
retrieval-augmented/multimodal methods as related LLM work. Treat this as a reading list,
not a verified claim that they share one limitation or that they are directly comparable.
Check primary sources and avoid the slide's generalization that repair necessarily leaves
translation unconstrained unless each cited paper supports that specific claim.

## Contribution-to-gap mapping, with honest status

| Candidate gap | Project response/design decision | Current status and evidence limit |
|---|---|---|
| Scalability | Normalize parsed programs into an intermediate representation instead of relying on arbitrary line-window fragmentation. | A normalized representation exists for prototype inputs, but the project has no large-program or >100-line scalability evaluation. Do not claim that it reduces cross-fragment errors. |
| Evaluation reliability | Keep validation and benchmark reporting in the project, expose failure categories, and compare expected outputs separately where available. | Implemented as prototype I/O checks and a 24-case pilot; the internal source interpreter is not independent. No compiler-flag or linker-configuration study has been performed. |
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
7. **LLM fallback effect:** measure only after a fixed model is configured, candidates
   are integrated behind validation, and paired rule-only/hybrid runs use the same
   cases and independent outcomes. Report calls, candidates, accepted candidates,
   validated translations, unchanged/unsupported cases, failures, and latency. Current
   evidence has zero configured cases and zero calls, so fallback improvement is
   unmeasured.
8. **Scalability, cross-language semantics, and bias:** require purpose-built
   benchmarks and controlled analyses; none are established by the current 24-case
   pilot.

## Current evidence summary

The pinned evidence snapshot reports 23/24 end-to-end passes, 24/24 expected outcomes
matched (23 supported translations and one correctly recognized unsupported COBOL
loop), 23/23 available expected-output comparisons matched, and 29 tests passed at its
recorded revision. A fresh local rerun on 2026-10-16 produced the same benchmark totals
and 31 passing tests; it also recorded zero configured LLM cases, zero LLM calls, and
zero generated candidates in both experiment variants. The rerun includes the current
uncommitted documentation/UI alignment changes; benchmark implementation and case data
were unchanged. This remains a small project-authored/task-derived pilot and does not
establish broad generalization or LLM improvement. See
[`project_report_evidence.json`](./project_report_evidence.json) for the pinned and
latest validation records.
