# 0027 — Export the candidates, the vector layers and a fed route ink

Status: accepted

## Context

A caller that chooses its own names, draws its own map when nothing is painted, or draws
different routes in different inks needs three things no public name gives: what a track
passes, the basemap's vector layers, and a route drawn in a colour and width of its
choosing. Each is a caller-supplies-the-data need; none needs pyntpot to know what a track
records.

## Decision

This ADR amends ADRs 0007 and 0026, which both stay as written.

These names join `pyntpot.maps.__all__`; none is top-level:

| Public name | Defining module | Package |
| --- | --- | --- |
| `candidate_export` | `maps.candidates.export` (was `landmark_export`) | `pyntpot.maps` |
| `vector_layers` | `maps.vector_layers` (new) | `pyntpot.maps` |
| `VectorLayers` | `maps.vector_layers` (new) | `pyntpot.maps` |

One method joins `Style` and is public with it under ADR 0026's member rule, so no
`__all__` changes for it: `with_route_ink`.

`landmark_export` is renamed as it is promoted, because it exports the route, its
settlements and its climbs as well as the landmarks; every importer is repointed at once
and no shim is left behind.

The signatures:

- `candidate_export(track, cache, key)`, returning a fresh JSON-ready `dict[str, Any]`
  that is the caller's to change.
- `vector_layers(track, cache, key, style, places=(), *, origin=None)`, returning a
  `VectorLayers` or `None` when neither the features nor the elevation payload is cached
  under `key`. The picks travel in `style.basemap`'s `pick_landmarks`, `pick_roads` and
  `pick_places`, not in a parameter. `origin` is where the track's first point sits in
  card metres; with none, the track's south-west corner is 0, 0. The ground kept round the
  track is fixed at 900 m before the box's scale. Six parameters is the most ruff's
  `max-args` allows.
- `Style.with_route_ink(*, colour=None, width_px=None)`, returning a copy of the style
  whose `route_ink()` has this colour and this width, each kept from the theme when
  `None`; with neither, the copy equals the style. It raises `ValueError` when `colour` is
  not a `#` and six hexadecimal digits, or `width_px` is not above zero.

Both cache readers take the cache key (`Cache.key` of the track and the providers that
filled the cache), not the providers: the key is all they read the providers for, it is
what `Cache`'s own readers take, and neither ever fetches. The key must be the track's; a
key for another box reads that box's payloads. Neither writes anything.

ADR 0007's fixed route ink is replaced by: the route ink is the theme's unless a caller
feeds its colour and width. pyntpot has no notion of what a track records, and a caller
that inks routes differently keeps its own table. The treatment and the effect stay the
theme's. `NibStyle.label_route_ink`, the lettering's route-coloured ink, stays independent
(ADR 0005).

The boundary is unchanged: `maps -> letters -> ink`, `ink` and `letters` import neither
`httpx` nor `pydantic`, and the import-linter contracts stay as they are.

### Contracts

The candidate export is a plain dictionary of numbers and strings, read from the payloads
cached under `key` only. Its keys:

- `id` (the cache key), `points`;
- `route`: `total_km`, `sustained_ascent_m` and `settlements`, each settlement with
  `name`, `kind`, `km` and `off_route_m`;
- `climbs`, in route order, each with 29 keys: `approach_trimmed_km`, `avg_grade_pct`,
  `bearing_deg`, `bottom_ele_m`, `end_km`, `end_lat`, `end_lng`, `features`, `from`,
  `gain_m`, `heading`, `length_km`, `near_start`, `near_top`, `of_climbs`,
  `position_pct`, `rank_by_gain`, `rank_by_steepness`, `roads`, `runout_trimmed_km`,
  `share_of_climbing_pct`, `start_km`, `start_lat`, `start_lng`, `steepest_500m_km`,
  `steepest_500m_pct`, `through`, `to`, `top_ele_m`;
- `candidates`, each with `class`, `distance_m`, `lat`, `lng`, `name`, `notable`,
  `reach_m`, `tags`, `x` and `y`.

It chooses nothing and fetches nothing: a box with nothing cached has no candidates, no
settlements and climbs that are not grounded.

`VectorLayers` is a frozen value whose fields are `key`, `clip`, `bounds`, `span_m`,
`scale`, `river_width_px`, `sea`, `mapped_sea`, `park`, `wood`, `lakes`, `rivers`,
`coastline`, `roads`, `contours`, `hachures`, `hillshade_bands`, `hillshade_image`,
`trees`, `landmarks`, `places` and `sources`. Every path is SVG path data in card metres
at the vector output's 0.1 m, y north. The same payloads, track, key, style, places and
origin always give the same value.

Under ADR 0026's token rule:

- `VectorLine.cls`'s `"major"`, `"minor"`, `"river"` and `"stream"` are tokens;
- the `landmarks` entries carry the keys the vector map carries today (`n`, `cls`, `d`,
  `x`, `y`, `tags`, and `picked` or `missing` for a pick), and the `places` entries the
  keys `Basemap.places` carries (`n`, `sym`, `kind`, `always`, `x`, `y`, `note`);
- `with_route_ink`'s colour is a free value, not a token.

`VectorArea`, `VectorLine`, `HillshadeBand` and `HillshadeImage` are reached only through
`VectorLayers` and are not public names (ADR 0026, "Members").

## Consequences

- The default render, every golden and the pinned digests are unchanged: each name takes
  data the caller supplies, and the default behaviour does not move.
- `with_route_ink` moves `digest()` and neither `base_digest()` nor `lettering_digest()`,
  so a fed route ink repaints no plate.
- A new public name, or a change to one, still needs a new ADR.
- The theme's `route_inks` table keeps four named inks of which `route_ink()` reads one;
  renaming it is a later issue (`docs/issues/maps-style-route-inks-one-read.md`).
