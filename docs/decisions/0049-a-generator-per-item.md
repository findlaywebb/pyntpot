# 0049 — A generator per item: the eighth golden regeneration

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
  proposed. The painter has no stable ids at the ink layer, so an item is named by its own
  geometry, rounded to a grid (1 m for a cover ring, 1 render pixel for a stroke) so a
  last-bit difference in the arithmetic does not rename it:
  - A stroke (`line_key`) by its first point, its last point and the point halfway along
    its length. Measuring the halfway point along the length keeps ways chained with
    repeated joints (`chain_lines`) named as the line drawn whole. A stroke whose key
    repeats an earlier one's in the same `InkPad.lay` call is told apart by its count.
  - A cover ring by `line_key` too. A closed ring's first point is its last, so its key
    reads only its start and halfway points, and a nudge to its points moves each of them
    by all of the nudge.
- **A steadier ring key was built, measured and not taken.** Naming a ring by its
  centroid and the root of its signed area (sums over every edge, so a nudge moves them
  by a small share of it, and independent of the start point and the sampling) cut the
  renames sharply: on 4000 random lumpy rings, points nudged independently by up to
  0.05 m renamed 0.303 of the rings under `line_key` and 0.035 under the centroid key;
  the whole ring shifted by up to 0.05 m renamed 0.097 and 0.048. Adding a word to
  `line_key` instead (the area or the bounding box) could not have cut the flips: a key
  flips when any of its words flips, so every word added is one more chance to. It was
  dropped because re-seeding every ring moved the Y Fenni card's cover enough that its
  lettering, which reads the plates, seated two leaders across each other, failing
  `test_places.test_a_focus_place_paints_from_its_cache_alone[y-fenni]` (main and this
  branch with `line_key` pass it). That is the placer's sensitivity to cover texture,
  not a fault in the key, and this branch keeps main's lettering code as it is. The
  trade-off taken: a sub-0.05 m nudge renames about three rings in ten, each of which
  repaints only its own outline; no other ring moves. A steadier ring key can come back
  once leader crossing does not hang on the cover's random wobble.
- `deform_ring` keys its generator from the ring; `Deform` carries a seed, not a generator.
- `InkPad.lay(items, seed, profiles)` takes a seed and keys each stroke. This covers the
  lettering (`nib_plate`, the label seed), the watercourses, coast and roads
  (`ink_seed`), and the route pen (`PaintJob.pen_seed`, `ink_seed + 1` as before). A
  second lay of the same marks, as the backing wash's `keep` pad does, now lays the same
  bristles as the first.
- **Blooms move to their own module, `ink.bloom`** (`bloom`, `bloom_radius`, `highest`,
  `Blooms`), out of `ink.wash`, which had grown past the 400-line budget; `wash` calls it.
