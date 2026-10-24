# Pictures: layered hill washes and a lettered Derwentwater

You paint a Lake District view in one script: five washes of hill receding into mist, a
lake that carries their reflection, a wooded island, and the name written by hand beneath.
Nothing here is a map. Every shape is a numpy mask, and `wash` turns each one into pigment.

![Five washes of hill in blue-grey, grey-brown and green recede above a streaked blue lake that mirrors them; a small wooded island sits on the water and "Derwentwater" is written below.](../../images/painting-with-python/derwentwater.webp)

Painted by `examples/derwentwater.py`, seed 21.

The picture reads "Derwentwater". Run the script yourself:

```bash
uv run python examples/derwentwater.py out/
```

It writes `out/derwentwater.png` and the nib plate `out/derwentwater-plate.webp`. Every
seed is fixed, so you get the same picture each time. `--size` sets the width in pixels;
the height is two thirds of it.

## Paint far to near

A ridge is a line, not a shape. The script draws each from a handful of seeded sines (the
broad fells) plus a few fast, small ones (the crags), and the ground below the line down to
the shore is the mask:

```python
cover = ((yy >= ridge[None, :]) & (yy < shore + 2) & inside).astype(np.float32)
dens = wash(cover, sheet, crest, 0.25)
```

`inside` is the sheet less its margin, so no wash reaches the edge and the paper stays
bare all round. `crest` is the density of the flat body of the wash and `0.25` the extra
pigment that pools at its edge, which is what outlines each hill.

The three far fells and two banks are painted in order, far to near, each in its own
pigment from `PIGMENTS`: `wetland`, `rock` and `relief` for the fells, `scrub` and `heath`
for the banks that frame the lake. The default `PaperStyle` composites by multiplying, so
a pixel under two washes is darker than under one. That is the recession: the far fell,
under nothing but its own wash, is pale; the near bank sits on the washes before it and is
dark. Nothing darkens a hill by hand.

Two touches finish each hill. The density fades toward its foot, where mist lies:

```python
mist = 0.62 + 0.38 * np.exp(-np.clip(yy - ridge[None, :], 0, None) / (0.14 * h))
```

And the nearer hills granulate. `wash` has its own granulation; the script adds more by
scaling the density with the sheet's `gran` field, which is the paper's noise, so the
pigment settles in the same hollows wherever it is laid. The far fell takes none of it
and the banks take the most.

## The lake and what it holds

The water is the `water` pigment under a density streaked along x. The streaks are small
random noise, one cell per few rows, stretched across the width, so they run level as a
calm lake does.

The reflection is not painted again. Each hill's density is already an array, so the
script turns it over about the shore line, shifts each row a pixel or two sideways so the
edge ripples, softens it, fades it with depth and lays it back in its own pigment. The
island and its mirror image come the same way, from one mask of overlapping crowns.

## The name

The last step is the lettering rung over again. A `Hand` writes "Derwentwater" at a
`Setting` centred on the bottom margin, `nib_plate` strokes its marks onto an RGBA plate
and the plate is laid over the painting by its alpha: the nib plate is composited
normally, not multiplied, so the ink stays dark whatever lies beneath.

## Try it

- Change `HILLS` or `BANKS`: add a sixth hill, or swap `rock` for `heath` and watch the
  mood turn warm.
- Change `SEED` and the ridges, ripples and paper all change with it.
- Set `MARGIN` to `0.0` and see how much the bare paper frames the view.

The next page, [Vector drawing](vector-drawing.md), paints a picture someone else drew.
