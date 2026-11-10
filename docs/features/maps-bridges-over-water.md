# A road that crosses a river could read as a bridge

GitHub issue: [#209](https://github.com/findlaywebb/pyntpot/issues/209)

**What exists today.** A road and a river that cross are two strokes, one laid over the
other, and the map shows a junction rather than a crossing. The road pass drops the way's
`bridge` and `layer` tags: `_road` in `src/pyntpot/maps/osm_elements.py` (line 224 on)
files each piece as a dict of `c`, `n`, `r`, `k` and `d` only (lines 250 to 257), so
nothing downstream can tell a bridge from a ford. The Overpass feature query does fetch
the tags, because it asks for `out geom` and the way query at
`src/pyntpot/maps/providers/overpass.py:116` takes every tag on a highway. The only place
`bridge` is read today is as a landmark: `way["bridge"]["name"]` at
`overpass.py:140`, and `"bridge"` in `LANDMARK_TAG_KEYS` (`osm_elements.py:41-52`, entry
at line 49). `layer` is not read anywhere under `src/pyntpot/maps`.

**What the feature would add.** A road that OpenStreetMap tags `bridge=yes` (or
`viaduct`, `cantilever` and the like) is drawn as a bridge: a late pass over the water,
its casing knocking out the water beneath it so the river is seen to pass under. The
Wye at Hay-on-Wye and the Usk at Crickhowell are the obvious cases to try; a small
Welsh or Border fixture with a named bridge fits the fixture-box rule in
`CONTRIBUTING.md`.

**Why.** At the scales the library paints, a bridge is the one place a road and a river
meet on purpose. Hand-drawn maps mark it with a short casing that breaks the river line;
the current map shows a tangle.

**Approach sketch.**

- The features provider keeps `bridge` and `layer` on each road piece (a field beside
  `k` in the dict at `osm_elements.py:250`, small values only so the cache stays small).
  `Features` is a settled provider protocol, so the payload shape change is an ADR.
- A late bridge pass with its own shared sort key, as openstreetmap-carto does with its
  bridges layer (CartoCSS attachments: `::casing` then `::fill`, ordered by `layer`).
  Bridges are sorted by `layer` so a bridge over a bridge stacks correctly. `layer`
  alone, with no `bridge` tag, is not enough to draw one (a tunnel is `layer=-1`).
- The casing knocks the water out beneath it, using the casing and line-effect model of
  spec 009. Note that spec 009 already draws the road group after the water group
  (`specs/009-line-effects-and-registry/research.md`, section 2), so an ordinary road
  casing already breaks the river line. The bridge pass is what adds the tag-driven part:
  which pieces get a casing, a wider one, and the late ordering over other roads.
- A theme field for the bridge casing, defaulting to off so no pinned image moves.

**Dependencies.** The line-effect model and casing from spec 009 ([ADR 0070](../decisions/0070-line-effects-and-one-pigment-registry.md)). The
route's casing, set in a theme as `line_effects: {route: cased}`, shares the same casing primitive; see [Case, light or shadow a line](../how-to/case-light-or-shadow-a-line.md).

**Open questions.**

- Does a bridge keep its ordinary road class colour, or take its own?
- Tunnels (`tunnel=yes`, `layer=-1`): drawn dashed under the water, or left out?
- A bridge shorter than a few pixels at the map's scale: dropped, like the generalisation
  thresholds drop short ways?
- Railway bridges, once railways are fetched at all.
