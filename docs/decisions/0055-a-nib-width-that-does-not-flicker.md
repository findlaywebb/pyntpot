# 0055 — A nib width that does not flicker: a golden regeneration

Status: accepted

## Context

A glyph's width along each stroke follows the angle between the stroke and the nib
(`letters.nib._pen_profile`, ADR 0008): `1 - label_pen_thin` of the width along the nib, all
of it across, the sine between. The direction was read segment by segment from the stroke's
own points, and a glyph's stroke comes off a thinned skeleton (`letters.skeleton`) that turns
a pixel at a time, a staircase of flats and diagonals. Where a stroke ran close to the nib's
angle and `label_pen_thin` was high, each step swung the width between full and a hairline,
stamp by stamp (GitHub issue #42). On `docs/images/explanation/nib-angles.webp` at 0.85 the
thinned strokes' edges were stair-stepped, with spikes where the width flipped, and at the
90 degree cell the K and the w broke into dots. Measured on "Keswick" at 52 px with
`NibStyle(label_pen_angle_deg=90, label_pen_thin=0.85, label_pen_width_px=3.4)`, the width
profile changed by up to 0.77 of the full width between neighbouring samples, and zigzagged
(wide, thin, wide in three steps) 19 to 20 times a word over three hand seeds.

## Decision

- **The width is read from the stroke's smoothed direction.** `_pen_profile` takes a
  `window`, the nib's own width in render pixels (`Brush.width` of the glyph's brush, which
  `_items` now makes before the profile), and averages the stroke's unit tangent over it,
  weighted by length under a tent `window` wide at half its height, centred on each sample
  and cut to the stroke at its ends. The tent is a box of boxes: one box a window wide at
  each of `_TENT_TAPS` (8) points spread over a window round the sample, each box's integral
  read exactly from the running sum of the length-weighted tangent (`_integral`). A box
  alone leaves a ripple on a staircase about a sixth of the width at thin 0.85; the tent
  holds it under an eighth.
- **The raw tangent, not its doubled angle.** A doubled angle (which a stroke and its
  reverse share) cancels at a right-angled corner and the width jumps there in one step; the
  raw tangent turns through the angles between. A glyph's strokes are walked one way along a
  chain, so the only place a raw tangent cancels is a cusp that doubles straight back, which
  a traced glyph does not have.
- **The samples are evenly spaced and at most half a window apart**: a long stroke is
  sampled at `ceil(2 * length / window) + 1` points when that is more than the 24 it had.
  `stamp` already interpolates a profile of any length onto its stamps.
- Not changed: the nib's angle is still fixed to the page (issue #76), and no other mark
  (leader, span, tick, underline, pin) has a profile.

Pinned by `tests/property/test_nib.py` (turning a stroke by an angle moves no sample of its
width by more than `thin` times that angle; a pixel staircase at any angle to the nib keeps
within 0.12 of its straight line's width at thin 0.85, sample to sample and against the true
width) and `tests/unit/letters/test_nib.py::TestPenProfile` (a straight stroke keeps the
exact sine law; a corner climbs through the widths between; the sample count; "Keswick" at
the issue's settings, three seeds, has no zigzag).

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052. The tolerance bound is not
changed, no gate is loosened and the hash input does not change; the manifest hash does not
move (`340a7f6e260ee1e2-d9c56c0811177b0f`).

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.005035
map.png: identical no, differing fraction 0.002551
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Only the lettering moves, and only in its strokes' widths: placement does not read the
nib, so every name keeps its seat and `PINNED_LABELS` is unchanged. `GOLDEN_HASH` is not
re-pinned. The place pins (`tests/golden/test_places.py`), the map-styles means and
the smoke lock pass unchanged on the regenerated goldens, so none is re-pinned.

### Docs images

Every docs image and master was repainted on top of ADR 0047's. The 37 that letter
anything moved (every map card, the lettering, nib and tutorial figures, and the figures
whose grids carry lettered captions); every other entry is byte-identical. Master
differing fractions against main's masters:

| Image | Master | Image | Master |
|---|---|---|---|
| `explanation/nib-hands.webp` | 0.099392 | `tutorials/grid-nib.webp` | 0.081960 |
| `tutorials/grid-lettering.webp` | 0.072681 | `explanation/nib-angles.webp` | 0.055909 |
| `explanation/nib-backing.webp` | 0.027694 | `social-preview.jpg` | 0.020972 |
| `word.webp` | 0.016728 | `explanation/nib-ground.webp` | 0.015883 |
| `tutorials/grid-composition.webp` | 0.011733 | `gallery/lettering.webp` | 0.010234 |
| `tutorials/lettering.webp` | 0.010234 | `map-styles/bold.webp` | 0.005629 |
| `gallery/composition.webp` | 0.005130 | `tutorials/composition.webp` | 0.005130 |
| `tutorials/grid-brush.webp` | 0.004281 | `how-to/own-shapes.webp` | 0.004115 |
| `painting-with-python/derwentwater.webp` | 0.004115 | `reference/pigment-swatches.webp` | 0.003674 |
| `places/skye.webp` | 0.003641 | `how-to/route-ink-grid.webp` | 0.003554 |
| `places/y-fenni.webp` | 0.003485 | `map-styles/pen-and-ink.webp` | 0.003192 |
| `explanation/wash-glaze.webp` | 0.002817 | `how-to/route-ink.webp` | 0.002583 |
| `tutorials/route-map.webp` | 0.002534 | `gallery/route-map.webp` | 0.002485 |
| `places/ambleside.webp` | 0.002485 | `map-styles/winter.webp` | 0.002461 |
| `how-to/command-line.webp` | 0.002083 | `places/oxford.webp` | 0.002083 |
| `reference/brush-sheet.webp` | 0.002083 | `tutorials/grid-wash.webp` | 0.002067 |
| `tutorials/grid-paper.webp` | 0.001900 | `tutorials/grid-pigments.webp` | 0.001733 |
| `map-styles/sepia.webp` | 0.001389 | `places/yr-wyddfa.webp` | 0.001181 |
| `hero.webp` | 0.000828 | | |

Looked at side by side with `main` (the review images in the pull request): on
`nib-angles.webp` the top row (thin 0) is unchanged, and at 0.52 and 0.85 the strokes'
edges run smooth where they were stair-stepped; at the 90 degree cell the K and the w are
whole strokes that thin along the nib rather than strings of dots. On the map cards and the
Lynmouth label plate, at the default thin of 0.52, the names read the same at a glance:
the change is a pixel or two at the edges of the strokes, where a width that flickered now
holds.

## Consequences

- A glyph's width along a stroke is a continuous function of its direction and of where on
  the stroke it is; a staircase near the nib's angle reads as one width.
- A tight curve, shorter than the nib is wide, has its thinnest point softened: the width
  there is the average over a nib's width of path, which is the nib's own footprint.
- A further regeneration needs its own ADR.
