# The four private `Clip` aliases could be `Box`

GitHub issue: [#189](https://github.com/findlaywebb/pyntpot/issues/189)

**What exists today.** `pyntpot.ink.polyline.Box` is the one public alias for an
axis-aligned box `(x0, y0, x1, y1)` (ADR 0068). Four private modules still define their
own `Clip = tuple[float, float, float, float]` for the same concept: `maps/layers.py`,
`maps/relief_layers.py`, `maps/cover.py` and `maps/osm_elements.py`. No public signature
names them, so the public-signature gate does not see them.

**What the feature would add.** One name per concept: each `Clip` replaced by `Box`,
imported from `pyntpot.ink.polyline`, so a reader meets the same name for the same thing
everywhere.

**Possible shape.** A rename in the four modules and their annotations. No behaviour or pixel changes; no ADR, since nothing public
moves.
