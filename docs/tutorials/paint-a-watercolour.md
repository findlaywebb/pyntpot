# Paint a watercolour

You are going to paint seven small pictures, one after another, each with a short script. By the end you will have stretched paper, laid a wash on
it, pulled a brush and a pen across it, mixed two pigments, written a name by hand and
put the lot together on one painting. Nothing is drawn by a graphics library behind your
back: every mark comes from the engine you can read in the script.

The order is the painter's, and it is the code's too. You stretch paper and lay washes
with `ink`, you letter with `letters`, which is built on `ink`, and the route work comes
last, in `maps`, which is built on both. Each rung uses only what the one before it
taught you, so you never meet a name before you need it.

Every rung keeps to one rhythm. First the picture. Then what a painter does at the
bench, and how the engine models it. Then the code, and what to notice in the result.
Last, a grid: the same picture painted again and again by a `for` loop that changes one
thing at a time, so that a number you have read about is also a difference you can see.

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
there. Everything is seeded, so you will get the same pixels as the pictures on this
page.

The grids are all painted by one script, `examples/tutorial_grids.py`. It takes a
`--figure` for the rung (`paper`, `wash`, `brush`, `pigments`, `nib`, `lettering` or
`composition`) and writes `grid-<figure>.png`. The page quotes the loop of each grid
and leaves out its helpers: `_layout` finds the cells, `_labels` letters the names round
them, and `_letter` is the lettering rung's nib plate, painted twice as large and brought
down so that the letters stay crisp.

## Stretch the paper

![A piece of cream paper with a soft grain, a narrow brown edge that wanders a little, and a few small rust specks of foxing](../images/tutorials/paper.webp)

*Painted by `examples/paper.py`, seed 11.*

A painter starts with paper, stretched flat so that it dries tight. The sheet decides
how every wash behaves: its tooth holds the pigment, and its edge shows where the paper
was handled.

The engine models the paper in two parts. A `Sheet` holds the paper's noise fields: the
grain that pigment will settle into. A `Canvas` is the pixel grid you paint on.
`paper_plate` paints the cream rag itself from them, with its narrow edge and its
foxing, as a `PaperStyle` asks, and `save_image` writes the result to a file.

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

- The edge is browner than the middle, narrow and a little uneven, as if the sheet had
  been handled and left on a windowsill. Nothing straight or perfect has been drawn there.
- Fine grain runs all over, and a few small rust specks sit about the page. Real paper
  is never one flat colour, and this is the first thing that tells you it was made by a
  hand and not by a screen.
- The picture is plain because the paper has to be. Everything after this rung is
  painted onto it, and shows its grain through.

### Vary it

![Six pieces of paper in two rows of three. The top row has a grey shadow round its edge and the bottom row a narrow warm brown edge. The grain grows stronger from the left column to the right.](../images/tutorials/grid-paper.webp)

*Painted by `examples/tutorial_grids.py`, `figure="paper"`. The labels read 0.04, 0.085 and 0.16 across, and classic and warm down.*

`paper_tooth` is how strong the grain is: 0.04 is a smooth sheet, 0.085 the default and
0.16 a rough one. `paper_edge` chooses the edge: `"warm"`, the default, browns a narrow
edge; `"classic"` is the grey vignette the paper used to have. The loop paints one piece
of paper for each pair.

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

Try changing `teeth` to `(0.02, 0.085, 0.3)`: a far smoother sheet, and a far rougher one.

## Lay a wash

![A soft blue disc on cream paper, its edge a little darker than its middle and its body lightly granular](../images/tutorials/wash.webp)

*Painted by `examples/wash.py`, seed 11.*

A painter lays a wash by wetting an area, loading a brush with pigment and flooding the
water with it. As the water dries it carries pigment to the edge, where it gathers, and
it leaves the rest of the pigment settled into the hollows of the paper.

The engine follows the same order. You give `wash` a coverage mask, here a disc built
with numpy, and it returns a density: how much pigment lies at each pixel, from 0 to 1.
The density is not a colour yet. `composite` lays it over the paper in a pigment's
colour: `PIGMENTS` holds each pigment's `#rrggbb` hex, and `rgb` turns that into the
triple `composite` reads.

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

The two numbers after the sheet, `0.6` and `0.3`, are the strength of the body and the
extra pigment that pools just inside the edge.

### What to notice

- The edge is not a perfect circle. It wobbles a little, because the wash follows the
  paper's noise.
- Just inside the edge there is a slightly darker line, where the pigment dried last
  and gathered. Painters call this edge darkening, and a flat fill never has it.
- The body is granular. The pigment has settled into the valleys of the paper, so the
  grain you stretched in the first rung shows through the colour.

### Vary it

