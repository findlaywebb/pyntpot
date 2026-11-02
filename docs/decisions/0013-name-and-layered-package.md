# 0013 — The name and the layered package

Status: accepted

## Context

The project needed a name and a package shape that an agent can read cold. The
layering itself is already recorded: ADR 0002 set it and ADR 0010 added its contract.

## Decision

This is a pointer. The package is named `pyntpot` (it reads "paint pot"; it was free on
PyPI and GitHub on 2026-10-03) and ships as one distribution. Its subpackages are
`pyntpot.ink`, `pyntpot.letters` and `pyntpot.maps`, layered `maps -> letters -> ink`.
ADR 0002 records the layering and ADR 0010 records the import-linter contracts that
enforce it.

## Consequences

- Changing the name, the distribution count or the layers is an ADR.
- Nothing is decided here beyond what 0002 and 0010 say.
