# Paint a watercolour

You paint seven small pictures, one after another, each with a short script. You
stretch paper, lay a wash on it, pull a brush and a pen across it, mix two pigments,
write a name by hand and put it all together in one painting. The engine makes every
mark, and you can read how in the script.

The order is the painter's, and it is the code's too. You stretch paper and lay washes
with `ink`. You letter with `letters`, which is built on `ink`. The route work comes
last, in `maps`, which is built on both. Each rung uses only what the earlier rungs
taught you.

Every rung follows the same pattern. First the picture. Then what a painter does at the
bench, and how the engine models it. Then the code, and what to notice in the result.
Last, a grid: the same picture painted many times by a `for` loop that changes one thing
at a time, so you can see what each number does.

## Before you begin

You need Python 3.13 or later and [uv](https://docs.astral.sh/uv/). Fetch the repository
and let uv make its one virtual environment:

```console
$ git clone https://github.com/findlaywebb/pyntpot
$ cd pyntpot
$ uv sync
```

Run every command in this tutorial from the repository's top directory. Each script
takes the directory to write into, makes it if it is missing, and writes its picture
there. Everything is seeded, so you get the same pixels as the pictures on this page.

One script, `examples/tutorial_grids.py`, paints all the grids. It takes a `--figure`
for the rung (`paper`, `wash`, `brush`, `pigments`, `nib`, `lettering` or `composition`)
and writes `grid-<figure>.png`. The page quotes the loop of each grid and leaves out the
helpers. `_layout` finds the cells. `_labels` letters the names round them. `_letter` is
the lettering rung's nib plate, painted twice as large and brought down so that the
letters stay crisp.

## Stretch the paper

![A piece of cream paper with a soft grain, a faint brown edge and one or two small rust specks of foxing](../images/tutorials/paper.webp)

*Painted by `examples/paper.py`, seed 11.*

A painter starts with paper, stretched flat so that it dries tight. Its tooth holds the
pigment, and its edge shows where the paper has been handled.

The engine models the paper in two parts. A `Sheet` holds the paper's noise fields: the
grain that pigment settles into. A `Canvas` is the pixel grid you paint on.
`paper_plate` paints the cream paper from them, with its narrow edge and its foxing, as
a `PaperStyle` asks. `save_image` writes the result to a file.

```console
$ uv run python examples/paper.py out/
INFO:__main__:wrote out/paper.png
```

Here is the whole of `main`:

<!-- from examples/paper.py -->
```python
def main(out_dir: Path) -> Path:
    """Paint the paper, write it into `out_dir` as `paper.png` and return that path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)
    path = out_dir / "paper.png"
    save_image(paper, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

### What to notice

- The edge is a little browner than the middle. The effect is faint.
- The cream is not one flat colour. Fine grain runs across it, and one or two faint
  rust specks of foxing sit near the top.
- The picture is plain on purpose. Every later rung is painted onto this paper, and its
  grain shows through the paint.

### Vary it

![Six pieces of paper in two rows of three. The top row has a grey shadow round its edge and the bottom row a narrow warm brown edge. The grain grows stronger from the left column to the right.](../images/tutorials/grid-paper.webp)

*Painted by `examples/tutorial_grids.py`, `figure="paper"`. The labels read 0.04, 0.085 and 0.16 across, and classic and warm down.*

`paper_tooth` sets how strong the grain is: 0.04 is smooth, 0.085 is the default and
0.16 is rough. `paper_edge` chooses the edge. `"warm"`, the default, browns a narrow
edge. `"classic"` is a grey vignette. The loop paints one piece of paper for each pair.

<!-- from examples/tutorial_grids.py -->
```python
def _paper_grid() -> np.ndarray:
    """Paint `paper_tooth` across and `paper_edge` down, each cell its own piece of paper."""
    teeth = (0.04, 0.085, 0.16)
    edges: tuple[Literal["classic", "warm"], ...] = ("classic", "warm")
    boxes, h = _layout(len(teeth), len(edges), 150, 92, 46)
    out = _desk(h)
    for r, edge in enumerate(edges):
        for c, tooth in enumerate(teeth):
            x, y, w, ch = boxes[r][c]
            style = PaperStyle(paper_tooth=tooth, paper_edge=edge)
            out[y : y + ch, x : x + w] = _paper(w, ch, style, 11)
    return _labels(out, boxes, teeth, edges)
```

Try changing `teeth` to `(0.02, 0.085, 0.3)` for a smoother and a rougher paper.

## Lay a wash

![A soft blue disc on cream paper, its edge a little darker than its middle and its body lightly mottled](../images/tutorials/wash.webp)

*Painted by `examples/wash.py`, seed 11.*

A painter lays a wash by wetting an area, loading a brush with pigment and flooding the
water with it. As the water dries it carries pigment to the edge, where it gathers. The
rest of the pigment settles into the hollows of the paper.

The engine follows the same order. You give `wash` a coverage mask, here a disc built
with numpy. It returns a density: how much pigment lies at each pixel, from 0 to 1. The
density is not a colour yet. `composite` lays it over the paper in a pigment's colour.
`PIGMENTS` holds each pigment's `#rrggbb` hex, and `rgb` turns that into the triple
`composite` reads.

```console
$ uv run python examples/wash.py out/
INFO:__main__:wrote out/wash.png
```

<!-- from examples/wash.py -->
```python
def main(out_dir: Path) -> Path:
    """Lay a disc of water over the paper, write it into `out_dir` as `wash.png` and return that path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    yy, xx = np.mgrid[0:H, 0:W]
    disc = ((xx - W / 2) ** 2 + (yy - H / 2) ** 2 <= (0.3 * min(W, H)) ** 2).astype(np.float32)
    density = wash(disc, sheet, 0.6, 0.3)

    out = composite([(density, rgb(PIGMENTS["water"]))], paper, PaperStyle())
    path = out_dir / "wash.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

The two numbers after the sheet, `0.6` and `0.3`, set the strength of the body and the
extra pigment that pools just inside the edge.

### What to notice

- The edge is soft and slightly irregular, because the wash follows the paper's noise.
- Just inside the edge there is a slightly darker band, where the pigment gathered.
  Painters call this edge darkening. A flat fill does not have it.
- The body is mottled. The pigment has settled into the paper's grain, so the paper
  from the first rung shows through the colour.

### Vary it

![Six pale blue discs in two rows of three, each on its own piece of paper. The discs deepen from the left column to the right. The two rows differ slightly in the shape of the edge and the pattern of the mottle.](../images/tutorials/grid-wash.webp)

*Painted by `examples/tutorial_grids.py`, `figure="wash"`. The labels read 0.3, 0.6 and 0.9 across, and seed 11 and seed 23 down.*

The body is how much pigment the wash lays: 0.3 is a pale tint and 0.9 is a strong
wash. The seed belongs to the sheet, so a different seed is a different piece of paper.
The wash is the same, but its edge and its mottle fall in other places. Each cell has
its own sheet, and the loop makes it.

<!-- from examples/tutorial_grids.py -->
```python
def _wash_grid() -> np.ndarray:
    """Paint the wash body across and two `sheet_seed`s down, each cell its own piece of paper."""
    bodies, seeds = (0.3, 0.6, 0.9), (11, 23)
    boxes, h = _layout(len(bodies), len(seeds), 150, 92, 46)
    out = _desk(h)
    for r, seed in enumerate(seeds):
        for c, body in enumerate(bodies):
            x, y, w, ch = boxes[r][c]
            sheet = Sheet(ch, w, GRAN_PX, seed)
            paper = paper_plate(sheet, Canvas(0, 0, w, ch, w, ch), PaperStyle(sheet_seed=seed), w)
            density = wash(_disc(w, ch, w / 2, ch / 2, 0.36 * ch), sheet, body, 0.5)
            out[y : y + ch, x : x + w] = composite(
                [(density, rgb(PIGMENTS["water"]))], paper, PaperStyle()
            )
    return _labels(out, boxes, bodies, [f"seed {seed}" for seed in seeds])
```

The `0.5` after `body` is the pooled edge. Try changing it to `0.0`, and the dark band inside each edge fades.

## Pull a brush

![Two strokes on cream paper: a steady, wet blue stroke above a drier olive stroke that breaks into flecks towards its end](../images/tutorials/brush-stroke.webp)

*Painted by `examples/brush_stroke.py`, seed 11.*

A painter chooses a brush for what it does. A loaded round brush makes a wet, even
line. A drier, stiffer one skips over the tooth of the paper. The hand sets how wide the
mark is, and the brush sets how it breaks up.

The engine keeps a catalogue of brushes, the brush sheet. `brush_from_id` reads a name
from it and gives back the brush and the colour of its ink as hex. `RIV1-a` is a wet
brush and `TRK4-d` is a dry one. `stamp` lays the bristles down along a path into an
accumulator. `ink_density` turns what has gathered there into density on the paper's
tooth, ready for `composite` as before.

```console
$ uv run python examples/brush_stroke.py out/
INFO:__main__:wrote out/brush_stroke.png
```

<!-- from examples/brush_stroke.py -->
```python
def _stroke(
    brush_id: str, width_px: float, line: np.ndarray, sheet: Sheet
) -> tuple[np.ndarray, str]:
    """Stamp one stroke of a brush sheet cell along a line; return its density and ink hex."""
    brush, ink_hex = brush_from_id(brush_id, width_px, 1.0, BrushStyle())
    acc = np.zeros((H, W), np.float32)
    stamp(acc, line, brush, np.random.default_rng(SEED))
    return ink_density(acc, brush, sheet), ink_hex


def main(out_dir: Path) -> Path:
    """Paint a wet and a dry stroke on the paper, write `brush_stroke.png` into `out_dir` and return its path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    x = np.linspace(0.1 * W, 0.9 * W, 200)
    wet_line = np.column_stack([x, H / 2 + 0.12 * H * np.sin(2 * np.pi * x / W)])
    dry_line = np.column_stack([x, 0.78 * H + 0.08 * H * np.sin(2 * np.pi * x / W + np.pi)])
    wet, wet_hex = _stroke("RIV1-a", 6.0, wet_line, sheet)
    dry, dry_hex = _stroke("TRK4-d", 4.0, dry_line, sheet)

    out = composite([(wet, rgb(wet_hex)), (dry, rgb(dry_hex))], paper, PaperStyle())
    path = out_dir / "brush_stroke.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

### What to notice

- The blue stroke is wet. It lies down steadily, with soft ends and a smooth edge.
- The olive stroke is dry. It starts solid, and from about halfway along the bristles
  run short of paint. The line thins and breaks into flecks on the paper's grain.
- The wet stroke keeps an even width and tapers at both ends.

### Vary it

![Twelve strokes in three rows of four, each a wave across its cell. The columns are a wet blue brush, a brown one with ragged ends, a dry olive one that breaks into flecks and a scratchy dark one. The rows get wider from the top to the bottom, and the differences between the brushes grow.](../images/tutorials/grid-brush.webp)

*Painted by `examples/tutorial_grids.py`, `figure="brush"`. The labels read RIV1-a, MAJ3-b, TRK4-d and MAJ7-e across, and 3 px, 6 px and 12 px down.*

The four brushes differ at every width. At 3 pixels the blue one is smooth and solid.
The brown one has a few gaps, the olive one is flecked along its right half, and the
dark one is a pale line with black specks. At 12 pixels the differences grow. The blue
stroke stays solid with soft edges. The brown one has ragged ends. The olive one breaks
into heavy flecks. The dark one is a band of grey and black streaks. The width is the
second argument of `brush_from_id`, and the loop steps it.

<!-- from examples/tutorial_grids.py -->
```python
def _brush_grid() -> np.ndarray:
    """Paint four brushes across, each at three widths down, on one sheet of paper."""
    brushes, widths = ("RIV1-a", "MAJ3-b", "TRK4-d", "MAJ7-e"), (3.0, 6.0, 12.0)
    boxes, h = _layout(len(brushes), len(widths), 80, 92, 46)
    sheet = Sheet(h, W, GRAN_PX, SEED)
    out = paper_plate(sheet, Canvas(0, 0, W, h, W, h), PaperStyle(paper_foxing=0.0), W)
    t = np.linspace(0.0, 1.0, 120)
    for r, width in enumerate(widths):
        for c, brush_id in enumerate(brushes):
            x, y, w, ch = boxes[r][c]
            brush, ink_hex = brush_from_id(brush_id, width, 1.0, BrushStyle())
            acc = np.zeros((h, W), np.float32)
            wave = y + ch / 2 + 0.26 * ch * np.sin(2 * np.pi * t)
            stamp(
                acc,
                np.column_stack([x + 12 + t * (w - 24), wave]),
                brush,
                np.random.default_rng(SEED),
            )
            out = composite([(ink_density(acc, brush, sheet), rgb(ink_hex))], out, PaperStyle())
    return _labels(out, boxes, brushes, [f"{width:g} px" for width in widths])
```

Try changing `"MAJ7-e"` to `"RIV1-a"`, and a second wet brush replaces the scratchy one.

## Mix two pigments

![Two panels, each with a blue disc overlapping a yellow-ochre one; the overlap is a different green in the two panels](../images/tutorials/pigments.webp)

*Painted by `examples/pigments.py`, seed 11.*

Where one wash crosses another, the paint underneath matters. A painter mixes two
pigments on the paper by glazing one over the other. A transparent stain lets the layer
under it through. A covering colour hides it.

The engine holds that as a number. Each `PigmentLayer` is a density, a colour from
`PAINTERS_PIGMENTS` and a `PAINTERS_TRANSPARENCY`: what the pigment shows over black, as
a share of what it shows over white. These are a painter's tubes, here cerulean and
yellow ochre. A pigment near 0 is a transparent glaze. One near 1 covers what lies
beneath it.

`composite` stacks the layers the way the `PaperStyle` asks. With `km_glazing=False` it
multiplies them. With `km_glazing=True` it glazes them by Kubelka-Munk, which reads each
layer's transparency. The script paints both and sets them side by side, multiplied on
the left and glazed on the right.

```console
$ uv run python examples/pigments.py out/
INFO:__main__:wrote out/pigments.png
```

<!-- from examples/pigments.py -->
```python
def _disc(centre_x: float) -> np.ndarray:
    """A disc mask on one panel, centred at `centre_x` across and halfway down."""
    yy, xx = np.mgrid[0:H, 0:W]
    return ((xx - centre_x) ** 2 + (yy - H / 2) ** 2 <= (0.3 * min(W, H)) ** 2).astype(np.float32)


def main(out_dir: Path) -> Path:
    """Composite two overlapping washes both ways, write `pigments.png` into `out_dir` and return its path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    layers: list[PigmentLayer] = [
        (
            wash(_disc(centre_x), sheet, 0.6, 0.3),
            rgb(PAINTERS_PIGMENTS[key]),
            PAINTERS_TRANSPARENCY[key],
        )
        for key, centre_x in (("cerulean", 0.38 * W), ("yellow_ochre", 0.62 * W))
    ]
    multiplied = composite(layers, paper, PaperStyle(km_glazing=False))
    glazed = composite(layers, paper, PaperStyle(km_glazing=True))

    out = np.concatenate([multiplied, glazed], axis=1)
    path = out_dir / "pigments.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

### What to notice

- Look at the lens where the two discs overlap. It is a darker, duller green in the left
  panel and a clearer green in the right, though the discs are identical.
- Nothing recolours the overlap. It is what happens when the two pigments meet.
- Both panels share one paper, so the grain falls in the same places.

### Vary it

![Eight pairs of overlapping discs in two rows of four. The pairs are blue and ochre, which make green; rose and blue, which make violet; ochre and rose, which make red-orange; and sienna and blue, which make a dark grey-green. The top row is multiplied and the bottom row glazed. The glazed overlaps are a little clearer and lighter, most plainly in the first and last pairs.](../images/tutorials/grid-pigments.webp)

*Painted by `examples/tutorial_grids.py`, `figure="pigments"`. The labels read 1 to 4 across, and multiply and glazed down.*

The map's own pigments, `PIGMENTS` and `TRANSPARENCY`, are pale on purpose, so that a
map's washes sit quietly under its lettering. A painter's tubes are stronger, and the
engine keeps them beside the map's. The grid uses cerulean, yellow ochre, quinacridone
rose and burnt sienna. It glazes them over each other in four pairs. The loop lays each
pair twice, once multiplied and once glazed.

<!-- from examples/tutorial_grids.py -->
```python
def _pigment_grid() -> np.ndarray:
    """Paint four pigment pairs across, multiplied above and glazed by Kubelka-Munk below."""
    pairs = (
        ("cerulean", "yellow_ochre"),
        ("quinacridone_rose", "cerulean"),
        ("yellow_ochre", "quinacridone_rose"),
        ("burnt_sienna", "cerulean"),
    )
    boxes, h = _layout(len(pairs), 2, 150, 92, 46)
    sheet = Sheet(h, W, GRAN_PX, SEED)
    out = paper_plate(sheet, Canvas(0, 0, W, h, W, h), PaperStyle(paper_foxing=0.0), W)
    for r, glazed in enumerate((False, True)):
        for c, pair in enumerate(pairs):
            x, y, w, ch = boxes[r][c]
            layers: list[PigmentLayer] = [
                (
                    wash(_disc(W, h, x + w * cx, y + ch / 2, 0.36 * ch), sheet, 0.7, 0.4),
                    rgb(PAINTERS_PIGMENTS[key]),
                    PAINTERS_TRANSPARENCY[key],
                )
                for key, cx in zip(pair, (0.36, 0.64), strict=True)
            ]
            out = composite(layers, out, PaperStyle(km_glazing=glazed))
    return _labels(out, boxes, range(1, len(pairs) + 1), ["multiply", "glazed"])
```

Try changing a pair to `("ultramarine", "yellow_ochre")`, and look at the overlap it makes.

## Take up the pen

![A dark ink spiral of three turns drawn with a pen nib on cream paper, its line narrow, smooth and even](../images/tutorials/nib-line.webp)

*Painted by `examples/nib_line.py`, seed 11.*

A painter's pen is a nib, and a nib is not round. Held at an angle, it draws its full
width across itself and almost nothing along itself. A pen line swells and thins with
the direction of the stroke.

The engine's nib is a brush too. Row 6 of the brush sheet is a pen, so
`brush_from_id("MAJ6-e", ...)` gives a narrow nib. The steps are the brush stroke's.
`stamp` the line into an accumulator. `ink_density` it on the paper's tooth.
`composite` it over the paper in the ink colour the brush came with. Here the line is a
spiral of three turns.

```console
$ uv run python examples/nib_line.py out/
INFO:__main__:wrote out/nib_line.png
```

<!-- from examples/nib_line.py -->
```python
def main(out_dir: Path) -> Path:
    """Draw a spiral with a pen nib, write `nib_line.png` into `out_dir` and return its path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    theta = np.linspace(0.0, TURNS * 2 * np.pi, 600)
    radius = 0.42 * min(W, H) * (0.1 + 0.9 * theta / theta[-1])
    line = np.column_stack([W / 2 + radius * np.cos(theta), H / 2 + radius * np.sin(theta)])

    brush, ink_hex = brush_from_id("MAJ6-e", 3.0, 1.0, BrushStyle())
    acc = np.zeros((H, W), np.float32)
    stamp(acc, line, brush, np.random.default_rng(SEED))
    density = ink_density(acc, brush, sheet)

    out = composite([(density, rgb(ink_hex))], paper, PaperStyle())
    path = out_dir / "nib_line.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

### What to notice

- The line is narrow, dark and steady, and its edge is slightly soft where the ink
  meets the paper.
- The width barely changes along the spiral. A spiral turns through every direction, so
  the nib's angle makes no visible difference here. The grid below shows it.
- The code is the brush rung's, with a different brush name and size. The pen is the
  same machinery with a different tip.

### Vary it

![The name Ambleside written six times in two rows of three. The columns turn the nib through three angles, and the rows thin the strokes along the nib by about half and by most. The top row keeps more weight in its strokes. In the bottom row the upright stems of the right-hand cell, where the nib is turned to 90 degrees, are hairlines.](../images/tutorials/grid-nib.webp)

*Painted by `examples/tutorial_grids.py`, `figure="nib"`. The name is Ambleside. The labels read -38, 0 and 90 across, and 0.5 and 0.85 down.*

A name has strokes in known directions, so this grid writes one. It uses the next
rung's hand early. A `NibStyle` sets two things. `label_pen_angle_deg` is the nib's
angle in degrees from the page's horizontal. `label_pen_thin` is how much of its width a
stroke along the nib loses. At 0 the pen is a plotter's, one width all the way round.
The grid uses 0.5 and 0.85. Turning the nib changes which strokes thin: the rising ones
at -38, the level ones at 0 and the upright ones at 90. The change is clearest at 0.85
and 90, where the stems of "Ambleside" become hairlines. The labels in every grid on
this page are written the same way.

<!-- from examples/tutorial_grids.py -->
```python
def _nib_grid() -> np.ndarray:
    """Letter a name with the nib at three angles across and two `label_pen_thin`s down."""
    angles, thins = (-38, 0, 90), (0.5, 0.85)
    boxes, h = _layout(len(angles), len(thins), 100, 92, 46)
    out = _paper(W, h)
    for r, thin in enumerate(thins):
        for c, angle in enumerate(angles):
            x, y, w, ch = boxes[r][c]
            nib = NibStyle(label_pen_angle_deg=angle, label_pen_thin=thin, label_pen_width_px=2.0)
            setting = Setting(NIB_NAME, 50.0, anchor=(w / 2, 0.68 * ch), align="middle", wash=False)
            cell = out[y : y + ch, x : x + w]
            out[y : y + ch, x : x + w] = _letter(cell, [setting], nib, pool=0.15)
    return _labels(out, boxes, angles, thins)
```

Try changing `thins` to `(0.0, 0.3)`, and the strokes keep a more even width.

## Letter a name

![The name Ambleside written by hand in dark ink on a gently curving line, its letters each a little different in size and slant](../images/tutorials/lettering.webp)

*Painted by `examples/lettering.py`, seed 7. The name is Ambleside.*

A letterer does not stamp letters. They write them, and no two come out the same. The
slant drifts, the baseline wanders and the pen is never held at quite the same angle
twice.

Now the hand. A `Hand` writes a `Setting`, which is a text at a size set along a line.
It writes the text as a list of `Mark`, the strokes the nib will run along. You give it
a face (`FaceStyle`) and a style (`HandStyle`). The nib's own style groups (`NibStyle`,
`NibGroups`) say how the ink goes down. `nib_plate` strokes the marks onto one RGBA
plate, a layer that carries its own transparency. The script lays that plate over the
paper by its alpha, instead of multiplying it. It writes two files: the plate as
`lettering-plate.webp` and the finished picture.

```console
$ uv run python examples/lettering.py out/
INFO:__main__:wrote out/lettering.png
```

Here is `main`:

<!-- from examples/lettering.py -->
```python
def main(out_dir: Path) -> Path:
    """Write a hand-lettered name over the paper and return the finished image's path.

    Args:
        out_dir: The directory the nib plate and the finished image are written into.

    Returns:
        The path of the finished image, `lettering.png`.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    marks: list[Mark] = hand.write(Setting(NAME, 36.0, path=_line()), hand.generator(SEED))

    canvas2 = Canvas(0, 0, NIB_SCALE * W, NIB_SCALE * H, NIB_SCALE * W, NIB_SCALE * H)
    dark2 = np.zeros((NIB_SCALE * H, NIB_SCALE * W), np.float32)
    surface = NibSurface(canvas2, NIB_SCALE, dark2, GRAN_PX * NIB_SCALE)
    groups = NibGroups(NibStyle(), face, hand_style, BrushStyle(), PaperStyle())
    plate_path = nib_plate(marks, surface, groups, out_dir / f"{STEM}-plate.webp")
    if plate_path is None:
        raise RuntimeError("the hand wrote no marks")

    with Image.open(plate_path) as big:
        small = big.convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    rgba = np.asarray(small, np.float32) / 255
    alpha = rgba[..., 3:]
    out = paper * (1 - alpha) + rgba[..., :3] * alpha

    path = out_dir / f"{STEM}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

### What to notice

- The hand writes each letter afresh, so the two e's of "Ambleside" are alike but not
  copies.
- The name follows the gentle curve of its line. The word tilts up to the right, with
  the letters turned to the line beneath them.
- The ink sits on the paper and does not multiply into it. The letters are plain dark
  ink.

### Vary it

![The name Keswick written nine times in three rows of three. Every copy is the same word and no two are quite alike: the letters differ slightly in lean, height and size.](../images/tutorials/grid-lettering.webp)

*Painted by `examples/tutorial_grids.py`, `figure="lettering"`. The name is Keswick; the nine copies are nine hand seeds, 1 to 9.*

The hand draws every wobble from one generator, so one seed writes a name one way.
`hand.generator(seed)` makes the generator, and the loop gives each cell its own.

<!-- from examples/tutorial_grids.py -->
```python
def _lettering_grid() -> np.ndarray:
    """Letter a name nine times, once for each of nine hand seeds, three by three."""
    boxes, h = _layout(3, 3, 96, PAD, PAD)
    out = _paper(W, h)
    for r, row in enumerate(boxes):
        for c, (x, y, w, ch) in enumerate(row):
            setting = Setting(NAME, 56.0, anchor=(w / 2, 0.7 * ch), align="middle", wash=False)
            nib = NibStyle(label_pen_width_px=1.8)
            seed = 3 * r + c + 1
            cell = out[y : y + ch, x : x + w]
            out[y : y + ch, x : x + w] = _letter(cell, [setting], nib, seed, pool=0.15)
    return out
```

Try changing the `seed` to `7` in every cell. The nine copies become one name, written
the same way nine times.

## Compose the painting

![A pale blue wash disc on cream paper with the name Keswick written by hand across its middle, and a wet burnt sienna brush stroke curving under the name and across the disc's foot](../images/tutorials/composition.webp)

*Painted by `examples/composition.py`, seed 7. The name is Keswick.*

The last rung adds nothing new. It puts the others together, in the order a painter
works. The paper goes first. The wash and the wet brush stroke go over it. The lettering
goes last, on top of the paint. Where the paint is dark enough to hide the name, a
painter first lifts a patch of colour with a damp brush, so the name has a pale place to
sit.

The engine works in the same order. The paper goes down first. The wash and the wet
brush stroke are composited over it. Then the hand sets "Keswick" along a nearly level
line, centred on the disc and above the stroke. `_line` measures the word with
`hand.measure`, so the line is exactly as long as the word is wide. The nib strokes its
marks onto a plate, and the plate is laid over everything by its alpha. The paint is
underneath and the lettering is on top.

```console
$ uv run python examples/composition.py out/
INFO:__main__:wrote out/composition.png
```

<!-- from examples/composition.py -->
```python
def main(out_dir: Path) -> Path:
    """Paint a wash and a stroke, write a name over them, and return the finished image's path.

    Args:
        out_dir: The directory the nib plate and the finished image are written into.

    Returns:
        The path of the finished image, `composition.png`.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    wash_density, stroke_density, stroke_hex = _wash_and_stroke(sheet)
    paper = composite(
        [(wash_density, rgb(PIGMENTS["water"])), (stroke_density, rgb(stroke_hex))],
        paper,
        PaperStyle(),
    )

    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    marks: list[Mark] = hand.write(Setting(NAME, NAME_PX, path=_line()), hand.generator(SEED))

    canvas2 = Canvas(0, 0, NIB_SCALE * W, NIB_SCALE * H, NIB_SCALE * W, NIB_SCALE * H)
    dark2 = np.zeros((NIB_SCALE * H, NIB_SCALE * W), np.float32)
    surface = NibSurface(canvas2, NIB_SCALE, dark2, GRAN_PX * NIB_SCALE)
    groups = NibGroups(
        NibStyle(), face, hand_style, BrushStyle(pen_pool_radius_frac=0.15), PaperStyle()
    )
    plate_path = nib_plate(marks, surface, groups, out_dir / f"{STEM}-plate.webp")
    if plate_path is None:
        raise RuntimeError("the hand wrote no marks")

    with Image.open(plate_path) as big:
        small = big.convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    rgba = np.asarray(small, np.float32) / 255
    alpha = rgba[..., 3:]
    out = paper * (1 - alpha) + rgba[..., :3] * alpha

    path = out_dir / f"{STEM}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

The helpers `_line` and `_wash_and_stroke`, defined above `main` in the script, hold the
line the name follows and the disc and the brush stroke from the earlier rungs. The
stroke is laid in burnt sienna, one of the painter's pigments from the pigments rung.

### What to notice

- Each layer stays distinct where it meets the others. The brown stroke crosses the
  foot of the disc, and the lettering sits crisp on the blue.
- The name is on top of the paint because it was laid last.
- Each earlier rung was a whole picture. Here they are ingredients.

### Vary it

![Six small copies of the painting in two rows of three, each a blue disc with the name Keswick centred on it and a dark blue brush stroke under the name. The three columns differ only in the hand's seed, so the name is written three slightly different ways. In the top row the name sits straight on the paint. In the bottom row a pale band shows behind the letters.](../images/tutorials/grid-composition.webp)

*Painted by `examples/tutorial_grids.py`, `figure="composition"`. The name is Keswick. The labels read seed 1, seed 2 and seed 3 across, and off and on down.*

Two things change here. The hand's seed rewrites the name. `Setting.wash` turns the
backing wash off or on. The backing wash is a soft, paper-coloured patch the nib lifts
under a name where the ground is dark enough to need it. The nib reads how dark the
ground is from the `ground` it is given. The script above gives it none, so it never
lifts a patch. The grid gives it the density of the wash and the stroke, which is why
the patch shows.

<!-- from examples/tutorial_grids.py -->
```python
def _composition_grid() -> np.ndarray:
    """Paint the composition for three hand seeds across, the name's backing wash off and on down."""
    seeds, backings = (1, 2, 3), (False, True)
    boxes, h = _layout(len(seeds), len(backings), 150, 92, 46)
    out = _desk(h)
    for r, backing in enumerate(backings):
        for c, seed in enumerate(seeds):
            x, y, w, ch = boxes[r][c]
            out[y : y + ch, x : x + w] = _composition_cell(w, ch, seed, backing=backing)
    return _labels(out, boxes, [f"seed {seed}" for seed in seeds], ["off", "on"])
```

Try changing `seeds` to `(4, 5, 6)`, and the name is written three other ways.

## Where next

You have painted each layer: paper, wash, brush, pigment, pen and hand. Next you put
them to work on real country. In [First map](first-map.md) you paint a route round
Keswick from recorded data, with no network, and then from a track of your own.
