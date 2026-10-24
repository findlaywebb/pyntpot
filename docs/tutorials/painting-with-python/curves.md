# Curves: a rose, a Lissajous figure and a spirograph

![A five-petalled rose curve drawn in ink with a pen, its petals washed pale tan, on cream paper with a wide margin](../../images/curves/rose.webp)

Painted by `examples/curves.py` (seed 5, `figure="rose"`).

A curve is a rule that gives a point on the paper for every value of a number `t`. Step
`t` in small increments, join the points with a pen, and the curve appears. This page
draws three curves that way. Each is drawn with the narrow pen nib of the nib line rung,
over a light wash of one pigment, and each is scaled to the same reach so that a clear
margin of bare paper is left round it.

Run any of them with `uv run python examples/curves.py out/ --figure rose`, choosing
`rose`, `lissajous` or `spirograph`. The script writes `out/curves-<figure>.png`.

## The three formulas

<!-- from examples/curves.py -->
```python
def rose(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the rose `r = cos(5 t)` over `t` from 0 to pi, which closes after half a turn."""
    r = np.cos(5 * t)
    return r * np.cos(t), r * np.sin(t)


def lissajous(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the Lissajous figure with three swings across for two down."""
    return np.sin(3 * t + np.pi / 2), np.sin(2 * t)


def spirograph(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the hypotrochoid with ring 9, wheel 4 and pen distance 6 over four turns."""
    ring, wheel, pen = 9.0, 4.0, 6.0
    k = (ring - wheel) / wheel
    return (ring - wheel) * np.cos(t) + pen * np.cos(k * t), (ring - wheel) * np.sin(
        t
    ) - pen * np.sin(k * t)
```

- **The rose** is `r = cos(5 t)`. The radius swells and shrinks as the angle turns, and
  with a factor of 5 the curve makes five petals. `t` runs from 0 to pi: the second half
  of a turn would only draw the same petals again.
- **The Lissajous figure** is two swings at right angles, `x = sin(3 t + pi / 2)` and
  `y = sin(2 t)`. It swings across three times for every two it swings down, and the
  picture is a knot where the path crosses itself.
- **The spirograph** is the path of a pen fixed to a small wheel as the wheel rolls round
  inside a ring. The wheel has radius `r = 4`, the ring `R = 9`, and the pen sits at
  `d = 6` from the wheel's centre, which is further than the wheel's radius, so the path
  makes a loop at every turn of the wheel. The pen comes home after four turns, because 9
  and 4 share no factor, and by then it has made nine loops.

![A Lissajous figure in ink, three swings across to two down, crossing itself in a knot, with its enclosed loops washed pale blue](../../images/curves/lissajous.webp)

Painted by `examples/curves.py` (seed 5, `figure="lissajous"`).

## Scale the curve to the paper

The formulas give numbers between about -1 and 1 for the rose and the Lissajous figure,
and between about -10 and 10 for the spirograph. One function turns any of them into
pixels: it divides by the largest value, multiplies by the reach, which is 38% of the
width of the image, and centres the result. That reach is the margin: the paper left bare
is 12% of the width on every side.

<!-- from examples/curves.py -->
```python
def _points(figure: str, size: int) -> np.ndarray:
    """Return the figure's points in pixels, centred, scaled to `REACH` of the image."""
    formula, t_end, _pigment, _width = FIGURES[figure]
    x, y = formula(np.linspace(0.0, t_end, STEPS))
    scale = REACH * size / max(np.abs(x).max(), np.abs(y).max())
    return np.column_stack([size / 2 + scale * x, size / 2 + scale * y])
```

## Lay the wash under the curve

The wash needs a coverage mask: 1 inside the shape and 0 outside. Pillow's
`ImageDraw.polygon` fills the polygon the curve's points make, and it fills where the
outline winds an odd number of times round a spot. That is why the middle of the
Lissajous figure and the heart of the spirograph stay bare paper while the loops carry
colour. `wash` turns the mask into pigment density on the paper's noise, and `composite`
lays that density over the paper in the pigment's colour.

<!-- from examples/curves.py -->
```python
def _cover(points: np.ndarray, size: int) -> np.ndarray:
    """Return a 0 to 1 mask of the polygon the points make, filled where it winds an odd number of times."""
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).polygon([(float(px), float(py)) for px, py in points], fill=255)
    return np.asarray(mask, np.float32) / 255
```

<!-- from examples/curves.py -->
```python
    points = _points(figure, size)
    under = wash(_cover(points, size), sheet, 0.45, 0.35)
    paper = composite([(under, rgb(PIGMENTS[pigment]))], paper, PaperStyle())
```

## Take up the pen

The pen is the narrow nib of brush `MAJ6-e`, exactly as in the nib line rung. `stamp`
sets the nib's bristles along the curve's 4000 points into an accumulator, `ink_density`
turns the accumulator into ink on the paper's tooth, and `composite` lays the ink over
the painted paper in the ink colour the brush came with.

<!-- from examples/curves.py -->
```python
    brush, ink_hex = brush_from_id("MAJ6-e", nib_px * size / SIZE + 1.0, 1.0, BrushStyle())
    acc = np.zeros((size, size), np.float32)
    stamp(acc, points, brush, np.random.default_rng(SEED))
    density = ink_density(acc, brush, sheet)

    out = composite([(density, rgb(ink_hex))], paper, PaperStyle())
```

![A spirograph curve in ink: nine long loops round a small bare centre, with the loops washed pale green](../../images/curves/spirograph.webp)

Painted by `examples/curves.py` (seed 5, `figure="spirograph"`).

## What to notice

- The wash fills where the curve winds an odd number of times, so the picture shows the
  curve's structure, not just its outline.
- The nib's width is the only thing that changes with the size of the image: the script
  scales it so that a small test image and the full-size one keep the same proportions.
- Every seed is fixed, so one run writes the same file again.

## Try changing

Change the factor 5 in `rose` to 4 for eight petals: an even factor doubles the petals.
Change 3 and 2 in `lissajous` to 5 and 4 for a denser knot.
