# ICSE 2027 Tool Demonstration submission checklist

**Target:** ICSE 2027 Tool Demonstration and Data Showcase track
**Submission deadline:** 23 October 2026, Anywhere on Earth
**Draft:** [`ICSE_2027_TOOL_DEMO.tex`](./ICSE_2027_TOOL_DEMO.tex)
**Artifact:** [public GitHub repository](https://github.com/yoshi-hue/transpiler); usage instructions are in `README.md`.

The official track requests a PDF of at most four pages including references, the IEEE
conference format (`IEEEtran`, 10pt conference), author identities (single-anonymous
review), a publicly available tool and usage instructions, and a public YouTube video
between three and five minutes. The video's URL must appear at the end of the abstract.
The submission site is [ICSE 2027 demos HotCRP](https://icse27demos.hotcrp.com/).

## Draft scope

The paper presents an early prototype demonstration, not a new translation algorithm
or a claim of improved correctness. It describes deterministic translation for declared
language subsets, inspectable intermediate data, unsupported-syntax reporting, optional
LLM proposals, and current validation boundaries. It excludes scalability and model-bias
contributions, makes no causal claim for contracts/risk/failure/learned-rule metadata,
and reports the v3 model request failures without extrapolating from the prior v2 pilot.

## Items that still require author action

- [ ] Replace the author, affiliation, and contact placeholders with verified identities.
- [ ] Record and publish a three-to-five-minute demo video; put its public YouTube URL at
  the end of the abstract.
- [ ] Compile with the official IEEE conference template and verify the PDF is no more
  than four pages including references. No LaTeX compiler is installed in this
  workspace, so the checked-in `.tex` is a source draft, not a validated PDF.
- [ ] Review the paper, code, README setup instructions, and artifact URL together after
  the final source changes; ensure the public repository points to the intended commit.
- [ ] Check final references against the cited primary papers and confirm there are no
  unresolved citation placeholders. The unidentified Xu et al. 2026 slide reference is
  omitted from the submission.
- [ ] Submit through the official HotCRP site before the deadline. No submission has
  been made.

## Evidence snapshot

The refreshed v3 paired run at pushed commit `ade68dc44200b043e77617857717d8da687b6699`
used prompt `legacy-modernizer-llm-v3` and model `gemini-3.1-flash-lite`. It produced no
candidate after three provider attempts per target. The strengthened held-out subset has
20 examples from two task groups; 17 supported target outputs matched separately
authored expected outputs in both targets, while three COBOL loops were correctly
reported unsupported. The expected outputs match a separate reference evaluator (20/20), but have not been
cross-checked against native source compilers or a second human reviewer. Full provenance and raw case files are in
[`data/EVIDENCE_V3_REFRESH.md`](./data/EVIDENCE_V3_REFRESH.md) and
[`data/evaluation_v3_javascript.json`](./data/evaluation_v3_javascript.json),
[`data/evaluation_v3_python.json`](./data/evaluation_v3_python.json).
