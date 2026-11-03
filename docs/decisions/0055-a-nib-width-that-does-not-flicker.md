# 0055 — A nib width that does not flicker: a golden regeneration

Status: accepted

## Context

A glyph's width along each stroke follows the angle between the stroke and the nib
(`letters.pen_profile.pen_profile`, formerly `letters.nib._pen_profile`, ADR 0008): `1 - label_pen_thin` of the width along the nib, all
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

- **The width is read from the stroke's smoothed direction.** `pen_profile` takes a
  `window`, the nib's own width in render pixels (`Brush.width` of the glyph's brush, which
  `_items` now makes before the profile), and averages the stroke's unit tangent over it,
  weighted by length under a tent `window` wide at half its height, centred on each sample.
  The tent is a box of boxes: one box a window wide at each of `_TENT_TAPS` (8) points
  spread over a window round the sample. The length-weighted tangent over a box is the chord
  between its ends, so each box is read from the stroke's own points, interpolated at the
  box's ends (`_point`); no running sum is kept. A box alone leaves a ripple on a staircase
  about a sixth of the width at thin 0.85; the tent holds it under an eighth.
- **The raw tangent, not its doubled angle.** A doubled angle (which a stroke and its
  reverse share) cancels at a right-angled corner and the width jumps there in one step; the
  raw tangent turns through the angles between, which is right where the stroke turns
  gently and wrong at a sharp corner. Averaged across a corner, the raw tangent points along
  the corner's bisector, a direction neither leg has; where the nib lies along it the width
  falls to a hairline that neither leg has. That is not only at a cusp: on "Keswick" at 52 px,
  nib 90 degrees, thin 0.85, seed 7, turns of 110 to 127 degrees fell to 0.18 to 0.30 where
  both legs were 0.8 to 0.95, and at 20 px under the default -38 degree nib a corner dipped
  0.38 below its legs.
- **A corner is floored at its legs, by cutting the tent at the stroke's vertices.** Each
  sample's tent is also cut in two at every vertex of the stroke it reaches (`_cuts`), and
  each side is read as a width on its own (`_side`; an empty side, past an open stroke's
  end, reads full, so the other side decides). The narrower side of each cut is a floor, and
  the sample's width is the widest of those floors and the whole tent's:
  `max(whole, max over vertices v of min(before_v, after_v))`. The sides are the same box
  chords, each box cut at the vertex: a running sum of the box ends at or before the vertex,
  plus the vertex once for each end past it (`_reached`), so the cut needs no more points
  read off the stroke than the whole tent does.
  - **Why it holds wherever the samples fall.** Cut at a corner, each side of a tent that
    covers only two straight legs is one leg, so a stroke of two straight legs is nowhere
    thinner than the narrower leg: at the point, beside it, and at a sample just past half a
    window, where the tent still reaches round the corner. The floor is read from the
    stroke's vertices, which are the stroke's own, not from the samples, so there is no reach
    to round to a whole number of samples.
  - **Why it does not bend the L.** Where both sides of a cut lie on one side of the nib's
    direction, the whole (their sum) lies between them, and `|sin|` has no minimum inside
    such an arc, so the whole is no narrower than the narrower side and the floor does not
    bind. That covers a straight run (a staircase's sides agree with its whole to within the
    ripple) and an L whose leg lies along the nib, which climbs exactly as before.
  - **Why it is continuous in the nib.** Every width is `|sin|` of a direction the stroke
    alone fixes less the nib's angle (or full, for an empty side, which the stroke alone
    decides too), and the floor is a widest of narrowest of them; nothing is gated on a
    width. So turning the nib, or the stroke, by an angle moves no sample by more than
    `thin` times that angle.
  - **How far it reaches.** A floor binds only where the two sides lie either side of the
    nib's direction, and never above the narrower of them. A hairline running straight along
    the nib is lifted only where its tent reaches a vertex past the turn's first, and never
    above the side of that cut that holds the hairline. Where a curve turns through the nib's
    own direction within a window (a small `o` at a high thin), its sides straddle the nib,
    and its thinnest point is read as wide as the narrower side of a cut there.
  - **What it replaced.** The version this PR first carried compared the halves of the tent
    cut at each sample with the whole, and where they beat it (the whole was "pinched") it
    carried the narrower half to the samples half a window either side (`_spread`). That
    floor depended on where the samples fell: with the default 24 samples a ±45 degree V
    under a flat nib dipped to 0.471 beside its point against legs of 0.751, and at 61
    samples to 0.673, because the reach was truncated to whole samples (2.83 px of the 4).
    Its gate (`np.where(legs > whole, legs, 0)`) switched the floor on at full strength, so
    on a hairline running into a 2 px kink, turning the nib by 1.6e-4 rad moved a sample from
    0.187 to 0.473, against the 1.4e-4 the sine law allows. Both are pinned below.
