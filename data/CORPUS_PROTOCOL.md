# Corpus protocol

## Purpose and status

This protocol defines selection and evaluation rules for the current small
project-authored, task-derived pilot and a future independent legacy-program corpus.
The current held-out set has whole-task grouping and 26 cases in eight task groups:
22 supported-translation cases and four expected-unsupported cases. The separate
reference evaluator matches 25 expected-output records and 38 declared fixtures. The six
CodeNet cases cover six distinct task groups: p02600, p02606, p02607, p03997 (Trapezoids),
p02724 (Golden Coins), and p03238 (Programming Education). Their source files have
hash-bound GNU Fortran 14.3.0 builds and fixed fixture results. Independent owner review
of source/task semantics, fixtures, and reuse terms remains pending. The prepared
case-by-case review packet is [`independent_oracle_review_queue_v2.json`](./independent_oracle_review_queue_v2.json);
its decisions and elapsed review time are blank until a human completes it. The corpus
is still a small pilot, not a representative sample.

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

The corpus manifest carries `split_group` and `split`. The current manifest has 16
development records and 26 held-out cases across eight task groups (Maximum of two numbers,
Loops/For, and six CodeNet AtCoder problems). The runner evaluates only test records
and reports development records excluded. Five held-out groups remain too few for a
generalization estimate. For a larger set, use deterministic 70/15/15 group
splitting with a fixed seed and publish the split manifest. The CodeNet candidate export
uses seed 2026 and groups submissions by problem; this is only a reproducible triage
split, not an evaluation split until candidates pass curation.
Report group counts per split; if the independent test split is too small, do not present
the score as a generalization estimate.

## CodeNet assessment

Project CodeNet documents 13,916,868 submissions across 55 languages in its README and
describes the full archive as 7.8 GB. IBM released the full dataset under
CDLA-Permissive-2.0; the CDLA FAQ says the agreement is intended to cover datasets and
their individual contents. It permits use, modification, and sharing subject to making
the agreement text available with redistributed data. The GitHub repository's
Apache-2.0 license covers repository code, not the dataset. Preserve source-site
provenance and review any conflicting terms for each selected task.

IBM's published [CodeNet statistics workbook](https://github.com/IBM/Project_CodeNet/blob/main/assets/Project_CodeNet_statistics.xlsx)
reports these language totals:

| Published language label | Submissions | Accepted |
|---|---:|---:|
| Fortran | 15,059 | 8,018 |
| Pascal | 8,727 | 4,820 |
| COBOL | 1,277 | 727 |
| Visual Basic | 2,116 | 1,087 |

The workbook has no plain BASIC row; Visual Basic is a different dialect and is not
counted as a match for this project's BASIC subset. These published totals are metadata
statistics, not usable-sample counts.

### Local archive audit (2026-10-25)

The extracted local archive was inventoried with the conservative audit tool. The
machine-readable outputs are
[`codenet_audit.json`](./codenet_audit.json) and the metadata-only
[`codenet_candidate_manifest.jsonl`](./codenet_candidate_manifest.jsonl). The audit
read 4,053 per-problem metadata files and counted 13,916,868 submissions, of which
7,460,588 have metadata status `Accepted`. Source-file presence was checked only for
accepted submissions whose CodeNet language label maps to this prototype's supported
subsets; other languages are metadata-counted only.

| CodeNet label | Submissions | Accepted | Accepted source present | Screened sample |
|---|---:|---:|---:|---:|
| COBOL | 1,277 | 727 | 727 | 10 |
| Fortran | 15,059 | 8,018 | 8,018 | 10 |
| Pascal | 8,727 | 4,820 | 4,820 | 10 |
| plain BASIC | no matching row | â€” | â€” | 0 |

All 30 sampled records received source hashes, CodeNet problem/task groups, and a
deterministic provisional split assignment (22 train, 4 development, 4 test across
30 task groups). The sample screen produced 27 parser/pipeline errors and 3
unsupported-syntax results; **zero** passed the prototype screen. The parser errors
include constructs outside the documented subsets and are recorded per candidate in
the candidate manifest. This small hash-sampled screen is not a representative success
rate.

At the user's direction, the Fortran candidate `codenet-p02606-s368691152` is included
in [`codenet_local_screening_manifest.jsonl`](./codenet_local_screening_manifest.jsonl)
as a **local restricted screening challenge** in the main corpus manifest. It is not
part of the scored benchmark or held-out score. The record preserves the source hash, local archive
reference, five fixtures, compiler command/results, and review scope. Its GNU Fortran
14.3.0 explicit-free-form build passed the three official samples and two derived
fixtures. CodeNet's `Accepted` status and GNU Fortran 9.2.1 compiler are metadata; the
local build does not reproduce that original environment. The dataset-level
CDLA-Permissive-2.0 license covers individual contents according to the CDLA FAQ. No
separate license header was found in this submission. AtCoder copyright ownership is
recorded as provenance; the CodeNet data license is the documented reuse basis. If
source data is redistributed, make the CDLA agreement text available. This challenge
remains unscored because it is one task group and the source is stored outside this
repository.

