# 0014 — How the code was ported

Status: accepted

## Context

The painting code existed before this package. Moving it and restructuring it in one
step would have let a behaviour change hide inside a layout change.

## Decision

The port went in order: move the code with `ruff format` applied and only the listed
edits; prove parity with a golden plate test; scrub; build the façade; then split into
layers. While the code sat in the private `pyntpot._port` subpackage, the lint, type and
line budget gates carried an explicit exemptions file for it, which the split emptied.

The parity test is `tests/golden/test_parity.py`, against the plates in
`tests/golden/lynmouth/`. ADR 0006 records how those goldens are regenerated.

## Consequences

- `pyntpot._port` no longer exists and `tests/architecture/exemptions/` holds header
  comments only. ADR 0010 records the end of the package.
- The strategy is finished history. It is recorded so the shape of the early commits is
  explained, not as a procedure to repeat.
