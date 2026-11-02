# The engine could read an SVG drawing

GitHub issue: [#74](https://github.com/findlaywebb/pyntpot/issues/74)

**What exists today.** `pyntpot.maps.svg_path.parse_path` reads back only the
`M` and `L` path data that `path_d` writes, and it is private to `maps`. The
public `ink` names (`wash`, `stamp`, `Brush`, `paper_plate`, `composite`) take
numpy masks and point lists, so a caller who wants to paint a vector drawing
must read the SVG with another library and hand pyntpot the shapes.

**What the feature would add.** A public reader that turns an SVG file into
what the engine paints: filled shapes as masks for `wash`, stroked paths as
point lists for `stamp` or the nib, with curves flattened to a stated
tolerance and the drawing's colours offered as pigment choices.

**Why it is not a defect.** The engine paints shapes; it never claimed to read
a drawing format. The tutorial that paints an SVG drawing uses a third-party
reader in the example script only (maintainer, 2026-10-23, P7 research Q-P6).

**Possible shape.** A module in `ink` (it says nothing about maps) with one
function from a path to a list of shapes, each a mask or a polyline with its
fill or stroke colour. It needs an ADR for the public name and a decision on
whether the reader is written in-house (paths, basic shapes, transforms) or an
optional dependency, kept out of `ink`'s required imports.
