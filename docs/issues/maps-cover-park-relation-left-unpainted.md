# Christ Church Meadow is left as bare paper

GitHub issue: [#45](https://github.com/findlaywebb/pyntpot/issues/45)

On the Oxford card the largest shape inside the loop, Christ Church Meadow, is unpainted
cream. The land cover payload holds it as relation 1102976 (`leisure=park`, which
`maps/cover.py` classes as `meadow`); `polygon_rings` joins its ten outer members into one
closed ring of 174 points. A theme cannot reach it: with the meadow pigment set to pure
red at full strength the rest of the meadow in the card turns red and this shape stays paper.
The cause was not found; it lies between the ring and the painted plate.

Found by the round-2 map critique (2026-10-25).

To show it: set `[cover.pigments].meadow` to `#ff0000` and `[cover.cover_cfg].meadow` to
`[1.0, 0.0]` in `examples/themes/oxford.toml` and paint the Oxford card.

Possible fix: find where the ring is lost (the clip against the card box, the simplify, the
cover fill, or the ribbon fill that excludes the inside of a loop) and keep it.
