# Fractals: a fern and a gasket

Two old pieces of mathematics make good paintings, because each one is a few lines of
rule that fill a whole sheet. In this page you paint a Barnsley fern, whose rule is four
affine maps and their odds, and an Apollonian gasket, whose rule is Descartes' circle
theorem. The engine does the painting: the maths only says where the pigment goes.

## The fern

![A fern with a thin stem and curling fronds, washed in two greens on cream paper. The fronds are a deeper green and the two lowest leaflets a paler one.](../../images/painting-with-python/fern.webp)

Painted by `examples/fern.py`, seed 7.

Run it with:

```bash
uv run python examples/fern.py out/
```

It writes `out/fern.png` in about two seconds.

### The four maps

A point starts at the origin. Each step chooses one of four affine maps at random and
applies it. A map is the pair of equations `x' = a x + b y + e` and `y' = c x + d y + f`,
so it turns, stretches and moves the whole picture at once. Michael Barnsley's four maps do
different jobs:

| Map | Chosen | What it does |
| --- | --- | --- |
| Stem | 1 per cent | Flattens the point onto the stem. |
| Frond | 85 per cent | Carries the point up the frond: a copy of the whole fern, a little smaller and tilted. |
| Left leaflet | 7 per cent | Throws the point onto the largest leaflet on the left. |
| Right leaflet | 7 per cent | Throws the point onto the largest leaflet on the right. |

Each row of `MAPS` below is `a, b, c, d, e, f` for one of them, and `PROBABILITIES` holds
the odds in the same order.

<!-- from examples/fern.py -->

```python
MAPS = np.array(
    [
        [0.00, 0.00, 0.00, 0.16, 0.0, 0.00],
        [0.85, 0.04, -0.04, 0.85, 0.0, 1.60],
        [0.20, -0.26, 0.23, 0.22, 0.0, 1.60],
        [-0.15, 0.28, 0.26, 0.24, 0.0, 0.44],
    ]
)
```

<!-- from examples/fern.py -->

```python
PROBABILITIES = (0.01, 0.85, 0.07, 0.07)
```

Because the frond map copies the whole fern, each leaflet on the frond is itself a small
fern, which is why the picture looks the same at every size. `fern_points` iterates the
maps and keeps every point with the map that made it:

<!-- from examples/fern.py -->

```python
def fern_points(n: int, seed: int) -> np.ndarray:
    """Iterate the four maps `n` times; return an `(n, 3)` array of x, y and the map last chosen."""
    rng = np.random.default_rng(seed)
    choices = rng.choice(4, size=min(n, MAX_POINTS), p=PROBABILITIES)
    out = np.empty((len(choices), 3))
    x = y = 0.0
    for i, k in enumerate(choices.tolist()):
        a, b, c, d, e, f = MAPS[k]
        x, y = a * x + b * y + e, c * x + d * y + f
        out[i] = x, y, k
    return out
```

### From points to washes

The script keeps at most 200 000 points. It counts them into a grid the size of the
canvas, and turns each count into a coverage between 0 and 1. A pixel stops getting
darker once it is well covered, as a pixel of paint would:

<!-- from examples/fern.py -->

```python
def _count(points: np.ndarray, w: int, h: int) -> np.ndarray:
    """Count the points into a `(h, w)` grid, y up the page, fern fitted to the canvas."""
    col = (points[:, 0] - X_MIN) / (X_MAX - X_MIN) * w
    row = (1.0 - points[:, 1] / Y_MAX) * h
    grid, _, _ = np.histogram2d(row, col, bins=(h, w), range=((0, h), (0, w)))
    return grid.astype(np.float32)


def _cover(grid: np.ndarray, k: float) -> np.ndarray:
    """A coverage mask in 0 to 1: a pixel saturates once it is well covered."""
    return (1.0 - np.exp(-k * grid)).astype(np.float32)
```

That coverage is the mask of a `wash`. The frond (the points that last took the stem or
the frond map) is laid in `wood` and the leaflets (the points of the two 7 per cent maps)
in `scrub`. `composite` with `km_glazing=True` glazes the two greens, so where they meet
they stay green. A second, sharper count of every point is laid over them in `wood` as the
veins and the stem, and last, at most 400 sampled points get a short dab of a wet brush.

## The gasket

![Washed discs packed inside a ringed circle: two large pale blue discs, a large green one and ochre and green ones below, with ever smaller discs filling the gaps and brown beads at the rim. Where two discs overlap, a darker lens shows both pigments.](../../images/painting-with-python/gasket.webp)

Painted by `examples/gasket.py`, seed 11.

