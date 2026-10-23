# Candidate acceptance and review policy

## Current rule

Model output is an unaccepted proposal. A successful syntax check or one successful
execution does not establish translation correctness. The application must not merge a
candidate into trusted output automatically. Python candidates remain syntax-only and
must not be executed inside the application process.

## Evidence required before a candidate can be accepted

1. **Source review:** confirm that every source construct is understood, identify
   unsupported language features and external dependencies, and record the source
   dialect and complete input program hash.
2. **Build and static checks:** parse/compile with the actual target toolchain and
   intended target version; reject syntax errors, unresolved placeholders, TODOs,
   invented APIs, and undeclared dependencies.
3. **Behavioral checks:** run every independently specified input fixture plus boundary
   cases (zero, negative and equal operands where legal; empty/singleton/multiple loop
   iterations; both branches; and error/termination cases that are in scope). Compare
   output, exit status, and specified side effects against an oracle independent of the
   transpiler's interpreter. Test the same source program against more than one input
   where the source dialect supports runtime input; otherwise use distinct source
   variants and label them as such.
4. **Regression checks:** run the entire relevant source-to-target suite and confirm
   that adding the candidate does not change unrelated translations.
5. **Security checks:** inspect filesystem, network, subprocess, environment, and
   dependency use. Restrict generated behavior to the declared program contract.
6. **Human review:** one reviewer with source-language knowledge and one reviewer with
   target/runtime knowledge inspect the source, candidate diff, fixtures, failures, and
   dependencies. Both record a decision; unresolved semantic questions mean reject or
   retain as a proposal.
7. **Acceptance record:** store source/candidate hashes, model and prompt versions,
   fixtures and oracle source, toolchain/runtime versions, test results, reviewer
   identities, date, and accept/reject decision.

## Safe execution

JavaScript candidate execution is currently delegated to Node's permission mode with a
short timeout and a scrubbed environment. This is a prototype safeguard, not a complete
sandbox or acceptance policy. Python candidates are not executed. If Python execution is
added, run candidates in a disposable container or VM with no credentials, no network,
read-only inputs, a separate writable scratch directory, CPU/memory/process/output
limits, and a hard wall-clock timeout. Do not execute generated Python in the web/API
process or on the host filesystem.

## Current status

No model candidate has passed this policy. The v3 refresh returned no candidate in the
paired JavaScript or Python run. The one-candidate v2 result is historical and was
validated on only one fixed input; it is not accepted translation evidence.

## Learned-rule behavior

The current implementation can induce an experimental statement-pattern rule from one
deterministic translation that passes the configured finite checks at low or medium
risk. The supported schema is limited to flat assignment/print programs whose
expressions are single literals or identifiers. Variable and literal values become
slots in the target template. The rule is keyed by source language, target language,
schema, and deterministic rule-table version; every match is revalidated. Loops,
branches, compound expressions, high-risk cases, and model candidates are not learned.
This restricted rule induction is not the human-reviewed candidate acceptance
workflow described above, and passing finite checks does not establish semantic
correctness for every program matched by the pattern.
