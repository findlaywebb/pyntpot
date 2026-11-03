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
- **The wash gives it grain, not an edge.** `wash` is laid over everything within
  `_GRAIN_REACH` (2.5) reaches of the ink, where the feather is already nothing, with no
  pool, and its density is multiplied by the feather: the granulated body on the paper's own
  pits stays, the thresholded edge and the rim fall where nothing is drawn.
- Unchanged: the darkness gate (`label_wash_dark_floor`), `label_wash_alpha`,
  `label_wash_spread` and every style field, the colour, and which marks ask for the wash
  (the furniture still does; taking it off is the placement tuning feature's, #113).

The lift is weaker than it was between and round the letters (about 0.21 alpha beside them
against 0.33), so a name on dark paint reads with its own ink more than with a pale patch;
the maintainer's review is the check that it still reads.

Pinned by `tests/unit/letters/test_nib.py::TestBackingWash`, on one line of ink over dark
paint: half a reach out the lift is under half its strength beside the letters (fails on
the old plateau), no step outwards is more than a tenth of the peak (fails on the old edge),
nothing is left two reaches out, and its strength, grain and weight are pinned literals.

### Mutation testing

`pyntpot.letters.nib.x__backing_wash*`, 107 mutants: 88 killed, 19 survived, named in the
PR description. Fifteen are equivalent: clip bounds that cannot bind (the feather, the gate
and the alpha are multiplied into an alpha clipped at zero, and none can pass one), a
comparison at an exact float, a dtype, and the wash's pool, whose rim lies where the feather
is zero. Four are a test gap left open: the reach at a scale other than one and its 2 px
floor, and `gran_gamma`, which the unit test's default `PaperStyle` (fibre off) never reads.

## Golden regeneration

Process as ADR 0036, with ADR 0052's review images. The tolerance bound is not changed, no
gate is loosened and the hash input does not change.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.060331
map.png: identical no, differing fraction 0.023906
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Only the label plate and the map move, round every name; no name moves and `PINNED_LABELS`
and `GOLDEN_HASH` are unchanged. The goldens were regenerated with `make_golden.py`.

### Docs images

Every docs image was repainted with `repaint.py` on top of ADR 0055's images; the sixteen that letter a map or show the
backing wash moved, and only they (`map-styles/pen-and-ink.webp` lays no wash):

| Image | Image changed | Master changed |
|---|---|---|
| `places/skye.webp` | 0.400402 | 0.110495 |
| `places/yr-wyddfa.webp` | 0.294977 | 0.079811 |
| `explanation/nib-backing.webp` | 0.288514 | 0.290320 |
| `places/ambleside.webp` | 0.268159 | 0.094834 |
| `gallery/route-map.webp` | 0.268159 | 0.094834 |
| `places/oxford.webp` | 0.222926 | 0.062052 |
| `places/y-fenni.webp` | 0.198611 | 0.057886 |
| `hero.webp` | 0.149214 | 0.033967 |
| `map-styles/sepia.webp` | 0.135018 | 0.026438 |
| `map-styles/bold.webp` | 0.123947 | 0.024927 |
| `how-to/command-line.webp` | 0.119273 | 0.024613 |
| `map-styles/winter.webp` | 0.106673 | 0.013134 |
| `how-to/route-ink.webp` | 0.104167 | 0.013231 |
| `tutorials/route-map.webp` | 0.096667 | 0.013231 |
| `tutorials/grid-composition.webp` | 0.069716 | 0.038500 |
| `social-preview.jpg` | 0.038619 | 0.027465 |

The largest channel change in a docs image is 77, under the letters. Looked at side by side with `main`: on
Yr Wyddfa the pale lozenges behind "Llyn Llydaw" and "Glaslyn", the bands along their
leaders and the patches round "A4086" and "Crib Goch" are gone, and the paint shows up to the
letters; the same on every card, most on Skye's dark sea. `explanation/nib-backing.webp` now
shows a lift close round "Keswick" instead of a pale patch behind it, and its text says so.
The place pins did not move.

## Consequences

- A name's backing wash has no edge and no body of its own; on dark paint the name reads by
  its ink with the paint lifted close round it.
- A further regeneration needs its own ADR.