Run it with:

```bash
uv run python examples/gasket.py out/
```

It writes `out/gasket.png` in about five seconds.

### Descartes' circle theorem

Four circles that each touch the other three are tied together by one rule. Write each
circle's curvature as `k = 1 / r`, and give the circle that contains the others a
negative curvature. Then

```text
(k1 + k2 + k3 + k4)^2 = 2 (k1^2 + k2^2 + k3^2 + k4^2)
```

Given three circles, that leaves two possible fourth circles, one on each side of the gap,
and their curvatures are `k1 + k2 + k3 +/- 2 sqrt(k1 k2 + k2 k3 + k3 k1)`. Add the
two curvatures and the root cancels, which gives the shortcut the script uses: once one fourth circle
`k4` is known, the other is `2 (k1 + k2 + k3) - k4`. The same sum works on the centres,
read as complex numbers, if each is weighted by its curvature (`k z`). The script starts from
the container, with `k = -1`, and three circles inside it with `k = 2`, `3` and `6`, and
checks the theorem in its tests.

<!-- from examples/gasket.py -->

```python
def _replace(quad: list[Circle], j: int, depth: int) -> Circle:
    """The circle that takes the place of `quad[j]`: `2 (k1 + k2 + k3) - k4`, for `k` and for `k z`."""
    others = [c for i, c in enumerate(quad) if i != j]
    k = 2 * sum(c.curvature for c in others) - quad[j].curvature
    kz = 2 * sum(c.curvature * c.centre for c in others) - quad[j].curvature * quad[j].centre
    return Circle(k, complex(kz) / k, depth)
```

`gasket_circles` makes four new circles from the first four, one in each gap, then
a new circle in every gap each of those opens, to recursion depth 5. The count grows by
about three times at each step, so it keeps at most 300 circles, the largest first.

<!-- from examples/gasket.py -->

```python
def gasket_circles(depth: int) -> list[Circle]:
    """The four seed circles and every circle found by `depth` rounds of Descartes, at most `MAX_CIRCLES`."""
    seeds = _seed_circles()
    found = list(seeds)
    frontier: list[tuple[list[Circle], int]] = [(seeds, -1)]
    for level in range(1, depth + 1):
        grown: list[tuple[list[Circle], int]] = []
        for quad, skip in frontier:
            for j in range(4):
                if j == skip:
                    continue
                new = _replace(quad, j, level)
                found.append(new)
                grown.append(([*quad[:j], new, *quad[j + 1 :]], j))
        frontier = grown
    found.sort(key=lambda c: (-c.radius, c.depth))
    return found[:MAX_CIRCLES]
```

### From circles to washes

Each circle is a `wash` of its own (the smallest are a flat soft disc): a disc, a shade larger than the circle so that
neighbours overlap, and kept inside the container. A thin brush stroke inked round the container's edge makes the outer circle visible. The washes are grouped by depth into at most six pigment layers, one
pigment each from `wetland`, `water`, `wood`, `heath`, `scrub` and `rim`, and `composite`
glazes them by Kubelka-Munk. Where two discs overlap, the lens shows both pigments, as
two real washes would.

<!-- from examples/gasket.py -->

```python
    centre_px, scale_px = size / 2, 0.40 * size
    layers = [np.zeros((size, size), np.float32) for _ in range(MAX_LAYERS)]
    for circle in gasket_circles(MAX_DEPTH):
        layer = 0 if circle.curvature < 0 else 1 + min(circle.depth, MAX_LAYERS - 2)
        base = (
            0.3 if circle.curvature < 0 else rng.uniform(0.2, 0.45) + 0.5 * circle.depth / MAX_DEPTH
        )
        disc = _disc(circle, size, centre_px, scale_px)
        small = scale_px * circle.radius < SMALL_PX
        body = disc * base * 1.3 if small else wash(disc, sheet, base, 0.55)
        layers[layer] = np.maximum(layers[layer], body)
    layers[MAX_LAYERS - 1] = np.maximum(
        layers[MAX_LAYERS - 1], 0.9 * _ring(size, centre_px, scale_px, sheet, rng)
    )
    stack: list[PigmentLayer] = [
        (density, rgb(PIGMENTS[key]), TRANSPARENCY[key])
        for density, key in zip(layers, LAYER_PIGMENTS, strict=True)
    ]
```

## Try changing

- In `fern.py`, change the `1.60` in the second map's row. The frond's rise changes, and
  the fern leans or straightens.
- In `gasket.py`, change `LAYER_PIGMENTS` to another set of keys from `PIGMENTS`.
