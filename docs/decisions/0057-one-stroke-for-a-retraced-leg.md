# 0057 — One stroke for a retraced leg: a golden regeneration (amends 0007 and 0036)

Status: accepted

## Context

ADR 0036 (P7.V7) pulled the two passes of a doubled-back route apart, two and a half stroke
widths centre to centre, so an out-and-back read as two strands with paper between them.
The round-2 map critique (GitHub issue #58) found that this is what makes a retraced leg
hard to read: on the Skye card the Armadale spur, run out and back on the A851, is drawn as
two red strokes with the brown road showing between them, three near-parallel lines, and the
Dunvegan and Fairy Pools spurs the same. A leg recorded a few metres off its first line on
the way back fared worse: `separate_strands` chose each pass's side by its direction of
travel, so a return a few pixels to the outward pass's left was pushed back across it, and
near half the gap the two landed on top of each other or crossed. The Oxford card's
out-and-back to Magdalen Bridge reads as one stroke, because it is shorter than
`STRAND_MIN_ARC` reaches and was never separated, and the critique takes that as the
reading to aim for.

## Decision

- **A stretch the route runs more than once is drawn as one stroke.**
  `strands.merge_strands` replaces `separate_strands`. Where a later pass comes within the
  reach (`STRAND_MERGE_WIDTHS`, 2.5 stroke widths, the old gap) of an earlier one, after at
  least `STRAND_MIN_ARC` reaches of path between them, each point is pulled along its own
  normal to the middle of the passes near it: the nearest point of each other pass (a run
  of nearby points with no more than `PASS_BREAK_REACHES` reaches of path in it is one
  pass), its offset across the line, summed and divided by the number of passes, this one
  included. Two passes meet halfway, three meet on their middle. The pull is eased over
  `STRAND_EASE_WIDTHS` reaches as the push was.
- A pass run on the very pixels of an earlier one is not moved, so an exact out-and-back,
  which is what the fixtures' synthetic tracks are, is drawn on its own line, once. A pass
  further off than the reach is another road and keeps its own line. The route keeps every
  point, in order: `Plates.strands` still has one point per point of `route_px`.
- `strand_gap_px` becomes `strand_merge_px` and `STRAND_GAP_WIDTHS` becomes
  `STRAND_MERGE_WIDTHS`, with the same rule for which width they read (the pen's for a pen
  route ink, the ink's otherwise). The pen plate merges by `route_pen_width_px *
  STRAND_MERGE_WIDTHS * scale` as it separated by it. Both passes are still laid on the pen
  pad; on the same pixels they are one line.
- ADR 0007 described `Plates.strands` as "the route separated where it runs twice"; it is
  now the route merged where it runs twice. The field, its type and its length are
  unchanged. ADR 0036's P7.V7 decision to keep the legs apart is withdrawn; its pen-gap rule
  (which width the pen reads) stands.

Pinned by `tests/unit/maps/test_strands.py` (an exact out-and-back is returned as it was; a
return 6 px off meets the outward leg midway; a leg run three times ends on one line; a pass
beyond the reach, a hairpin and a route that never comes back are left alone; the pull is a
ramp, not a step) and `tests/unit/maps/painter/test_pen_strands.py` (a column across an
out-and-back on the pen plate crosses one inked run).

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052. The tolerance bound is not
changed, no gate is loosened and the hash input does not change; the manifest hash does not
move (`3976d23ae248ca86-d9c56c0811177b0f`).

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical no, differing fraction 0.010347
labels-centreline.webp: identical no, differing fraction 0.000662
map.png: identical no, differing fraction 0.000828
manifest hash: 3976d23ae248ca86-d9c56c0811177b0f here, 3976d23ae248ca86-d9c56c0811177b0f in the goldens
```

The composed map moves only in the box where the Lynmouth track doubles back, which is now
one line; the lettering moves with the route it is set against. The pen plate moves along
the whole route, faintly, at the edges of its stroke: the route pen is one stroke, keyed by
its geometry (ADR 0049), so moving the doubled stretch re-keys the whole stroke's
bristles. Its strong difference is the doubled stretch.
`PINNED_LABELS` is unchanged, as are the place pins and the map-styles means. The
Lynmouth track's first points lie on a stretch it runs again, so `FIRST_STRANDS` in
`tests/unit/maps/test_pipeline_fetch_paint.py` moves by about a pixel and is re-pinned. The goldens were regenerated from that paint and every gate run on it.
`GOLDEN_HASH` is not re-pinned. Landed with ADR 0064's leader price, "Shepherd's Ice Cream" on
Y Fenni no longer crosses the route (the strand it crossed is one stroke now) and leaves
`HEMMED_LEADERS` in `tests/golden/test_places.py`.

### Docs images

Every docs image and master was repainted with `repaint.py`. The 15 that draw a route with a
retraced stretch moved, and only they; every other entry is byte-identical. Master differing
fractions against `main`:

| Image | Master | Image | Master |
|---|---|---|---|
| `how-to/route-ink-grid.webp` | 0.066544 | `places/skye.webp` | 0.019938 |
| `places/y-fenni.webp` | 0.018127 | `map-styles/bold.webp` | 0.016155 |
| `map-styles/sepia.webp` | 0.014059 | `gallery/route-map.webp` | 0.004678 |
| `places/ambleside.webp` | 0.004678 | `places/oxford.webp` | 0.003660 |
| `how-to/route-ink.webp` | 0.003436 | `map-styles/winter.webp` | 0.003289 |
| `map-styles/pen-and-ink.webp` | 0.003265 | `tutorials/route-map.webp` | 0.002973 |
| `hero.webp` | 0.002680 | `social-preview.jpg` | 0.002674 |
| `how-to/command-line.webp` | 0.002448 | | |

`how-to/route-ink-grid.webp` moves most because its six cards ink the route with a pen,
which is re-keyed along its whole length, as on the Lynmouth pen plate above.
The lossy WebP images move further than their masters (up to 0.26 of their pixels), almost
all by one to a few levels: the encoder's blocks after the moved route are coded afresh.

Looked at side by side with `main`: on Skye the Armadale spur and the Dunvegan and Fairy
Pools spurs are one red stroke over their road, and the junction where the Armadale spur
leaves the A87 no longer crosses itself; on Y Fenni the spur by the start is one stroke and
"start" moves to sit beside it; on Oxford the spur at the Bridge of Sighs is one stroke and
the Magdalen Bridge out-and-back is unchanged; on the Ambleside cards the doubled stretch into Ambleside is one stroke. The paint under
the route does not move. The names set against the route move with it where it was
doubled: on the Ambleside cards the names round the doubled stretch ("A591", "Ambleside",
"St Mary's") shift a few pixels. Painted on `main` after ADR 0049, no other name takes a
new seat.

## Consequences

- A retraced leg reads as one line, as on a hand-drawn route map; an out-and-back reads as a
  spur. What it does not show is that the leg was run twice: a route-ink treatment that says
  so (arrows, a doubled line weight) would be a feature of its own.
- A second road nearer than two and a half stroke widths to the route is drawn on the
  route's line where the route runs both, as before it was pushed off it.
- A further regeneration needs its own ADR.
