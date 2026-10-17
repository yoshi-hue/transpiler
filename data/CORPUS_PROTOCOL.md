# Corpus protocol

## Purpose and status

This protocol defines selection and evaluation rules for the current small
project-authored, task-derived pilot and a future independent legacy-program corpus.
The present held-out set has whole-task grouping and separately authored expected
outputs; those outputs match a separate reference evaluator (20/20), but have not been
checked against native source compilers or by a second human reviewer. This is not an
independent or representative corpus.

## Supported subset

The machine-readable subset definition is [`supported_subset.json`](./supported_subset.json).
It mirrors the implemented parser/backend behavior in `backend/legacy.py` and the
Python-like grammar in `backend/lexer.py`, `backend/parser.py`, and `backend/codegen.py`.
It is a deliberately narrow subset, not a claim of full dialect support.

## Inclusion and exclusion

Include a candidate only when all of these are recorded:

- stable program ID and source SHA-256
- origin dataset/repository and immutable URL or commit
- explicit license identifier and redistribution decision
- language and dialect/version when known
- task/problem grouping, and repository grouping where applicable
- expected outcome and a separately sourced or independently executed oracle
- adaptation notes; untouched source is marked as such

For the supported-translation set, require the original source to be accepted/buildable
or runnable in its original environment and to be within the documented subset. A case
that uses unsupported syntax may instead enter the unsupported-challenge set, but must
have that expected outcome declared before evaluation.

Exclude generated, vendored, copied dependency, malformed, exact duplicate, and
near-duplicate programs. Exclude any source whose license/terms cannot be established
for the intended research use. Do not redistribute code merely because it was publicly
downloadable.

## Oracle and correctness

Prefer documented input/output fixtures from the original task or execute the original
program in a pinned original runtime. Store input and expected output separately from
the translator's source interpreter. The current fixed-constant edge cases use
separately authored expected outputs derived from arithmetic and inclusive-loop
semantics; they have not been cross-checked against native compilers. Mark them as
separately authored (not independently executed) and do not present them as proof of
source-language equivalence. If no independently checkable oracle is available, mark
the case `oracle_status: unavailable` and exclude it from correctness claims.

For supported cases, require:

1. no unsupported syntax reported by the translator
2. target compilation/execution success
3. target output equals the independent oracle for all recorded inputs

Report semantic translation accuracy separately from unsupported-syntax recognition.
Never combine the two into one success rate without displaying both denominators.

## Deduplication and splits

Exact duplicates are detected using source SHA-256. Near duplicates must be
clustered by task/problem and reviewed before splitting. All programs from the same task
and repository must stay in one split. Do not randomly split submissions/snippets from
the same task across development and test.

The corpus manifest carries `split_group` and `split`. For the current pilot, all local
smoke tests and all A+B task variants are in development; Maximum-of-two-numbers and
Loops/For task groups are held out together in test. The benchmark runner evaluates only
test records and reports the number of development records excluded. This leaves two
held-out task groups, so its rate is a descriptive pilot statistic, not a generalization
estimate. For a larger set,
use deterministic 70/15/15 group splitting with a fixed seed and publish the split
manifest. The CodeNet candidate export uses seed 2026 and groups submissions by problem;
this is only a reproducible triage split, not an evaluation split until candidates pass
curation.
Report group counts per split; if the independent test split is too small, do not present
the score as a generalization estimate.

## CodeNet assessment

Project CodeNet documents 13,916,868 submissions across 55 languages in its README and
describes the full archive as 7.8 GB. The GitHub repository's Apache-2.0 license covers
that repository's licensed materials; it does **not**, by itself, establish that every
third-party submission in the dataset can be redistributed or used under the same
terms. Review the dataset/source-site terms and any per-file rights before reuse.

IBM's published [CodeNet statistics workbook](https://github.com/IBM/Project_CodeNet/blob/main/assets/Project_CodeNet_statistics.xlsx)
reports these language totals:

| Published language label | Submissions | Accepted |
|---|---:|---:|
| Fortran | 15,059 | 8,018 |
| Pascal | 8,727 | 4,820 |
| COBOL | 1,277 | 727 |
| Visual Basic | 2,116 | 1,087 |

The workbook has no plain BASIC row; Visual Basic is a different dialect and is not
counted as a match for this project's BASIC subset. These are published metadata
statistics, **not** source-present or usable sample counts. The full archive transfer
was attempted but not completed in this workspace, so no source-present counts or
translator-screened sample counts are claimed. Run the audit script on the extracted
archive to obtain them. It reports metadata counts separately from conservative
translator-screened candidates and marks licensing as requiring review. The screen is
a triage measure, not original-language compilation or an independent semantic oracle.

## Current manifest

[`corpus_manifest.jsonl`](./corpus_manifest.jsonl) lists the project's current local and
task-derived examples, source hashes, expected outputs/outcomes, source provenance,
license status, and task split grouping. It is deliberately explicit that adapted
Rosetta Code cases contain project-authored source, not copied Rosetta Code programs.

## Reproduction

From the repository root:

```powershell
python tools\corpus.py validate-manifest
python tools\corpus.py audit-codenet --root C:\datasets\Project_CodeNet --output data\codenet_audit.json
```

The CodeNet audit requires its extracted `metadata` and `data` directories. It does not
download the archive or copy source code into this repository.
Add `--candidate-manifest data\codenet_candidate_manifest.jsonl` to write metadata-only
records for a deterministic sample of screened candidates. Their `expected_outcome` is
`screening_only`, their oracle is unavailable, and their license status is
`review_required`; these records are not eligible evaluation cases until a curator
reviews them.
