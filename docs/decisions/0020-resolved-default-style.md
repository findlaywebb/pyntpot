# 0020 — The default style is the resolved one

Status: accepted

## Context

The reference sheets were painted with a resolved style: the old painter's defaults
with the theme's overrides applied, and one route ink per sport.

## Decision

This is a pointer. ADR 0005 records the decision: the style groups carry the resolved
default style, not the theme JSON of the old code, and no `ChartStyle` or theme merge
logic was ported. The packaged theme `src/pyntpot/maps/themes/default.toml` holds those
resolved values, and `Style.default` reads it; the groups' dataclass defaults are the
old class defaults and are not what the sheets were painted with.

## Consequences

- A change to a default value in the theme moves the golden plates and is a golden
  regeneration under ADR 0006.
