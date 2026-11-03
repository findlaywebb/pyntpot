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

Pinned by `tests/property/test_pen_profile.py`: no sample of a V is thinner than its
narrower leg, at any turn, nib angle, leg lengths (2 to 40 px, shorter and longer than the
window) and sample count (2 to 90, odd and even); turning the nib by up to 0.01 rad on any
stroke of up to five straight pieces moves no sample by more than `thin` times the turn;
turning a pixel staircase moves no sample by more than `thin` times the turn; a pixel
staircase at any angle to the nib keeps within 0.12 of its straight line's width at thin
0.85, sample to sample and against the true width, under a 12 px window, and within 0.3
under the 5.46 px window a 52 px glyph has under the default nib; starting a closed ring
one vertex on shifts its widths and changes none. And by `tests/unit/letters/test_pen_profile.py`: a
straight stroke keeps the exact sine law; an L climbs through the widths between, pinned,
unchanged from the first version; a ±45 degree V under a flat nib keeps its legs' 0.751 at
every sample at 24, 25, 60 and 61 samples and with its point off centre (the first version
read 0.471 at 24 and 0.673 at 61); a closed V started 3.5 px past its point reads 0.751 at
both ends (0.7377 before); a hairline running into a 2 px kink (`TestHairlineKink`) moves by
at most `thin` times a 1.6e-4 rad turn of the nib (0.29 before), climbs into the kink by
pinned widths with no step, and is untouched (0.1873) more than half a window before the
kink and under 0.3 to 1 px before it (0.487 before); a ring shorter than the tent is cut at
every lap of its vertices, pinned; a ring's first and last widths agree; the sample count;
"Keswick" at the issue's settings, three seeds, its window from `nib_brushes`, has no zigzag;
nor do Keswick, Ambleside, Aberystwyth and Machynlleth at 14, 20, 30 and 52 px under the
default nib's own narrower window at thin 0.85; a window under a quarter pixel is read as
a quarter pixel.
`tests/benchmarks/test_letters.py::test_the_nib_widths_of_a_name` times the profile along
every glyph stroke of a long name, which no other benchmark runs.

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052, on `main` with ADR 0059 merged.
The tolerance bound is not changed, no gate is loosened and the hash input does not change;
the manifest hash does not move (`340a7f6e260ee1e2-d9c56c0811177b0f`).

### Lynmouth compare, against `main`'s goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.005672
map.png: identical no, differing fraction 0.002459
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Only the lettering moves, and only in its strokes' widths: placement does not read the
nib, so every name keeps its seat and `PINNED_LABELS` is unchanged. `GOLDEN_HASH` is not
re-pinned. The goldens were regenerated in place with `make_golden.py` and compared with the
paint they came from (`--require-identical all --require-hash equal`): every output
byte-identical. The place pins (`tests/golden/test_places.py`), the map-styles means and
the smoke lock pass unchanged on the regenerated goldens, so none is re-pinned.

### Docs images

Every docs image and master was repainted with `make_docs_images.py` on the merged code.
The 37 that letter anything moved (every map card, the lettering, nib and tutorial
figures, and the figures whose grids carry lettered captions); every other entry is
byte-identical. Master differing fractions against `main`'s masters:

| Image | Master | Image | Master |
|---|---|---|---|
| `explanation/nib-hands.webp` | 0.103299 | `tutorials/grid-nib.webp` | 0.084203 |
| `tutorials/grid-lettering.webp` | 0.073877 | `explanation/nib-angles.webp` | 0.057538 |
| `explanation/nib-backing.webp` | 0.029543 | `social-preview.jpg` | 0.021076 |
| `word.webp` | 0.016821 | `explanation/nib-ground.webp` | 0.015727 |
| `tutorials/grid-composition.webp` | 0.012633 | `gallery/lettering.webp` | 0.010156 |
| `tutorials/lettering.webp` | 0.010156 | `gallery/composition.webp` | 0.005156 |
| `tutorials/composition.webp` | 0.005156 | `map-styles/bold.webp` | 0.005044 |
| `how-to/own-shapes.webp` | 0.004427 | `painting-with-python/derwentwater.webp` | 0.004089 |
| `tutorials/grid-brush.webp` | 0.004052 | `reference/pigment-swatches.webp` | 0.003943 |
| `how-to/route-ink-grid.webp` | 0.003881 | `places/y-fenni.webp` | 0.003485 |
| `explanation/wash-glaze.webp` | 0.003333 | `places/skye.webp` | 0.003135 |
| `map-styles/pen-and-ink.webp` | 0.002997 | `gallery/route-map.webp` | 0.002461 |
| `places/ambleside.webp` | 0.002461 | `how-to/route-ink.webp` | 0.002412 |
| `tutorials/route-map.webp` | 0.002388 | `tutorials/grid-wash.webp` | 0.002367 |
| `map-styles/winter.webp` | 0.002290 | `tutorials/grid-paper.webp` | 0.002067 |
| `how-to/command-line.webp` | 0.002062 | `reference/brush-sheet.webp` | 0.001941 |
| `places/oxford.webp` | 0.001908 | `tutorials/grid-pigments.webp` | 0.001667 |
| `map-styles/sepia.webp` | 0.001340 | `places/yr-wyddfa.webp` | 0.001160 |
| `hero.webp` | 0.000780 |  |  |

