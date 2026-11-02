# Curves: a rose and a spirograph in brush, a Lissajous figure in pen

![A five-petalled rose curve painted with a brush: each petal is washed in rose pink and outlined in a maroon stroke that is thick at the tip and thins towards the centre, on cream paper with a wide margin](../../images/curves/rose.webp)

*Painted by `examples/curves.py` (seed 5, `figure="rose"`).*

A curve is a rule that gives a point on the paper for every value of a number `t`. Step
`t` in small increments, join the points, and the curve appears. This page paints three
curves that way. A painter uses a brush when a line should have weight and a pen when it
should not. The rose and the spirograph are painted with the brush, and the Lissajous
figure is drawn with the pen. Each is laid over a light wash and scaled to the same
reach, which leaves a margin of bare paper round it.

Run any of them with `uv run python examples/curves.py out/ --figure rose`. Choose
`rose`, `lissajous` or `spirograph`. The script writes `out/curves-<figure>.png`.

## The three formulas

<!-- from examples/curves.py -->

```python
def rose(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the rose `r = cos(5 a)` over `t` from 0 to pi, from one crossing of the centre to the last, tip up.

    The angle `a` is `t` turned by a tenth of a half turn, so that `t = 0` is a crossing of the centre; five petals
    follow, each ending at the centre.
    """
    a = t + np.pi / 10
    r = np.cos(5 * a)
    return r * np.sin(a), -r * np.cos(a)


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

- **The rose** is `r = cos(5 a)`. The radius swells and shrinks as the angle turns, and
  with a factor of 5 the curve makes five petals. `t` runs from 0 to pi. The angle `a` is
  `t` turned a little, so that the curve starts at the centre and each petal ends there.
  The second half of a turn would only draw the same petals again.
- **The Lissajous figure** is two swings at right angles, `x = sin(3 t + pi / 2)` and
  `y = sin(2 t)`. It swings across three times for every two it swings down. The path
  crosses itself in a knot.
- **The spirograph** is the path of a pen fixed to a small wheel as the wheel rolls round
  inside a ring. The wheel has radius `r = 4` and the ring `R = 9`. The pen sits at
  `d = 6` from the wheel's centre, which is further than the wheel's radius, so the path
  makes a loop at every turn of the wheel. The pen comes home after four turns round the
  ring, because 9 and 4 share no factor.

## Scale the curve to the paper

The formulas give numbers between about -1 and 1 for the rose and the Lissajous figure,
and between about -10 and 10 for the spirograph. One function turns any of them into
pixels. It divides by the largest value, multiplies by the reach, which is 38% of the
width of the image, and centres the result. The paper left bare is 12% of the width on
every side.

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

A painter lays the wash first and lets it dry, then paints the line. The wash needs a
coverage mask: 1 inside the shape and 0 outside. Pillow's `ImageDraw.polygon` fills the
polygon the curve's points make. It fills only where the outline winds an odd number of
times round a spot. That is why the two lens-shaped areas in the middle of the Lissajous
figure stay bare paper while the areas beside them carry colour. The spirograph is
washed one loop at a time instead, and the washes of the loops add up where they cross.
`wash` turns the mask into pigment density on the paper's noise. `composite` lays that
density over the paper in the pigment's colour.

<!-- from examples/curves.py -->

```python
def _cover(points: np.ndarray, size: int) -> np.ndarray:
    """Return a 0 to 1 mask of the polygon the points make, filled where it winds an odd number of times."""
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).polygon([(float(px), float(py)) for px, py in points], fill=255)
    return np.asarray(mask, np.float32) / 255
```

## Paint the rose with a brush

![A spirograph painted with a brush: a pale blue wash fills its nine loops, and one long line runs round them, deep blue and thick at the start, shading to green and thinner towards the end; the washes deepen where the loops cross](../../images/curves/spirograph.webp)

*Painted by `examples/curves.py` (seed 5, `figure="spirograph"`).*

A painter does not outline a flower with a pen of one width. Each petal is one stroke of
a wet brush. It starts at the centre with nothing on the paper, swells as it goes out
and thins as it comes back. The script cuts the rose where it crosses the centre into
five petals:

<!-- from examples/curves.py -->

```python
def _petal(points: np.ndarray, index: int) -> np.ndarray:
    """Return the points of the rose's `index`th petal: one fifth of the curve, from the centre round and back."""
    each = (len(points) - 1) // 5
    return points[index * each : (index + 1) * each + 1]


def _taper(count: int, floor: float, power: float) -> np.ndarray:
    """Return a width profile of `count` samples that swells from `floor` to 1 and back, a petal's stroke."""
    return np.maximum(np.sin(np.linspace(0.0, np.pi, count)) ** power, floor)
