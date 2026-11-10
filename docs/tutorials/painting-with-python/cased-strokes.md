# Cased strokes: case, light and shadow one stroke

A line effect is not only for maps. It is a function of the colours beneath a line and the line's mask, so it works on any stroke you can draw. This page takes one brush stroke over a wash and gives it a casing, a glow and a shadow with the `pyntpot.ink` primitives alone: no map, no theme and no style. You need only the first tutorial, [Paint a watercolour](../paint-a-watercolour.md). For why an effect works on colours and not as a glaze, see [Line effects](../../explanation/line-effects.md).

![One brown stroke over a wash of pale farmland and dark wood, painted four times in a grid of two across and two down. The plain stroke is bare. The cased stroke has a thin ring of paper round it. The glowing stroke has a soft pale margin over the wood. The shadowed stroke has a grey shadow to its south-east.](../../images/painting-with-python/cased-stroke.webp)

*Painted by `examples/cased_stroke.py`. The names are plain, cased, glow and shadow.*

Run it with `uv run python examples/cased_stroke.py out/`. The script writes `out/cased_stroke.png`.

## Case, light and shadow one stroke

Each cell is the same wash and the same stroke, so what changes from one cell to the next is the effect and nothing else. The effects' numbers are held at the top of the script. A width, spread, blur or offset is in pixels, and the light is in the north-west, at azimuth 315 degrees, so the shadow falls to the south-east.

<!-- from examples/cased_stroke.py -->

```python
#: The casing's width in pixels, white so that it is the paper's colour.
CASING_PX, CASING_COLOUR = 2.5, Colour("#ffffff")
#: The glow's spread and blur in pixels, and how strongly it lifts.
GLOW_SPREAD_PX, GLOW_BLUR_PX, GLOW_STRENGTH = 3.0, 4.0, 0.8
#: The shadow's offset and blur in pixels, how strongly it darkens, its colour and the light's azimuth.
SHADOW_OFFSET_PX, SHADOW_BLUR_PX, SHADOW_STRENGTH = 4.0, 2.0, 0.7
SHADOW_COLOUR, AZIMUTH_DEG = pigment("paynes_grey").colour, 315.0
```

A cell goes down in one order: the wash, then the effect with the stroke's density as its mask, then the stroke over it, and last the paper plate's crop multiplied in. The wash is in wash space, where the paper is 1, so a white casing is the paper's own colour and never a white ring on cream paper.

<!-- from examples/cased_stroke.py -->

```python
    ground, density, ink = _scene()
    under = ground
    if name == "cased":
        ring = Casing(width_px=CASING_PX, colour=CASING_COLOUR, strength=1.0)
        under = casing(ground, density, ring, paper=None)
    elif name == "glow":
        lift = Glow(spread_px=GLOW_SPREAD_PX, blur_px=GLOW_BLUR_PX, strength=GLOW_STRENGTH)
        under = glow(ground, density, lift, paper=None)
    elif name == "shadow":
        cast = Shadow(
            offset_px=SHADOW_OFFSET_PX,
            blur_px=SHADOW_BLUR_PX,
            strength=SHADOW_STRENGTH,
            colour=SHADOW_COLOUR,
        )
        under = shadow(ground, density, cast, azimuth_deg=AZIMUTH_DEG)
    laid = composite([(density, ink)], under, PaperStyle())
    x, y = at
    crop = _paper()[y : y + laid.shape[0], x : x + laid.shape[1]]
    return np.clip(laid * crop, 0.0, 1.0).astype(np.float32)
```

`casing(rgb, mask, effect, *, threshold, paper)` and `glow(rgb, mask, effect, *, threshold, paper)` return the wash with a ring round the stroke. `shadow(rgb, mask, effect, *, azimuth_deg, threshold)` returns it darkened beside the stroke, away from the light, and it has no `paper`. The mask is the stroke's density. A pixel at or above `threshold`, which these calls leave at its default, is the line, and the effect leaves it as it was.

The effect goes down before the stroke. A casing and a glow paint only the ring outside the stroke, so the stroke laid over them keeps its own colour; a casing laid after the stroke would eat into its soft edge, and the stroke would not glaze over the ring. The glow only lifts and the shadow only darkens, which is why the cased and glowing cells are never darker than the plain one, and the shadowed cell never lighter.

## A pen casing

A pen drawing has no washes to case against, but a line can still be set off from a tint. A pen casing leaves a reserve of bare paper round the line, and draws two ink lines along the reserve's edges, as an engraver or a cartographer would.

![One thin ink line over a grey tint in two rows of five. The first column is the bare line. The other columns leave a strip of bare paper round the line, edged by two ink lines, the strip widening from left to right and the edge lines thin in the top row and thick below.](../../images/painting-with-python/pen-casing-sweep.webp)

*Painted by `examples/line_effect_grids.py` (figure pen-casing). The labels read 1, 2, 3 and 4 across, and 0.75 and 1.5 down. The first column has no casing. The gap and the edge lines' width are in pixels.*

`pen_casing(rgb, mask, effect, *, threshold, paper)` returns two arrays, not one: the tint knocked back to the paper inside the reserve, and the density of the two ink edge lines. The gap is the `PenCasing`'s `width_px`, and the edge lines' width is its `edge_px`.

<!-- from examples/line_effect_grids.py -->

```python
def _reserved(
    scene: Scene, width_px: float | None = None, edge_px: float = 0.0
) -> tuple[np.ndarray, np.ndarray]:
    """The tint with a reserve round the stroke and the density of the ink edge lines."""
    effect = PenCasing() if width_px is None else PenCasing(width_px=width_px, edge_px=edge_px)
    return pen_casing(scene.wash, scene.density, effect, paper=None)
```

The edge lines are ink, so the script lays them as a pigment layer of their own, over the knocked-back tint and under the centre line. It does so only when there are any, so a plain cell never composites a layer of zeros.

<!-- from examples/line_effect_grids.py -->

```python
    if edges is not None and edges.any():
        under = composite([(edges, scene.ink)], under, PaperStyle())
    laid = composite([(scene.density, scene.ink)], under, PaperStyle())
```

A pen casing has no theme key. It is for a picture you paint in Python, and a map's lines take the casing, glow and shadow of [Case, light or shadow a line](../../how-to/case-light-or-shadow-a-line.md) instead. Every field and its range is in [Line effects](../../reference/line-effects.md).

Next: [the how-to guides](../../how-to/index.md), each one task done with the engine.
