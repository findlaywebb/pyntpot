# 0002 — Layered package, enforced by import-linter and AST tests

Status: accepted

## Context

Agentic development discovers code by reading it; a clean, machine-enforced dependency
direction keeps each layer's responsibility obvious and stops an agent from quietly
wiring a dependency in the wrong direction.

## Decision

One distribution, three target subpackages, dependencies pointing towards `ink`:
`maps -> letters -> ink`.

- `ink` is the painting engine and imports nothing outside itself.
- `letters` is hand lettering and imports `ink` only.
- `maps` is the route-map application and imports `letters` and `ink`.

The layering is a later outcome. The port lands first as the private subpackage
`pyntpot._port` with no layer contract, and the layers contract is added when the port is
split. Until then one forbidden-imports contract keeps plotting, dataframe, template and
YAML libraries out of the package.

This is enforced two ways: import-linter (`[tool.importlinter]` in `pyproject.toml`) for
the import graph, and AST fitness tests (`tests/architecture/`) for what import-linter
cannot express: no `print`, no clock or module-level randomness, the file-size budget,
the no-mock rule, the banned-term scan and the coordinate allowlist.

## Consequences

- Adding a new cross-layer edge is itself an ADR.
- The architecture tests parse source directly, so they fail fast and cheaply.
- The exemptions directory is the only sanctioned relaxation, and the split empties it.
