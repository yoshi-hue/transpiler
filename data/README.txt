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
