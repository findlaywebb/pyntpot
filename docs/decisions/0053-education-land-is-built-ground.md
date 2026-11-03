# 0053 — Education land is built ground: a golden regeneration

Status: accepted

## Context

`maps/cover.py` maps a fixed list of OpenStreetMap tags to pigment classes, and neither
`landuse=education` nor `amenity=university` was on it (GitHub issue #44). The land cover
query did not ask for them either. On the Oxford card the historic core, which is mostly
college land, was cream paper with the green of the quads, while the suburbs
(`landuse=residential`) carried the honey of `built`. The core read emptier than its edges.

## Decision

- **Education land is `built`.** `COVER_TAGS` gains `landuse=education`,
  `amenity=university` and `amenity=college`, all classed `built`. It is the closest
  existing class: a campus is the town's ground, painted as the town is, and the theme's
  `built` pigment already reaches it. A class of its own was the note's other option; it
  would add a pigment, a `cover_cfg` entry and a transparency to every theme for a
  difference no theme asks for yet, so it is left until one does.
- **`amenity` is read, and read first.** `cover_rings` takes the class of the last of
  `amenity`, `landuse`, `natural` and `leisure` that matches, so a college's own garden or
  park (`leisure=garden` on the same element) keeps its green.
- **The land cover query asks for them.** `LANDCOVER_LANDUSE` gains `education`, and the
  query gains `way` and multipolygon `relation` lines for `amenity=university|college`
  (`LANDCOVER_AMENITY`). A campus `type=site` relation is a list of buildings and entrances,
  not an area, so it is not asked for.
- **The fixtures carry the new ground.** Re-recording would bring a month of unrelated
  OpenStreetMap edits into every card, so only those query lines were run, on 2026-11-03,
  from the same mirror over each fixture's land cover box, trimmed as the payload was, and
  appended to the land cover payload; nothing already there changed. Oxford gains 88
  elements, Ambleside two (the University of Cumbria's Ambleside campus), Skye five
  (Sabhal Mòr Ostaig and UHI West Highland); Lynmouth, Y Fenni and Yr Wyddfa have none in
  their boxes. The fixture READMEs record it.
- Pinned by `tests/unit/maps/test_cover.py` (education land, a university and a college are
  `built`; a garden tag on a college stays `meadow`) and
  `tests/unit/maps/providers/test_overpass.py` (the land cover query asks for them, and not
  for site relations).

## Golden regeneration

Process as ADR 0036. The tolerance bound is not changed, no gate is loosened and the hash
input does not change.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical yes, differing fraction 0.000000
map.png: identical yes, differing fraction 0.000000
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Lynmouth has no education land in its box, so nothing moves. `GOLDEN_HASH` is not re-pinned.

### Docs images

The fixture entries were repainted with `make_docs_images.py`; every other entry reads no
fixture that changed. Master differing fractions against `main`:

| Image | Master | Image | Master |
|---|---|---|---|
| `places/skye.webp` | 0.419509 | `places/oxford.webp` | 0.328096 |
| `hero.webp` | 0.316228 | `social-preview.jpg` | 0.285694 |
| `places/ambleside.webp` | 0.272831 | `gallery/route-map.webp` | 0.272831 |
| `how-to/route-ink-grid.webp` | 0.181127 | `map-styles/bold.webp` | 0.133528 |
| `map-styles/winter.webp` | 0.102169 | `tutorials/route-map.webp` | 0.098343 |
| `how-to/route-ink.webp` | 0.097734 | `map-styles/sepia.webp` | 0.095565 |

`places/yr-wyddfa.webp`, `places/y-fenni.webp` and `map-styles/pen-and-ink.webp` (which
paints no cover) are byte-identical.

Looked at side by side with `main`. On Oxford the core between Radcliffe Camera, the Bridge
of Sighs, Christ Church and the High Street is now honey, as Jericho and the Iffley Road
are, and the card no longer has a pale hole at its centre; the small quad greens inside
college land go under the honey with it, because `built` paints over `meadow`, while
Christ Church Meadow and the larger greens outside college land keep their colour. On Ambleside the campus on
Rydal Road is a small honey patch north of the town. On Skye the campuses are under a
pixel. The rest of each card's movement is not new ground: the extra rings change what the
shared deform and bloom generators draw for every later ring and wash (issue #61), so wash
edges and blooms shift by a few pixels across the card. Nothing changes character: the
same classes lie in the same places, and the lettering, roads and route do not move. The
place pins and the map-styles means did not move.

## Consequences

- A college, university or school with its own land is painted with the town.
- Quads and lawns that are not mapped as their own garden or park element are painted as
  built ground. A theme that wants campuses to read differently needs a class of its own,
  which is a further ADR.
- A further regeneration needs its own ADR.
