# 0050 — The coast cut at the card edge: a golden regeneration

Status: accepted

## Context

On the Skye card the mainland east of Kyle Akin was painted as sea, with its rivers and
roads drawn over the blue, so the Skye Bridge seemed to land in the water (GitHub issue
#59). The sea mask covered 78% of the card.

`sea.sea_from_coast` closes each land region from the open coastline chains that cross the
card, and keeps an open chain only if both its ends lie within `EDGE_GAP_M` (30 m) of the
card edge. The issue note blamed the fetch box for cutting the coast inside the card. It
does not: the Skye feature payload holds the full geometry of every coastline way, and its
coast reaches 4 to 12 km past the card on every side (ADR 0040's invariant, that the card
lies inside the fetched box, holds). The chains stopped short because
`cover.coastline_chains` clipped the ways with `ink.polyline.clip_line`, which keeps or
drops vertices whole: a chain ended at its last vertex inside the card, up to one survey
segment from the edge. On Skye the mainland's coastline vertices are hundreds of metres
apart, and all ten of its open chains ended 41 to 269 m inside the edge, so every one was
dropped and only the islands' closed rings cut the sea. On Lynmouth the one open chain
ended 3 and 11 m inside, under the bound, and was snapped onto the edge.

## Decision

- **The coast is cut where it crosses the card edge.** `maps.rings.cut_line` splits a
  polyline into its runs inside a rectangle, clipping each segment (Liang-Barsky) so that a
  run ends at the point where it crosses the edge; vertices inside are kept as they are,
  and a segment with no length inside adds nothing. `cover.coastline_chains` uses it in
  place of `clip_line`, so every open chain ends on the edge however far apart the survey's
  vertices are. The coast keeps its own vertices; it gains only its two edge crossings.
- **`EDGE_GAP_M` drops from 30 m to 1 m** and now means "on the edge, to rounding". A cut
  end is on the edge to floating-point error; an end further in is a coast the survey left
  broken, which the sea still leaves out.
- Rejected: a larger `EDGE_GAP_M`, or snapping each end to its nearest edge within a bound
  taken from the fetch margin. No bound follows from the geometry: how far a clipped end
  lies from the edge is one survey segment, which OSM does not bound, and a large snap
  would close a genuinely broken coast across the land. Cutting at the edge makes the
  distance zero by construction.
- `ink.polyline.clip_line` is unchanged: roads, rivers and the vector export still clip
  vertex by vertex, and changing the ink function would move every golden for no fault a
  reader sees.

Pinned by `tests/unit/maps/test_rings.py` (`TestCutLine`: a line is cut at its crossings, a
segment through a corner keeps its inside piece, a line that leaves and comes back is two
runs, one inside is kept whole and one outside dropped) and `tests/unit/maps/test_cover.py`
(a coast surveyed a kilometre between vertices ends on the card edge and its land is not
sea; it failed before the fix with the chain ending 120 m short). `tests/golden/test_places.py`
now asserts, on the Skye card, that Kyle of Lochalsh, Kyleakin, Balmacara, Plockton and
Dornie are land and that Kyle Akin and Loch Alsh are sea.

## Golden regeneration

Process as ADR 0036. The tolerance bound is not changed, no gate is loosened and the hash
input does not change.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.131084
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.014197
map.png: identical no, differing fraction 0.127123
manifest hash: 3976d23ae248ca86-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

Lynmouth's sea moves by one render pixel of 2.6 million: its open chain now ends at the
edge crossings rather than at its last vertices snapped 3 and 11 m onto the edge. The wash
moves by far more than that because the blooms are seeded from it: `ink.wash.bloom` draws
each bloom's candidates by index from the list of the wash's thick pixels, so one pixel more
in the sea shifts every index after it and the sea's blooms land elsewhere. The sea's
outline, the land and the pen plate are unchanged and the paper is byte-identical.
`PINNED_LABELS` is unchanged and every name keeps its seat: the labels plate differs by at
most 9 levels in alpha, where the backing wash lifts a wash whose blooms moved. The manifest hash moves in its basemap half, from
`340a7f6e260ee1e2` to `3976d23ae248ca86`, because the sea ring holds two new points;
`GOLDEN_HASH` is re-pinned. The goldens were regenerated in place with `make_golden.py` and
compared with the paint they came from (`--require-identical all --require-hash equal`):
every output byte-identical.

### Docs images

Every docs image and master was repainted with `make_docs_images.py` and compared with the
committed ones. Two entries moved, and only they; the other 136 files are byte-identical.

| Image | Image fraction | Master fraction |
|---|---|---|
| `places/skye.webp` | 0.740999 | 0.555004 |
| `how-to/command-line.webp` | 0.258791 | 0.146843 |

`places/skye.webp` is the fix: the mainland from Plockton and Kyle of Lochalsh south to
Knoydart, and Applecross in the north east, are land, with their cover, rivers and roads on
paper instead of on blue, and the Skye Bridge lands on the shore. Applecross and the north
east carry no land cover in the payload, so they read as bare paper beside Skye's tinted
ground; that is the cover's honesty (`cover_rings`), not a fault of the sea. The sea that
remains moves its blooms for the reason Lynmouth's do. `how-to/command-line.webp` paints
the Lynmouth fixture, so it moves with the Lynmouth wash: its sea's blooms land elsewhere
and nothing else changes. No other card holds an open coast. The place pins and the
map-styles means are re-measured by the suite; none moved.

## Consequences

- Every open coastline chain ends on the card edge, so a mainland that the card cuts is
  closed as land whatever its survey's vertex spacing.
- A coast drawn in ink now reaches the card edge instead of stopping at its last vertex.
- A further regeneration needs its own ADR.
