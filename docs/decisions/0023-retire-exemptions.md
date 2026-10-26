# 0023 — Retire the exemptions mechanism

Status: accepted

Ends D5's interim relaxation.

## Context

`tests/architecture/exemptions/` let a file skip the 400-line budget and the clock and
random bans, and let a test be switched off by node id. It existed for the ported `_port`
package while it was split. P4.19 deleted `_port` and emptied the files, so all that was
left was code that read empty files.

## Decision

- Delete `tests/architecture/exemptions/` and `tests/support/exemptions.py`, and the
  collection hook in `tests/conftest.py` that read `gates_off.txt`.
- The line budget and the purity tests scan all of `src/pyntpot` with no skip list.
- No relaxation mechanism remains. A file over budget is split, not listed.

## Consequences

- The budget and purity tests have no escape hatch; a red one is fixed in the code.
- A test cannot be switched off by a list. Skipping one needs a marker in the test file,
  where review sees it.
