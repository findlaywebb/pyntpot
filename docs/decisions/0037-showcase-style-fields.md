# 0037 — Showcase style fields

Status: accepted

Amends 0005 (style groups): `BasemapStyle` and `CoverStyle` each gain one field. Follows 0035 for the digest rule.

## Context

The showcase maps need three things a theme could not say: a road set that leaves out service ways while
`roads = "all"`, a relief painted darker than the quiet default, and a route that darkens the wash it
crosses (a multiplied ink) or lies lightly on it (a part-opacity ink).

## Decision

- **`basemap.minor_road_classes`**, `tuple[str, ...]`, default `MINOR_ROADS` (`tertiary`,
  `unclassified`, `residential`, `track`, `service`): the minor highway classes `roads = "all"` keeps.
  `osm_elements._road` reads it. The fetch query is unchanged, so no payload or cache key moves.
- **`cover.relief_strength`**, `float`, default 1.0: multiplies the density of
  `painter.paper.relief_density`, and the 0.40 ceiling it is held to scales with it. `painter/relief.py`
  passes it in; at 1.0 the arithmetic is the same, so no golden moves.
- **Digests.** Both fields join `DIGEST_OMITS_AT_DEFAULT`, so at their defaults no digest of any
  style moves. A non-default value moves `base_digest` and `digest`, since the base plates read both.
- **Route blend and opacity.** `route_inks.<sport>.effect` is a free table that already holds
  `blend = "normal"`. `compose.route` now reads `blend` (`"normal"` or `"multiply"`, anything else is
  a `ValueError`) and `opacity` (0 to 1, read as 1.0 when absent, else `ValueError`), for the solid
  line and the pen route alike. `opacity` is not written into `default.toml`, because that would move
  the pinned `Style.digest()`. No other effect key is read.
- **Pinned tests.** The `CoverStyle` default digest in `test_style_groups.py` is re-pinned, since it
  hashes every dataclass field; the `BasemapStyle` defaults and both field-order rows gain the new names.

## Consequences

- A theme can drop service ways from a dense town map, strengthen the relief, and multiply or fade its route.
- The default style paints exactly as before.
- The effect table's casing, glow and shadow keys are still read by nothing.