![Six pale blue discs in two rows of three, each on its own piece of paper. The discs deepen from the left column to the right. The two rows differ in the wobble of the edge and in the pattern of the mottle.](../images/tutorials/grid-wash.webp)

*Painted by `examples/tutorial_grids.py`, `figure="wash"`. The labels read 0.3, 0.6 and 0.9 across, and seed 11 and seed 23 down.*

The body is how much pigment the wash lays: 0.3 is a pale tint and 0.9 a deep, strong wash. The seed belongs to the sheet, so a different seed is a different
piece of paper: the same wash, with its edge and its mottle falling in other places.
Each cell has its own sheet, and the loop makes it.

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

The `0.5` after `body` is the pooled edge. Try changing it to `0.0`, and the dark band inside each edge goes.

## Pull a brush

![Two strokes on cream paper: a steady, wet blue stroke above a drier olive stroke that breaks into flecks towards its end](../images/tutorials/brush-stroke.webp)

*Painted by `examples/brush_stroke.py`, seed 11.*

A painter chooses a brush for what it does: a loaded round brush for a wet, even line, a
drier, stiffer one for a line that skips over the tooth of the paper, a flat nib for a
hard edge. How wide the mark is depends on the hand, and how it breaks up depends on
the brush.

The engine keeps a catalogue of brushes, the brush sheet. `brush_from_id` reads a name
from it and gives back the brush and the colour of its ink as hex. `RIV1-a` is a wet
brush and `TRK4-d` a dry one. `stamp` lays the bristles down along a path into an
accumulator, and `ink_density` turns what has gathered there into density on the paper's
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

- The blue stroke is wet: it lies down steadily, with soft ends and a smooth edge.
- The olive stroke is dry. Watch its right-hand end: the bristles run short of paint
  and the line breaks into flecks that catch only the high points of the paper.
- Neither stroke has a constant width. The bristles spread and gather as the brush
  travels, which is why a pulled line never looks ruled.

### Vary it

![Twelve strokes in three rows of four, each a wave across its cell. The columns are a wet blue brush, a grainy brown one, a dry olive one and a scratchy dark one. The rows get wider from the top to the bottom, and the dry brushes break up more as they widen.](../images/tutorials/grid-brush.webp)

*Painted by `examples/tutorial_grids.py`, `figure="brush"`. The labels read RIV1-a, MAJ3-b, TRK4-d and MAJ7-e across, and 3 px, 6 px and 12 px down.*

A brush's character needs width to show. At 3 pixels the four brushes are four colours of
the same line; at 12 the wet one stays whole, the third turns grainy, the dry one
breaks into flecks and the last scratches the paper. The width is the second argument of
`brush_from_id`, and the loop steps it.

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

Try changing `"MAJ7-e"` to `"RIV1-a"`, and a fourth wet brush replaces the scratchy one.

## Mix two pigments

![Two panels, each with a yellow-green disc overlapping a deeper green one; the overlap is a different green in the two panels](../images/tutorials/pigments.webp)

*Painted by `examples/pigments.py`, seed 11.*

Where one wash crosses another, the paint underneath matters. A painter mixes two
pigments on the paper by glazing one over the other, and the result depends on how each
pigment behaves: a transparent stain lets the layer under it through, and a covering
colour hides it.

The engine holds that as a number. Each `PigmentLayer` is a density, a colour from
`PIGMENTS` and a `TRANSPARENCY`: what the pigment shows over black, as a share of what
it shows over white. A pigment near 0 is a transparent glaze; one near 1 covers what lies
beneath it. `composite` stacks the layers the way the `PaperStyle` asks. With
`km_glazing=False` it multiplies them. With `km_glazing=True` it glazes them by
Kubelka-Munk, which reads each layer's transparency. The script paints both and sets
them side by side, multiplied on the left and glazed on the right.

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
        (wash(_disc(centre_x), sheet, 0.6, 0.3), rgb(PIGMENTS[key]), TRANSPARENCY[key])
        for key, centre_x in (("farmland", 0.38 * W), ("wood", 0.62 * W))
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

- Look at the lens where the two discs overlap. It is not the same green in the two
  panels, though the discs are identical. Glazing lets the colour underneath speak, in
  the way real washes do.
- Neither disc has been recoloured to make the overlap: the overlap is what happens
  when the two pigments meet.
- Both panels share one paper, so the grain runs through them in the same places.

### Vary it

![Eight pairs of overlapping discs in two rows of four. The pairs are blue over ochre, which makes green; rose over blue, which makes violet; ochre over rose, which makes orange; and sienna over blue, which makes a dark grey-brown. The top row is multiplied and the bottom row glazed, so the overlaps in the bottom row are cleaner.](../images/tutorials/grid-pigments.webp)

*Painted by `examples/tutorial_grids.py`, `figure="pigments"`. The labels read 1 to 4 across, and multiply and glazed down.*

