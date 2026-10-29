# Prototype walkthrough

This walkthrough shows one supported translation and one unsupported construct. It
takes about five minutes. Deterministic translation works without an LLM key; model
fallback is optional and depends on the configured provider.

## Start the prototype

From the repository root:

```bash
docker compose up --build
```

Open <http://127.0.0.1:8000> and stop the server with Ctrl+C. The container includes
Python and Node.js so both target paths are available. The default Compose setup does
not pass `.env` into the container. For local development, see **Run locally** in
`README.md`.

## Walkthrough

1. **State the scope (30 seconds).** This prototype translates documented subsets of
   COBOL, FORTRAN, Pascal, BASIC, and a project-specific Python-like language. It
   exposes unsupported syntax and reports finite target-side checks. It is not a
   general-purpose migration system.
2. **Show a supported translation (90 seconds).** Select COBOL and JavaScript, load
   the built-in example, and translate. The example computes the maximum of 17 and
   25, producing `25`. Open the compiler details to show tokens, normalized IR,
   translation rules, and validation output. This is a fixed example, not evidence of
   general semantic equivalence.
   Open **Validation evidence** to show the API's `acceptance_policy` decision and
   reasons. A finite-check pass is eligible only when all required contract checks
   pass and risk is below high. Low risk runs once; medium risk repeats source and
   target twice; high risk uses three runs and requires human review. High-risk,
   failed-contract, unsupported, or model-candidate results cannot enter learned-rule
   memory. These gates control prototype use and storage; they do not certify correctness.
   For an input-driven example, select FORTRAN and enter whitespace-separated values
   in **Program input (stdin)**. The subset supports scalar list-directed `READ(*,*)`
   and scalar formatted `WRITE`; without supplied values, code is generated but runtime
   validation stays pending.
3. **Show an unsupported construct (90 seconds).** Load the LLM fallback example.
   Point out the unsupported external `CALL`, the deterministic partial output, and
   the separate fallback status. Without a configured provider, the request is
   skipped. With a provider, any returned candidate is still unaccepted and requires
   the review process in `CANDIDATE_ACCEPTANCE.md`.
   If discussing the fixed COBOL `PERFORM` provider trial, show its report separately:
   both target candidates passed the recorded runtime check and matched one predeclared
   output, while the Python review report records 3/3 fixture-variant matches. State that
   these are one-source smoke results, the source was not native-compiler checked, and
   required reviews remain pending.
4. **State the evidence boundary (30 seconds).** The held-out pilot contains 23
   records across five task groups: 19 expected-translatable and four expected-
   unsupported cases. Nineteen supported outputs matched the expected outputs for
   each target; all four unsupported cases (three COBOL loops and one CodeNet Fortran
   array-input case) were recognized. CodeNet p02600 passed 17 fixtures and p02606
   passed five fixtures and a native Fortran build; p02607 passed two official and two
   derived fixtures under a native Fortran build. The owner's independent CodeNet reviews remain pending. The other task-derived outputs have
   not had native source-compiler checks or a second human review. This pilot does not
   establish general semantic equivalence or an effectiveness gain from model fallback.
   The current v6 live ablation on these same cases had no provider candidates because
   all eligible project-authored requests failed to connect; CodeNet input was withheld
   from the provider. Do not present it as evidence of model improvement.

## Recording notes

- Keep source code, metrics, and validation messages readable on screen.
- Do not present a model response as guaranteed or semantically validated.
- If showing a live provider request, ensure credentials are not visible and narrate
  only the result observed in that run.
