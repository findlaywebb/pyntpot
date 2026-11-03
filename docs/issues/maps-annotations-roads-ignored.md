# `Annotations.roads` is accepted and then ignored

GitHub issue: [#161](https://github.com/findlaywebb/pyntpot/issues/161)

Area: maps (annotations).

`Annotations` in `src/pyntpot/maps/annotations.py` has a field `roads: tuple[str, ...] = ()`.
The model forbids unknown fields and validates this one, so a caller can pass
`Annotations(roads=("A591",))` and the call succeeds. Nothing reads it: no module under
`src/pyntpot` touches `Annotations.roads`, and the roads a card letters are the ones the
lettering picks itself (`maps/lettering/picks_roads.py`). The module and field docstrings
say so ("Accepted and not read"), but the caller who sets it sees no error, no log line and
no road named.

The only working way to keep a named minor road is the theme's `[basemap] pick_roads`
(`BasemapStyle.pick_roads` in `maps/style_groups.py`), which is a style field, not an
annotation. So the public request type advertises a control that has no effect, next to a
`places` field that does work.

Possible fix: remove `roads` from `Annotations` (a public-API change, so an ADR), or make a
non-empty value raise a `ValueError` that points at `pick_roads`. If road picking per map is
wanted, wire `Annotations.roads` into the same path `pick_roads` feeds.
