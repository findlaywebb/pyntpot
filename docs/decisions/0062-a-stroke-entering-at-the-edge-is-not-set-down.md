# 0062 — A stroke that enters at the card's edge is not set down: a golden regeneration

Status: accepted

## Context

On the Ambleside hero card (`docs/images/hero.webp`) the Brathay starts at the lower left
with a soft, wide blob, and a short piece of it by the left edge is a dark dot (GitHub issue
#55). Lowering the theme's `pen_pool_gain`, `ink_dip_mult` and the `major` override's
`pool` did not remove it, because the cause is not the setting.

`rivers_from_paths` cut each watercourse to the card with `ink.polyline.clip_line`, which
keeps or drops whole points. A river that comes in from beyond the card therefore started
at its first OSM point inside, not on the edge: the Brathay's main stroke began 61 m (about
23 plate pixels) inside the bottom edge, and a 2-point piece 16 m inside the left edge. The
stamp then treated each start as a nib set down on the paper: pressure from zero, the
set-down load (`Brush.load`) and the touch-down blot (`pool`, here 0.8 from the hero's
`major` override). A river does not start at the card's edge; it is already under way.

## Decision

- **A river is cut where it crosses the card's edge.** `ink.cut.cut_line(line, box)` splits
  a polyline into its pieces inside a rectangle, each cut on the edge where the line comes
  in or goes out (Liang and Barsky's clip per segment, each cut held exactly on the side it
  crosses), and drops a piece that only touches the box. `rivers_from_paths` uses it in
  place of `clip_line`, so a river runs to the card's edge. It is a module of its own
  because `ink/polyline.py` would pass its 400-line budget. `clip_line` is unchanged and
  still cuts roads, the coast and the vector layers.
- **A stroke that starts on or beyond the plate's edge is not set down.** `stamp` asks
  `_enters`: whether the path's first point lies within one plate pixel (`Brush.unit`) of the
  accumulator's edge, or past it. Such a stroke came in from off the paper, so it is stamped
  with no set-down load and no blot (`load` and `pool` 0). It draws from the generator
  exactly as before. The pressure still rises from the start over the brush's lift, so the
  river comes in thin at the edge, as a river cut there should. The rule is the ink's own and
  reaches any stroke so cut, not only rivers.

Pinned by `tests/unit/ink/test_cut.py` (pieces cut on the edge through each side and on a
box off the origin, a corner cut with no point inside kept, a line along an edge kept, a
first segment wholly outside skipped, a touching line dropped), `tests/property/test_polyline.py` (every piece lies in
the box and a piece's end that is not a point of the line lies on its edge),
`tests/unit/ink/test_stamp.py` (a stroke starting on each edge of the plate, or beyond it,
lays exactly what the same stroke with no load and no pool lays, and what a bare stroke lays
further in; one starting a plate pixel inside each edge is set down) and
`tests/unit/maps/test_basemap_strokes.py` (a river crossing the card's west edge starts on
it; one that runs off the south edge and back is two strokes, each cut on that edge).

### Mutation testing

Run on `ink.cut.cut_line`, `ink.cut._cut_segment`, `ink.stamp._enters` and `ink.stamp.stamp`:
274 mutants, 246 killed by the first run; the tests above then killed 16 more (every
`_enters` boundary, the set-down's load and pool, the off-origin box sides, a short segment,
an edge-hugging segment, a first segment outside, a two-point piece). 12 survive:

- `cut_line` 23 and 30 (`len(run) >= 1` for `> 1`): a run is started with its cut point and
  given its second at once, so it never holds one point.
- `_cut_segment` 59 and 67 (`step <= 0`, `step >= 0`): a zero step is handled before them.
  61 and 69 (`>=`, `<=` on `t`): a tie is a corner, where both sides give the same point.
  75 (`lo >= hi`): an equal pair is a single point, which `cut_line` drops anyway.
- `stamp` 23 (the pressure's random phase drawn over a narrower range), 127 (`pool >= 0`,
  which adds a zero blot), and 128, 138 and 140 (`pool > 1`; the blot centred on the second
  stamp's x or y): lines this branch does not change, where the blot's own tests on `main`
  stamp straight strokes with pools of at most 1.4; they are pinned on the branch for
  issue #39 (ADR 0060).

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052, on top of ADR 0059's images (main
at `4fed836`). The tolerance bound is not changed and no gate is loosened.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.070019
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.014207
map.png: identical no, differing fraction 0.067188
manifest hash: eb86b256459e2f0f-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

The manifest hash's first half moves, because the basemap's rivers move, so `GOLDEN_HASH` is
re-pinned to `eb86b256459e2f0f-d9c56c0811177b0f`. `PINNED_LABELS`, the place pins, the
map-styles means and the smoke lock do not move. Most of the wash and map change is not the
fix: rivers, the coast and roads share one generator (issue #61), and a river that now runs
to the edge is longer, draws a longer lattice and moves every later stroke's bristle
texture; strokes keep their paths and widths. The intended change is local: the East and
West Lyn and the coast-side streams now reach the card's edge. The label plate moves where
the placement prices names off the water, which now reaches the edge too.

### Docs images

Every docs image and master was repainted with `make_docs_images.py`, on top of main at
`b78a1bb`. The 16 that paint a map card moved, and only they; every other entry is
byte-identical. Master differing fractions:

| Master | Fraction | Max delta | Master | Fraction | Max delta |
|---|---|---|---|---|---|
| `places/oxford.png` | 0.318750 | 209 | `places/y-fenni.png` | 0.255004 | 192 |
| `places/skye.png` | 0.204887 | 80 | `how-to/route-ink-grid.png` | 0.145343 | 174 |
| `map-styles/bold.png` | 0.120541 | 226 | `tutorials/route-map.png` | 0.110746 | 212 |
| `how-to/route-ink.png` | 0.109771 | 212 | `map-styles/winter.png` | 0.107359 | 211 |
| `map-styles/sepia.png` | 0.100073 | 145 | `gallery/route-map.png` | 0.099172 | 210 |
| `places/ambleside.png` | 0.099172 | 210 | `map-styles/pen-and-ink.png` | 0.093348 | 146 |
| `how-to/command-line.png` | 0.090442 | 185 | `places/yr-wyddfa.png` | 0.067418 | 181 |
| `hero.png` | 0.066618 | 191 | `social-preview.png` | 0.039410 | 149 |

Looked at side by side with `main`: on the hero the soft blob where the Brathay started at the
lower left is gone and the river runs on to the bottom edge, thin where it enters; the dark
dot by the left edge is now a short line coming in from that edge. On every card, rivers that
leave the card now reach its edge instead of stopping short of it. The large fractions are
the shared-generator reshuffle above: bristle texture along rivers, the coast and roads,
which a reader sees only by flicking between the two; a few names and leaders shift by a few
pixels where the water they avoid now reaches the edge (on Oxford, "Christ Church"'s leader).

## Consequences

- A watercourse that runs off the card is drawn to the edge and enters without a blot.
- Roads are still cut by `clip_line`, so a road still stops at its last point inside the
  card and a lane there still gets its blot; cutting them at the edge is its own change.
- A further regeneration needs its own ADR.
