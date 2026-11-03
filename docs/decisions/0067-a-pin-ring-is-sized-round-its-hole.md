# 0067 — A pin ring is sized round its hole: a golden regeneration

Status: accepted

## Context

A leader points at a pin: a small ring drawn round the thing a name is about, never a
filled dot (GitHub issue #130). `maps.lettering_furniture.pin` set the ring's centreline at
`max(size * 0.14, 2.2)` display pixels, 2.8 px at the shipped 20 px type size, and the nib
draws it with the `pin` role's pen, `MARK_WEIGHT["pin"]` times the leader pen: 1.5 times
0.85 px, 1.275 px. Half that pen falls inside the ring, so the paper left in the middle was
about 2.2 px across, and the organic brush's bristles spread a fixed distance either side of
a stroke whatever its width.

Measured as `TestCounters` in `tests/unit/letters/test_nib.py` measures a small "o" (the mean
alpha inside half the ring's radius, at render scale 2), a pin stroked alone with the default
theme over 400 seeds had a core above 0.4 on 21% of them and 0.67 at worst, a filled dot.
With the pin brush's jitter at 0 none closed, but the mean core was still 0.26: the ring was
too small for its pen. Smaller names were worse, because the floor of 2.2 px is the
centreline and the spread does not shrink with the pen: 43% closed at 14 px (worst 0.90).
On `main` the Lynmouth "Lynton and Exmoor Museum" pin was open by luck (0.38); the skeleton
change of issue #43 reshuffles the generator and closes it (0.75).

Two fixes were weighed:

- **Bound the jitter on a ring.** Scaling the pin brush's jitter down to half still closed
  4% of pins (worst 0.50), and at 0 the hole is still a quarter inked on average. It also
  takes the bristles' wander off the one mark that is meant to look drawn by hand, and the
  nib would need to know which strokes are rings.
- **Size the ring round its hole.** The ring keeps its pen, its brush, its jitter and its
  hand wander; only its radius changes, so it is drawn as before and is a little larger.

## Decision

- **The hole is sized and the pen laid outside it.** `pin(hand, lb, rng, pen_px)` puts the
  ring's centreline at `max(size * PIN_HOLE_SIZE_FRAC, PIN_HOLE_MIN_PX) + pen_px / 2`: the
  paper inside the ink has the radius the type size gives (0.14 of it, as before), and never
  less than `PIN_HOLE_MIN_PX`, 2.8 display pixels, the old shipped radius. At 20 px the ring
  goes from 2.8 to 3.44 px (23% wider); at 11 and 14 px from 2.2 to 3.15 and 3.25 px.
- **The pen width comes from the nib.** `letters.nib.mark_width_px(nib, role, size,
  outline=...)` is the width a mark of one role and type size is drawn at, in display
  pixels; `nib_brushes` now reads it, so the brush and the ring are sized from one number.
  `maps.lettering_marks.marks` and `label_marks` take the `NibStyle` (the pipeline and the
  attribution pass `style.nib`) and pass the `pin` width to `pin`.
- Not changed: the pin's weight, brush and jitter, its hand wander (0.2), its 14 sides, the
  leader, and every other mark's width (`nib_brushes` computes the same float as before).

Pinned by `tests/unit/maps/test_lettering_furniture.py`: a pin at the shipped size, weight
and brush keeps a core below 0.4 over 400 seeds (0.67 before the fix, 0.29 after); the ring
starts at the pinned radius for 11, 20 and 40 px names; a wider pen draws a wider ring round
the same hole. `TestMarkWidth` in `tests/unit/letters/test_nib.py` pins `mark_width_px` and
the brush widths `nib_brushes` makes from it.

Over 400 seeds the worst core is now 0.29 at every size tried (11, 14, 20 and 23 px), and no
seed reaches 0.4.

## Golden regeneration

Process as ADRs 0036 and 0052. The tolerance bound is not changed, no gate is loosened and
the hash input does not change; the manifest hash does not move
(`340a7f6e260ee1e2-d9c56c0811177b0f`), so `GOLDEN_HASH` is not re-pinned.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.024313
map.png: identical no, differing fraction 0.016347
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Only the lettering moves. A larger ring is a longer stroke, so the hand's wander and the
nib's bristles take more draws from their generators and every mark after a pin is drawn
from a different state (issue #61): the leaders bend another way and the strokes of later
names are redrawn, which is why the differing fraction is wider than the pins themselves.
`PINNED_LABELS` is unchanged: no name moves seat. The "Lynton and Exmoor Museum" pin and
the others round Lynton are open rings.

### Docs images

Every docs image and master was repainted with `make_docs_images.py`. The 15 that letter a
pinned name moved, with their masters, and only they; every other entry is byte-identical.
Master differing fractions against `main`'s masters:

| Image | Master | Image | Master |
|---|---|---|---|
| `places/skye.webp` | 0.052044 | `gallery/route-map.webp` | 0.039839 |
| `places/ambleside.webp` | 0.039839 | `places/y-fenni.webp` | 0.034677 |
| `places/oxford.webp` | 0.024299 | `how-to/command-line.webp` | 0.024034 |
| `places/yr-wyddfa.webp` | 0.021456 | `map-styles/bold.webp` | 0.019907 |
| `map-styles/sepia.webp` | 0.018835 | `tutorials/route-map.webp` | 0.017958 |
| `how-to/route-ink.webp` | 0.017909 | `map-styles/winter.webp` | 0.017690 |
| `social-preview.jpg` | 0.015278 | `map-styles/pen-and-ink.webp` | 0.014717 |
| `hero.webp` | 0.013865 | | |

Looked at side by side with `main`: every pin is an open ring, a little larger, and no name
moves. The leaders take other bends and the lettering's texture is redrawn, for the reason
above.

## Consequences

- A pin ring keeps an open hole whatever the seed, at any type size and for any pen the nib
  style sets, because the hole is sized first and the pen added outside it.
- A pin is about a quarter wider at the shipped size, and more on a small name.
- The leader still starts 2 px past the pin's centre (`leader`'s over-run), so on the map
  a short stub of it crosses the hole, as it did before. That stub is the leader's, drawn
  by design, and it is not what closed a ring; this decision leaves it as it is.
- `lettering_marks.marks` and `label_marks` take the nib style; a caller that letters names
  passes the one it will stroke them with.
- A further regeneration needs its own ADR.
