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

- **The blot is laid only where the stroke's set-down lays ink.** `pool(acc, b, lay, pos, wgt)`
  multiplies the Gaussian by `blot_share(nib_cover(...), width)`. `nib_cover` is the share of
  each pixel the stroke's own tip passes over as it sets down: each sample that lays ink
  (`wgt > 0`) stands for one stamp spacing along and one sample spacing across the tip, and
  is splatted bilinearly as `deposit` lays ink, then capped at 1. A sample at zero pressure,
  as at the very start, lays no ink and covers nothing, so every pixel the cover reaches is
  one the stroke inks. `blot_share` counts a pixel whole from an eighth of cover
  (`_FULL_COVER`) and in proportion under it, so the blot keeps its full height inside the
  line. The blot keeps its radius, height and three-radius cut.
- **A thin nib's cover is grown by a pixel, fading out from 2.5 to 3.5 render px.** A nib a
  pixel or two wide covers no pixel whole, and on its own cover alone its blot keeps about
  two fifths of `main`'s ink, so at 2.5 render px and under the cover is grown by a pixel
  each way (`ink_cover`, the most of it in each 3 by 3 neighbourhood). That reaches at most a
  pixel and a half past the line's ink, which on a line a pixel or two wide is the line's own
  soft edge. From 2.5 to 3.5 px (`_GROW_FADE_PX`) the share is the own cover's plus the grown
  band's times a weight `((3.5 - width) / 1) ** 1.5` (`_GROW_FADE_POWER`), and at 3.5 px and
  wider nothing is grown, so the blot lies on no paper the stroke does not ink. **A pen under
  3.5 render px carries a faint rim a pixel wide by design**: 3.1 to 3.9 of blot ink off its
  stroke at 1 to 2.5 px, 2.00 at 3 px, 0.79 at 3.25 px, and none from 3.5 px.

  The fade replaces a step. An earlier version grew every nib under 3 px whole and none from
  3 px: the blot's ink then fell 35% at 3 px (19.50 at 2.99 px, 12.69 at 3.0), so a 2.99 px
  pen laid more than a 3.5 px one. The grown band holds more ink the wider the nib (5.3 at
  2.5 px, 8.7 at 3.5), so its weight falling in a straight line takes it away faster than the
  own cover adds ink and the blot's ink dips by 0.06 just under 3.5 px, and a smoothstep dips
  by 0.12 at 3.15 px; falling as the 1.5 power, it rises at every 0.05 px step from 1 to 6 px
  on that line, and on 120 random sub-pixel offsets and seeds it falls no more than 2.1% a
  step, which is the stroke's own wobble. A version before that grew every nib's cover, and
  counted the inkless samples at the start: it put a rim of up to 1.4 px at full blot height
  round every wide pen's start, and on a start that turns back on itself reached 3.4 px past
  the ink. Measured with `MAJ6-e` on a straight 70 px stroke at scale 2 (y 30.3, seed 9), the
  blot's ink, then the ink it lays on pixels the stroke without it does not ink; "grown
  whole" grows every nib's cover, "own cover" grows none:

  | Render width | Blot ink: `main` / grown whole / own cover / this | Off the stroke's ink: `main` / grown whole / this |
  |---|---|---|
  | 1 px | 15.47 / 12.49 / 5.98 / 12.49 | 6.34 / 3.37 / 3.37 |
  | 1.5 px | 15.47 / 13.10 / 7.21 / 13.10 | 5.49 / 3.13 / 3.13 |
  | 2 px | 15.47 / 13.41 / 8.04 / 13.41 | 5.49 / 3.43 / 3.43 |
  | 2.5 px | 16.78 / 14.56 / 9.22 / 14.56 | 6.15 / 3.93 / 3.93 |
  | 2.75 px | 20.31 / 17.02 / 10.87 / 14.87 | 8.03 / 4.74 / 3.08 |
  | 3 px | 24.17 / 19.63 / 12.69 / 15.15 | 10.20 / 5.66 / 2.00 |
  | 3.25 px | 28.34 / 22.36 / 14.54 / 15.52 | 12.28 / 6.30 / 0.79 |
  | 3.5 px | 32.89 / 25.10 / 16.40 / 16.40 | 14.61 / 6.82 / 0 |
  | 4 px | 42.89 / 30.81 / 20.36 / 20.36 | 20.79 / 8.71 / 0 |
  | 5.2 px | 72.49 / 46.58 / 32.36 / 32.36 | 37.84 / 11.94 / 0 |
  | 12 px | 385.23 / 175.76 / 140.61 / 140.61 | 238.88 / 29.41 / 0 |

  A pen 1 to 2 px wide keeps 81% to 87% of `main`'s blot on this line, and 76% at worst over
  sub-pixel offsets (1 px, the line 0.73 px below a pixel's centre), with its 1.71 peak. A
  wider pen keeps the ink its blot laid on its line's dark core (123.09 of `main`'s 123.09 at
  12 px) and loses the ring round it, which was the fault; between 2.5 and 3.5 px the blot's
  total holds at 14.6 to 16.4 while `main`'s doubles, because what goes is the ink beside the
  line. Holding the whole of `main`'s total would mean laying the ink that sat beside the
  line on the line itself, darker than the blot's own centre ever was, or spreading it along
  the line past the three-radius cut, which brings back the square end that ADR 0036 (P7.V6)
  removed; neither is done.
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
path, the blot lays no ink more than 3 px past the stroke's own ink, with the turning start
that once reached 3.4 px as an explicit example; from 1 to 6 render px in 0.05 px steps, at
any sub-pixel offset and seed, the blot's ink falls no more than 3% a step),
`tests/unit/ink/test_stamp_pool.py` (a pen of 5 or 12 render px adds under 0.01 of density
on average 1 to 2 px out from its ink, which is the bleed of its darker start, where `main`
added 0.038 and 0.133, and under 0.0001 3 to 8 px out; a pen 3.5, 4 or 12 px wide adds no
blot ink to a pixel its stroke does not ink; a pen 1 to 2 render px wide lays 74% to 100% of
the 15.468 its blot laid before at five sub-pixel offsets, the worst measured 76.0%; a stroke
starting 80 px off the plate in one axis inks the plate and lays no blot; a loop back over
its start, 8 px across or 30, does not widen the blot) and `tests/unit/ink/test_deposit.py`
(along its own stroke, in each direction, a wide blot still fades to under 1.5% of its peak
at the end of its span and stops there, reaches the plate's first row and column, keeps its
1.2 px floor radius and scales with pool times gain; beside the stroke it lays nothing;
`nib_cover` holds the paper its samples stand for, with five samples across or two, caps a
pixel passed over twice at 1, leaves out a sample that lays no ink and counts a diagonal
set-down to the window's far corner; `blot_share` grows a nib of 2.5 px whole, one of 3.5 px
not at all, and between them weights the grown rim by the 1.5 power; `ink_cover` grows the
cover by one pixel and counts an eighth whole).