- **A closed stroke has no ends.** `skeleton._loops` closes a ring back on its start, so a
  stroke whose last point is its first is read round the ring: a span reaching past the seam
  carries on from the start, and the vertices a tent is cut at are read round the ring too
  (so a ring's width does not depend on which vertex it starts at). Cutting the window at the seam,
  as the first version of this change did, gave the seam a width jump of 0.05 to 0.12 that
  the segment-by-segment width did not have (0.84 at the worst on "Keswick" at 20 px).
- **The profile is its own module**, `letters/pen_profile.py`, split from `letters/nib.py`
  along the responsibility line (the width law, against the plate), so `nib.py` stays under
  the 400-line budget. `PROFILE_SAMPLES` moves with it.
- **The samples are evenly spaced and at most half a window apart**: a long stroke is
  sampled at `ceil(2 * length / window) + 1` points when that is more than the 24 it had.
  `stamp` already interpolates a profile of any length onto its stamps.
- Not changed: the nib's angle is still fixed to the page (issue #76), and no other mark
  (leader, span, tick, underline, pin) has a profile.

Pinned by `tests/property/test_pen_profile.py` (a V's point is never thinner than the
narrower of its legs, at any turn and nib angle; starting a closed ring one vertex on shifts
its widths and changes none; both fail on the first version of this change, which the next
two do not: turning a stroke by an angle moves no sample of its
width by more than `thin` times that angle; a pixel staircase at any angle to the nib keeps
within 0.12 of its straight line's width at thin 0.85, sample to sample and against the true
width) and `tests/unit/letters/test_pen_profile.py` (a straight stroke keeps the exact sine law; an
L climbs through the widths between, pinned; a V along the nib keeps its legs' 0.751 at
the point, where the first version read 0.15; a ring's first and last widths agree; the
sample count; "Keswick" at the issue's settings, three seeds, its window from
`nib_brushes`, has no zigzag).

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052. The tolerance bound is not
changed, no gate is loosened and the hash input does not change; the manifest hash does not
move (`340a7f6e260ee1e2-d9c56c0811177b0f`).

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.005128
map.png: identical no, differing fraction 0.002638
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Only the lettering moves, and only in its strokes' widths: placement does not read the
nib, so every name keeps its seat and `PINNED_LABELS` is unchanged. `GOLDEN_HASH` is not
re-pinned. The place pins (`tests/golden/test_places.py`), the map-styles means and
the smoke lock pass unchanged on the regenerated goldens, so none is re-pinned.

### Docs images

Every docs image and master was repainted on top of ADR 0047's, on the final code (with the
corner floor and the closed ring; the numbers here replace those of the first version). The 37 that letter
anything moved (every map card, the lettering, nib and tutorial figures, and the figures
whose grids carry lettered captions); every other entry is byte-identical. Master
differing fractions against main's masters:

