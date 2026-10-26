# 0015 — Pydantic at the boundary only

Status: accepted

## Context

Validated input is needed where data enters: a style from a TOML theme, a track from a
GPX file, annotations from a caller. The painting internals are numeric and gain
nothing from validation models.

## Decision

Pydantic v2 is a runtime dependency (`pydantic>=2.13`) and is used only at the boundary,
in `Style` (`pyntpot.maps.style`), `Track` (`pyntpot.maps.track`) and `Annotations`
(`pyntpot.maps.annotations`). Internals stay numpy arrays and frozen dataclasses. The
style groups are dataclasses for that reason (ADR 0005). An import-linter contract keeps
`pyntpot.ink` and `pyntpot.letters` free of `httpx` and `pydantic` (ADR 0010). The
public names built on these models are listed in ADR 0007.

## Consequences

- A boundary type that needs validation lives in `maps`.
- Importing pydantic from `ink` or `letters` fails `lint-imports`.
