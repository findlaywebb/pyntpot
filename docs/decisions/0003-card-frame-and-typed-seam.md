# 0003 — One card frame and a typed seam between fetch, paint and lettering

Status: accepted

## Context

The seam between fetching, painting and lettering a map is an untyped dict with short
keys (`c`, `n`, `k`, `r`, `d`, `w`, `wn`, `wp`). Geometry is written as SVG path strings
and parsed back by two copies of the same parser. The painter copies road, river and
coast geometry into its manifest (`label_geom`) only because the payload is thrown away,
so lettering reads map data through the painter. `compose` projects the track a second
time and patches the drift with a `route0` offset. Metres, display pixels and render
pixels are converted in at least three places, one of them an ad hoc card class built
from the manifest.

## Decision

- **One card frame.** `pyntpot.maps.card.Card` is the coordinate frame of one map: a box
  in card metres and the display and render pixel grids it maps to. It is the only place
  that converts between card metres, display pixels and render pixels. It is a leaf: it
  holds no raster and imports nothing from the painter.
- **A typed seam.** `Basemap` (what was fetched and projected) and `Plates` (what was
  painted) are typed values. Geometry is carried as point lists in card metres, not as
  SVG path strings.
- **One projection.** The track projection is computed once, carried with the basemap,
  and reused by painting and lettering; nothing re-projects the track.
- **No cache key on the basemap.** The cache owns keys; `Basemap` carries none.
- **The base hash** covers the card and a typed `Layers` value holding exactly what the
  painter reads, hashed in a canonical form with every float formatted to three
  decimals, so a last-ulp difference between two machines' maths libraries cannot move
  it.
- **Removed inside the one golden regeneration:** `label_geom`, the second path parser,
  and the `route0` patch with the card offset that carries it.
- **The manifest** keeps only painter outputs and measurements. Its final key set is
  fixed inside the regeneration and does not change after it.
- **Golden `plates.json`** is compared by its `hash` only.

## Consequences

- Frame and projection bugs live in one module, tested on literal frames.
- The card lands first, behaviour-neutral: it reproduces the replaced class's operation
  order, so every pixel stays byte-identical against the same machine's output.
- Removing the one-decimal path round trip and the `route0` patch can move pixels, so
  those steps happen inside the single golden regeneration, each bounded against the
  step before it.
- Tests build typed values instead of dicts with magic keys.
- A later change to the card's fields, the `Layers` fields, the hash input or the
  manifest key set after the regeneration is itself an ADR.
