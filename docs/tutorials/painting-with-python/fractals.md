# Fractals: a fern, a family of ferns and a tree

Two kinds of rule make a plant from nothing. The fern's rule is four affine maps and their
odds, applied again and again to a point. The tree's rule is a limb that splits into
shorter limbs, each of which does the same. In both, the rule only says where the paint
goes: the engine does the painting. This page paints a fern, then nine ferns of one
species, then a tree, then nine trees of one species.

## The fern

![A fern with a thin stem and curling fronds, washed in two greens on cream paper. The fronds are a deeper green and the two lowest leaflets a paler one.](../../images/painting-with-python/fern.webp)

*Painted by `examples/fern.py`, seed 7.*

Run it with:

```bash
uv run python examples/fern.py out/
```

It writes `out/fern.png` in about two seconds.

### What a painter does

A painter of a fern lays a pale green over the whole frond first, a deeper one where the
leaflets crowd, and draws the stem and the veins last with a fine brush.

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

### What to notice

- The pale holes between the pinnae are where few points land, so the wash thins to bare
  paper there, and they are part of why the fern reads as pressed and painted.
- The two lowest leaflets are paler because they are laid in `scrub`, with a lighter
  wash, and the rest of the frond in `wood`.

## A family of ferns

![Nine ferns in a three by three grid, each in two greens on cream paper. All nine have the same pale lowest leaflets and curling tip, and no two curl or spread alike.](../../images/painting-with-python/fern-family.webp)

*Painted by `examples/fern_family.py`, seed 7.*

Run it with:

```bash
uv run python examples/fern_family.py out/
```

It writes `out/fern-family.png` in about four seconds.

### What a painter does

A botanical plate shows one species nine times, and the plants are never copies: one
stands straighter, one curls further, one is lacier. The painter keeps the species and
lets the plant vary.

### How the engine models it

A fern's character is in its four maps, so a family of ferns is the same four maps with
their numbers moved a little. `perturbed` keeps the stem map, which only draws the stem.
It turns the frond map by between minus one degree and six, scales it by a few
per cent, and moves every entry of the two leaflet matrices by up to 6 per cent:

<!-- from examples/fern_family.py -->

```python
def perturbed(maps: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Return the four maps moved a few per cent: the frond turned and scaled, the leaflets' matrices nudged."""
    out = maps.copy()
    theta = np.radians(rng.uniform(-1.0, 6.0))
    scale = rng.uniform(0.835, 0.865)
    out[1, :4] = scale * np.array([np.cos(theta), np.sin(theta), -np.sin(theta), np.cos(theta)])
    out[1, 5] = maps[1, 5] * rng.uniform(0.94, 1.06)
    for k in (2, 3):
        out[k, :4] = maps[k, :4] * rng.uniform(0.94, 1.06, 4)
    return out
```

Moving the maps moves the fern's extent, so `_fit` measures each fern's points and fits
them into its cell, foot low and centred.

<!-- from examples/fern_family.py -->

```python
def _fit(points: np.ndarray, w: int, h: int) -> np.ndarray:
    """Return `points` as pixels in a `(h, w)` cell: the fern centred, its foot low, y up the page."""
    lo, hi = points[:, :2].min(axis=0), points[:, :2].max(axis=0)
    k = min(FIT_WIDTH * w / (hi[0] - lo[0]), FIT_HEIGHT * h / (hi[1] - lo[1]))
    col = w / 2 + k * (points[:, 0] - (lo[0] + hi[0]) / 2)
    row = h * (0.5 + FIT_HEIGHT / 2) - k * (points[:, 1] - lo[1])
    return np.column_stack([col, row, points[:, 2]])
```

### The loop

Each fern is painted in a cell of its own, at the cell's size, with the points and the dabs
in proportion to the cell's area. The loop paints one cell at a time into the nine-cell
grid, giving every cell its own seed, which is the only thing that differs between cells.
`pad`, defined above the loop, is the margin of paper round the grid, 5 per cent of its width:

<!-- from examples/fern_family.py -->

```python
    for i in range(ACROSS * DOWN):
        row, col = divmod(i, ACROSS)
        window = (
            slice(pad + row * ch, pad + (row + 1) * ch),
            slice(pad + col * cw, pad + (col + 1) * cw),
        )
        sheet = Sheet(ch, cw, GRAN_PX * cw / 600, seed + i)
        for target, density in zip(densities, paint_fern((ch, cw), sheet, seed + i), strict=True):
            target[window] = density
```

### What to notice

- Every cell uses the single fern's washes, pigments and dabs, so all nine look like the
  fern above, and only their curl, spread and leaflets differ.
- Nine seeds are enough to see the range: the frond's turn decides how far the fern curls,
  and its scale decides how lacy the frond is.

## A tree

