# 0060 — The pen's set-down blot stays on its stroke: a golden regeneration

Status: accepted

## Context

A pen or nib stroke starts with a blot (`ink.deposit.pool`): a Gaussian of radius
`max(width * pen_pool_radius_frac, 1.2)` render pixels and height `pool * pen_pool_gain`,
cut at three radii, laid at the stroke's first point. The radius grows with the pen, so the
blot reaches one and a half widths from the start in every direction, behind the start and
past both sides of the line. A pen wider than about two pixels then leaves a soft grey disc
round the start of every stroke; on a lettered word, where every glyph stroke starts with a
blot, it reads as a grey drop shadow 3 to 8 pixels wide (GitHub issue #39). Measured on a
2.6 px `MAJ6-e` pen at scale 2, the blot added 0.0067 of density on average to the paper
3 to 8 pixels from the ink. The docs examples worked round it with
`BrushStyle(pen_pool_radius_frac=0.15)` wherever a pen of 2 px or more lettered a word.

## Decision

- **The blot is laid only on the paper the stroke's own ink covers.** `pool(acc, b, lay, pos)`
  multiplies the Gaussian by `ink_cover(nib_cover(...))`. `nib_cover` is the share of each
  pixel the stroke's own tip passes over as it sets down: each sample of the stroke stands for
  one stamp spacing along and one sample spacing across the tip, and is splatted bilinearly as
  `deposit` lays ink, then capped at 1. It reads the samples' positions, not their weights, so
  the stroke's very start, where the pressure is still zero, is under the nib all the same.
  `ink_cover` grows that cover by a pixel each way (the most of it in each 3 by 3
  neighbourhood), because the ink itself reaches a pixel past the nib by the splat and the
  bleed, and counts a pixel whole from an eighth of that (`_FULL_COVER`), because a nib a pixel
  or two wide covers no pixel whole. The blot keeps its radius, height and three-radius cut.
- **A thin pen keeps its start.** Laid on the nib's cover alone (the first version of this
  fix), a pen 1 to 2 render px wide kept a tenth to a fifth of its blot's ink and its peak fell
  to under half; on the ink's own cover it keeps 84% to 89% of the ink it laid before and the
  same peak. What it loses is the Gaussian more than a pixel beside its line and behind its
  start. Measured with `MAJ6-e` on a straight 70 px stroke at scale 2, the blot's ink against
  `main`'s (15.47 at 1 to 2 px, its whole Gaussian):

  | Render width | `main` | nib cover only | ink cover (this) | Peak, `main` / nib / ink |
  |---|---|---|---|---|
  | 1 px | 15.47 | 1.60 | 13.00 | 1.71 / 0.38 / 1.71 |
  | 1.5 px | 15.47 | 2.32 | 13.53 | 1.71 / 0.52 / 1.71 |
  | 2 px | 15.47 | 2.98 | 13.70 | 1.71 / 0.63 / 1.71 |
  | 3 px | 24.17 | 5.76 | 19.85 | 1.71 / 0.94 / 1.71 |
  | 5.2 px | 72.49 | 18.88 | 46.97 | 1.71 / 1.34 / 1.71 |

  Of `main`'s ink at 1 to 2 px, 12.97 lay on the pixels the line's own ink darkens past 0.2;
  this lays 12.55 to 12.97 there. A wider pen keeps the ink its blot laid on its line (40.08
  of `main`'s 40.17 at 5.2 px) and loses the ring round it, which was the fault. Holding the whole of `main`'s total would mean laying the
  ink that sat beside the line on the line itself, darker than the blot's own centre ever was,
  or spreading it along the line past the three-radius cut, which brings back the square end
  that ADR 0036 (P7.V6) removed; neither is done.
- **The cover counts the set-down only.** `nib_cover` slices the samples to the stamps no
  further along the path than the blot's window reaches from the start (plus the tip's widest
  offset) before it masks and splats them, so a stroke that comes back over its own start
  later does not add to the cover, and a long stroke's cover costs what a short one's does.
  It splats with one `np.bincount` on the window with a pixel's margin, not through `deposit`.
- The fix is in the pool, not in the brush style: `pen_pool_radius_frac` and `pen_pool_gain`
  keep their meaning and defaults, and no theme changes.
- The examples' work-around goes: `examples/word.py`, `composition.py`, `how_to_own_shapes.py`,
  `nib_stages.py` and `tutorial_grids.py` letter with the default `BrushStyle()`, and the
  tutorial's quoted code follows.

Pinned by `tests/property/test_stamp.py` (at any pen width from 1 to 8 display pixels, on any
path, the blot lays no ink more than 3 px past the stroke's own ink: the zero-weight samples
at the start, the splat's pixel and `ink_cover`'s pixel), `tests/unit/ink/test_stamp_pool.py`
(a 2.6 px pen adds nothing to the paper 3 to 8 px from its ink; a pen 1 to 2 render px wide
lays 80% to 100% of the 15.468 its blot laid before; a stroke starting 80 px off the plate in
one axis inks the plate and lays no blot) and `tests/unit/ink/test_deposit.py` (along its own
stroke, in each direction, a wide blot still fades to under 1.5% of its peak at the end of its
span and stops there, reaches the plate's first row and column, keeps its 1.2 px floor radius
and scales with pool times gain; beside the stroke it lays nothing; `nib_cover` holds the
paper its samples stand for and caps a pixel passed over twice at 1; `ink_cover` grows the
cover by one pixel and counts an eighth whole).

