# 0066 — The backing wash fades out from the letters: a golden regeneration

Status: accepted

## Context

`label_wash` lifts the paint under a name towards the paper's colour so the ink reads on
dark ground (`letters.nib._backing_wash`, ADR 0008's backing wash). On the Yr Wyddfa card it
showed as a pale lozenge behind "Llyn Llydaw" and "Glaslyn" and a pale band along their
leaders, and round "A4086" and "Crib Goch" (GitHub issue #49). Reproduced on `main` before
any change: the description "box" was out of date, the shape already followed the word
block, not its rectangle, but the patch was there.

The cause was the shape of the lift, not its outline. The blob was the distance from the ink,
blurred, then `* 1.6` and clipped, which makes a flat body over the whole word block and the
gaps between its letters; that went through `wash`, whose edge is the blurred mask
thresholded (a step) with a pooled rim (`pool=0.3`) at it. A flat, uniformly pale body with a
denser rim is a patch with an edge: on paint dark enough for the darkness gate to let the
lift through at full strength, a lozenge. Measured on a line of ink on dark paint, the old
lift held about 0.33 alpha out to a third of a reach and then dropped 0.069 a pixel, a fifth
of its peak.

## Decision

- **The lift is strongest at the letters and fades out from them.** Its strength is the
  distance falloff squared, `(1 - near / reach)²`, blurred by a third of the reach as before,
  with no `* 1.6` plateau; under `_FEATHER_FLOOR` (0.02) it is nothing, so the blur's tail
  leaves no stray alpha out on the paper.
- **Its peak is as strong as the old box's.** The alpha is `label_wash_alpha` times
  `_LIFT_GAIN` (1.57): the squared fall-off holds less of the wash at the letters than the
  plateau did, and the gain gives that back at the peak without giving back the plateau or
  the rim.
- **The wash gives it grain, not an edge.** `wash` is laid over everything within
  `_GRAIN_REACH` (2.5) reaches of the ink, where the feather is already nothing, with no
  pool, and its density is multiplied by the feather: the granulated body on the paper's own
  pits stays, the thresholded edge and the rim fall where nothing is drawn.
- Unchanged: the darkness gate (`label_wash_dark_floor`), `label_wash_alpha`,
  `label_wash_spread` and every style field, the colour, and which marks ask for the wash
  (the furniture still does; taking it off is the placement tuning feature's, #113).

Without the gain the lift was weaker than it had been round the letters (about 0.21 alpha
beside them against 0.33), and the names read with less contrast than on `main`. The
maintainer compared four variants of the lift on the Yr Wyddfa card and chose the stronger
peak (variant A): the same reach and the same squared curve, with the peak raised by 1.57.
Contrast of the two lake names against the paint round them, and the steepest step at the
wash's edge (the gradient, times 1000):

| Lift | "Llyn Llydaw" | "Glaslyn" | Max wash-edge gradient ×1000 |
|---|---|---|---|
| `main` (the box) | 0.323 | 0.350 | 22 |
| Squared fall-off, no gain | 0.290 | 0.320 | |
| Variant A, gain 1.57 (chosen) | 0.317 | 0.347 | 9.3 |

Variant A gives back nearly all of `main`'s contrast while its edge is under half as steep
as the box's, so it shows no box and no rim.

Pinned by `tests/unit/letters/test_nib.py::TestBackingWash`, on one line of ink over dark
paint: half a reach out the lift is under half its strength beside the letters (fails on
the old plateau), no step outwards is more than a tenth of the peak (fails on the old edge),
nothing is left two reaches out, the peak above the ink is the old box's (0.3365 there) to
within five per cent (fails without the gain), and its strength, grain and weight are
pinned literals.

### Mutation testing

`pyntpot.letters.nib.x__backing_wash*`, 108 mutants with the gain: 89 killed (the gain's
own mutant among them), 19 survived, named in the PR description. Fifteen are equivalent:
clip bounds that cannot bind (the feather, the gate and the alpha are multiplied into an
alpha clipped at zero, and none can pass one; the alpha stays under `label_wash_alpha`
times the gain, 0.785), a comparison at an exact float, a dtype, and the wash's pool, whose
rim lies where the feather is zero. Four are a test gap left open: the reach at a scale other than one and its 2 px
floor, and `gran_gamma`, which the unit test's default `PaperStyle` (fibre off) never reads.

## Golden regeneration

Process as ADR 0036, with ADR 0052's review images. The tolerance bound is not changed, no
gate is loosened and the hash input does not change.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.058664
map.png: identical no, differing fraction 0.012675
manifest hash: 3976d23ae248ca86-d9c56c0811177b0f here, 3976d23ae248ca86-d9c56c0811177b0f in the goldens
```

Only the label plate and the map move, round every name; no name moves and `PINNED_LABELS`
and `GOLDEN_HASH` are unchanged. The goldens were regenerated with `make_golden.py`.

### Docs images

Every docs image was repainted with `repaint.py` on top of `main`'s images after ADR 0049 (a generator per item, #124); the sixteen that letter a map or show the
backing wash moved, and only they (`map-styles/pen-and-ink.webp` lays no wash):

| Image | Image changed | Master changed |
|---|---|---|
| `explanation/nib-backing.webp` | 0.286125 | 0.286591 |
| `places/y-fenni.webp` | 0.266865 | 0.041160 |
| `places/ambleside.webp` | 0.265503 | 0.079898 |
| `gallery/route-map.webp` | 0.265503 | 0.079898 |
| `places/skye.webp` | 0.259556 | 0.088843 |
| `places/oxford.webp` | 0.213606 | 0.053368 |
| `places/yr-wyddfa.webp` | 0.185109 | 0.065314 |
| `map-styles/sepia.webp` | 0.172168 | 0.020370 |
| `map-styles/bold.webp` | 0.142917 | 0.024342 |
| `hero.webp` | 0.141558 | 0.027047 |
| `how-to/command-line.webp` | 0.114339 | 0.012650 |
| `tutorials/route-map.webp` | 0.112722 | 0.009284 |
| `how-to/route-ink.webp` | 0.111884 | 0.009211 |
| `map-styles/winter.webp` | 0.096848 | 0.010161 |
| `tutorials/grid-composition.webp` | 0.067068 | 0.038267 |
| `social-preview.jpg` | 0.035526 | 0.022222 |

The largest channel change in a docs image is 68, under the letters. Looked at side by side with `main`: on
Yr Wyddfa the pale lozenges behind "Llyn Llydaw" and "Glaslyn", the bands along their
leaders and the patches round "A4086" and "Crib Goch" are gone, and the paint shows up to the
letters; the same on every card, most on Skye's dark sea. `explanation/nib-backing.webp` now
shows a lift close round "Keswick" instead of a pale patch behind it, and its text says so.
The place pins did not move.

## Consequences

- A name's backing wash has no edge and no body of its own; on dark paint the name reads by
  its ink with the paint lifted close round it.
- A further regeneration needs its own ADR.