![A tree with a brown trunk that forks into thinner limbs and fine dark twigs, with washes of green and yellow ochre and flecks of leaf laid over its outer limbs as foliage, and a short ochre stroke of ground at its foot.](../../images/painting-with-python/tree.webp)

*Painted by `examples/trees.py`, seed 4, `figure="tree"`.*

Run it with:

```bash
uv run python examples/trees.py out/ --figure tree
```

It writes `out/trees-tree.png` in about three seconds.

### What a painter does

A painter of a tree starts with the trunk, in a wet brush that is wide at the foot and
thins as it climbs. At each fork the brush lifts and a new stroke starts from the same
point. Where the limbs are too thin for a brush, the painter takes up a pen, and draws the
twigs. The leaves are a few washes of green and ochre over the twigs' ends, with a few
dabs of a darker green on top.

### How the engine models it

A tree is one rule applied to itself. A limb grows along a heading, bending a little, and
at its tip it splits into two limbs, now and then three. Each child is shorter than its
parent by `ratio` and turned away from it by `spread` degrees. Young limbs are drawn up
toward the light and old limbs sag. The numbers of the rule are the fields of `Shape`:

<!-- from examples/trees.py -->

```python
@dataclass(frozen=True)
class Shape:
    """The few numbers that make one species of tree, before a seed's own wander."""

    #: How far a child turns from its parent, in degrees.
    spread: float = 31.0
    #: A child's length as a share of its parent's.
    ratio: float = 0.8
    #: How much an old limb sags toward the ground, in radians over its length.
    droop: float = 0.3
    #: How far the whole tree leans, in degrees: the wind.
    lean: float = 0.0
```

`grow` follows the rule to `DEPTH` splits and returns every limb as a `Limb`: a path of
points, the splits from the trunk, the width the limb starts at and the width it ends at,
and the stroke it belongs to:

<!-- from examples/trees.py -->

```python
@dataclass(frozen=True)
class Limb:
    """One limb: its path, its splits from the trunk, its widths and the stroke it belongs to."""

    path: np.ndarray
    depth: int
    w_start: float
    w_end: float
    stroke: int
```

The child nearest to straight carries on its parent's stroke and starts exactly as wide as
its parent ends, so the widths taper by depth with no step at a joint:

<!-- from examples/trees.py -->

```python
def grow(
    start: np.ndarray, length: float, width: float, shape: Shape, rng: np.random.Generator
) -> list[Limb]:
    """Grow a tree from `start`: the trunk, then every limb to `DEPTH` splits.

    Args:
        start: Where the trunk's foot is, in pixels.
        length: The trunk's length in pixels.
        width: The trunk's width at its foot in pixels.
        shape: The species' numbers.
        rng: The generator the wander, the splits and the lengths are drawn from.

    Returns:
        Every limb, the trunk first.
    """
    limbs: list[Limb] = []
    strokes = 1
    todo = [(start, np.radians(shape.lean), length, width, 0, 0)]
    while todo:
        foot, heading, ln, w, depth, stroke = todo.pop()
        path = _path(foot, heading, ln, depth, shape, rng)
        w_end = w * (0.62 if depth == 0 else 0.78 if depth < LAST_BRUSHED else 0.62)
        limbs.append(Limb(path, depth, w, w_end, stroke))
        if depth == DEPTH:
            continue
        turn = np.radians(shape.spread) * (0.45 if depth == 0 else 0.8 if depth == 1 else 1.0)
        three = rng.random() < THREE_ODDS and depth < DEPTH - 2
        offsets = [-1.3 * turn, 0.1 * turn, 1.2 * turn] if three else [-turn, turn]
        lead = int(np.argmin(np.abs(offsets)))
        dx, dy = path[-1] - path[-2]
        base = float(np.arctan2(dx, -dy))
        for i, off in enumerate(offsets):
            kid_len = ln * shape.ratio * rng.uniform(0.75, 1.15)
            heading_i = base + off * rng.uniform(0.7, 1.3)
            if i == lead:
                todo.append((path[-1], heading_i, kid_len, w_end, depth + 1, stroke))
            else:
                todo.append((path[-1], heading_i, kid_len, w_end * 0.88, depth + 1, strokes))
                strokes += 1
    return limbs
```

### From limbs to strokes

Each stroke is the chain of limbs that carry on from one another, as one path. `stamp` lays
a brush along the path and its `wprof` argument says how the width changes along it, so
the stroke is wide at the foot and thin at the tip. The trunk and the limbs to depth 3
are laid with a wet brush of the brush sheet (`RIV2-a`), and the thinner limbs after them
with a pen (`MAJ6-e`), picking up where the brush left off:

<!-- from examples/trees.py -->

