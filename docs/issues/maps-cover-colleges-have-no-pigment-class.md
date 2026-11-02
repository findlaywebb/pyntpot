# Colleges and other education land have no pigment class

GitHub issue: [#44](https://github.com/findlaywebb/pyntpot/issues/44)

`maps/cover.py` maps a fixed list of OpenStreetMap tags to pigment classes, and
`landuse=education` and `amenity=university` are not on it. On the Oxford card the historic
core, whose land is mostly colleges, is cream paper with the green of the quads while the
suburbs, which are `landuse=residential`, carry the honey. The core reads emptier than its
edges. A theme can only recolour the classes there are, so it cannot favour the colleges.

Found by the round-2 map critique (2026-10-25).

To show it: paint `docs/images/places/oxford.webp` from `tests/fixtures/oxford/` and compare
the core with Jericho or the Iffley Road.

Possible fix: add `landuse=education` (and `amenity=university` areas) to `COVER_TAGS`, as
`built` or as a class of its own that a theme can set. The land cover plates and docs
images move, so it needs a regeneration window of its own with an ADR.
