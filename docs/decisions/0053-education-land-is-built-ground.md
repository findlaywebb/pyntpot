# 0053 — Education land is built ground: a golden regeneration

Status: accepted

## Context

`maps/cover.py` maps a fixed list of OpenStreetMap tags to pigment classes, and neither
`landuse=education` nor `amenity=university` was on it (GitHub issue #44). The land cover
query did not ask for them either. On the Oxford card the historic core, which is mostly
college land, was cream paper with the green of the quads, while the suburbs
(`landuse=residential`) carried the honey of `built`. The core read emptier than its edges.

## Decision

- **Education land is `campus`, painted in `built`'s pigment.** `COVER_TAGS` gains
  `landuse=education`, `amenity=university` and `amenity=college`, all classed `campus`.
  A campus is the town's ground and is painted as the town is: `PAINTED_AS` maps
  `campus` to `built`, so `paint_cover` washes campus and built pixels as one wash in
  `built`'s pigment, and no theme gains a pigment, a `cover_cfg` entry or a
  transparency.
- **Quads on top.** `campus` is first in `COVER_ORDER`, below the greens (meadow, grass,
  park and the rest), where `built` sits above them. A later class replaces an earlier one
  where they overlap, so a quad, a lawn or a college garden mapped inside college land
  keeps its green, while a green inside ordinary town `built` is still painted over as
  before. Plain `built` was tried first and covered the quads and college meadows, the
  green heart of the Oxford card; the maintainer chose quads on top. The order is a
  constant: a layering order a theme could set is issue #147
  (`docs/features/maps-cover-layering-order.md`).
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
  `campus`; a garden tag on a college stays `meadow`; campus is painted as `built` and
  sits below `meadow`, which sits below `built`), `tests/unit/maps/painter/test_cover.py`
  (a meadow inside a campus keeps its label, and campus and built make one wash) and
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
manifest hash: 3976d23ae248ca86-d9c56c0811177b0f here, 3976d23ae248ca86-d9c56c0811177b0f in the goldens
```

Lynmouth has no education land in its box, so nothing moves. `GOLDEN_HASH` is not re-pinned.

### Docs images

Every entry was repainted with `make_docs_images.py` on `main` after ADR 0049 (a generator
per item), so a ring or wash is keyed by its own points and class and the new rings no
longer move what the rest of the card draws. Master differing fractions against `main`:

| Image | Master | Image | Master |
|---|---|---|---|
| `places/oxford.webp` | 0.163649 | `how-to/route-ink-grid.webp` | 0.002165 |
| `social-preview.jpg` | 0.000903 | `hero.webp` | 0.000877 |
| `map-styles/bold.webp` | 0.000682 | `places/ambleside.webp` | 0.000634 |
| `gallery/route-map.webp` | 0.000634 | `map-styles/sepia.webp` | 0.000512 |
| `map-styles/winter.webp` | 0.000463 | `how-to/route-ink.webp` | 0.000439 |
| `tutorials/route-map.webp` | 0.000439 | `places/skye.webp` | 0.000000 |

Every other entry, `places/yr-wyddfa.webp`, `places/y-fenni.webp` and
`map-styles/pen-and-ink.webp` (which paints no cover) among them, is byte-identical.

Looked at side by side with `main`. On Oxford the college land between Radcliffe Camera,
the Bridge of Sighs, Christ Church and the High Street is now honey, as Jericho and the
Iffley Road are, and the card no longer has a pale hole at its centre; the quads, college
gardens and Christ Church Meadow stay green on top of it. The Magdalen Bridge label moves
to a free spot on the east bank. On the Ambleside cards (and the hero, gallery, how-to,
tutorial and map-styles images, which paint the same walk) the University of Cumbria
campus is a small honey patch by the town, a few master pixels. On
Skye the campuses are under a master pixel. Nothing else changes: the same classes lie in
the same places, and the roads and route do not move. The place pins and the map-styles
means did not move.

## Consequences

- A college, university or school with its own land is painted with the town.
- A quad or lawn mapped as its own green element inside college land stays green; one
  that is not mapped is painted as built ground.
- `campus` is a cover class that no theme colours: it always takes `built`'s pigment and
  wash. A theme that wants campuses to read differently, or the greens painted under
  them, needs the configurable layering of issue #147, which is a further ADR.
- A further regeneration needs its own ADR.
