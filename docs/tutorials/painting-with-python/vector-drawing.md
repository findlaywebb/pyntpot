# Vector drawing: a small drawing, its filled shapes washed and its strokes inked

You paint a drawing that is not yours to the engine: a small SVG of a fell, a tarn, a
dry-stone wall and two trees. Filled shapes become washes; strokes are inked with a pen.

pyntpot does not read SVG itself. The engine paints masks and point lists, and this script
does its own reading of one file with the standard library. If you want pyntpot to read
drawings for you, [the feature note](https://github.com/findlaywebb/pyntpot/blob/main/docs/features/ink-read-svg-drawings.md) says what
that would look like.

![A pale sun, a blue-grey far fell and a green main fell stand above two green banks; a tarn sits on the fell, a pen-ruled wall crosses the left bank, and a track and a beck run down towards two small trees and a pair of birds.](../../images/painting-with-python/svg-drawing.webp)

*Painted by `examples/svg_drawing.py`, seed 5.*

Run the script yourself:

```bash
uv run python examples/svg_drawing.py out/
```

It reads [`examples/drawings/fell.svg`](https://github.com/findlaywebb/pyntpot/blob/main/examples/drawings/fell.svg), a drawing
made for this repository and released under its MIT licence, and writes
`out/svg_drawing.png`.

## What the script reads

The drawing is a handful of `<path>` elements. Each carries a `fill` or a `stroke`, and a
`d` attribute of path data. The script reads only four commands, all absolute:

| Command | Meaning | Numbers |
| --- | --- | --- |
| `M` | start a new subpath | x y |
| `L` | a straight line | x y |
| `C` | a cubic Bezier curve | x1 y1 x2 y2 x y |
| `Z` | close the subpath | none |

A curve is flattened into `CURVE_SEGMENTS` (twelve) straight segments, so every shape is
a list of points. Any other command, a lowercase one included, raises `ValueError`. That
is deliberate: a drawing outside the subset fails at once instead of painting half of
itself. The file is written by hand with this subset in mind.

## Fills become washes

A filled path is a mask. The script draws its points with Pillow's `ImageDraw.polygon`
onto a greyscale image and hands that array to `wash`, exactly as the rungs handed it a
disc. The `fill` colour picks the pigment: the script takes the nearest colour in
`PIGMENTS`, so `#bfd2cd` is `wetland` and `#9ec4de` is `water`.

The file lists its shapes back to front. The script keeps that order, and the default
compositing multiplies, so the tarn tints the fell it lies on and the oak's crown sits
darker where it overlaps the bank.

## Strokes become ink

A stroked path is a list of points, which is what `stamp` lays a brush along. The path's
`class` names the pen: `pen` is a fine black nib, `track` a broken brown line for a
footpath, `beck` a blue one for the stream. The `stroke-width` sets the brush's width.
`ink_density` turns what the stamps laid into ink, and `composite` lays it over the
washes.

## Fit it to the paper

The drawing's `viewBox` is 600 by 400. The script scales it to fill 88 per cent of the
paper's width and centres it, so the picture keeps a margin of bare paper. That is the
only transform: there are no `transform` attributes, and the script ignores any it meets.

## Try it

- Add a path to `fell.svg`: a second wall, or a sheep as a short `C` curve with a fill.
- Change a `fill` to `#dcd6c6` and the shape takes `rock`.
- Give a stroke a new `class` and add a pen to `PENS`.
