# Project Report Writing Prompt

Copy the prompt below into an AI writing assistant, attach the project report outline image if it is not already available, and provide any required institution-specific formatting rules. The prompt is tailored to this repository and tells the writer how to keep claims aligned with the implementation and evidence.

---

## Copy-and-use prompt

Act as an academic technical writer and software engineering report reviewer. Write a clear, detailed project report for the repository **Multi-Language Legacy Code Modernizer**, a research/course prototype for rule-first transpilation of documented subsets of legacy languages.

### Required report structure

Use the following seven numbered main headings, in this order, matching the supplied report-outline image exactly:

1. **Abstract**
2. **Introduction**
3. **Novelty in Project**
4. **Proposed Work**
5. **Implementation & Screenshots**
6. **Conclusion**
7. **Project Repository Link (GitHub or drive link)**

Use useful subheadings inside these sections. Keep the report academically readable and specific to the actual code. Do not add claims, results, screenshots, authors, institutional details, or citations that were not provided or verified.

### Required report length and page plan

The completed report must be **25–30 pages total**. Aim for about **27 pages**, counting the title page, table of contents, main text, figures/tables, references, and appendices. Follow any institution-specified paper size, margins, font, line spacing, and citation style; do not manipulate formatting or add filler to reach the page count. Use this allocation as a guide and adjust within the total:

| Report component | Target pages | What to include |
|---|---:|---|
| Title page and table of contents | 2 | Project title and only verified author/course/supervisor details; contents with page numbers. Leave clearly marked placeholders for missing personal or institutional details. |
| 1. Abstract | 1 | A concise abstract, keywords, and the scope/evidence caveat. |
| 2. Introduction | 3–4 | Context, motivation, problem statement, objectives, scope, research questions, and report organization. |
| 3. Novelty in Project | 3–4 | Contribution versus prior work, design rationale, what is an engineering contribution versus established novelty, and a concise related-work comparison table based on verified sources. |
| 4. Proposed Work | 4–5 | Proposed/current architecture, workflow, component status, algorithms or pseudocode, design choices, and future hypotheses. Distinguish implemented flow from presentation-only or planned flow. |
| 5. Implementation & Screenshots | 9–11 | Technology and repository structure, language subsets, compiler pipeline, LLM boundary, validation, UI/API, benchmark and corpus protocol, a worked example, genuine screenshots, reproducibility, results, and threats to validity. |
| 6. Conclusion | 1–2 | Summary of verified accomplishments, evidence limits, and prioritized future work. |
| 7. Project Repository Link, references, and appendices | 3–4 | Verified repository/commit link, complete references, and concise supporting appendices such as test commands, manifest schema, additional result tables, or glossary. |

The ranges are planning guidance, not permission to repeat material. Keep all seven required numbered headings in their original order. Place references and supporting material under section 7 or in clearly labeled appendices while retaining that heading. If a school template defines the page-count convention differently, prioritize the template and state which front matter/back matter is included in the count.

To reach the required length with useful content, specifically develop:

