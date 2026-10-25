# Paint your own shapes

Wash an outline of your own, ink its edge and letter a name along a line, with no map
involved. The outline can be a polygon you drew, a silhouette, or an image's alpha channel.

**Before you start:** work through [Paint a watercolour](../tutorials/paint-a-watercolour.md).
This guide shows where your own shapes go in; it does not teach `Sheet`, `wash`, `stamp`
or `Hand` again.

## Steps

1. Put your outline in a mask. A mask is a `float32` array shaped `(height, width)`, the
   size of your canvas. It is 1.0 where the wash goes and 0.0 where it does not. Pillow
   rasterises a polygon of your own points. Coordinates are pixels, with y down:

   ```python
   image = Image.new("L", (W, H), 0)
   ImageDraw.Draw(image).polygon(corners, fill=255)
   mask = np.asarray(image, np.float32) / 255
   ```

   For a picture's own silhouette, take its alpha channel and size it to the canvas:
   `np.asarray(Image.open("fell.png").convert("RGBA").resize((W, H)))[..., 3] / 255`.
   Any way of making such an array works: a drawing, a threshold of a photograph, a
   function of `numpy.mgrid`.

2. Lay the wash and ink the edge. `wash` turns the mask into pigment density on the
   paper's noise. A pen brush `stamp`s your own points as a line:

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

   `line` is an `(n, 2)` array of x, y points in canvas pixels. It need not follow the
   outline's edge. Any path is inked the same way. Before you stamp a polygon, cut its
   corners to round them, as the script does three times. Otherwise the line shows every
   vertex.

3. Set a name along a path of your own. Give a `Setting` a `path` of at least two `(x, y)`
   points. The hand writes the name along it from the first point to the last, each letter
   on the line's tangent:

   ```python
   marks = hand.write(Setting(NAME, 38.0, path=path), hand.generator(SEED))
   ```

   Then stroke the marks onto a plate with `nib_plate` and lay the plate over the painting
   by its alpha, as the tutorial's lettering step does. The letters sit on the path, so
   leave room for it below or above the shapes. Run it left to right to read left to right.

4. Run the whole script. It holds these steps with the polygon, the line and the path
   filled in:

   ```bash
   uv run python examples/how_to_own_shapes.py out/
   ```

   It writes `out/own_shapes.png` and the nib plate, `out/own_shapes-plate.webp`.

## Result

![A hill-shaped fell washed in pale blue-grey that fades out toward its foot. A black pen line, heavier in places, follows its smooth skyline. The name Skiddaw is lettered by hand, centred beneath it on clean paper.](../images/how-to/own-shapes.webp)

*Painted by `examples/how_to_own_shapes.py`, seed 5.* The skyline is nine points in
`SKYLINE` near the top of the script. Replace them and the picture follows.

## When it goes wrong

- `ValueError: operands could not be broadcast together with shapes (100,100) (320,480)`:
  `wash` is refusing a mask that is not the size of the canvas. The mask's shape is
  `(height, width)`, the reverse of the `(width, height)` that Pillow's `Image.new` takes.
  It must equal the `Sheet`'s. Resize the mask, or build the `Sheet` from the mask's shape.
- The wash is heavier than you expect: the mask runs from 0 to 255 or some other range.
  Divide by 255 so that it runs from 0 to 1.
- `ValueError: a path to write along needs at least two points`: the `Setting`'s path has
  one point or none.
- The name is upside down or reads backwards: the hand writes from the path's first point
  to its last. Reverse the path.
- `RuntimeError: the hand wrote no marks`, from the script's own check: the hand wrote
  nothing, so `nib_plate` returned nothing. Check that the name is not empty.
- `KeyError: 'watr'`, or `ValueError: no such brush 'MAJ9-z'`: a pigment key or a brush id
  that does not exist. [Pigments](../reference/pigments.md) and
  [Brushes](../reference/brushes.md) list every one.
