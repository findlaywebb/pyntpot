# Paint a watercolour

You are going to paint seven small pictures, one after another, each with a short script. By the end you will have stretched paper, laid a wash on
it, pulled a brush and a pen across it, mixed two pigments, written a name by hand and
put the lot together on one painting. Nothing is drawn by a graphics library behind your
back: every mark comes from the engine you can read in the script.

The order is the painter's, and it is the code's too. You stretch paper and lay washes
with `ink`, you letter with `letters`, which is built on `ink`, and the route work comes
last, in `maps`, which is built on both. Each rung uses only what the one before it
taught you, so you never meet a name before you need it.

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

## Stretch the paper

![A piece of cream paper with a soft grain, a darker worn border and a few pale blotches of foxing](../images/tutorials/paper.webp)

*Painted by `examples/paper.py`, seed 11.*

A painter starts with paper, and so does the engine. A `Sheet` holds the paper's noise
fields: the grain that pigment will settle into. A `Canvas` is the pixel grid you paint
on. `paper_plate` paints the cream rag itself, its worn border, its vignette and its
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

- The edge is darker than the middle, as if the paper had been handled and left on a
  windowsill. Nothing straight or perfect has been drawn there.
- Fine grain runs all over, and a few soft blotches sit about the page. Real paper
  is never one flat colour, and this is the first thing that tells you it was made by a
  hand and not by a screen.
- The picture is plain because the paper has to be. Everything after this rung is
  painted onto it, and shows its grain through.

**Try changing** `SEED` to another number: you get another piece of the same stock, its
blotches in different places.

## Lay a wash

![A soft blue disc on cream paper, its edge a little darker than its middle and its body lightly granular](../images/tutorials/wash.webp)

*Painted by `examples/wash.py`, seed 11.*

A wash is pigment spread over a shape in one go. You give `wash` a coverage mask, here a
disc built with numpy, and it returns a density: how much pigment lies at each pixel,
from 0 to 1. The density is not a colour yet. `composite` lays it over the paper in a
pigment's colour: `PIGMENTS` holds each pigment's `#rrggbb` hex, and `rgb` turns that
into the triple `composite` reads.

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

**Try changing** the `0.3` to `0.6` and run it again: the pooled edge grows from a hint
to a clear line.

## Pull a brush

![Two strokes on cream paper: a steady, wet blue stroke above a drier olive stroke that breaks into flecks towards its end](../images/tutorials/brush-stroke.webp)

*Painted by `examples/brush_stroke.py`, seed 11.*

A brush is a tip of bristles. `brush_from_id` reads a name from the brush sheet, the
catalogue of brushes the engine ships with, and gives back the brush and the colour of
its ink as hex. `RIV1-a` is a wet brush and `TRK4-d` a dry one. `stamp` lays the bristles
down along a path into an accumulator, and `ink_density` turns what has gathered there
into density on the paper's tooth, ready for `composite` as before.

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

**Try changing** `"TRK4-d"` to `"RIV1-a"` in the second call. The dry stroke turns wet
and takes the wet brush's colour, which shows how much of its character came from the
brush and how little from the path.

## Mix two pigments

![Two panels, each with a yellow-green disc overlapping a deeper green one; the overlap is a different green in the two panels](../images/tutorials/pigments.webp)

*Painted by `examples/pigments.py`, seed 11.*

Where one wash crosses another, the paint underneath matters. Each `PigmentLayer` is a
density, a colour from `PIGMENTS` and a `TRANSPARENCY`: what the pigment shows over
black, as a share of what it shows over white. A pigment near 0 is a transparent glaze;
one near 1 covers what lies beneath it. `composite` stacks the layers the way the
`PaperStyle` asks. With `km_glazing=False` it multiplies them. With `km_glazing=True` it
glazes them by Kubelka-Munk, which reads each layer's transparency. The script paints
both and sets them side by side, multiplied on the left and glazed on the right.

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

**Try changing** the pair `("farmland", 0.38 * W), ("wood", 0.62 * W)` to use `"water"`
in place of `"farmland"`. A blue under a green gives a different overlap again.

## Take up the pen

![A dark ink spiral of three turns drawn with a pen nib on cream paper, its line slightly uneven where the ink meets the grain](../images/tutorials/nib-line.webp)

*Painted by `examples/nib_line.py`, seed 11.*

A nib is a brush too. Row 6 of the brush sheet is a pen, so `brush_from_id("MAJ6-e", ...)`
gives a narrow nib that sets ink down where it touches and nowhere else. The sequence is
the brush stroke's: `stamp` the line into an accumulator, `ink_density` it on the
paper's tooth, and `composite` it over the paper in the ink colour the brush came with.
Here the line is a spiral of three turns.

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

**Try changing** `TURNS` to `5`, and the nib packs more turns into the same space.

## Letter a name

![The name Ambleside written by hand in dark ink along a gentle wave, its letters each a little different in size and slant](../images/tutorials/lettering.webp)

*Painted by `examples/lettering.py`, seed 7. The name is Ambleside.*

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

**Try changing** `SEED` to `8` and run it again. The hand writes the same name another
way, the way a second try at your own signature differs from the first.

## Compose the painting

![A pale blue wash disc on cream paper, a wet blue brush stroke running across it in a long wave and the name Keswick written by hand over both](../images/tutorials/composition.webp)

*Painted by `examples/composition.py`, seed 7. The name is Keswick.*

The last rung adds nothing new; it puts the others together, in the order a painter
works. The paper goes down first. The wash and the wet brush stroke are composited over
it. Then the hand sets "Keswick" along a wave across the middle, the nib strokes its
marks onto a plate, and the plate is laid over everything by its alpha. The paint is
underneath and the lettering on top.

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

**Try changing** `SEED` to `8`. The paper's blotches move, the stroke's bristles fall
differently and the hand writes "Keswick" another way, and the layers still sit
together as before.

## Where next

You have painted every layer the engine has: paper, wash, brush, pigment, pen and hand.
The next step puts them to work on real country. In [First map](first-map.md) you paint
a route round Keswick from recorded data, with no network, and then from a track of
your own.
