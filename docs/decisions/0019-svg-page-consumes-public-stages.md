# 0019 — The upstream SVG page consumes public pipeline stages

Status: accepted

## Context

The upstream journal map page keeps its own SVG pipeline. It needs the projection, the
layers, the plate paths, the route pixels and the placed labels, and it must never reach
for a private name.

## Decision

This is a pointer. ADR 0007 records the decision and lists the attributes the page
reads: `Basemap` (`projection`, `layers`, `track`, `track_time`), `Plates` (`manifest`,
`paths`, `card`, `route_px`, `strands`) and `Lettering` (`labels`, `spans`,
`plate_path`). `Track` carries an optional `time`, in seconds from the first point, so
time-stated spans still resolve. ADRs 0026 and 0027 amend 0007 with later additions.

Rejected: embedding the composed PNG in the page, because the page would lose its
vector route marks.

## Consequences

- The page imports public names only; a name it needs is added by an ADR.
