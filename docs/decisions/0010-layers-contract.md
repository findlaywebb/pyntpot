# 0010 — Layers contract and the end of the port package

Status: accepted

## Context

ADR 0002 set the layering `maps -> letters -> ink` but deferred its contract: the ported
code lived in the private `pyntpot._port` subpackage, which no layer contract covered, and
the exemptions directory listed it. The split has since moved every `_port` module into
`ink`, `letters` or `maps`.

## Decision

`pyproject.toml` carries two more import-linter contracts beside the existing
forbidden-libraries one:

- A `layers` contract over `pyntpot.maps`, `pyntpot.letters`, `pyntpot.ink`: each layer
  imports only the layers below it.
- A `forbidden` contract: `pyntpot.ink` and `pyntpot.letters` may not import `httpx` or
  `pydantic`. Network access and validated models belong to `maps`.

`src/pyntpot/_port/` is deleted, with its per-file ruff ignores and its `ty` exclude. The
three exemption files shrink to a header comment. `tests/unit/maps/test_import_order.py`
loses the `_port` modules and the adapter checks, which the contract replaces; its
cold-import list names the final modules.

A1. The brush-sheet catalogue lives in `ink/brush.py`. Brush ids are opaque sheet cell
names: `ink` never reads a prefix as a map class. The choice of cell for each map class
stays in the style groups.

## Consequences

- A cross-layer edge in the wrong direction fails `lint-imports`; fix the code, never the
  contract.
- Changing either contract is an ADR.
- Adding an exemption is no longer available as a way to land code: the exemption files
  are empty.