```

`stamp` sets the brush's bristles along a petal's points. Its `wprof` argument says how
the width changes along the stroke. `_taper` gives the swell, so the strokes thin where
the five petals meet and leave no dark knot at the centre. Each petal has a `wash` of its
own in `quinacridone_rose`. Its density is drawn from the generator, it sits a little out
of register with its stroke, and it is deeper toward the centre. The strokes are laid in
`perylene_maroon`. Both are painter's pigments, from `PAINTERS_PIGMENTS`, glazed by
Kubelka-Munk with `km_glazing=True`.

<!-- from examples/curves.py -->

```python
def _paint_rose(
    points: np.ndarray, sheet: Sheet, size: int, rng: np.random.Generator
) -> list[PigmentLayer]:
    """Return the rose's layers: a wash for each petal, then one brush stroke round each."""
    wet, _ = brush_from_id("RIV2-a", 14.0 * size / SIZE, 1.0, BrushStyle())
    petals = np.zeros((size, size), np.float32)
    strokes = np.zeros((size, size), np.float32)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    for i in range(5):
        petal = _petal(points, i)
        drift = rng.normal(0.0, 0.006 * size, 2)
        body = wash(_cover(petal + drift, size), sheet, rng.uniform(0.3, 0.5), 0.45)
        reach = np.hypot(*(petal - size / 2).T).max()
        deepen = 1.45 - 0.9 * np.hypot(xx - size / 2, yy - size / 2) / reach
        body = np.clip(body * deepen, 0.0, 1.0)
        petals = np.maximum(petals, body)
        stamp(strokes, petal, wet, rng, wprof=_taper(24, 0.05, 0.6) * rng.uniform(0.75, 1.1))
    return _stack(
        [
            (petals, "quinacridone_rose"),
            (0.55 * ink_density(strokes, wet, sheet), "perylene_maroon"),
        ]
    )
```

## Paint the spirograph with one long stroke

The spirograph is one stroke from start to end, and the brush runs drier as it goes.
Under the stroke, the script lays a pale `cerulean` wash for each of the nine loops.
Where loops cross, the washes add up and the crossings deepen. The stroke itself is one
brush (`TRK3-a`) cut into sixteen short pieces laid end to end. Each piece is a step
further along a blend from `ultramarine` through `cerulean` to `sap_green` (`_mixed`), so
the colour changes gradually. `wprof` thins the width along the stroke, and the density
falls with it, so the line thins and lightens towards the end.

<!-- from examples/curves.py -->

```python
def _paint_spirograph(
    points: np.ndarray, sheet: Sheet, size: int, rng: np.random.Generator
) -> list[PigmentLayer]:
    """Return the spirograph's layers: a pale wash for each loop, then one long stroke that changes colour as it runs drier."""
    layers: list[PigmentLayer] = [
        (wash(_cover(loop, size), sheet, 0.2, 0.3), rgb(PAINTERS_PIGMENTS["cerulean"]), 0.22)
        for loop in _loops(points, 9, 222)
    ]
    brush, _ = brush_from_id("TRK3-a", 6.0 * size / SIZE, 1.0, BrushStyle())
    pieces = np.array_split(np.arange(len(points)), 16)
    for idx in pieces:
        t0, t1 = idx[0] / len(points), (idx[-1] + 1) / len(points)
        part = points[idx[0] : min(idx[-1] + 3, len(points))]
        acc = np.zeros((size, size), np.float32)
        stamp(acc, part, brush, rng, wprof=np.linspace(1.0 - 0.55 * t0, 1.0 - 0.55 * t1, 24))
        colour, clear = _mixed((t0 + t1) / 2)
        layers.append(
            (ink_density(acc, brush, sheet) * (1.0 - 0.45 * (t0 + t1) / 2), colour, clear)
        )
    return layers
```

## Draw the Lissajous figure with the pen

![A Lissajous figure in black ink, three swings across to two down, crossing itself in a knot, with some of its enclosed areas washed pale blue-grey](../../images/curves/lissajous.webp)

*Painted by `examples/curves.py` (seed 5, `figure="lissajous"`).*

The Lissajous figure is a technical figure, and the pen keeps it one. The pen is the
narrow nib of brush `MAJ6-e`, as in the nib line rung. `stamp` sets the nib's bristles
along the curve's 4000 points into an accumulator. `ink_density` turns the accumulator
into ink on the paper's tooth. `composite` lays the ink over the painted paper in the
ink colour the brush came with.

<!-- from examples/curves.py -->

```python
        brush, ink_hex = brush_from_id("MAJ6-e", nib_px * size / SIZE + 1.0, 1.0, BrushStyle())
        acc = np.zeros((size, size), np.float32)
        stamp(acc, points, brush, rng)
        out = composite([(ink_density(acc, brush, sheet), rgb(ink_hex))], paper, style)
```

## What to notice

- A brush stroke has weight where a pen line does not. The petal outlines swell and thin,
  and the spirograph's line changes colour and thins towards its end.
- The wash fills where the curve winds an odd number of times, so the picture shows the
  curve's structure, not just its outline.
- The brush and the pen differ in one call. Both use `stamp`, and the brush id and
  `wprof` change what it draws.
- Every seed is fixed, so one run writes the same file again.

## Try changing

Change the `14.0` in `_paint_rose` to `6.0` for a finer outline. Change the `0.006` in its
`drift` to `0.02` for a wash that wanders further from its stroke.
Change 3 and 2 in `lissajous` to 5 and 4 for a denser knot.
Change `"TRK3-a"` in `_paint_spirograph` to `"RIV2-a"` for a line that does not run so dry.
