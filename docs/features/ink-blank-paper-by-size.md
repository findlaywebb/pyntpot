# Blank paper could be set up from a size alone

GitHub issue: [#166](https://github.com/findlaywebb/pyntpot/issues/166)

**What exists today.** Painting on blank paper with `pyntpot.ink` takes three calls that
repeat the same numbers:

```python
sheet = Sheet(H, W, GRAN_PX, SEED)
canvas = Canvas(0, 0, W, H, W, H)
paper = paper_plate(sheet, canvas, PaperStyle(), W)
```

- `Canvas` is a metre box and a pixel grid; outside `maps` the box means nothing, so the
  examples write `Canvas(0, 0, w, h, w, h)` 47 times in 25 files under `examples/`, and the
  tutorial another 12 times.
- `paper_plate` reads only the canvas's `w` and `h`, then takes `display_px`, which is the
  width again in all 35 of its calls under `examples/` (25 files).
- `Sheet(h, w, ...)` takes height first; `Canvas(x0, y0, x1, y1, w, h)` and Pillow take width
  first. A copied call with the two swapped is a silent transposition on a non-square image.
- `brush_from_id(brush_id, width_display_px, scale, style)` has no defaults: 21 of its 22
  calls in `examples/` pass `scale=1.0`, 16 of them with `BrushStyle()` as well.
- `wash(cover, sheet, base, pool)` is called 30 times in `examples/`, every time with the two
  densities by position, 24 times as two bare literals (`wash(disc, sheet, 0.6, 0.3)`).

**What the feature would add.** A blank sheet of paper from a size and a seed, one axis
order across `Sheet` and `Canvas`, and the numbers a reader cannot guess named at the call:
the wash's body and pool densities, the brush's scale and style.

**Possible shape.** A suggestion:

- `Canvas.pixels(w, h)` for the pixels-only case, and `paper_plate`'s `display_px`
  defaulting to `canvas.w`.
- `Sheet` taking `(w, h, ...)`, or both taking a keyword-only size, so the order cannot be
  copied wrong.
- `wash(cover, sheet, *, body, pool)` and `brush_from_id(brush_id, width_px, *, scale=1.0,
  style=BrushStyle())`.

Changing `Sheet`'s order and making arguments keyword-only breaks every caller, so this
needs an ADR and a breaking-change entry in the changelog. Pixels must not move: the examples
and tutorial are rewritten to the new calls and the docs images and goldens stay as they
are.

**Related.** `docs-examples-review` (#63); `ink-one-pigment-registry` (#72), the colour half
of the same boilerplate; `ink-public-wash-options` (#73), which touches the same `wash`
signature.
