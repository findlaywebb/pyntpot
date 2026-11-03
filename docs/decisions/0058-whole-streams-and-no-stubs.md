# 0058 — Whole streams and no stubs: a golden regeneration

Status: accepted

## Context

On the Ambleside card short brown hairs stick out of the route between Rydal and Ambleside,
and short blue dashes of stream stop dead on the land south of Loughrigg Terrace (GitHub
issue #56). The issue put it down to clipping to the route's corridor. There is no corridor:
every layer is cut to the card box. Measured on the Ambleside fixture, the stubs have three
causes.

- **A stream was kept way by way.** With `rivers = "key"`, `osm_elements._waterway` asked
  the interaction test of each way, so of a brook OSM cut into three ways only the one the
  track crossed was drawn: a dash across the route. Roads have been kept per road since the
  port, for this reason ("every side street would come off the route as a stub and the map
  would read as a comb"); streams had not.
- **An unnamed way was a road on its own.** A road with no number and no name was decided
  way by way, so a service road or a stream cut where a tag changes kept the block the track
  met and lost the next.
- **Nothing dropped a short loose piece.** A road stroke shorter than its brush was dropped;
  nothing longer was, and a watercourse had no floor at all. Of the Ambleside card's 44 road
  strokes 20 were under 20 display pixels, most of them service ways a few pixels long whose
  end the track touched on the A591: the brown hairs.

## Decision

- **A stream is kept or dropped per watercourse.** `_waterway` collects every piece of a
  stream and records in `Harvest.stream_keep` whether any of it met the track;
  `osm._open_rivers` draws a watercourse whole when it did. A named one is gathered by its
  name, as its underground share already was.
- **An unnamed way carries on into the way it continues as.** Each unnamed road and stream
  files its two ends, as mapped and before the clip, under its highway or waterway value
  (`Harvest.road_ends`, `Harvest.stream_ends`). `osm.carried_on` joins two ways where exactly
  two of a kind end at one point (`CARRIED_ON_WAYS`), which is how OSM cuts one road; at a
  point where three or more end, a junction, none is joined, so an unnamed network is not
  drawn whole because the track touched one corner of it. The keep test is answered for the
  joined chain.
- **A short lane, path or stream with a loose end is not drawn.** After chaining, a stroke of
  the minor or path road band, or of the minor watercourse class, shorter than
  `STUB_FLOOR_PX` (20 display pixels) is dropped unless both its ends meet another stroke
  (within `MEET_PX`, 1.5 display pixels; a stream's end may also meet a lake shore):
  `basemap_strokes.stubs`. A short street joining two streets, or a beck from a river to a
  lake, is a link and stays. The major roads and the rivers are not cut, since a gap in
  either would show. The road brush floor stays below it.
- Not changed: a numbered road whose ways carry different names ("Rydal Bridge", "Market
  Place" on the A591) is still chained by name and number, so those pieces are strokes of
  their own on the road's line. They lie on the road, not off it.

Pinned by `tests/unit/maps/test_layers.py` (a named brook cut into two ways is kept whole; an
unnamed stream and an unnamed service road carry on into the way that continues them; three
unnamed ways ending at one point are decided each on its own) and
`tests/unit/maps/test_basemap_strokes.py` (a short driveway off a road is dropped, a short link
between two roads and a short piece of a major road are kept, a long lane with a loose end is
kept; a short stream dash is dropped, a short beck from a river to a lake is kept).

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052. The tolerance bound is not
changed and no gate is loosened. The hash input does not change, but the vector map it hashes
does, so the manifest hash moves in its input half.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.009010
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.003065
map.png: identical no, differing fraction 0.008483
manifest hash: 643c61991c4a08ce-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

`PINNED_LABELS` is unchanged. `GOLDEN_HASH` is re-pinned to
`643c61991c4a08ce-d9c56c0811177b0f`. The Lynmouth box's road strokes go from 39 to 35
(`test_basemap.py`, `test_pipeline_fetch_paint.py`) and its vector roads from 82 to 85, the
unnamed ways now kept with the way they carry on from (`FIXTURE_ROADS` in
`test_vector_layers.py`). The map-styles means (`tests/golden/test_map_styles.py`) move by
1.1 to 2.2 levels and are re-measured and re-pinned, all four themes. The place pins did not
move. The goldens were regenerated from that paint and every gate run on it.

### Docs images

Every docs image and master was repainted with `repaint.py`. The 16 that draw a map moved,
and only they; every other entry is byte-identical. Master differing fractions against
`main`:

| Image | Master | Image | Master |
|---|---|---|---|
| `places/oxford.webp` | 0.321379 | `places/skye.webp` | 0.290790 |
| `places/y-fenni.webp` | 0.195775 | `how-to/route-ink-grid.webp` | 0.164420 |
| `map-styles/bold.webp` | 0.141886 | `tutorials/route-map.webp` | 0.133650 |
| `places/yr-wyddfa.webp` | 0.132882 | `how-to/route-ink.webp` | 0.132481 |
| `map-styles/winter.webp` | 0.129215 | `gallery/route-map.webp` | 0.121199 |
| `places/ambleside.webp` | 0.121199 | `map-styles/sepia.webp` | 0.120054 |
| `map-styles/pen-and-ink.webp` | 0.109795 | `hero.webp` | 0.082432 |
| `social-preview.jpg` | 0.065000 | `how-to/command-line.webp` | 0.016903 |

The fractions are large because the roads and watercourses draw from one generator in the
order laid: a stroke dropped or added changes the brush texture of every stroke laid after
it, so nearly every road and stream on a card is repainted with the same line and new
texture. The strokes added or dropped, counted on each fixture (road strokes, then river
strokes, `main` to this change): Ambleside 44 to 35 and 18 to 31, Skye 39 to 39 and 308 to
368, Yr Wyddfa 19 to 17 and 23 to 25, Oxford 376 to 284 and 32 to 34, Y Fenni 140 to 128
and 2 to 3.

Looked at side by side with `main`: on Ambleside the brown hairs off the A591 between Rydal
and Ambleside are gone, and the becks the route crosses on Loughrigg Terrace are drawn as far
as OSM maps them, down towards Rydal Water and the Rothay, where `main` drew a dash across
the route; they still start on the fell, where the mapped stream starts. On Oxford and Y Fenni
the short dead-end service ways and footway ends off the streets are gone and the street grid
is otherwise the same. On Skye more of the streams the route crosses are drawn, and the
names placed after them in tier order move: the Thursday callout takes a seat further north,
and Portree and the start move a little. On Y Fenni an
unnamed stream the route crosses in a culvert is now drawn either side of it: on `main` the
culvert way alone met the track, and being underground end to end it was dropped, with the
open ways round it never asked; now the stream is decided whole and only the culvert is left
out. The name "Y Fenni" moves up off it.

## Consequences

- A stream the track met is drawn whole, as a road is; a card whose route crosses many becks
  shows more water than before.
- No lane, path or stream is drawn as a piece under 20 display pixels with a loose end; a
  real cul-de-sac that short is not drawn either.
- A numbered road cut into differently named ways is still several strokes along one line.
- A further regeneration needs its own ADR.
