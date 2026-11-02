# 0047 — Names on the paper and off the water: the seventh golden regeneration

Status: accepted

## Context

On the Yr Wyddfa place card "Afon Arddu" read "fon Arddu" (GitHub issue #53). The name was
set flat, because its seven-point course bends too sharply for any reach of it to be written
along, and a flat name's box was measured without its kind's tracking while the hand writes
it with it (issue #48): 0.24 em on a river, about 30 display pixels on this name. The box
passed the paper test at x 40 to 121 and the letters ran from x 11.5, inside the 14 px torn
margin.

Measured right, the box no longer fitted west of the anchor and the name moved under it,
onto a small lake and across its own stream (issue #52). The maintainer's review also found
the landmark names round Glaslyn and Llyn Llydaw moved onto the lakes, which then read as
moved water. The water had not moved: `paint` runs before `letter` and takes nothing from
it, and the Lynmouth paper, wash and pen plates stayed byte-identical. What moved is the
backing wash (ADR 0008, `letters.nib._backing_wash`), the paper-coloured lift under every
name and its furniture, which washes out the part of a lake a name lands on. The landmarks
moved because placement is greedy in tier order: the wider river and road boxes changed the
separation term every later name is scored on, so "Afon Nant Peris" took another window and
the landmarks after it other seats.

## Decision

- **A flat name is measured as the hand writes it.** `label.kind_measure(measure_tracked,
  kind)` is the kind's tracked measure; `_place` measures both the window of a curved name
  and the box of a flat one through it. `_place` no longer takes the untracked `Measure`;
  `place` keeps it for the spans' own seats.
- **A river or road name with no seat on the paper is dropped** (`OFF_PAPER_DROPPED_KINDS`),
  rather than set in the margin; a usable window along the line beats a flat seat that is
  off the paper.
- **A flat name keeps itself and its backing wash off the water.** The backdrop and the
  terms carry `placement_water.Water`: the basemap's lake rings (even-odd, so an island is
  dry) and every watercourse stroke at its painted half width, in display pixels. A flat
  candidate pays `water_cost`: `WATER_COST` (480) for each share of its box grown by the
  wash's reach (`WASH_REACH_EM`, 0.75 em, the nib's default spread) that lies on water, and
  up to `WATER_UNDER_COST` (160) more for water under the ink itself, in full once a tenth
  of it is (`UNDER_FULL_SHARE`). The ramp matters: charged in full for any touch, a
  five-point pond grazing one serif of "Crib Goch" sent the name a long leader away and
  across Llyn Llydaw's. The swap pass prices a seat on the same terms, so a swap cannot put
  a name back on a lake. A name written on the water is not priced.
- **A river's flat name may sit beside any point of its course** (`COURSE_KINDS`,
  `COURSE_ANCHORS` = 12 points on the paper, plus its anchor), paying `ANCHOR_PULL` a pixel
  of travel, the pull a curved name already paid; the constant moves from `placement_along`
  to `placement_flat`. "Afon Arddu"'s anchor sits between its stream and a lake, with no dry
  paper within a rung of it.
- `placement.py` reached its 400-line budget, so the leader swap moves to
  `placement_leaders` (`uncross_leaders`, `reseat`), and `route_for` with
  `SPAN_OWN_ROUTE_FRAC` to `placement_costs`.
- Not changed: the backing wash still runs under the pins and leaders as well as the
  letters, as ADR 0008 records. A leader across a lake lifts a band of paper along it.
  Leaving furniture out of the wash is a one-line change (`wash=False` on the pin and
  leader marks in `lettering_marks._furniture`) but changes ADR 0008's decision, so it is
  left to its own ADR.

Pinned by `tests/unit/maps/lettering/test_placement_flat.py` (a river name set flat near
each edge is written inside its box and the paper; a name wider than the paper is dropped;
a river whose water leaves the card is named on a reach on the paper) and
`test_placement_water.py` (the water share; a landmark seated on the dry side of a lake; a
river kept off its own stroke and slid along its course to dry paper; a swap onto a lake
refused). `tests/golden/test_places.py` now also asserts, for every focus place, that no
two leaders cross and that no flat name sits on a lake.

## Golden regeneration (the seventh)

Process as ADR 0036. The tolerance bound is not changed, no gate is loosened and the hash
input does not change; the manifest hash does not move (`340a7f6e260ee1e2-d9c56c0811177b0f`).

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.027965
map.png: identical no, differing fraction 0.005091
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Only the lettering moves. `PINNED_LABELS` is unchanged. "B3234" moves left off the road
and river it sat against, and "Barbrook" moves right off the end of the water. The goldens
were regenerated in place with `make_golden.py` and compared with the paint they came from
(`--require-identical all --require-hash equal`): every output byte-identical.
`GOLDEN_HASH` is not re-pinned.

### Docs images

Every docs image and master was repainted with `make_docs_images.py` on top of ADR 0045's
images. The 15 that letter a map moved, and only they; every other entry is byte-identical.
Master differing fractions against ADR 0045's masters:

| Image | Master | Image | Master |
|---|---|---|---|
| `gallery/route-map.webp` | 0.138621 | `places/ambleside.webp` | 0.138621 |
| `places/skye.webp` | 0.104400 | `places/oxford.webp` | 0.069996 |
| `places/yr-wyddfa.webp` | 0.067590 | `social-preview.jpg` | 0.048542 |
| `map-styles/bold.webp` | 0.037183 | `hero.webp` | 0.034698 |
| `how-to/route-ink.webp` | 0.029240 | `tutorials/route-map.webp` | 0.029240 |
| `map-styles/sepia.webp` | 0.026901 | `map-styles/winter.webp` | 0.024269 |
| `map-styles/pen-and-ink.webp` | 0.023051 | `places/y-fenni.webp` | 0.022800 |
| `how-to/command-line.webp` | 0.006980 | | |

Looked at side by side with `main` and ADR 0045: on Yr Wyddfa "Afon Arddu" reads whole on
dry paper beside its stream, Crib Goch keeps its seat above the route, and Glaslyn and Llyn
Llydaw sit below their lakes with the water unwashed under the names; on Oxford, Radcliffe
Camera and Christ Church leave the stream they sat across (Christ Church now on two lines); on
Skye, Portree and "Sligachan" leave the water; on the Ambleside hero, Rydal Water, Grasmere
and Loughrigg Fell move off the lakes and becks. The paint under the names is unchanged.
The place pins and the map-styles means did not move.

## Consequences

- Every glyph of a flat name lies inside the box the placer kept on the paper.
- A flat name and its backing wash avoid lakes and watercourse strokes where the paper
  allows; it is a price, so a card with no dry seat still letters the name.
- A name set along a line is not priced on the water; issue #52 keeps that and the road
  density penalty.
- A further regeneration needs its own ADR.
