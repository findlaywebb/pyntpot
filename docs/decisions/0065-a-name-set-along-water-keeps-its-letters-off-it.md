# 0065 — A name set along water keeps its letters off it: a golden regeneration

Status: accepted

## Context

ADR 0047 priced a flat name for the lakes and watercourse strokes under it and its backing
wash, and left a name set along a line unpriced: issue #52 kept that, with "Cherwell" on the
Oxford card. The Cherwell runs in several channels there, and its name, lifted clear of the
one channel it follows (`placement_lift.lift_px`), was written across the next: on the docs
card the lower "Cherwell" sat over a parallel channel, and on the fixture card the upper one
had its last letters on the channel beside it. "Brathay" on the Ambleside cards and "Rothay"
on `map-styles/bold.webp` sat on a side stream the same way. Nothing in a window's cost
(`placement_along._ground_cost`) knew where the water was.

The issue's second case, "Magdalen Bridge" across three streets, is not fixed here (see
Consequences).

## Decision

- **The letters of a name set along a line are priced on the water under them.**
  `placement_along.ink_band` samples the band the pen writes, `INK_ASCENT_CAPS` and
  `INK_DESCENT_CAPS` of the type size about `lift_middle`, as three offset lines of the
  window; `placement_water.ink_on_water` is the share of those points on a lake or under a
  stroke, and `along_water_cost` charges `WATER_UNDER_COST` (160), in full once
  `UNDER_FULL_SHARE` (a tenth) of the ink is on water, the price a flat name's letters pay.
- **Points, not boxes.** The placer's boxes along a window are axis-aligned and, on a
  diagonal reach, their corners claim water the ribbon of letters never touches; the band
  is tested point by point where it lies.
- **Its own stroke counts, and there is no wash term.** The lift already clears the
  followed channel on a straight reach, so ink on it means the line bends under the letters;
  the backing wash of a name beside its own water always reaches it, so pricing the wash
  would charge every window alike.
- Not discounted by `RIVER_GROUND_FRAC`, for the reason overlap is not: a letter under a
  stroke is a letter painted over, wherever the river runs. A name written on the water
  (`in_water`) is not priced.

Pinned by `tests/unit/maps/lettering/test_placement_water.py`: `TestInkOnWater` (a stroke, a
lake and its island, no water) and a "Cherwell" set along one of two parallel channels
keeping its ink off the other, which fails with the price at zero.

## Golden regeneration

Process as ADR 0036, with ADR 0052's review images. The tolerance bound is not changed, no
gate is loosened and the hash input does not change.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical yes, differing fraction 0.000000
map.png: identical yes, differing fraction 0.000000
manifest hash: 3976d23ae248ca86-d9c56c0811177b0f here, 3976d23ae248ca86-d9c56c0811177b0f in the goldens
```

No Lynmouth river name lies on water, so nothing moves; `PINNED_LABELS` and `GOLDEN_HASH`
are unchanged.

### Docs images

Repainted on `main` after ADR 0049 (a generator per item), ADR 0053, ADR 0063 and ADR 0064
were merged in. Every docs image was repainted with `make_docs_images.py --compare` against
`main`'s; eight moved, and only they:

| Image | Image changed | Master changed |
|---|---|---|
| `places/oxford.webp` | 0.187411 | 0.057165 |
| `map-styles/bold.webp` | 0.118500 | 0.010551 |
| `tutorials/route-map.webp` | 0.100760 | 0.004922 |
| `map-styles/sepia.webp` | 0.085729 | 0.004727 |
| `map-styles/winter.webp` | 0.071785 | 0.005117 |
| `how-to/route-ink.webp` | 0.069737 | 0.004922 |
| `hero.webp` | 0.020017 | 0.003850 |
| `map-styles/pen-and-ink.webp` | 0.017225 | 0.005044 |

The masters' changes are local to the names that move. The WebP images' larger, widespread
fractions are faint speckle at a channel delta of a few levels, where the lossy encoder
re-quantises the paper and washes around those names; the paint under them is unchanged.

Looked at side by side with `main`: on Oxford the lower "Cherwell" leaves the parallel
channel it was written over for the meadow on the other side of its own, and the upper one
and "Thames" shift along their water; "Magdalen Bridge" then takes the seat east of its pin
with a short leader, in place of the seat south east of it with a long one, and "A4158"
moves down beside it. The bridge's move was not there when this change was painted on the
earlier `main`; painting this change on `main` without ADR 0064 moves it the same way, so it
comes from the change meeting `main`'s earlier merges (ADRs 0049, 0053 and 0063), not from
ADR 0064's leader price. ADR
0064's own Oxford moves ("Christ Church", "Radcliffe Camera", "The Bridge of Sighs") are
unchanged by this change. On the Ambleside cards (the hero, the map styles, the route-map
tutorial and the route-ink how-to) "Brathay" moves off the side stream onto clear paper beside
it, and on `map-styles/bold.webp` "Rothay" moves off a channel to sit beside it. No other
name moves. The place pins and the map-styles means did not move.

## Consequences

- A name set along a line keeps its letters off the lakes and strokes where its line
  offers a dry window; it is a price, so a river whose every window is wet still letters.
- "Magdalen Bridge" stays across streets on Oxford (its new seat east of the pin lies over
  "A4158" and the streets beside it), so issue #52 stays open for it.
  Counting the roads under a seat (the first in full, each further one at half, three at
  most) was tried in this window and moved no name there: every seat within `LEADER_RUNGS`
  of the bridge's pin lies across three streets or on the Cherwell and its meadow, so the
  count raised every seat alike and only shifted names on other cards. It needs seats
  further out, which is the placement tuning feature's leader pricing (#113).
- A further regeneration needs its own ADR.
