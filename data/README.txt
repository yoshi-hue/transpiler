validated_examples.jsonl is created automatically after a translation passes semantic validation.
It stores source, target, shared IR and validation information as small project-specific reference data.

external_task_cases.jsonl is a small, versioned task-derived evaluation set. Its A+B,
Maximum of two numbers, and Loops/For prompts refer to independently published Rosetta
Code tasks.
The source snippets in this file were authored for this project's restricted subset;
they are not copied source programs. Interactive input was replaced with fixed values.
Each case records its task URL, adaptation, and a separately authored expected output
when translation is expected. This is external-task-derived evidence,
not a large independently collected corpus, and the small set is not sufficient to
support broad generalization claims.

The current manifest has 42 records: 16 development and 26 held-out across eight task
groups. The held-out set has 22 supported cases and four expected-unsupported cases.
Six CodeNet Fortran cases span six task groups. Their hash-bound source/build/fixture
records are in the codenet_case_review*.json files. The separate oracle checker matches
25 expected-output records and 38 fixtures. Independent owner review remains pending.
See ../documentation/CORPUS_PROTOCOL.md for current counts, license scope, inclusion criteria, and limits.