```python
def _lay(
    acc: np.ndarray, strokes: list[tuple[np.ndarray, np.ndarray]], row: str, floor: float, seed: int
) -> None:
    """Stamp each `(path, widths)` into `acc` with a brush of `row` as wide as its stroke starts, tapering by `wprof`."""
    for i, (path, widths) in enumerate(strokes):
        width = max(float(widths.max()), floor)
        brush, _ = brush_from_id(row, width, 1.0, STYLE)
        along = np.r_[0.0, np.cumsum(np.hypot(*np.diff(path, axis=0).T))]
        at = np.linspace(0.0, along[-1], 48)
        wprof = np.maximum(np.interp(at, along, widths), floor) / width
        stamp(acc, path, brush, np.random.default_rng([seed, i]), wprof=wprof)
```

The foliage goes over the limbs, as the leaves of a tree in leaf hang in front of its
branches. The limbs go down first in `burnt_sienna` and the twigs in `perylene_maroon`. Then
`_crown` marks a lumpy disc at each of the last limbs' tips (each disc's edge swells and
dips, so the crown is not a ring of bubbles), and `wash` turns the mask into a green wash.
A second, smaller wash of the same green deepens some tips, and a wash of `yellow_ochre`
warms a few. `composite` glazes them all by Kubelka-Munk, so the limbs show through the
foliage and a warm leaf is still a leaf. A few short dabs of a wet brush in `sap_green` and
`indigo` are laid last, as the leaves.

### What to notice

- The trunk is a brush stroke with a soft, streaked edge, and the twigs are fine, even
  lines: the hand-over from brush to pen is where a limb gets thinner than a brush can
  draw.
- The foliage stops short of some twigs and runs past others, because it is laid over
  the limbs' tips and not over the limbs, so the trunk and the first forks read plainly and
  the twigs show through the leaves.
- A child starts exactly as wide as the limb it carries on from ends, so no joint has a
  step in it.

## A family of trees

![Nine trees in a three by three grid, each with a brown trunk, fine dark twigs and a crown of green and ochre washes, with a margin of paper round every tree. All nine are one kind of tree, and no two have the same shape, lean or crown.](../../images/painting-with-python/tree-family.webp)

*Painted by `examples/trees.py`, seed 4, `figure="family"`.*

Run it with:

```bash
uv run python examples/trees.py out/ --figure family
```

It writes `out/trees-family.png` in about nine seconds.

### What a painter does

A painter who draws one tree and then draws eight more does not copy it. The kind of tree
stays, and the angle of each fork, the length of each limb and the lean of the whole tree
change a little every time.

### How the engine models it

A family is the same rule with nine seeds. `perturbed` moves `spread`, `ratio` and `droop` by
a few per cent, leans the tree by a few degrees, and the seed also draws every limb's own
wander:

<!-- from examples/trees.py -->

```python
def perturbed(shape: Shape, rng: np.random.Generator) -> Shape:
    """Return `shape` with each number moved by a few per cent, so a seed grows a new tree of one species."""
    return Shape(
        spread=shape.spread * rng.uniform(0.85, 1.2),
        ratio=shape.ratio * rng.uniform(0.95, 1.04),
        droop=shape.droop * rng.uniform(0.5, 1.6),
        lean=shape.lean + rng.normal(0.0, 4.0),
    )
```

### The loop

Each tree is painted in its own cell at the cell's size, never at the grid's size and
downsized. The loop gives each cell its own shape, its own paper noise and its own seed, and
pastes the cell's layers into the grid's. The paper is laid once, under all nine:

<!-- from examples/trees.py -->

```python
    for i in range(across * down):
        rng = np.random.default_rng([seed, i])
        shape = Shape() if figure == "tree" else perturbed(Shape(), rng)
        cell_sheet = Sheet(ch, cw, GRAN_PX * cw / REFERENCE, seed + i)
        row, col = divmod(i, across)
        window = (slice(row * ch, (row + 1) * ch), slice(col * cw, (col + 1) * cw))
        for name, density in paint_tree((ch, cw), cell_sheet, shape, seed + i).items():
            grid[name][window] = density
```

### What to notice

- `figure="tree"` and `figure="family"` run the same loop: a tree is a grid of one cell,
  with the unperturbed `Shape`.
- A cell's seed is `seed + i`, so the same seed always paints the same nine trees.

## Try changing

- In `fern.py`, change the `1.60` in the second map's row. The frond's rise changes, and
  the fern leans or straightens.
- In `fern_family.py`, widen the range in `perturbed`'s `rng.uniform(0.5, 5.5)`. The ferns
  curl further and further apart.
- In `trees.py`, change `spread` in `Shape` from `31.0` to `45.0`. The crown opens out
  into a wide fan.
- In `trees.py`, change `LAST_BRUSHED` from `3` to `5`. The brush draws more of the limbs
  and the pen only the finest twigs.
