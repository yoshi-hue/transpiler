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

### Project facts to use and verify against the repository

- The project is a prototype, not a full compiler or full-language migration product.
- Implemented source-language subsets are documented in `data/supported_subset.json`: COBOL, FORTRAN, Pascal, BASIC, and a project-specific Python-like grammar. JavaScript and Python are target backends for the implemented subsets.
- The legacy-language pipeline has tokenization/parsing, normalized intermediate representation (IR), deterministic rule-first code generation, and executable validation. Describe only implementation details verified in the code.
- The LLM is an optional, scoped fallback for unsupported constructs. It can generate suggestions/candidates, but generated fallback code is not integrated into the final generated target program or automatically accepted. Do not say that the model completes or repairs end-to-end translations.
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

Include research questions or hypotheses that can be tested, such as whether rule-first translation improves inspectability or whether a validated fallback can improve outcomes. Do not write these as established findings. Explain a future fair evaluation: fixed model/prompt/runtime, larger independently sourced corpus, independent output oracles, repository/task-level splits, deduplication, per-language and per-construct metrics, and rule-only versus hybrid versus a genuinely toggled full-system ablation.

#### 5. Implementation & Screenshots

Describe only verified implementation details. Include:

- technology stack and how to run the application, using current `README.md` instructions
- source/target language subsets and their explicit exclusions
- pipeline components and API/UI surfaces, where present
- benchmark inputs, oracle sources, evaluation procedure, and runtime versions
- how to reproduce tests and benchmark results
- the corpus manifest and CodeNet audit workflow, with licensing and oracle caveats
- limitations and threats to validity

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
