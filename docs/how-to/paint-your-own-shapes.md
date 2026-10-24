# Paint your own shapes

You have an outline of your own, a polygon you drew, a silhouette or an image's alpha
channel, and a line you want a name set along. You want the engine to wash the outline, ink
its edge and letter the name, with no map involved.

You need the tutorial's seven steps behind you
([Paint a watercolour](../tutorials/paint-a-watercolour.md)): this guide does not teach
`Sheet`, `wash`, `stamp` or `Hand` again. It shows where your shapes go in.

## Steps

1. Put your outline in a mask. A mask is a `float32` array the size of your canvas, shaped
   `(height, width)`, 1.0 where the wash goes and 0.0 where it does not. Pillow rasterises a
   polygon of your own points; coordinates are pixels, with y down:

   ```python
   image = Image.new("L", (W, H), 0)
   ImageDraw.Draw(image).polygon(corners, fill=255)
   mask = np.asarray(image, np.float32) / 255
   ```

   For a picture's own silhouette, take its alpha channel instead and size it to the canvas:
   `np.asarray(Image.open("fell.png").convert("RGBA").resize((W, H)))[..., 3] / 255`.
   Anything that makes such an array will do: a drawing, a threshold of a photograph, a
   function of `numpy.mgrid`.

2. Lay the wash and ink the edge. `wash` turns the mask into pigment density on the
   paper's noise, and a pen brush `stamp`s your own points as a line:

   ```python
   density = wash(mask, sheet, 0.6, 0.3)

   brush, ink_hex = brush_from_id("MAJ6-e", 3.0, 1.0, BrushStyle())
   acc = np.zeros((H, W), np.float32)
   stamp(acc, line, brush, np.random.default_rng(SEED))
   line_density = ink_density(acc, brush, sheet)
   painted = composite(
       [(density, rgb(PIGMENTS["water"])), (line_density, rgb(ink_hex))], paper, PaperStyle()
   )
   ```

   `line` is an `(n, 2)` array of x, y points in canvas pixels. It need not be the outline's
   edge; any path is inked the same way. Round a polygon's corners by cutting them (the
   script does, three times) before you stamp it, or the line shows every vertex.

3. Set a name along a path of your own. A `Setting` with a `path` of at least two
   `(x, y)` points is written along it, each letter on the line's tangent, from the first
   point to the last:

   ```python
   marks = hand.write(Setting(NAME, 38.0, path=path), hand.generator(SEED))
   ```

   Then stroke the marks onto a plate with `nib_plate` and lay the plate over the painting
   by its alpha, as the tutorial's lettering step does. The path is the line the letters
   sit on, so give it room below or above the shapes, and run it left to right to read left
   to right.

4. Run the whole script, which holds these steps with the polygon, the line and the path
   filled in:

   ```bash
   uv run python examples/how_to_own_shapes.py out/
   ```

   It writes `out/own_shapes.png` and the nib plate, `out/own_shapes-plate.webp`.

## Result

![A hill-shaped fell washed in pale blue-green with a black pen line along its smooth skyline, and the name Skiddaw lettered by hand along a gentle curve beneath it.](../images/how-to/own-shapes.webp)

Painted by `examples/how_to_own_shapes.py`, seed 5. The name lettered along the bottom is
"Skiddaw". The skyline is nine points of your own, in `SKYLINE` at the top of the script;
replace them and the picture follows.

## When it goes wrong

- `ValueError: operands could not be broadcast together with shapes (100,100) (320,480)`:
  `wash` is refusing a mask that is not the size of the canvas. The mask's shape is `(height, width)`, the
  reverse of the `(width, height)` Pillow takes in `Image.new`, and it must equal the
  `Sheet`'s. Resize the mask, or build the `Sheet` from the mask's own shape.
- The wash is heavier than you expect: the mask holds 0 to 255 or another range. Divide by
  255 so that it runs from 0 to 1.
- `ValueError: a path to write along needs at least two points`: the path given to the
  `Setting` has one point, or none.
- The name is upside down or reads backwards: the hand writes from the path's first point
  to its last. Reverse the path.
- `RuntimeError: the hand wrote no marks`, from the script's own check: `nib_plate` returned
  nothing because the hand wrote nothing. Check that the name is not empty.
- `KeyError: 'watr'`, or `ValueError: no such brush 'MAJ9-z'`: a pigment key or a brush id
  that does not exist. [Pigments](../reference/pigments.md) and
  [Brushes](../reference/brushes.md) list every one.
