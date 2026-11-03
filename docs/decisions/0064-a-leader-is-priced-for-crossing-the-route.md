# 0064 — A leader is priced for crossing the route: a golden regeneration

Status: accepted

## Context

A callout's leader runs from its pin to its name's block. The placer priced the leader for
its length (`LEADER_COST_PX`) and for each placed box it cuts (`leader_crossings`, ADR
0036's P7.V3), and the swap pass uncrosses two leaders that meet (ADR 0047). Nothing priced
the route: a leader was free to cross the track, and on a doubled-back route to cross both
strands (GitHub issue #51). Lettering the five focus places from their fixtures on `main`,
four leaders crossed the drawn route past their own pin: on Yr Wyddfa "Garnedd Ugain" across
the descent 24 px out, on Y Fenni "Bean & Bread" five pixels from its pin, on Skye the
Thursday journal note 24 px out, and on Y Fenni "Shepherd's Ice Cream" across the second
strand. A reader follows such a line as a turn off the track, or to the wrong side of it.

The note's other cases are already fixed: the label crossings by P7.V3 and the crossed
leaders by ADR 0047's swap and its `test_places` check.

## Decision

- **A leader is charged for each crossing of the route past its pin.**
  `placement_costs.leader_route_crossings(start, end, segments)` counts the segments of the
  drawn route (`Backdrop.strands`, unthinned) a leader meets, half open along the route so a
  leader through a route point counts once. A crossing within `LEADER_ROUTE_SLACK_PX` (4 px)
  of the pin is not counted: that is the pin's ring (never under 2.2 px) and half the route's
  pen, the track through a pin set on it.
- `LEADER_CROSS_ROUTE_COST` (`placement_flat`) is a crossing's price: `ROAD_CROSS_COST`, 90,
  as `LEADER_CROSS_LABEL_COST` is. It is a price and not a ban: a pin hemmed in by the route
  or the roads on its own side still has to be named. Priced at `ROUTE_ON_COST` (260) it
  cleared "Bean & Bread" but sent it and "Shepherd's Ice Cream" onto long leaders running
  side by side inside the loop, the Shepherd's one still across a strand, which read worse.
- **The route is held as arrays once a card.** `RouteSegments` holds the route's segment
  ends; `Backdrop.segments` builds it once, and `Terms.segments` carries it to the flat
  placer and the journal notes, so a seat's leader is priced against every segment in a few
  array operations. The swap pass (`placement_leaders._seat_cost`) prices the same term, so
  a swap cannot put a leader back across the track.

Pinned by `tests/unit/maps/lettering/test_placement_costs.py::TestLeaderRouteCrossings` (a
leader kept to its pin's side, one across the track beside its pin, both strands, a route
point, the track through the pin, no route) and `test_placement_flat.py` (a pin six pixels
west of the track keeps its name to the west, where the east seat is otherwise cheaper).
`tests/golden/test_places.py` now asserts, for every focus place, which leaders still cross
the route (`HEMMED_LEADERS`): the Thursday note on Skye, whose every seat off the track pays
the route or a road, and on Y Fenni "Bean & Bread" and "Shepherd's Ice Cream", pinned inside
the loop where the route and the roads hem them. Any other leader across the route fails.

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
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

No Lynmouth leader crosses the route, so nothing moves; `PINNED_LABELS` and `GOLDEN_HASH`
are unchanged.

### Docs images

Every docs image was repainted with `repaint.py`; two moved, and only they:

| Image | Image changed | Master changed |
|---|---|---|
| `places/oxford.webp` | 0.238284 | 0.056231 |
| `places/y-fenni.webp` | 0.181720 | 0.058664 |

The image fractions are mostly lossy re-encoding round the moved names; the names are the
part past 32. Looked at side by side with `main`: on Oxford "Christ Church" leaves the seat
west of the loop whose leader crossed the route and sits inside the loop beside its pin, and
"Radcliffe Camera" and "The Bridge of Sighs" trade seats north of it with leaders clear of
the track; on Y Fenni "Tŷ Melin" moves out of the loop to the west and "Bean & Bread",
"Shepherd's Ice Cream" and "Angel Bakery" restack east of the loop. The paint under the
names is unchanged. The place pins and the map-styles means did not move.

## Consequences

- A leader crosses the route only where every seat on its pin's side costs more than a road
  crossing; `test_places` names each such leader on the focus places.
- The leader is priced as a straight segment and drawn bent (`lettering_furniture.leader`),
  so a drawn leader can still graze the track the priced one cleared; pricing the leader as
  drawn is part of the placement tuning feature (#113).
- A further regeneration needs its own ADR.