### Cost

`stamp` on 400 short glyph-like `MAJ6-e` strokes (8 to 40 px, 220 px plate, best of 7, the
machine shared): `main` 0.59 to 0.61 ms a stroke; the first version of this fix 0.69 to
0.75 ms (+21%); this one 0.66 to 0.69 ms (+13%). The rest of the cost is the cover's splat
and mask on the set-down's samples, about 30 µs a stroke.

### Mutation

Run on every function the branch changes (`ink.deposit.pool`, `blot_share`, `ink_cover`,
`nib_cover`, `ink.stamp.stamp` and `ink.stamp._width`) with the tests above: 501 mutants,
474 killed, 27 survived, none in `ink_cover`. Killed by tests added for them: `pool` 48 (`or`
to `and` in the empty-window return: a stroke starting more than three radii off the plate
in one axis reached `nib_cover` with a negative window and raised), by
`test_a_stroke_from_far_off_the_plate_in_one_axis_lays_no_blot`; `nib_cover` 28 (no
set-down slice), by `test_a_stroke_that_comes_back_over_its_start_does_not_widen_the_blot`;
`nib_cover` 17, 19, 25 and 27 (the reach made the start's coordinate plus the window's, 60
px or more), by `test_a_tight_loop_back_over_its_start_does_not_widen_the_blot`, a loop back
behind its start 44 px on; `nib_cover` 11 (the reach's y term dropped), by
`test_a_diagonal_set_down_covers_the_window_s_far_corner`; `nib_cover` 61 (`max(m_hi - 1,
2)`), by `test_a_nib_two_samples_across_holds_the_paper_they_stand_for`. 36 (the tip's
offset taken off the reach), a survivor in the review before, is now killed too. The
survivors, each with its reason:

- Equivalent. `pool` 49, 50: `<=` to `<` in the empty-window return lets an empty window
  through, which adds nothing. `pool` 68, `nib_cover` 142: float64 in place of float32, the
  last bit only, and the sum is float32 again in the accumulator. `nib_cover` 141:
  `reshape(-2, ...)` reads as `reshape(-1, ...)`. `nib_cover` 52: the floor of 1 on
  `len(t) - 1` raised to 2; a stamped stroke has at least three stamps. `nib_cover` 67, 70,
  71, 74: `>`/`<` to `>=`/`<=` on the mask, which differ only for a sample exactly on the
  margin's edge, whose splat then lands its weight on the cropped margin with a zero share.
  `blot_share` 23: `/ (hi - lo)` to `* (hi - lo)`, the same while the fade is 1 px wide.
- Not equivalent, not killed: the set-down's reach by a pixel or a stamp. `nib_cover` 4, 6
  (the start read from the second stamp's x or y, half a stamp on), 16, 18, 24, 26 (the reach
  a pixel or two shorter or longer on one side) and 35 (`searchsorted` on the left, one stamp
  fewer where a stamp sits exactly on the reach): on a path that does not come back to its
  start inside the window, any reach at least the window's lays the same cover, and only a
  path that curls back within a pixel of the reach would tell them apart.
- `stamp` 8: the pressure's random phase drawn over a narrower range is still a random
  phase. 112: `pool >= 0` calls `pool` for a zero pool, which adds zero.
- `_width` 9, 10, 25, 27, 29, 39, 47: in lines this branch does not change (only a comment
  in `_width` moved, which put the function in scope), as they are on `main`, so outside this
  fix: 9 and 10 move the guard on a width profile's length, 25 its first knot, 27, 29 and 39
  a dtype, and 47 drops the profile's `spent`.

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052. The tolerance bound is not changed,
no gate is loosened and the hash input does not change; the manifest hash does not move
(`340a7f6e260ee1e2-d9c56c0811177b0f`), so `GOLDEN_HASH` is not re-pinned. The smoke lock's
`pen` hash is re-pinned; its `paper` and `wash` do not move.

### Lynmouth compare, against the committed goldens

Painted on this branch merged with `main` at `5f14f6b` (ADR 0061, the nib's eased reload,
included), against the goldens committed on `main` there:

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.000803
pen.webp: identical no, differing fraction 0.000149
labels-centreline.webp: identical no, differing fraction 0.004179
map.png: identical no, differing fraction 0.002800
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

The goldens were then regenerated in place and compared with that paint
(`--require-identical all --require-hash equal`): identical. The fade from 2.5 to 3.5 px was
painted again on the same tree and is byte-identical to that paint on every Lynmouth plate
and the map, because no Lynmouth pen is between 2.5 and 3.5 render px wide; the fractions
above stand, and the smoke lock does not move with it.

`PINNED_LABELS`, the place pins and the map-styles means do not move. The wash plate moves
where a lane's blot sat on it. On the label plate most of the measured change is the grey
lift round the leaders' pins and the glyph starts, now gone, while the starts themselves keep
their dark touch.

### Docs images

Every docs image and master was repainted with `make_docs_images.py` on the merge with
`main` at `5f14f6b` (ADR 0061's images under it) and diffed with `main`'s. The 48 docs
images that draw a pooled pen or nib stroke moved, with their 48 masters (17 of them past
the 0.005 parity fraction, all with the change at stroke starts); the other 22 are
byte-identical. The fade from 2.5 to 3.5 px moved 8 of them again (kaleidoscope, lissajous,
the two nib lines, own shapes, the two trees and the brush sheet), each master by under
0.006 of its pixels, where a pen between 2.5 and 3.5 px wide starts. The largest master
fractions against `main`:

| Master | Fraction | Max delta | Master | Fraction | Max delta |
|---|---|---|---|---|---|
| `explanation/nib-hands.png` | 0.024870 | 34 | `explanation/nib-angles.png` | 0.022727 | 32 |
| `social-preview.png` | 0.019965 | 77 | `reference/brush-sheet.png` | 0.017945 | 173 |
| `places/oxford.png` | 0.017543 | 50 | `places/y-fenni.png` | 0.016491 | 77 |
| `reference/pigment-swatches.png` | 0.010305 | 16 | `tutorials/grid-nib.png` | 0.009112 | 15 |
| `curves/kaleidoscope.png` | 0.008872 | 83 | `map-styles/bold.png` | 0.008480 | 20 |

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

- A pen 3.5 render px wide or wider lays its blot on no paper its own stroke does not ink, so
  a wide pen letters with the library's defaults. A thinner pen's blot keeps a faint rim at
  most a pixel and a half past its line's ink, inside the line's soft edge, fading out from
  2.5 to 3.5 px.
- The blot's ink rises with the pen's width with no step: from 14.56 at 2.5 px through 15.15
  at 3 px to 16.40 at 3.5 px.
- A stroke that starts where another's ink already lies is darkened only on its own ink.
- A pen 1 to 2 px wide lays 76% to 87% of the ink its blot laid before; the rest, more than a
  pixel and a half beside the line and behind its start, is the price of laying nothing off
  it.
- A further regeneration needs its own ADR.
