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
- Prompt-v3 refresh from pushed commit `ade68dc`: no candidate returned after three
  provider attempts for either target; no fallback effectiveness claim is supported.
- Contracts, risk scores, failure records, and learned-rule examples are prototype
  diagnostics. No ablation or causal benefit is claimed.
- No scalability or multilingual-bias experiment was performed; neither is a paper
  contribution or finding.

## Submission package

The track-specific source is [`ICSE_2027_TOOL_DEMO.tex`](./ICSE_2027_TOOL_DEMO.tex).
The track requires IEEE conference format, a maximum of four pages including
references, identified authors, a public artifact and usage instructions, and a public
three-to-five-minute YouTube video. The deadline is 23 October 2026 AoE. See the
[official call](https://conf.researchr.org/track/icse-2027/icse-2027-demonstrations).

Author identities and video URL are placeholders, and this workspace has no LaTeX
compiler, so a final page-count-verified PDF has not been produced. The final paper also
needs a final author review. No submission has been made.
