# 0063 — Long landmark names rank last: a golden regeneration

Status: accepted

## Context

With no annotations, `letter` names the leading `label_max` (3) landmark candidates in the
basemap's order, which is `landmark_rank`'s: tier, then whether the record knows the thing,
then how comfortably it sits inside its own reach. Nothing in that order looks at the name.
On the Lynmouth card the third candidate was "Living Waters Lynton United Reformed Church",
a recorded church 63 m off the route: 43 characters, wrapped over two lines on a leader
that ran from the west edge of the town to the coast road (GitHub issue #47, found by the
round-2 map critique). "Lynmouth Flood Memorial Hall" (28) and "Lee Abbey Christian
Conference, Retreat and Holiday Centre" (58) sit in the same list.

The note offered three fixes: drop candidate names over about 25 characters, rank places
of worship below landmarks, and always letter the place the route starts in.

## Decision

- **A landmark name over `LANDMARK_NAME_MAX` (25) characters ranks after every name that
  fits.** It is the first term of `landmark_rank`, ahead of the tier, so `rank_landmarks`
  (the export and the basemap's candidates), `pick_landmarks` in both modes, and the
  lettering's fallback all agree. The name is read from `n` or `name`, so the box rows and
  the export rows rank alike.
- **It is a demotion, not a filter.** A long-named thing is still offered and exported, a
  card with nothing shorter still letters it, and a payload pick (`pick_landmarks`) names it
  as asked. Dropping it would hide a real record from the coach that reads the export.
- **25 characters** is the note's figure and the longest name the Lynmouth card should keep:
  "Lynton and Exmoor Museum" is 24. Past it a name on a leader wraps into a two-line phrase
  that reads as a sentence on the map.
- **Not done: places of worship are not demoted.** A spire is something someone on the
  track navigates by, which is why `worship` is tier one (ADR 0036); "Saint Mary the Virgin"
  is the parish church beside the route and stays the first pick. The complaint was the
  long name, not the class.
- **Not done: the start place is not forced.** "Lynton" is lettered on this card;
  always lettering the place a route starts in is a settlement-picking rule
  (`picks_settlements`), not a landmark one, and is left to its own change.

Pinned by `tests/unit/maps/candidates/test_landmarks.py`: 25 characters fits and 26 does
not; a `name` row ranks as an `n` row does; a recorded 43-character church at 63 m ranks
below an unrecorded ruin at 190 m; mode `all` and the export offer it last; a payload may
still pick it.

## Golden regeneration

Process as ADR 0036, on top of `main` at 1873a6d (PR #151, after the keyed generators of PR #124). The tolerance bound is not
changed, no gate is loosened and the hash input does not change; the manifest hash does not
move (`3976d23ae248ca86-d9c56c0811177b0f`), so `GOLDEN_HASH` is not re-pinned.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.054307
map.png: identical no, differing fraction 0.029841
manifest hash: 3976d23ae248ca86-d9c56c0811177b0f here, 3976d23ae248ca86-d9c56c0811177b0f in the goldens
```

Only the lettering moves. `PINNED_LABELS` loses "Living Waters Lynton United Reformed
Church" and gains "Wind Hill", the recorded summit 607 m off the route, in the same slot.

### Docs images

Every docs image and master was repainted with `repaint.py`. Only the one that letters the
Lynmouth card from the heuristic moved; every other entry, including the place cards, whose
landmarks are curated in `examples/places.toml`, is pixel-identical.

| Image | Master | Image |
|---|---|---|
| `how-to/command-line.webp` | 0.037414 | 0.121172 |

The WebP's fraction is widespread because the lossy encode shifts with the content; the
lossless master's change is local to the names. The place pins, the map-styles means and
the smoke lock did not move.

Looked at side by side with `main`: the two-line church name and its leader are gone from
the west of the town. "Lynton and Exmoor Museum" takes that western seat, on a longer
leader that arcs down to the museum; "Saint Mary the Virgin" keeps its seat above the
bridge; "Wind Hill" is lettered on a short pin at the east, by the East Lyn. The museum's
and the church's leaders still meet the route close together by Lynton, so the converging
leaders the note mentions are reduced, not gone.

## Consequences

- No heuristic landmark name on a card is over 25 characters while a shorter candidate
  remains.
- Places of worship keep their tier, and the start place is still lettered only when the
  settlement rules pick it.
- A further regeneration needs its own ADR.
