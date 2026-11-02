# Improvement plan

## Inspected baseline (2026-11-02)

The repository was inspected at commit `ba5a018` on branch `master`. The tracked
worktree was clean; an existing untracked `.vscode/` directory was preserved.
There is no `AGENTS.md`. Python 3.13.1 and Node.js v24.20.0 are available. No
GnuCOBOL, GNU Fortran, Free Pascal, or documented BASIC compiler was found on
PATH. The existing suite passed: `python -m pytest -q` (37 tests).

The current prototype has deterministic legacy front ends, a shared IR for the
legacy path, a complete-program provider fallback, restricted Node execution,
Docker-only isolated Python candidate execution, finite I/O comparison, and
historical benchmark evidence. The principal gaps found in code and documents
were that candidate states were mostly ad-hoc fields, review was not an API
operation bound to hashes, repair was not a reusable bounded lifecycle, and
evaluation artifacts did not have a single immutable run writer.

## Prioritized work and acceptance criteria

1. **Candidate lifecycle and review** — explicit states, exact candidate and
   evidence hashes, user-supplied reviewer identity, and invalidation on changes.
   Accepted when unit tests cover approval, rejection, and changed evidence.
2. **Bounded repair** — at most two repairs, complete revalidation, preserved
   attempt lineage, repeated-output termination, and development-only diagnostics.
   Accepted when deterministic mock-provider tests pass.
3. **Reproducibility** — every new run gets a unique UTC ID, command, settings,
   runtime, input hashes, case outcomes, and no overwrite. Accepted when the
   offline evidence CLI produces a new file and tests verify its schema.
4. **Native validation adapters and live paired trials** — implement only when
   toolchains/credentials are available; otherwise record `not_run` with reasons.
5. **UI exposure** — surface lifecycle state, evidence hashes, and review action
   without exposing hidden fixtures.

## Progress

- [x] Baseline and local toolchain audit.
- [x] Hash-bound candidate lifecycle and review endpoint.
- [x] Bounded repair helper with a two-repair ceiling.
- [x] Immutable offline evidence writer and CLI.
- [x] Native compiler adapter interface and bounded compile/run implementation;
  local execution is blocked by unavailable compilers.
- [ ] Live provider paired effectiveness evaluation (blocked unless explicitly
  configured and authorized; no paid run was started).
- [x] Persistent review endpoint and UI review form; independent evidence and
  second-reviewer identities remain required before approval.

Passing finite tests remains evidence for tested inputs only. It is not formal
equivalence and it is not human approval.