The map pigments are pale on purpose. A painter's tubes are not, and the engine keeps
them beside the map's, in `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY`: cerulean,
yellow ochre, quinacridone rose and burnt sienna here. The grid glazes them over each
other in four pairs, and the loop lays each pair twice, once multiplied and once glazed.

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

Try changing a pair to `("ultramarine", "yellow_ochre")`, and look at the green it makes.

## Take up the pen

![A dark ink spiral of three turns drawn with a pen nib on cream paper, its line slightly uneven where the ink meets the grain](../images/tutorials/nib-line.webp)

*Painted by `examples/nib_line.py`, seed 11.*

A painter's pen is a nib, and a nib is not round. Held at an angle it draws its full
width across itself and almost nothing along itself, which is why a pen line swells and
thins with the direction of the stroke.

The engine's nib is a brush too. Row 6 of the brush sheet is a pen, so
`brush_from_id("MAJ6-e", ...)` gives a narrow nib that sets ink down where it touches
and nowhere else. The sequence is the brush stroke's: `stamp` the line into an
accumulator, `ink_density` it on the paper's tooth, and `composite` it over the paper
in the ink colour the brush came with. Here the line is a spiral of three turns.

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

- Look closely at the edge of the line. It is ink on paper, and it is slightly rough
  where the nib met the grain. A drawn vector line would have no such edge.
- The width stays narrow and steady, which is the difference between a pen and the wet
  brush you pulled before.
- Nothing about the code changed from the brush rung but the brush's name and its size.
  The pen is the same machinery with a different tip.

### Vary it

![The name Keswick written twelve times in three rows of four. The columns turn the nib through four angles; the rows thin the line along the nib by none, about half and most. In the top row every stroke is one width; in the bottom row the strokes along the nib fall away to hairlines, and which strokes those are changes with the angle.](../images/tutorials/grid-nib.webp)

*Painted by `examples/tutorial_grids.py`, `figure="nib"`. The name is Keswick. The labels read -38, 0, 38 and 90 across, and 0, 0.52 and 0.85 down.*

The spiral turns in every direction, so the nib's angle does not show in it. A name has
strokes in known directions, so the grid writes one. This is the next rung's hand, met
early: a `NibStyle` sets the nib's angle in degrees from the page's horizontal
(`label_pen_angle_deg`) and how much of its width a stroke along it loses
(`label_pen_thin`). At 0 the pen is a plotter's, one width the whole way round. At 0.85
the strokes along the nib are fine hairlines, and turning the nib moves them from the
rising strokes (-38) to the level ones (0), the falling ones (38) and the upright ones (90). The labels in every grid
on this page are written the same way.

<!-- from examples/tutorial_grids.py -->
```python
def _nib_grid() -> np.ndarray:
    """Letter a name with the nib at four angles across and three `label_pen_thin`s down."""
    angles, thins = (-38, 0, 38, 90), (0.0, 0.52, 0.85)
    boxes, h = _layout(len(angles), len(thins), 92, 92, 46)
    out = _paper(W, h)
    for r, thin in enumerate(thins):
        for c, angle in enumerate(angles):
            x, y, w, ch = boxes[r][c]
            nib = NibStyle(label_pen_angle_deg=angle, label_pen_thin=thin, label_pen_width_px=3.6)
            setting = Setting(NAME, 42.0, anchor=(w / 2, 0.68 * ch), align="middle", wash=False)
            out[y : y + ch, x : x + w] = _letter(out[y : y + ch, x : x + w], [setting], nib)
    return _labels(out, boxes, angles, thins)
```

Try changing `thins` to `(0.0, 0.3, 0.6)`, and the swelling softens.

## Letter a name

![The name Ambleside written by hand in dark ink along a gentle wave, its letters each a little different in size and slant](../images/tutorials/lettering.webp)

*Painted by `examples/lettering.py`, seed 7. The name is Ambleside.*

A signwriter or a letterer does not stamp letters; they write them, and no two come out
the same. The slant drifts, the baseline wanders, and the pen is never held at quite
the same angle twice.

Now the hand. A `Hand` writes a `Setting`, which is a text at a size set along a line,
as a list of `Mark`: the strokes the nib will run along. You give it a face (`FaceStyle`)
and a style (`HandStyle`), and the nib's own style groups (`NibStyle`, `NibGroups`) say
how the ink goes down. `nib_plate` strokes the marks onto one RGBA plate, a layer that
carries its own transparency, and the script lays that plate over the paper by its
alpha, the normal way, instead of multiplying it. The script writes two files: the plate
as `lettering-plate.webp` and the finished picture.

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

    surface = NibSurface(canvas, 1.0, np.zeros((H, W), np.float32), GRAN_PX)
    groups = NibGroups(NibStyle(), face, hand_style, BrushStyle(), PaperStyle())
    plate_path = nib_plate(marks, surface, groups, out_dir / f"{STEM}-plate.webp")
    if plate_path is None:
        raise RuntimeError("the hand wrote no marks")

    rgba = np.asarray(Image.open(plate_path).convert("RGBA"), np.float32) / 255
    alpha = rgba[..., 3:]
    out = paper * (1 - alpha) + rgba[..., :3] * alpha

    path = out_dir / f"{STEM}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