### Cost

`stamp` on 400 short glyph-like `MAJ6-e` strokes (8 to 40 px, 220 px plate, best of 7, the
machine shared): `main` 0.59 to 0.61 ms a stroke; the first version of this fix 0.69 to
0.75 ms (+21%); this one 0.66 to 0.69 ms (+13%). The rest of the cost is the cover's splat
and mask on the set-down's samples, about 30 µs a stroke.

### Mutation testing

Run on `ink.deposit.pool`, `ink.deposit.nib_cover`, `ink.deposit.ink_cover` and
`ink.stamp.stamp`, after the tests below were added; 29 survived, none in `ink_cover`.
`pool` 48 (`or` to `and` in the empty-window return) is not equivalent: a stroke starting
more than three radii off the plate in one axis only reached `nib_cover` with a negative
window and raised; `test_a_stroke_from_far_off_the_plate_in_one_axis_lays_no_blot` kills it.
`nib_cover` 28 (no set-down slice) is killed by
`test_a_stroke_that_comes_back_over_its_start_does_not_widen_the_blot`. The survivors:

- Equivalent. `pool` 49, 50: `<=` to `<` in the empty-window return lets an empty window
  through, which adds nothing. `pool` 68, `nib_cover` 141: float64 in place of float32, the
  last bit only. `nib_cover` 52, 61: the floor of 1 on `len(t) - 1` and `m_hi - 1` raised to
  2; a stamped stroke has at least three stamps and more than two samples across. `nib_cover`
  66, 69, 70, 73: `>`/`<` to `>=`/`<=` on the mask, which differ only for a sample exactly on
  the window's edge. `nib_cover` 140: `reshape(-2, ...)` reads as `reshape(-1, ...)`.
- Not equivalent, not killed: the set-down's reach. `nib_cover` 4, 6, 11, 16 to 19, 24 to 27,
  35, 36 move the arc length the slice stops at by a pixel or a stamp, or widen it on one axis;
  on a path that does not come back to its start inside the window, any reach at least the
  window's lays the same cover, and only a path that curls back within a pixel of the reach
  would tell them apart. 67 and 71 drop samples in the window's first two columns or rows,
  where the Gaussian is under 1.1% of its centre and the test strokes lay no ink.
- `stamp` 8: the pressure's random phase drawn over a narrower range is still a random phase.
  112: `pool >= 0` calls `pool` for a zero pool, which adds zero.

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052. The tolerance bound is not changed,
no gate is loosened and the hash input does not change; the manifest hash does not move
(`340a7f6e260ee1e2-d9c56c0811177b0f`), so `GOLDEN_HASH` is not re-pinned. The smoke lock's
`pen` hash is re-pinned; its `paper` and `wash` do not move.

### Lynmouth compare, against the committed goldens

Painted on this branch merged with `main` at `b78a1bb` (ADR 0055 included), against the
goldens committed there:

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.000343
pen.webp: identical no, differing fraction 0.000038
labels-centreline.webp: identical no, differing fraction 0.003472
map.png: identical no, differing fraction 0.002113
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

`PINNED_LABELS`, the place pins and the map-styles means do not move. The wash plate moves
where a lane's blot sat on it. On the label plate most of the measured change is the grey
lift round the leaders' pins and the glyph starts, now gone, while the starts themselves keep
their dark touch.

### Docs images

Every docs image and master was repainted with `make_docs_images.py` on the merge with
`main` at `b78a1bb` (ADR 0055's images under it). The 48 docs images that draw a pooled pen
or nib stroke moved, with their 48 masters (12 of them past the 0.005 parity fraction, all
with the change at stroke starts); the other 22 are byte-identical. The largest master
fractions:

| Master | Fraction | Max delta | Master | Fraction | Max delta |
|---|---|---|---|---|---|
| `explanation/nib-hands.png` | 0.031207 | 30 | `explanation/nib-angles.png` | 0.029773 | 27 |
| `social-preview.png` | 0.019757 | 76 | `reference/brush-sheet.png` | 0.016051 | 155 |
| `tutorials/grid-lettering.png` | 0.013841 | 11 | `places/oxford.png` | 0.013220 | 37 |
| `places/y-fenni.png` | 0.012987 | 64 | `tutorials/grid-nib.png` | 0.012225 | 9 |
| `curves/kaleidoscope.png` | 0.007465 | 48 | `hero.png` | 0.003533 | 159 |

Looked at side by side with `main`: on the brush sheet the 12 px pen swatches lose the round
dark disc at their start and begin as a dark touch inside the line; the lettered words and
the leaders lose the faint grey cloud round their glyph starts and pins, and the glyph
starts keep their dark touch. On the hero the soft blue disc round the Brathay's first point
at the lower left goes, because it was this blot laid past the river's line; the wet brush's
heavy dab and its comma-shaped tail, which GitHub issue #55 records, are the river brush's
own load and are not changed here (PR #137 takes them). The lossy WebP docs images show
change across the whole picture at one or two levels, which is the encoder, not the paint:
the masters' changes are local to the stroke starts.

## Consequences

- A pen's blot can no longer show past its own line at any width, so a wide pen letters
  with the library's defaults.
- A stroke that starts where another's ink already lies is darkened only on its own ink.
- A pen 1 to 2 px wide lays about 85% of the ink its blot laid before, all of it on its line;
  the rest, beside the line and behind its start, is the price of laying nothing off it.
- A further regeneration needs its own ADR.