| Image | Master | Image | Master |
|---|---|---|---|
| `explanation/nib-hands.webp` | 0.102170 | `tutorials/grid-nib.webp` | 0.083745 |
| `tutorials/grid-lettering.webp` | 0.073587 | `explanation/nib-angles.webp` | 0.057841 |
| `explanation/nib-backing.webp` | 0.029104 | `social-preview.jpg` | 0.021042 |
| `word.webp` | 0.016667 | `explanation/nib-ground.webp` | 0.015821 |
| `tutorials/grid-composition.webp` | 0.012333 | `tutorials/lettering.webp` | 0.010313 |
| `gallery/lettering.webp` | 0.010313 | `map-styles/bold.webp` | 0.005361 |
| `tutorials/composition.webp` | 0.005156 | `gallery/composition.webp` | 0.005156 |
| `how-to/own-shapes.webp` | 0.004245 | `painting-with-python/derwentwater.webp` | 0.004219 |
| `tutorials/grid-brush.webp` | 0.004090 | `how-to/route-ink-grid.webp` | 0.004003 |
| `reference/pigment-swatches.webp` | 0.003719 | `places/y-fenni.webp` | 0.003583 |
| `places/skye.webp` | 0.003485 | `explanation/wash-glaze.webp` | 0.003214 |
| `map-styles/pen-and-ink.webp` | 0.002997 | `map-styles/winter.webp` | 0.002534 |
| `how-to/route-ink.webp` | 0.002534 | `places/ambleside.webp` | 0.002510 |
| `gallery/route-map.webp` | 0.002510 | `tutorials/route-map.webp` | 0.002485 |
| `tutorials/grid-wash.webp` | 0.002267 | `how-to/command-line.webp` | 0.002255 |
| `reference/brush-sheet.webp` | 0.002036 | `places/oxford.webp` | 0.002025 |
| `tutorials/grid-paper.webp` | 0.001867 | `tutorials/grid-pigments.webp` | 0.001767 |
| `map-styles/sepia.webp` | 0.001365 | `places/yr-wyddfa.webp` | 0.001181 |
| `hero.webp` | 0.000780 | | |

Looked at side by side with `main` (the review images in the pull request): on
`nib-angles.webp` the top row (thin 0) is unchanged, and at 0.52 and 0.85 the strokes'
edges run smooth where they were stair-stepped; at the 90 degree cell the K and the w are
whole strokes that thin along the nib rather than strings of dots. On the map cards and the
Lynmouth label plate, at the default thin of 0.52, the names read the same at a glance:
the change is a pixel or two at the edges of the strokes, where a width that flickered now
holds.

## Mutation

Run on the changed functions as CONTRIBUTING.md says (`pen_profile`, `_point`, `_across`,
`_leg`, `_spread`, and `letters.nib._items` and `_sheet`, which `tests/mutation/scope.py`
picks up from the hunks the split touched). Every survivor of `letters.pen_profile` was
killed by a focused test or is equivalent:

- `pen_profile`: `at + taps` made `at - taps`. The taps are symmetric about zero, so the
  same boxes are summed in another order.
- `_spread`: the loop bound `min(reach, len(ring) - 1)` made `len(ring) + 1` or
  `len(ring) - 2`. Past `len - 1` an open stroke's slices are empty and a ring's roll comes
  back round to a shift already taken; `len - 2` drops only the shift to the far end, and a
  pinched sample is never an open stroke's end (there one half is empty and the other is the
  whole window, so the halves cannot beat it) nor needs it on a ring, where a roll by
  `len - 1` is the roll by -1 already taken.
- `_leg`: `>` made `>=` against `_MIN_LENGTH_PX`, which differs only on a half exactly that
  long; the empty half's 1.0 made 2.0, which `min` with the other half (at most 1) never
  picks, and both halves are empty only on a stroke of no length, which returns before.

The clip bounds of the first version (`np.clip(..., 0, total)` on each box's ends) were
made redundant by `np.interp`'s clamp and are gone, as are the running sums, and with them
their mutants. The four survivors of `letters.nib._items` are on lines this change did not
write and are equivalent: the label token renamed in the set of named inks (an unknown ink
falls back to `label` anyway) and the `float64` dtype dropped from `np.asarray` (the points
are floats). `_sheet` is unchanged here; its survivors (which paper parameters reach the
sheet) are not this change's and are left to a test of the sheet.

## Consequences

- A glyph's width along a stroke is a continuous function of its direction and of where on
  the stroke it is; a staircase near the nib's angle reads as one width.
- A tight curve, shorter than the nib is wide, has its thinnest point softened: the width
  there is the average over a nib's width of path, which is the nib's own footprint. Where
  such a curve turns through the nib's own direction, the corner floor softens it a little
  further, since within a window a curve and a corner look alike: a smooth ring of radius
  12 px under an 8 px window at thin 0.85, sampled every few tenths of a pixel, reads 0.33
  at its thinnest against 0.15 unfloored. At the profile's own spacing (about half a window)
  a sample seldom lands on the thinnest point, and the same ring reads 0.214 against 0.208.
- A sharp corner is never read thinner than both its legs at a sample on it, and the
  samples half a window either side carry that floor; a ring's width runs on round its
  seam.
- A further regeneration needs its own ADR.