The held-out corpus now also contains the separate CodeNet submission
`codenet-p02607-s779285219` for AtCoder AIsing 2020 B: An Odd Problem. It is expected
unsupported because array-section input is outside the documented subset. Its two
official samples and two derived fixtures were checked against GNU Fortran 14.3.0; its
source SHA-256 and build record are in
[`codenet_case_review_p02607.json`](./codenet_case_review_p02607.json). The complete
CDLA-Permissive-2.0 text is included at
[`licenses/CDLA-Permissive-2.0.txt`](./licenses/CDLA-Permissive-2.0.txt). The case
contributes only to unsupported-syntax recognition, not supported-translation success.

Three more fixture-backed CodeNet Fortran cases were promoted after target screening,
independent task-formula checking, and native source rebuilds:

| Case | Task group | Target fixtures | Native Fortran outputs | Translation subset |
|---|---|---:|---|---|
| `codenet-p03997-s040559345` | ABC045 A: Trapezoids | 4 | 7, 16, 5000, 2 | scalar input, integer arithmetic, formatted output |
| `codenet-p02724-s408275047` | ABC160 B: Golden Coins | 5 | 2020, 0, 495, 1000, 2000000000 | integer division and Fortran `MOD` |
| `codenet-p03238-s608868631` | ABC112 A: Programming Education | 3 | Hello World, 8, 10 | scalar input, block IF, addition |

The native builds used GNU Fortran 14.3.0 in `gcc:14-bookworm`, with networking disabled
and source mounted read-only. The source hashes, individual fixture outputs, license basis,
and pending owner review are recorded in `codenet_case_review_p03997.json`,
`codenet_case_review_p02724.json`, and `codenet_case_review_p03238.json`. The separate
arithmetic/task evaluator matches all 38 fixtures (including unsupported challenge fixtures);
both target benchmark runs match all 34 fixtures for the 22 supported cases. The owner has
not yet recorded an independent human review, so these are machine-checked cases, not
independently human-reviewed cases. Adding these three groups increases the held-out count
by 13% and task groups by 60%; the resulting eight groups remain far below the planned
100-group study.

The audit checks file presence and a bounded translation screen; neither is original-
language compilation or an independent semantic oracle. The GitHub repository license
does not grant rights to every third-party submission.

The saved 30-record screen predates the FORTRAN scalar `READ(*,*)` and formatted
`WRITE` support added to the prototype. The current screen reports a recognized
stdin-reading program as `input_fixture_required` when no fixture is present; this is
code-generation coverage, not a behavior pass. Re-run the audit with a predeclared
fixture for a candidate before reporting any new screen pass. No automatic inputs or
expected outputs are synthesized from CodeNet source.

## Current manifest

[`corpus_manifest.jsonl`](./corpus_manifest.jsonl) lists the project's current local and
task-derived examples, source hashes, expected outputs/outcomes, source provenance,
license status, and task split grouping. It is deliberately explicit that adapted
Rosetta Code cases contain project-authored source, not copied Rosetta Code programs.

## Independent-source curation log

[`corpus_exclusions.jsonl`](./corpus_exclusions.jsonl) records external-source leads
that were assessed but not admitted. Exclusion records preserve the source/repository,
task grouping, split disposition, license review, source hash status, original build
status, fixture/oracle status, and specific exclusion reasons. A missing source hash is
explicitly marked as unavailable; it must not be replaced with a hash of a URL or a
derived/transformed source.

The Exercism COBOL Hello World lead is excluded: its `src/hello-world.cob` file is an
unfinished student starter, and the exact candidate revision, build, fixture, and oracle
were not independently verified. The track repository documents a test command for
example implementations, which is useful provenance but does not establish that this
starter is a valid solution. The local CodeNet audit is complete, but most sampled
records remain screening-only. A later rescreen of the same 30 source files after
adding scalar Fortran stdin/output support produced one fixture-backed prototype pass,
24 parser/pipeline errors, and five unsupported-syntax results. The passing p02606 /
s368691152 case is catalogued as an unscored local challenge; its local build and
dataset-level license basis are documented above. The second held-out CodeNet case,
p02607/s779285219, is in the unsupported-recognition set with a native build and four
fixtures. The third curated submission, p02600/s098305279, is held out as a supported
scalar-input case with a native build and 17 fixtures. Its independent owner review is
pending. The CDLA license text is included. Most other triage
records still lack task-specific fixtures and independent oracles. The rescreen report
is `codenet_rescreen_v1.json`; candidate metadata and fixtures are in
`codenet_candidate_manifest.jsonl`.

Do not promote an exclusion into `corpus_manifest.jsonl` until all of the following are
complete for the exact immutable source revision: compute and verify its source SHA-256;
establish applicable redistribution/use terms; run the original build/test command or
record an independently verifiable accepted status; preserve predeclared fixtures; check
their expected outputs against an independent oracle; and assign the whole task/repository
group to one split. Record exclusions when any gate fails or cannot be checked.

## Reproduction

From the repository root:

```powershell
python tools\corpus.py validate-manifest
python tools\corpus.py audit-codenet --root C:\datasets\Project_CodeNet --output data\codenet_audit.json
```

The CodeNet audit requires its extracted `metadata` and `data` directories. It does not
download the archive or copy source code into this repository.
Add `--candidate-manifest data\codenet_candidate_manifest.jsonl` to write metadata-only
records for a deterministic sample of screened candidates. Uncurated records remain
`screening_only` with unavailable oracles; the CodeNet dataset-level CDLA license is
recorded, but each candidate still needs task/source provenance, fixtures, build status,
and an independent oracle before evaluation admission.
