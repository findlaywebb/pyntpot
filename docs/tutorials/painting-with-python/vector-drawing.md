# Vector drawing: a small drawing, its filled shapes washed and its strokes inked

You hand the engine a drawing that is not yours: a small SVG of a fell, a tarn, a
dry-stone wall and two trees. This page shows the file, then the drawing flat, then each
step the script takes towards a painting. You see what each step adds and what it
changes.

pyntpot does not read SVG itself. The engine paints masks and point lists. This script
reads one file with the standard library. [The feature note](../../features/ink-read-svg-drawings.md)
says what it would look like for pyntpot to read drawings for you.

![A pale ochre sun, a blue-grey far fell and a green main fell with a dark pen line along its top. Two green banks lie in front. A tarn sits on the main fell, with a blue beck running down from it and a broken brown track beside the beck. A dry-stone wall crosses the left bank. Two round dark green trees and two birds complete the scene.](../../images/painting-with-python/svg-drawing.webp)

*Painted by `examples/svg_drawing.py`, seed 5.*

Run the script:

```bash
uv run python examples/svg_drawing.py out/ --figure washes
```

It reads [`examples/drawings/fell.svg`](https://github.com/findlaywebb/pyntpot/blob/main/examples/drawings/fell.svg), a drawing
made for this repository and released under its MIT licence. `--figure` picks the picture:
`flat`, `washes`, `ink` or `painting` (the default). Each run writes one image into
`out/`. It is `svg_drawing-<figure>.png`, or `svg_drawing.png` for the painting.

## The raw SVG

Open [`examples/drawings/fell.svg`](https://github.com/findlaywebb/pyntpot/blob/main/examples/drawings/fell.svg)
alongside this page; it is short. The drawing is a handful of `<path>` elements, listed
back to front. The filled shapes come first, each with a `fill` colour and a `d`
attribute of path data. The strokes follow, each with a `stroke` colour, a `stroke-width`
and a `class` that names a pen: the skyline along the top of the main fell, the wall as a
base line with a row of stones on it, then the track, the beck, the two trunks and the
birds.

## What the script reads

The script reads only four commands, all absolute:

| Command | Meaning | Numbers |
| --- | --- | --- |
| `M` | start a new subpath | x y |
| `L` | a straight line | x y |
| `C` | a cubic Bezier curve | x1 y1 x2 y2 x y |
| `Z` | close the subpath | none |

A curve is flattened into `CURVE_SEGMENTS` (twelve) straight segments, so every shape is
a list of points. Any other command, a lowercase one included, raises `ValueError`. This
is deliberate. A drawing outside the subset fails at once instead of painting half of
itself. The file is written by hand with this subset in mind.

The drawing's `viewBox` is 600 by 400. The script scales it to fill 88 per cent of the
paper's width and centres it, so the picture keeps a margin of bare paper. That is the
only transform. The file has no `transform` attributes, and the script ignores any it
meets.

## The drawing flat

![The drawing in flat colour on white: a pale ochre sun, a blue-grey fell behind a green fell, a pale blue tarn, two green banks, a wall of small stones, a brown track, a blue beck, two round trees and two birds, all with hard clean edges.](../../images/painting-with-python/svg-flat.webp)

*Painted by `examples/svg_drawing.py`, figure flat.*

This is what a browser shows. Pillow fills each shape in its own `fill` colour and draws
each stroke in its own `stroke` colour, on white. Every edge is hard, every colour is
uniform and the near fell sits cleanly over the far one. Nothing here is pyntpot yet. It
is the drawing you are about to paint.

## Fills become washes

![The same drawing as washes on warm paper: the sun, the far fell, the main fell, the banks and the tarn are soft-edged washes of pigment, with two round trees in darker green. There are no lines.](../../images/painting-with-python/svg-washes.webp)

*Painted by `examples/svg_drawing.py`, figure washes.*

A filled path is a mask. The script draws its points with Pillow's `ImageDraw.polygon`
onto a greyscale image and hands that array to `wash`, as the rungs handed it a disc. The
`fill` colour picks the pigment. The script takes the nearest colour in `PIGMENTS` and
`PAINTERS_PIGMENTS`, so `#bfd2cd` is `wetland`, `#9ec4de` is `water` and `#4f7d36` is
`sap_green`.

This adds paper, soft edges that pool a little pigment, and grain in the body of each
wash. It also changes how shapes overlap. A shape is washed around the shapes in front of
it, so the paper is left bare under the tarn, and the far fell does not show through the
near one. The washes are glazed with Kubelka-Munk, so where two do overlap, at the wet
edges, they keep their hue. The two trees are the darkest washes.

## Strokes become ink

![The same drawing as pen lines alone on warm paper: a dark skyline along the top of the main fell, a wall of small stones, a broken orange-brown track, a blue beck, two short tree trunks and two birds. There are no washes.](../../images/painting-with-python/svg-ink.webp)

*Painted by `examples/svg_drawing.py`, figure ink.*

A stroked path is a list of points, which is what `stamp` lays a brush along. The path's
`class` names the pen. `pen` is a fine nib for the skyline, the wall, the trunks and the
birds. `track` is a broken line for a footpath. `beck` is a wet blue one for the stream.
The `stroke-width` sets the brush's width. `ink_density` turns what the stamps laid into
ink. The `stroke` colour picks its pigment from the same two tables, so `#3a3a46` is
`indigo`, a dark blue-black.

This adds lines with soft edges and a track that breaks into dashes where the brush
lifts. A stroke is a stamp of a brush, not a stripe of constant width, so the lines are
not as clean as the flat ones.

## The painting

![A pale ochre sun, a blue-grey far fell and a green main fell with a dark pen line along its top. Two green banks lie in front. A tarn sits on the main fell, with a blue beck running down from it and a broken brown track beside the beck. A dry-stone wall crosses the left bank. Two round dark green trees and two birds complete the scene.](../../images/painting-with-python/svg-drawing.webp)

*Painted by `examples/svg_drawing.py`, seed 5.*

`composite` lays the washes first and the inks over them, in the order the file lists
them. That is the whole script: the washes figure and the ink figure on one sheet of
paper. The lines sit on the pigment.

## Try it

- Add a path to `fell.svg`: a second wall, or a sheep as a short `C` curve with a fill.
- Change a `fill` to `#dcd6c6` and the shape takes `rock`.
- Change the oak's `fill` to `#2b3d8f` and it takes `ultramarine`, which makes a blue tree.
- Give a stroke a new `class` and add a pen to `PENS`.