1. **A precise problem definition:** intended users, migration workflow pain points, project objectives, in-scope/out-of-scope behavior, and measurable research questions.
2. **A related-work discussion:** compare the project with verified compiler/transpiler and LLM-assisted code translation literature. Use a table with source, approach, language/task scope, validation method, and the carefully stated distinction from this prototype. Do not invent sources or assert novelty from absence of a search.
3. **An architecture and data-flow description:** provide a labeled diagram and a step-by-step account of tokenization, parsing, normalized IR, deterministic lowering, optional LLM candidate generation, target execution, and validation. Mark each component with its implementation status and explain where the actual system stops short of the proposed presentation.
4. **A language-subset comparison:** use a table for each source language showing dialect/subset, implemented constructs, explicit exclusions, target support, and representative test case. Derive it from `data/supported_subset.json` and verify against the implementation.
5. **A worked translation case study:** show a short, repository-authored source example, its relevant parsed/IR representation, generated target code, execution output, validation result, and what this example does and does not establish. Choose one example that actually runs; do not invent an output or claim a general result from one case.
6. **Implementation detail:** explain important modules and responsibilities, API/UI surfaces, run setup, error/unsupported-syntax behavior, rule catalogue semantics, and how the corpus tool works. Use a concise module table and small code excerpts only when they clarify the implementation; cite file paths and symbols accurately.
7. **Evaluation methodology and results:** state benchmark composition, inclusion/provenance, expected outcomes, oracle sources, target/runtime versions, commands, date, denominators, metrics, and exact current results. Include tables for aggregate results, per-language results, per-construct results, and expected-unsupported recognition when the current output supports them. If a breakdown or measure is unavailable, say so rather than fabricate it.
8. **A limitations and threats-to-validity analysis:** discuss subset size, small/project-authored benchmark, task-derived rather than independent legacy programs, source-interpreter dependence, limited oracle independence, lack of integrated LLM candidates, metadata-only mechanisms, missing true full-stack ablation, licensing, and external validity. Explain how each limitation affects interpretation.
9. **A reproducibility and ethics/data-provenance subsection:** provide safe run/test commands, identify which files contain examples and metadata, explain source attribution, deduplication and split grouping, and describe licensing review. Never place credentials, private data, or unapproved third-party code in the report or repository.
10. **A future-work roadmap:** prioritize concrete work with dependencies and evaluation criteria, including integrating fallback candidates only behind validation, obtaining and auditing the corpus, securing rights and independent oracles, expanding test diversity, adding real ablation switches, and reporting confidence intervals.

Use figures, tables, and appendices to explain evidence—not to pad pages. Every screenshot must be captured from the actual running application, every graph must be generated from measured results, and every code/output example must match the repository. If required evidence is unavailable, include a clearly marked placeholder or “not measured” note and list it among missing author inputs.

### Project facts to use and verify against the repository

- The project is a prototype, not a full compiler or full-language migration product.
- Implemented source-language subsets are documented in `data/supported_subset.json`: COBOL, FORTRAN, Pascal, BASIC, and a project-specific Python-like grammar. JavaScript and Python are target backends for the implemented subsets.
- The legacy-language pipeline has tokenization/parsing, normalized intermediate representation (IR), deterministic rule-first code generation, and executable validation. Describe only implementation details verified in the code.
- The LLM is an optional, scoped fallback for unsupported constructs. It can generate suggestions/candidates, but generated fallback code is not integrated into the final generated target program or automatically accepted. Do not say that the model completes or repairs end-to-end translations.
- One project objective is to investigate whether an LLM fallback can improve handling of constructs not covered by deterministic rules, while keeping proposed output subject to validation. This is an objective and testable hypothesis, not a demonstrated result: the current evidence run had zero configured LLM cases and zero calls, and candidate output is not integrated into generated target programs.
- The project includes contract, risk, failure-diagnosis, and learned-rule metadata. These are prototype/reporting mechanisms; they do not currently change generation or acceptance decisions and are not validated causal improvements.
- The validation compares output from the project’s limited source interpreter with execution of generated target code. This is empirical I/O checking, not a formal equivalence proof; the source interpreter is not an independent oracle.
- The descriptive rules catalogue and `/rules` endpoint support inspection/reporting. Catalogue size or labels are not executable rule coverage and must not be used as proof of language coverage.
- `data/external_task_cases.jsonl` contains 12 project-authored adaptations of three published Rosetta Code task prompts (A+B, Maximum of two numbers, and Loops/For), with fixed values in place of interactive input. They are task-derived challenge cases, not copied Rosetta Code implementations or independently collected legacy programs.
- The current benchmark consists of 12 local cases and 12 task-derived adaptations. The COBOL `PERFORM` loop is intentionally outside the declared subset and is expected to be reported unsupported.
- `data/corpus_manifest.jsonl` records 24 cases with source hashes, provenance, expected outcomes/outputs, oracle labels, and task-group splits. The current set is a small pilot, not a large independent corpus.
- `data/CORPUS_PROTOCOL.md` documents candidate selection, provenance, licensing review, independent oracles, deduplication, and leakage-resistant group splitting.
- The CodeNet archive was not fully downloaded/audited. Do not claim any measured CodeNet source-present, compatible, translated, or usable-sample counts. The repository’s corpus tool can audit a locally extracted archive, but its screen is triage only and does not establish original-language compilation or independent semantic correctness.
- IBM’s published statistics workbook reports 15,059 Fortran submissions (8,018 accepted), 8,727 Pascal (4,820 accepted), 1,277 COBOL (727 accepted), and 2,116 Visual Basic (1,087 accepted). The workbook has no plain BASIC entry; Visual Basic is not equivalent to this project’s BASIC subset. Label these strictly as published dataset metadata totals, not as locally audited or usable samples. Cite the workbook and state when it was consulted.
- The current experiment compares rule-only behavior with optional LLM candidate generation. It is not a completed ablation proving the benefit of LLM integration, contracts, risk-aware validation, or learned rules.
- The project should be positioned as a transparent hybrid compiler/AI-assistance prototype with a carefully scoped subset and evaluation protocol. Do not call it conference-ready or claim state-of-the-art performance.