- **Blooms are placed by local position.** `PaintJob.bloom(cov, name)` keys each wash's
  seed from `bloom_seed` and the wash's name (its cover class, `lake`, `sea` or `pale`);
  `Blooms` carries that seed. In `bloom`, every thick pixel draws one lot from its own
  position (`uniform_at`, splitmix64 of the seed and the pixel index), weighted by its
  density (Efraimidis and Spirakis' weighted sampling), and the `count` highest lots are
  the centres. Each bloom draws its size and warp from a generator keyed by its centre.
- **The highest lots are found by partition** (`bloom.highest`): `np.argpartition` finds the
  `count`-th highest lot, the lots above it and the lowest-index ties at it are kept, and
  only those are sorted by lot and index. That is exactly the head of the stable full sort
  the first cut used, which sorted every thick pixel to keep five: 183 ms against 7 ms on
  1.5 million lots. The Lynmouth goldens regenerated byte-identical from that change alone.
  `tests/benchmarks/test_ink.py::test_laying_a_deformed_wash_with_blooms` times a deformed
  outline filled and washed with the flow rim and blooms, which no benchmark did before.
- **The base bloom radius is held on quarter-octave steps** (`bloom.bloom_radius`,
  `2 ** (k / 4)`). The radius follows the root of the wash's area, so an edge that moves a
  pixel anywhere changes it, and a changed radius resizes every bloom and, through its
  box, redraws every warp. Rounded to the pixel, as the first cut had it, the radius
  flipped at every half pixel: over square-ish washes 100 to 1225 px across with a quarter
  to all of one side moved a pixel, 0.26 of the moves resized the blooms. On quarter
  octaves 0.049 did for washes up to 400 px and 0.015 above. A step is a fifth of the
  radius, so the held radius is within a tenth of the raw one, inside the 0.7 to 1.3 each
  bloom already draws its own size from; the step does not show. Deriving the radius from
  something steadier than the area was considered and not taken: the area is what the
  bloom's size is meant to follow, and any other measure of the wash moves with its edge
  too.
- `PaintJob` loses `bloom_rng`, `deform_rng`, `ink_rng` and `pen_rng`. Only `dither_rng`
  stays shared: the wood's texture and dabs and the plates' dither draw a fixed amount from
  it for a given card, so no item's change shifts it.
- Not changed: the hand's per-label generator (`Hand.generator`), the sheet, the fluid pass
  and the sea's variation are seeded once per field already, and the cover's wet field and
  the bleed's blur are deterministic.

### Bloom placement changed on purpose

Bloom placement changes character as well as seed, deliberately. The old draw took 24
candidates from the thick pixels and seated the bloom on the densest of them, which put
blooms on the pooled rim, near the edge of the wash, almost every time: the rim is denser
than any of the body. The new draw gives every thick pixel a lot weighted by its density,
so the rim is favoured only in proportion to how much denser it is, and the blooms spread
more evenly through the body. A first cut weighted the lots by density to the 24th power,
which matches the old draw's mean density rank on the wash test's square (0.960 against
0.961) but on the Lynmouth sea put every bloom against the coast; the power was dropped to
1 after looking at it, and the blooms went back into open water.

### Tests pinned and re-measured

Pinned by `tests/unit/ink/test_keyed.py`: lengthening one stroke leaves the stroke laid
after it as it was (to a 1e-4 last-bit bound: the bleed's blur runs sums across the whole
pad); a ring moved by 0.05 m leaves the next ring's deformation identical; trimming one far
edge of a wash leaves the blooms more than 60 px from it identical; and, through `wash` with
the flow rim on (whose width follows the area and whose peak is normalised), trimming 4 px
off a far edge changes the bloom's own effect more than 80 px away by under 1e-3. With the
radius rounded to the pixel that trim resized every bloom and the far effect moved by 0.30.
`tests/unit/ink/test_bloom.py` pins `bloom_radius` and checks `highest` against the full
stable sort, ties included.

Two unit tests measured a statistic over particular random draws and were re-measured on
the new streams, their bars unchanged:

- `test_pad.shared_repeat` averages over 10 strokes instead of 6. The 0.15 bar on the
  organic repeat is noise-limited at 6: across five seed bases, main at n=6 read 0.05 to
  0.171 (MAJ6-e crossed 0.15 on one base, so main passed by the luck of its base), and this
  branch at n=6 read 0.056 to 0.194. At n=10 both read 0.097 or under, and the control with
  the organic flag off still reads 0.35 to 0.67, so the test still tells the two apart. The
  bar is not moved.
- `test_a_bloom_lifts_the_centre_and_deposits_it_at_the_front` lays 6 blooms instead of 3,
  because the three the new lots place on that square fall short of the core's
  darker-ring bar (0.678 against 0.683); six clear all three of its bars.

## Golden regeneration (the eighth)

Process as ADR 0036, with the review images of ADR 0052, on the tree merged with main
(after ADRs 0050, 0051, 0055, 0059, 0060 and 0061, at `8a105db`). The
tolerance bound is not changed, no gate is loosened and the hash input does not change.

### Lynmouth compare, against main's committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.362858
pen.webp: identical no, differing fraction 0.010369
labels-centreline.webp: identical no, differing fraction 0.050960
map.png: identical no, differing fraction 0.350016
manifest hash: 3976d23ae248ca86-d9c56c0811177b0f here, 3976d23ae248ca86-d9c56c0811177b0f in the goldens
```

Every plate drawn from a shared generator moves; the paper, seeded once per sheet, does
not. The goldens were then regenerated in place with `make_golden.py` and compared with that
paint: byte-identical for every output, the hash equal on both sides. On the earlier base
(main after ADR 0048), the radius steps accounted for 0.041 of the wash, 0.003 of the
labels-centreline plate and 0.036 of the map against this branch's first cut; the partition
for none. `PINNED_LABELS` is
unchanged, the manifest hash does not move (main's ADR 0050 moved its geometry half, to
`3976d23ae248ca86`, before this merge) and `GOLDEN_HASH` is not re-pinned: placement draws
nothing from the painter's generators. Looked at side by side, the change is random
texture only: the cover outlines wobble differently, the roads, rivers and route lay other
bristles, and the sea's blooms sit in other places, spread through the water rather than
along the coast. The composition, the colours and every label's seat are as they were.
The first cut laid the "o" of "Reformed" in "Living Waters Lynton United Reformed Church"
with its counter filled, so it read as a dot; the drift fix below opens it again.
In the smoke lock, `pen` is re-pinned on the merged tree: main's set-down blot (ADR 0060)
and this branch's keyed strokes both move it. `wash` and the committed
`tests/golden/smoke/wash.webp` keep the values this branch's first cut pinned (the smoke box
lays no blooms or deformed cover, and main's changes do not reach its wash), and `paper` does
not move.

On the merged tree no counter fills. Measured as `TestCounters` measures it (the mean alpha
of the label plate, painted without the backing wash, inside each closed mark's outline
shrunk to half about its centroid), the worst glyph counter on the Lynmouth card is 0.344
inked against main's 0.407, under `TestCounters`' 0.4 bar. The three pin rings read 0.853,
0.823 and 0.331 against main's 0.724, 0.574 and 0.435: the leader's end is laid into its
pin, and laid alone, with the same keyed bristles, the rings read 0.491, 0.198 and 0.399.
That is within what the ring draws on either tree: one pin ring laid alone over 150 label
seeds reads a median of 0.313 and at most 0.698 here, and 0.317 and 0.714 on main.

### Docs images

Every docs image and master was repainted with `make_docs_images.py` on the merged tree and
compared with main's (ADR 0061's) images and masters. 38 of the 70 masters moved, with
their images: every image that paints a wash with blooms or deformed cover, or lays strokes
through an `InkPad` (map cards, lettering, brush and nib figures); the rest, painted without
the pad or the painter, are byte-identical. The compare exits 1, as a regeneration that
moves random texture must: the parity bound is the regression gate, and the moved images are
the new goldens. Master differing fractions against main's masters:

| Master | Fraction | Master | Fraction |
|---|---|---|---|
| `places/y-fenni.png` | 0.578427 | `places/skye.png` | 0.572157 |
| `places/oxford.png` | 0.561994 | `places/ambleside.png` | 0.443981 |
| `gallery/route-map.png` | 0.443981 | `hero.png` | 0.440278 |
| `social-preview.png` | 0.431632 | `how-to/command-line.png` | 0.383999 |
| `how-to/route-ink-grid.png` | 0.349837 | `map-styles/bold.png` | 0.295054 |
| `places/yr-wyddfa.png` | 0.273647 | `tutorials/route-map.png` | 0.255531 |
| `how-to/route-ink.png` | 0.253899 | `map-styles/winter.png` | 0.251706 |
| `map-styles/sepia.png` | 0.241009 | `map-styles/pen-and-ink.png` | 0.211477 |
| `explanation/nib-hands.png` | 0.134852 | `tutorials/grid-nib.png` | 0.130815 |
| `tutorials/grid-lettering.png` | 0.126014 | `explanation/nib-angles.png` | 0.111061 |
| `explanation/nib-backing.png` | 0.061247 | `explanation/nib-centreline.png` | 0.056516 |
| `tutorials/grid-composition.png` | 0.035133 | `explanation/nib-ground.png` | 0.033051 |
| `word.png` | 0.029753 | `reference/pigment-swatches.png` | 0.024462 |
| `gallery/lettering.png` | 0.022057 | `tutorials/lettering.png` | 0.022057 |
| `tutorials/grid-brush.png` | 0.017775 | `reference/brush-sheet.png` | 0.015814 |
| `gallery/composition.png` | 0.013958 | `tutorials/composition.png` | 0.013958 |
| `painting-with-python/derwentwater.png` | 0.013073 | `how-to/own-shapes.png` | 0.012448 |
| `explanation/wash-glaze.png` | 0.011905 | `tutorials/grid-paper.png` | 0.009333 |
| `tutorials/grid-wash.png` | 0.008500 | `tutorials/grid-pigments.png` | 0.008100 |

Looked at side by side with main's masters (Skye, Y Fenni, Oxford, the Lynmouth map): the
change is random texture. The sea's blooms and the cover's wobble sit in other places and
the strokes lay other bristles; the composition, the colours and every label's seat are as
they were. No label moved seat.

### The drift's shared mean is no longer rescaled

The filled "o" was not the keying. Each stroke draws from the same distribution whether its
generator is shared or keyed; the keyed draw for that glyph landed in a tail that main's
draws can reach as well. The tail is in `ink.stamp._organic_fields`: on an organic brush
with coherence, the bristles' lattice drift is smoothed across the tip and rescaled to the
spread it had. A stroke shorter than the drift's coarsest cell (584 pad pixels for the
label brush, against 130 along that "o") has a field nearly constant along it, so the
spread is mostly the bristles' differences; smoothing removes those and the rescale, about
zero, multiplied the part every bristle shares several times over, past the field's own
range of 1.6 (to 4.5 on that glyph). That part is a constant offset along the stroke's
normal: on an open stroke a shift of the line, on a closed one a change of radius. The "o" took a shift of 8.1 pad pixels
inward and its bowl closed.

Over 2000 seeds on that glyph's own stroke, the mean sideways shift was 0.58 pad pixels at
the median and over 6 for 12 seeds with the shared generator (4 of 500 keyed); 16 of 2000
label seeds filled its counter on the nib plate. Across every closed glyph the docs images
and the Lynmouth card letter (518 counters), main's shared stream filled none (its closest
left 0.52 of the bowl's core bare) and the keyed draws filled one, this "o" (the Lynmouth
card is lettered twice, in its golden and in `how-to/command-line`). So it is one draw of
an existing variation, not a change the keying made more likely, and the variation is the
fault: the rescale now acts about the stroke's own mean, which smoothing leaves where it
was. The median shift falls to 0.18, the largest over 2000 seeds to 1.9, no seed fills the
counter, and every counter on the cards keeps at least 0.64 of its core bare. A long
stroke's mean is near zero already, so its wander is as it was.

This fix landed on main on its own (issue #125, ADR 0059), and the merged tree keeps main's
`_organic_fields` and main's tests of it: `tests/unit/letters/test_nib.py::TestCounters` (a
20 px "o" at scale 2 keeps its core under 0.4 inked for 400 label seeds) and
`tests/unit/ink/test_stamp_drift.py` (a small ring's ink stays within the drift's reach of
its path over 300 seeds). So this regeneration does not move the two tree figures, which
only the drift fix moved.

## Consequences

- A change to one ring, stroke or wash's edge moves only that item's pixels, plus the edge
  antialiasing round it, unless it moves the wash's area across a radius step; a later
  regeneration that moves one feature should move little else.
- Two strokes, rings or blooms that round to the same key are told apart only by their
  count, where there is one; two identical items in different calls lay the same
  randomness, which is the wanted behaviour for the backing wash's second lay.
- A further regeneration needs its own ADR.