### What to notice

- The letters are not stamped from a template. The hand writes each one afresh, so the
  three e's of "Ambleside" are cousins and not copies, as they would be in a person's
  writing.
- The name follows the wave and rides it, each letter turned to the line beneath it,
  and not stood upright on a baseline.
- The ink sits on the paper and does not multiply into it: where the letters are
  darkest they are simply ink, as a pen mark would be.

### Vary it

![The name Keswick written nine times in three rows of three. Every copy is the same word and no two are alike: the letters lean differently, sit at different heights and differ in size.](../images/tutorials/grid-lettering.webp)

*Painted by `examples/tutorial_grids.py`, `figure="lettering"`. The name is Keswick; the nine copies are nine hand seeds, 1 to 9.*

The hand draws every wobble from one generator, so one seed writes one name one way.
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
            nib = NibStyle(label_pen_width_px=2.6)
            seed = 3 * r + c + 1
            out[y : y + ch, x : x + w] = _letter(out[y : y + ch, x : x + w], [setting], nib, seed)
    return out
```

Try changing the `seed` to `7` in every cell. The nine copies become one name, written
the same way nine times.

## Compose the painting

![A pale blue wash disc on cream paper, a wet blue brush stroke running across it in a long wave and the name Keswick written by hand over both](../images/tutorials/composition.webp)

*Painted by `examples/composition.py`, seed 7. The name is Keswick.*

The last rung adds nothing new; it puts the others together, in the order a painter
works. The paper goes first. The wash and the wet brush stroke go over it. The lettering
goes last, on top of the paint, and where the paint is dark enough to hide it a painter
lifts a patch of colour with a damp brush first, so that the name has a pale place to sit.

The engine does it in the same order. The paper goes down first. The wash and the wet
brush stroke are composited over it. Then the hand sets "Keswick" along a wave across the
middle, the nib strokes its marks onto a plate, and the plate is laid over everything by
its alpha. The paint is underneath and the lettering on top.

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
    marks: list[Mark] = hand.write(Setting(NAME, 36.0, path=_line()), hand.generator(SEED))

    surface = NibSurface(canvas, 1.0, np.zeros((H, W), np.float32), GRAN_PX)
    groups = NibGroups(NibStyle(), face, hand_style, BrushStyle(), PaperStyle())
    plate_path = nib_plate(marks, surface, groups, out_dir / f"{STEM}-plate.webp")
    if plate_path is None:
        raise RuntimeError("the hand wrote no marks")

    rgba = np.asarray(Image.open(plate_path).convert("RGBA"), np.float32) / 255
    alpha = rgba[..., 3:]
    out = paper * (1 - alpha) + rgba[..., :3] * alpha

    path = out_dir / f"{STEM}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

The helper `_wash_and_stroke`, defined above `main` in the script, holds the disc and the
brush stroke from the earlier rungs.

### What to notice

- Every layer keeps its own character where it meets the others. The stroke's edge
  reads through the wash beneath it, and the lettering is crisp over both.
- The wash is a quiet field and the stroke a single confident line: the picture has a
  foreground and a background because the layers were put down in that order.
- Each rung's sample was a whole picture. Here they are ingredients, and that is how
  the engine is meant to be used.

### Vary it

![Six small copies of the painting in two rows of three, a blue disc with a wave of blue brushwork and the name Keswick over both. The three columns differ only in the hand's seed, so the name is written three ways. In the top row the name sits straight on the paint; in the bottom row a pale patch of paper shows through the paint behind the letters.](../images/tutorials/grid-composition.webp)

*Painted by `examples/tutorial_grids.py`, `figure="composition"`. The name is Keswick. The labels read seed 1, seed 2 and seed 3 across, and off and on down.*

Two things change here. The hand's seed rewrites the name, and `Setting.wash` turns the
backing wash off or on: a soft, paper-coloured patch the nib lifts under a name where
the ground is dark enough to need it. The nib reads how dark the ground is from the
`ground` it is given. The script above gives it none, so its name never needs a patch;
the grid gives it the density of the wash and the stroke, which is why the patch shows.

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

You have painted every layer the engine has: paper, wash, brush, pigment, pen and hand.
The next step puts them to work on real country. In [First map](first-map.md) you paint
a route round Keswick from recorded data, with no network, and then from a track of
your own.