### Presentation claims versus implementation status

The presentation may depict a proposed end-to-end hybrid system. Treat presentation diagrams and future-work descriptions as design intent, not proof that every box is implemented. Before writing the report, verify each claim against the current code and classify it using this matrix:

| Component or claim | Status to report | Required wording/evidence |
|---|---|---|
| Source tokenization/parsing, normalized IR, deterministic rules, target code generation | Implemented for the explicitly documented subsets | Describe the actual languages, constructs, and limits in `data/supported_subset.json`. Do not imply full-language support. |
| Generated-target execution and source-interpreter output comparison | Implemented as empirical validation | Call it I/O comparison over the tested cases. Explain that the source interpreter is part of the same prototype and is not an independent semantic oracle or proof of equivalence. |
| LLM fallback | Candidate/suggestion generation is implemented when configured; candidate integration into target output and automatic acceptance are not implemented | Say “fallback suggestion/candidate,” not “LLM-generated translation is integrated, repaired, or validated.” Report candidate generation separately from end-to-end translation correctness. |
| Semantic contracts, risk assessment, failure fingerprints, learned-rule records | Metadata, diagnostics, or reporting mechanisms in the prototype | State that these currently do not change code generation, acceptance decisions, or future model-call behavior. Do not attribute a correctness, reliability, or efficiency improvement to them without a controlled experiment. |
| Rules catalogue and `/rules` endpoint | Descriptive inspection/reporting surface | Do not describe catalogue size, labels, or family counts as executable rule coverage, language coverage, or correctness. |
| Full hybrid system and its claimed advantages | Proposed architecture/research hypothesis beyond the currently implemented end-to-end behavior | Present as proposed work or a hypothesis. Do not report as a demonstrated result. |
| Larger independent corpus, CodeNet compatibility, and usable sample count | Not established by the current repository evidence | The current 24-case manifest is a small pilot. Published CodeNet totals are metadata totals only; the archive was not fully audited, and its submissions have not been shown to be license-cleared, source-present, subset-compatible, or independently oracle-verified. |
| Benchmark and ablation claims | Only the exact current benchmark and experiment output may be reported | Run the current commands and preserve the output. Give denominators, per-language/construct breakdowns where available, and separate supported translation from expected-unsupported recognition. Do not claim an ablation for a component unless it is separately switchable and measured. |

For every feature shown in the presentation, label it in the report as **implemented**, **partially implemented**, **metadata/reporting only**, or **proposed/future work**. Use a diagram caption or callout to distinguish the current prototype path from any proposed path. If code inspection does not confirm a feature, do not silently infer that it exists from a slide, diagram, endpoint name, or architectural description; mark it unverified and ask the project author for clarification.

### Required content by section

#### 1. Abstract

Write one concise abstract (about 150–250 words) stating:

- the legacy-modernization problem and why semantics/correctness matter
- the research/project question
- the architecture and supported source/target subset
- what was actually implemented
- the evaluation design and only verified results
- the most important scope and evidence limitation

Avoid broad language-support or effectiveness claims.

#### 2. Introduction

Explain:

- the practical motivation and risks of modernizing legacy programs
- the distinction between syntax conversion and behavior preservation
- the problem statement and project objectives
- include this explicit objective: **investigate whether scoped LLM fallback can improve correct handling of unsupported-by-rules constructs without reducing reliability or bypassing validation**
- frame the corresponding hypothesis as untested: for cases where the deterministic translator reports unsupported constructs, a configured and properly integrated fallback, gated by independent validation, may increase the proportion of cases translated correctly compared with a rule-only baseline
- state that the current prototype/evidence does not test this improvement: the recorded run made zero LLM calls, and generated suggestions are not inserted into target output
- the declared source and target scope
- the report’s organization, if useful

Support general background claims with reliable, verifiable sources. Do not invent references or citations.

#### 3. Novelty in Project

Explain the contribution precisely and modestly:

- shared front-end/IR approach across a narrow set of legacy-language subsets
- deterministic rule-first translation for supported constructs
- optional, scoped LLM suggestions for unsupported constructs
- executable validation and transparent failure reporting
- provenance-aware benchmark/corpus workflow

Differentiate an engineering combination or prototype contribution from proven research novelty. Compare with prior work only when real sources have been verified. State what is not novel or not yet experimentally demonstrated where appropriate.

#### 4. Proposed Work

Describe the proposed workflow from source input through parsing, IR, deterministic translation, optional fallback suggestion, target execution, and validation. Separate:

- implemented system behavior
- planned extensions
- hypotheses that still need testing

Include research questions or hypotheses that can be tested, such as whether rule-first translation improves inspectability or whether a validated LLM fallback improves correct handling of constructs outside deterministic coverage. Make the latter a central project objective/hypothesis, not a result. A fair future test must use a configured, fixed model and prompt, integrate candidate output only behind an explicit validation/acceptance gate, compare paired rule-only and hybrid runs on the same independently sourced cases, and report how many unsupported cases become correctly translated, rejected, or remain unsupported. Use independent output oracles, repository/task-level splits, deduplication, per-language and per-construct metrics, and a genuinely toggled full-system ablation where applicable. Do not claim improvement from candidate-generation counts, an unconfigured run, or source-interpreter/target agreement alone.

#### 5. Implementation & Screenshots

Describe only verified implementation details. Include:

- technology stack and how to run the application, using current `README.md` instructions
- source/target language subsets and their explicit exclusions
- pipeline components and API/UI surfaces, where present
- benchmark inputs, oracle sources, evaluation procedure, and runtime versions
- how to reproduce tests and benchmark results
- the corpus manifest and CodeNet audit workflow, with licensing and oracle caveats
- limitations and threats to validity

#### Evidence snapshot already collected

Use [`data/project_report_evidence.json`](./data/project_report_evidence.json) as the auditable evidence snapshot for the current report draft. It records the run timestamp, source commit, commands, Python/Node versions, every benchmark case status, supported-versus-unsupported outcome counts, gold-output comparisons, LLM experiment summary, and test result. Cite the artifact in the report and make it available with the project materials.

For the snapshot generated on **2026-10-16** from source commit `08bf1367f34c581d04360c570318331269510c10`, the recorded results are:

