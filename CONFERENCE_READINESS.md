# Conference readiness: ICSE 2027 Tool Demonstration

## Defensible paper claim

The project is an inspectable compiler-design prototype for documented subsets of
COBOL, FORTRAN, Pascal, BASIC, and a project-specific Python-like language. It exposes a
rule-first translation path, normalized intermediate data, unsupported-syntax reporting,
optional complete-program model proposals, and finite target checks. The contribution
is the tool and its visible translation/validation boundary, not a new translation
algorithm or a demonstrated accuracy improvement.

## Current evidence

- Deterministic held-out pilot: 20 cases from two task groups; 17 supported outputs
  matched separately authored expected outputs for both JavaScript and Python; three
  COBOL `PERFORM` cases were recognized as outside the supported subset.
- The expected outputs match a separate reference evaluator (20/20) but have not been
  executed against native source-language compilers or reviewed by a second human. The
  two-task test set is not representative and does not establish general semantic
  equivalence.
- The historical prompt-v3 paired benchmark at pushed commit `ade68dc` returned no
  candidate after three provider attempts for either target. A later fixed, single-input
  provider trial generated JavaScript and Python candidates; both passed their recorded
  runtime check and matched one predeclared output. The Python review record also reports
  three fixture-variant matches. These trial candidates remain unaccepted: source and
  human review gates are pending, and the COBOL source was not checked with a native
  compiler. Neither run establishes fallback effectiveness.
- Contract and risk checks gate finite-test eligibility and learned-rule storage; the
  learned-rule store only reuses matching templates. Their benefit has not been measured,
  and no ablation or causal improvement is claimed.
- No scalability or multilingual-bias experiment was performed; neither is a paper
  contribution or finding.

## Submission package

The user has said this is not currently being prepared for ICSE submission. The checklist
below is retained only if a submission package is requested later; it is separate from
the prototype's reproducibility and evidence-polish work.

The track-specific source is [`ICSE_2027_TOOL_DEMO.tex`](./ICSE_2027_TOOL_DEMO.tex).
The track requires IEEE conference format, a maximum of four pages including
references, identified authors, a public artifact and usage instructions, and a public
three-to-five-minute YouTube video. The deadline is 23 October 2026 AoE. See the
[official call](https://conf.researchr.org/track/icse-2027/icse-2027-demonstrations).

Author identities and video URL are placeholders, and this workspace has no LaTeX
compiler, so a final page-count-verified PDF has not been produced. The final paper also
needs a final author review. No submission has been made.