The map cards' masters move by 0.000780 to 0.005044.
Looked at side by side with `main` (the review images in the pull request): on
`nib-angles.webp` the top row (thin 0) is unchanged, and at 0.52 and 0.85 the strokes'
edges run smooth where they were stair-stepped; at the 90 degree cell the K and the w are
whole strokes that thin along the nib rather than strings of dots. On the map cards and the
Lynmouth label plate, at the default thin of 0.52, the names read the same at a glance:
the change is a pixel or two at the edges of the strokes, where a width that flickered now
holds.

## Mutation

Run on the changed functions of `letters.pen_profile` as CONTRIBUTING.md says
(`pen_profile`, `_cuts`, `_reached`, `_point`, `_across`, `_side`). `letters.nib._items` and
`_sheet`, which `tests/mutation/scope.py` also picks up from the split's hunks, are not
changed by this rework; their survivors are those the first version listed (the label token
in the set of named inks, the `float64` dtype of `np.asarray`, and which paper parameters
reach the sheet), none on a line this change wrote. Every other survivor is killed or
equivalent:

- `_cuts`, the ring's lap count `ceil((end[-1] - start[0]) / cum[-1])` made `*`, `end[+1]`,
  `end[-2]`, `start[1]`, `cum[+1]` or `cum[-2]`, and the laps' range made one longer. Each
  gives at least as many laps as the tent needs (`ceil(15 W / 16 / length)` either way, where
  the count taken is about twice that), and a surplus lap only adds vertices outside every
  tent, which `searchsorted` never picks. The one mutant that gave too few (`end + start`)
  is killed by the ring shorter than the tent.
- `_cuts`, `searchsorted`'s `side` dropped (to its default) on either bound, `- first` made
  `+ first`, `slot < count` made `<=`, and the index clamp made `len - 2`. Each only adds or
  drops a cut at or past a tent's edge, or repeats one; a cut there leaves one side empty,
  and an empty side reads full, so that cut's floor is the whole tent's and never decides.
- `_reached`: `<=` made `<`. A box end exactly on the cut is the cut's own point either way.
- `_side`: `>` made `>=` against `_MIN_LENGTH_PX`, which differs only on a side exactly that
  long; the empty side's 1.0 made 2.0, which `min` with the other side (at most 1) never
  picks, and both sides are empty only on a stroke of no length, which returns before.

The first version's `_spread` and `_leg`, and with them their mutants, are gone.

## Consequences

- A glyph's width along a stroke is a continuous function of its direction and of the nib's
  angle. A staircase reads as one width only where the window spans enough steps for their
  turns to cancel. Over 20,000 random staircases at thin 0.85 (heading, nib and length 40 to
  160 px as the property draws them), every one keeps within 0.12 of its straight line's
  width (sample to sample and against the true width; 0.10 at the worst) under a 12 px
  window. Under the 5.46 px window of a 52 px glyph at the default nib (a 1.47 px one at
  14 px), 5.7 % step by more than 0.12 between samples and 8.7 % by either measure, 0.24 at
  the worst found; under 3.4 px, 31 % and 38 %, 0.33 at the worst. So the 0.12 bound is a
  property of a wide nib, not of every nib, and at the production window what holds is the
  looser 0.3 and, on written names, no zigzag of wide, thin, wide.
- The width depends on where the stroke's vertices fall as well as on where the samples
  do, since the floor is read at every vertex a tent reaches: a collinear point added to a
  stroke can move a sample by up to 0.15, and the density of a skeleton's vertices moves a
  bowl's thinnest point by about 0.07.
- A window narrower than a quarter render pixel is read as a quarter pixel
  (`_MIN_WINDOW_PX`), so a vanishing window cannot ask for samples without bound; no glyph
  brush is that narrow (`brush_from_id` makes none under 0.4 display px, at least 0.4
  render px at a whole supersample), so nothing painted moves.
- A stroke of two straight legs is nowhere thinner than its narrower leg, however the
  samples fall; the floor costs no truncated reach and no gate.
- A floor reaches as far as a sample's tent does (15/16 of a window either side), not half a
  window: just past half a window a V's tent still reaches round its point, and the whole
  tent there reads 0.66 against legs of 0.751, so the floor must reach it. It lifts a sample
  only where the two sides of a cut lie either side of the nib, and never above the narrower,
  so a straight hairline is not lifted until its tent reaches past the turn's first vertex;
  on the kink pinned above, nothing more than half a window out moves.
- A tight curve, shorter than the nib is wide, has its thinnest point softened: the width
  there is the average over a nib's width of path, which is the nib's own footprint. Where
  such a curve turns through the nib's own direction, the cut sides straddle the nib and
  soften it a little further, since within a window a curve and a corner look alike: a
  smooth ring of radius 12 px under an 8 px window at thin 0.85 reads 0.333 at its thinnest
  against 0.15 unfloored, every few tenths of a pixel or at 24 samples (0.337); the first
  version read 0.336 and 0.279, by where the samples fell.
- The profile costs more: along every glyph stroke of a long name
  (`test_the_nib_widths_of_a_name`'s workload) it takes 7.5 ms against the first version's
  4.8, from the cuts. End to end, `test_maps.py::test_letter` took 172.8 ms at best of three
  12-round runs against `main`'s 169.4 (2 %), on a shared four-core machine whose medians
  overlapped.
- A further regeneration needs its own ADR.