- **Benchmark:** 23/24 end-to-end cases passed (95.8%). One case was `not_run` because its COBOL `PERFORM` syntax is intentionally outside the implemented subset. Do not call that case a successful translation.
- **Expected outcomes:** 24/24 matched (100%): all 23 expected-translatable cases passed; the one expected-unsupported case was recognized. Report this separately from the end-to-end pass rate.
- **Independent expected-output comparison:** 23/23 available expected-output checks matched. This is a separate measure and does not make the source-interpreter comparison an independent oracle.
- **LLM comparison:** rule-only and hybrid variants each recorded 23/24 end-to-end passes, zero configured LLM cases, zero LLM calls, zero generated candidates, and zero accepted candidates. This run therefore did **not** exercise the LLM and provides **no evidence for or against an LLM improvement**; it is not a meaningful test of fallback efficacy.
- **Automated tests:** 29 tests passed. This is the software test-suite result, not the benchmark sample size or translation success count.
- **Environment:** Python 3.13.1 and Node.js v24.20.0, targeting JavaScript.

Do not replace these counts with “8/8.” The 8/8 figure is not the current complete benchmark result. When results are rerun after code or environment changes, regenerate the evidence snapshot, note its new date and source commit, and use the new artifact rather than silently carrying forward these historical numbers.

Before stating numerical benchmark results, run the current benchmark and tests, record the date, command, target runtime versions, and output artifact, then transcribe the values exactly. Report denominators and separate:

- expected-translatable cases from expected-unsupported cases
- end-to-end validation from unsupported-syntax recognition
- local/task-derived examples from independently collected programs
- catalogue entries from executable rule coverage

If results cannot be rerun, mark them as historical/unverified rather than presenting them as current. Do not infer correctness from a candidate-generation event or from source-interpreter/target agreement alone.

Provide a screenshot plan and captions for genuine screenshots captured from the running application. Recommended evidence:

1. application landing/source editor and language selectors
2. one representative legacy source-to-target translation, showing source, target, and validation status
3. benchmark results with denominators and supported/unsupported status visible
4. rules catalogue or coverage report, explicitly labeled descriptive
5. architecture/workflow diagram, if available

Do not fabricate screenshots or claim a view exists when it does not. Use explicit placeholders such as `[Insert screenshot captured from the running application: ...]` if images have not been supplied.

Discuss threats to validity: small benchmark, project-authored/task-derived cases, narrow subsets, limited oracle independence, source interpreter limitations, lack of completed causal ablations, possible dataset licensing constraints, and lack of measured CodeNet source-screen results.

#### 6. Conclusion

Summarize what was built, what evidence supports, and what remains unproven. State that this is a prototype with narrow language subsets and a small benchmark. Give a prioritized future-work list: execute the local CodeNet audit; curate license-cleared cases; add independent oracles; expand language/construct coverage; improve split sizes and deduplication; implement true ablation switches and integrate fallback candidates behind validation; then rerun reproducible evaluation.

#### 7. Project Repository Link (GitHub or drive link)

Use the public repository URL:

`https://github.com/yoshi-hue/transpiler`

If the repository is private, unavailable, or the final report requires a release/commit permalink, replace this with the verified URL and commit identifier. Do not invent a drive link.

### References and academic integrity

- Include a references list as a subsection under an appropriate numbered section or at the end of section 7, while keeping the seven required main headings intact.
- Cite the project repository and files for implementation-specific facts.
- Cite Rosetta Code task pages only as the origin of task prompts, not as the source of the authored code snippets.
- Cite IBM Project CodeNet’s repository/statistics workbook for published corpus metadata. Clearly distinguish it from a local audit of the full archive.
- Verify every bibliographic detail, URL, and claim. Never fabricate a citation, DOI, result, baseline, screenshot, user study, or implementation.
- Use consistent in-text citations and reference formatting; follow any supplied institutional style guide.
- Use original phrasing, explain technical terms, and avoid copying source text from websites.

### Final quality check

Before returning the report, verify that:

1. all seven numbered main headings match the supplied image and appear in order
2. every implementation statement is supported by the repository
3. every numerical result has a source, denominator, and reproducible procedure
4. published CodeNet totals are not mislabeled as usable program counts
5. unsupported cases and unsupported-language constructs are not counted as successful translations
6. limitations are prominent and no broad or conference-readiness claims are overstated
7. screenshot placeholders are clearly marked wherever real images are still needed

Return the completed report followed by a short list of any missing details, screenshots, or measurements that must be supplied by the project author.
