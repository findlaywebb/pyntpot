# A watercourse tagged tunnel=no counts as underground

`pyntpot.maps.osm_elements._waterway` sets `buried = bool(tags.get("tunnel"))`,
so any non-empty `tunnel` value marks the way's length as underground. OSM uses
`tunnel=no` to say a way is explicitly not in a tunnel, and that value is a
non-empty string, so a river whose ways all carry `tunnel=no` is gathered as
wholly underground and `pyntpot.maps.osm._open_rivers` drops it once its buried
share reaches `BURIED_FRAC`.

The docstring of `_open_rivers` said a river that is `tunnel=yes` end to end
goes; the code drops one that carries any `tunnel` tag end to end. P6 rewrote
the docstring to say what the code does and does not change code, so the
behaviour stays.

To show it: feed `sort_element` a `waterway=river` way with `tunnel=no` inside
the clip box, then call `_open_rivers` on the harvest; the river is missing
from the result and `counts["river_buried"]` is 1.

Possible fix: treat only the tunnel values that mean underground as buried
(for example any value other than `no`), with a test pinning `tunnel=no` and
`tunnel=culvert`. It can move a pixel on a card whose payload carries
`tunnel=no`, so it needs a G-self check against the Lynmouth fixture.
