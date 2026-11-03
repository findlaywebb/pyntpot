# 0056 — Terminal tails kept and crossings written through: a golden regeneration

Status: accepted

## Context

The centreline route thins a glyph to a skeleton, walks it into chains and prunes the short
spurs thinning grows (`letters.skeleton`, `letters.trace`, ADR 0036's P7.V4). The pruning
kept a short branch only when it ran straight on from another branch at its junction, so
four glyphs of the shipped hand were wrong (GitHub issue #43):

- `D`, `Q` and `3` lost their terminal tails: the stem of the `D` below its bowl (a 6 pixel
  branch on the 128 pixel grid), the tail of the `Q` where it leaves the bowl (9 pixels,
  hung off a crossing thinned into two forks 3 pixels apart), the tongue of the `3`
  (9 pixels). Each left skeleton pixels 0.031 to 0.072 em from any stroke.
- `8` kept a bridge: thinning forked its waist twice, 6 pixels apart, and the run between
  the forks was drawn as a stroke of its own, 0.047 em long, beside two bowls that did not
  join through the crossing.

`TestJoined` checked every letter and figure but these four.

## Decision

- **A spur that leaves its junction's ink ends a stroke and stays.** `prune` takes the ink's
  inscribed radius (`reach`, the chamfer distance `trace.centrelines` already has) and keeps
  a short branch whose free end lies further from its junction than `TERMINAL_OF_DISC`
  (0.5) of the junction's radius. A fork thinning grows stays inside the disc of the
  junction it grew from. Over every glyph of the shipped hand only six branches were
  pruned; their free ends lie 0.17 (`?`, `!`), 0.29 (`w`), 0.70 (`D`), 1.31 (`Q`) and 1.35
  (`3`) of their junction's radius away, so the rule keeps the three tails and still
  prunes the dot forks and the fork in the `w`'s first valley.
- **Two forks joined by a run shorter than a stroke are one crossing.** `join_through` takes
  `bridge`, twice the glyph's measured half-width; a run between two junctions of three arms
  or more that is shorter than it is dropped and the two junctions merged
  (`junction._bridged`), so the arms pair through the crossing as one junction's would. A
  short run to a free end is never a bridge.
- **A run that comes back to its junction straight on is closed.** Joined through its
  waist, the `8` is one run that leaves the crossing and returns to it; `junction._closed`
  makes it a ring when its two ends meet straight on (`THROUGH_DOT`), so both diagonals of
  the crossing are drawn.
- `skeleton.py` would have passed its 400-line budget, so `prune` and its helpers move
  verbatim, with the new rule, to `letters.spurs`.

Besides the four, the same rules change six more glyphs of the shipped hand, all for the
better: `X` and `x` are two strokes crossing (were three, one diagonal broken at a bridge),
`$` and `&` lose a broken stroke the same way, `#` joins its four crossings (ten strokes
to eight), and the stroke of `R`'s bowl and leg is 0.047 em shorter where they meet.

Pinned by `tests/unit/letters/test_skeleton_glyphs.py` (`TestJoined` now checks every letter
and figure; `TestTerminals` pins each changed glyph's stroke and free-end counts, `D` 1 and
1, `Q` 2 and 2, `3` 3 and 3, `8` 1 and 0 as one closed ring, `X` and `x` 2 and 4, `w` 2 and
2) and `tests/unit/letters/test_junction.py` (an `X` with a bridge is two diagonals; a
bridge as long as a stroke stays; a short run to a free end is no bridge; an `8` of two bowls
is one ring; a spur stays once it leaves half its junction's disc, on the edge it goes; the
limit, the order of the chains and the carry-on rule).

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052. The tolerance bound is not
changed, no gate is loosened and the hash input does not change; the manifest hash does not
move (`340a7f6e260ee1e2-d9c56c0811177b0f`).

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.023244
map.png: identical no, differing fraction 0.015170
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Only the lettering moves. Placement measures a name by the face's advances, not its
strokes, so `labels.txt` is unchanged and every name keeps its seat; `PINNED_LABELS` is
unchanged and `GOLDEN_HASH` is not re-pinned. The plate moves more than the glyphs that
changed would explain because the letters' strokes draw from the plate's one generator
(issue #61): a glyph with a stroke more or fewer shifts every draw after it, so the
leaders and pins drawn after the first changed glyph take another wander. The place pins
(`tests/golden/test_places.py`), the map-styles means and the smoke lock pass unchanged on
the regenerated goldens, so none is re-pinned.

### Docs images

Every docs image and master was repainted on top of ADR 0047's. The 24 that letter a name or
caption containing a changed glyph, or a mark drawn after one, moved; every other entry is
byte-identical. Master differing fractions against main's masters:

| Image | Master | Image | Master |
|---|---|---|---|
| `places/skye.webp` | 0.033898 | `reference/brush-sheet.webp` | 0.023911 |
| `how-to/command-line.webp` | 0.023411 | `places/oxford.webp` | 0.021865 |
| `places/yr-wyddfa.webp` | 0.019115 | `places/y-fenni.webp` | 0.018477 |
| `tutorials/grid-brush.webp` | 0.017164 | `tutorials/grid-nib.webp` | 0.011859 |
| `tutorials/grid-wash.webp` | 0.011033 | `tutorials/grid-pigments.webp` | 0.010767 |
| `explanation/nib-angles.webp` | 0.009886 | `tutorials/grid-paper.webp` | 0.008667 |
| `map-styles/bold.webp` | 0.005653 | `map-styles/pen-and-ink.webp` | 0.005458 |
| `how-to/route-ink.webp` | 0.004873 | `tutorials/route-map.webp` | 0.004751 |
| `map-styles/winter.webp` | 0.004703 | `places/ambleside.webp` | 0.004435 |
| `gallery/route-map.webp` | 0.004435 | `map-styles/sepia.webp` | 0.004069 |
| `tutorials/grid-composition.webp` | 0.003033 | `painting-with-python/derwentwater.webp` | 0.002422 |
| `social-preview.jpg` | 0.000937 | `hero.webp` | 0.000512 |

Looked at side by side with `main` (the review images in the pull request): the names keep
their seats on every card. Where a name has a `D`, `Q`, `3`, `8`, `X` or `R` the letter is
written whole (the `D`'s stem reaches the foot of the letter, the `8` has no stub across
its waist), a pixel or two of difference at map size; the leaders and pin rings after it on
the same plate are redrawn with a slightly different wander, a few display pixels at most.
The paint under the names is unchanged.

## Consequences

- A traced glyph reaches every terminal of its outline, and a shallow crossing is written as
  two strokes through it, not four arms and a stub.
- The rule reads the ink's own radius, so it holds for another face at the same raster; a
  face whose forks reach further than half their junction's disc would keep them.
- A further regeneration needs its own ADR.
