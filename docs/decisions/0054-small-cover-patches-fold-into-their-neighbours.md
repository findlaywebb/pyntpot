# 0054 — Small cover patches fold into their neighbours: a golden regeneration

Status: accepted

## Context

On the Ambleside hero card (`docs/images/hero.webp`) the woods, meadows and scrub are
painted as many small patches in contrasting greens over the tawny fell (GitHub issue #46).
At full size they read as texture; at the 400 px the README and the gallery show, they read
as noise. The calmer hero theme softened the palette but could not remove a patch: no theme
field merged or dropped cover below a size. `Generalisation.min_area_ha` drops blobs of the
wood, the parkland and the sea, in hectares, which is not the card's scale and does not
reach the land cover classes.

## Decision

- **A floor in display pixels.** `CoverStyle.min_patch_px` (theme key `[cover]
  min_patch_px`) is the smallest painted cover patch kept as it is, in display pixels, so
  one value means the same on a 720 px place card and a 1,800 px plate. Zero, the default,
  keeps every patch, so the default theme and every other theme paint as before.
- **Patches are measured as painted.** `maps.painter.patches` finds the four-connected
  patches of the label raster (one class per pixel) after `_label` has deformed, filled and
  cut the water out, so the floor sees the patches the card shows, not the surveyed
  polygons, many of which tile one field.
- **A small patch takes its largest painted neighbour's class** (the lower class on a
  tie). A patch that touches nothing painted is kept: Rydal Water's wooded islands are the
  only ground in the lake, and the first cut, which cleared such a patch to paper, left
  white holes in the water. Paper and water are never painted. One pass: a small patch whose
  largest neighbour is another small one takes that patch's class as it was.
- **It takes no draw from the deform generator**, so no outline moves. The washes see the
  new labels, and their blooms are drawn from the shared generator per class (issue #61),
  so the blooms of the hero move as a whole.
- **The hero theme sets 400** (`examples/themes/ambleside-hero.toml`): a patch under about
  20 by 20 display pixels on the 1,200 px hero, 7 by 7 at the README's 400 px.
- The search is on horizontal runs with a union-find, not a pixel flood, so it is a
  fraction of a second on the hero's label raster.
- Pinned by `tests/unit/maps/painter/test_patches.py`: patches are four-connected; a speck
  takes its field's class, and the larger of two neighbours; an island patch is kept; paper
  is never painted; the floor is the smallest patch kept; zero changes nothing; a property
  that no patch at the floor changes; and the cover phase folds a copse below the theme's
  floor into the meadow round it.

## Golden regeneration

Process as ADR 0036. The tolerance bound is not changed, no gate is loosened and the hash
input does not change. The default is off, so the Lynmouth goldens, the place pins, the
map-styles means and every docs image but the two painted in the hero theme are unchanged.

| Image | Image differing fraction | Master differing fraction |
|---|---|---|
| `hero.webp` | 0.389120 | 0.235453 |
| `social-preview.jpg` | 0.272316 | 0.204688 |

Looked at side by side with `main`, full size and 400 px wide: the small light-green flecks
on Loughrigg Fell, round Rydal and along the card's torn edge are gone into the fell's
tawny or the wood round them, and the thumbnail is a little calmer. The larger patches,
the lakes and their islands, the lettering, the roads and the route are where they were.
Most of the differing fraction is the blooms moving (above), not new shapes. The hero is
calmer, not calm: the patches above the floor still alternate greens over the fell, and a
higher floor or a narrower palette is the theme's next move.

## Consequences

- A theme can set how small a painted patch may be, at the card's own scale.
- Folding is by area alone: a long thin hedge of wood narrower than the floor but larger
  in area is kept.
- A further regeneration needs its own ADR.
