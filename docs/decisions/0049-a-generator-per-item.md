# 0048 — A generator per item: the eighth golden regeneration

Status: accepted

## Context

The painter and the lettering drew from random generators shared down a sequence of
independent items (GitHub issue #61): one generator deformed every cover ring in
`deform_ring`, one `bloom_rng` placed the blooms of every cover class, the lake and the sea,
one `ink_rng` stamped every watercourse, coast and road, and one label generator stamped
every stroke of every ink group in `nib_plate`. A discrete decision early in a sequence (a
median test, an argmax, an `int()` or a `round()`) that flips under a sub-pixel change alters
how much the generator consumes, so everything drawn after it changes. Bloom placement was
non-local as well: its candidate centres were drawn by rank among the thick pixels in
raster order, so a coast that moved by under a pixel relocated blooms in open sea.

ADR 0006 measured the cost: dropping the seam's 0.1 m rounding moved each point by at most
0.05 m, yet moved 0.207 of the wash plate, 0.042 of the labels-centreline plate and 0.193 of
the composed map.

## Decision

- **Every item draws from a keyed generator of its own** (`ink.keyed`, GLOSSARY "keyed
  generator"). `keyed_rng(seed, *words)` seeds a `SeedSequence` from the consumer's style
  seed and words naming the item; strings are hashed with BLAKE2b, never Python's salted
  `hash`, so a stream is the same on every run and platform. The streams are pinned
  literals in `tests/unit/ink/test_keyed.py`.
- **An item is named by what it is, not by where it falls in a sequence**, as the issue
  proposed. The painter has no stable ids at the ink layer, so a line or ring is named by
  its own points (`line_key`): its first point, its last point and the point halfway along
  its length, each rounded to a grid (1 m for a cover ring, 1 render pixel for a stroke).
  Rounding keeps a last-bit difference in the arithmetic from renaming an item; measuring
  the halfway point along the length keeps ways chained with repeated joints
  (`chain_lines`) named as the line drawn whole. A stroke whose key repeats an earlier
  one's in the same `InkPad.lay` call is told apart by its count.
- `deform_ring` keys its generator from the ring; `Deform` carries a seed, not a generator.
- `InkPad.lay(items, seed, profiles)` takes a seed and keys each stroke. This covers the
  lettering (`nib_plate`, the label seed), the watercourses, coast and roads
  (`ink_seed`), and the route pen (`PaintJob.pen_seed`, `ink_seed + 1` as before). A
  second lay of the same marks, as the backing wash's `keep` pad does, now lays the same
  bristles as the first.
- **Blooms are placed by local position.** `PaintJob.bloom(cov, name)` keys each wash's
  seed from `bloom_seed` and the wash's name (its cover class, `lake`, `sea` or `pale`);
  `Blooms` carries that seed. In `bloom`, every thick pixel draws one lot from its own
  position (`uniform_at`, splitmix64 of the seed and the pixel index), weighted by its
  density (Efraimidis and Spirakis' weighted sampling), and the `count` highest lots are
  the centres. Each bloom draws its size and warp from a generator
  keyed by its centre. The base radius is rounded to the pixel, so an edge that moves
  elsewhere does not resize every bloom and, through its box, redraw every warp.
- `PaintJob` loses `bloom_rng`, `deform_rng`, `ink_rng` and `pen_rng`. Only `dither_rng`
  stays shared: the wood's texture and dabs and the plates' dither draw a fixed amount from
  it for a given card, so no item's change shifts it.
- Not changed: the hand's per-label generator (`Hand.generator`), the sheet, the fluid pass
  and the sea's variation are seeded once per field already, and the cover's wet field and
  the bleed's blur are deterministic.

Pinned by `tests/unit/ink/test_keyed.py`: lengthening one stroke leaves the stroke laid
after it as it was (to a 1e-4 last-bit bound: the bleed's blur runs sums across the whole
pad); a ring moved by 0.05 m leaves the next ring's deformation identical; trimming one far
edge of a wash leaves the blooms more than 60 px from it identical.

Two unit tests measured a statistic over particular random draws and were re-measured on
the new streams, their bars unchanged: `test_pad.shared_repeat` averages over 10 strokes
instead of 6 (at 6, MAJ2-a's organic repeat read 0.194 against the 0.15 bar; at 10 every
class reads 0.10 or under, and at 16 0.08 or under, so the 6-stroke figure was noise), and
`test_a_bloom_lifts_the_centre_and_deposits_it_at_the_front` lays 6 blooms instead of 3,
because the three the new lots place on that square fall short of the core's darker-ring
bar (0.678 against 0.683); six clear all three of its bars.

## Golden regeneration (the eighth)

Process as ADR 0036. The tolerance bound is not changed, no gate is loosened and the hash
input does not change.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.375456
pen.webp: identical no, differing fraction 0.010426
labels-centreline.webp: identical no, differing fraction 0.047971
map.png: identical no, differing fraction 0.363315
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Every plate drawn from a shared generator moves; the paper, seeded once per sheet, does
not. `PINNED_LABELS` is unchanged, the manifest hash does not move and `GOLDEN_HASH` is not
re-pinned: placement draws nothing from the painter's generators. Looked at side by side,
the change is random texture only: the cover outlines wobble differently, the roads,
rivers and route lay other bristles, and the sea's blooms sit in other places. The
composition, the colours and every label's seat are as they were.

A first cut weighted the bloom lots by density to the 24th power, which matches the old
draw's mean density rank on the wash test's square (0.960 against 0.961) but on the
Lynmouth sea put every bloom against the coast, where the pooled rim is denser than any of
the body; the power was dropped to 1 (a pixel's weight is its density) after looking at
it, and the blooms went back into open water. The smoke lock's `pen` and `wash` and the
committed `tests/golden/smoke/wash.webp` are re-pinned; `paper` does not move.

### Docs images

Every docs image and master was repainted with `make_docs_images.py` on top of ADR 0047's images and compared with them. 38 of the 70 masters moved: every image that paints a wash with blooms or deformed cover, or lays strokes through an `InkPad` (map cards, lettering, brush and nib figures); the rest, painted without the pad or the painter, are byte-identical. The compare exits 1, as a regeneration that moves random texture must: the parity bound is the regression gate, and the moved images are the new goldens. Master differing fractions against ADR 0047's masters:

| Master | Fraction | Master | Fraction |
|---|---|---|---|
| `places/skye.png` | 0.678524 | `places/y-fenni.png` | 0.577336 |
| `places/oxford.png` | 0.565674 | `places/ambleside.png` | 0.449415 |
| `gallery/route-map.png` | 0.449415 | `hero.png` | 0.442812 |
| `social-preview.png` | 0.432882 | `how-to/command-line.png` | 0.397101 |
| `how-to/route-ink-grid.png` | 0.352328 | `map-styles/bold.png` | 0.299635 |
| `places/yr-wyddfa.png` | 0.277685 | `tutorials/route-map.png` | 0.261306 |
| `how-to/route-ink.png` | 0.259381 | `map-styles/winter.png` | 0.256725 |
| `map-styles/sepia.png` | 0.246467 | `map-styles/pen-and-ink.png` | 0.213231 |
| `explanation/nib-hands.png` | 0.134071 | `tutorials/grid-nib.png` | 0.129075 |
| `tutorials/grid-lettering.png` | 0.124855 | `explanation/nib-angles.png` | 0.109811 |
| `explanation/nib-backing.png` | 0.060338 | `explanation/nib-centreline.png` | 0.056610 |
| `tutorials/grid-composition.png` | 0.035367 | `explanation/nib-ground.png` | 0.031924 |
| `word.png` | 0.029414 | `reference/pigment-swatches.png` | 0.024014 |
| `tutorials/lettering.png` | 0.022344 | `gallery/lettering.png` | 0.022344 |
| `tutorials/grid-brush.png` | 0.017508 | `reference/brush-sheet.png` | 0.015625 |
| `tutorials/composition.png` | 0.013776 | `gallery/composition.png` | 0.013776 |
| `painting-with-python/derwentwater.png` | 0.012839 | `how-to/own-shapes.png` | 0.012292 |
| `explanation/wash-glaze.png` | 0.011667 | `tutorials/grid-paper.png` | 0.009367 |
| `tutorials/grid-wash.png` | 0.008467 | `tutorials/grid-pigments.png` | 0.008133 |

Looked at side by side with ADR 0047's masters (Skye, Y Fenni, the Lynmouth map): the change is random texture. The sea's blooms and the cover's wobble sit in other places and the strokes lay other bristles; the composition, the colours and every label's seat are as they were. No label moved seat.

## Consequences

- A change to one ring, stroke or wash's edge moves only that item's pixels, plus the edge
  antialiasing round it; a later regeneration that moves one feature should move little
  else.
- Two strokes, rings or blooms that round to the same key are told apart only by their
  count; two identical items in different calls lay the same randomness, which is the
  wanted behaviour for the backing wash's second lay.
- A further regeneration needs its own ADR.
