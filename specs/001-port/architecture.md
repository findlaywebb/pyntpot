# 001-port: architecture plan

Decided 2026-10-03 after a deepening review of `src/pyntpot/_port`. This is
the target shape for P3 and P4 of `plan.md`, with the reasoning kept so a
later session can tell a deliberate choice from an accident. Vocabulary
follows `GLOSSARY.md`: module, interface, depth, seam, locality, leverage.

Direction: three layers, `maps -> letters -> ink` (D2), behind the public
names in D6. Every item below is accepted (D27). Line numbers are not given
because formatting moves them; names are.

## Sequencing

1. **A4 first.** The typed `Basemap` and `Plates` frame shapes every P3
   façade type, so it lands before the façade.
2. **Single golden regeneration.** A4 and A5 remove a step that rounds
   every coordinate to one decimal place, and the P3 `Style` changes the
   digest. Both can move pixels. They go inside the one regeneration that
   P3 already schedules, with an ADR recording the old and new manifest
   hash. Everything before that point stays exact against the current
   goldens; everything after stays exact against the new ones.
3. **A2 before the split.** `Hand` taking a setting is the one seam a pure
   move cannot fix, so it is settled before P4 moves bytes.
4. **A1, A3, A6, A7, A8** are then moves and merges under the parity test.

## A1. Plate assembly leaves the ink engine

**Files.** `paint.py`: `paint`, `paint_activity`, `plate_brushes`,
`relief_density`, `sea_patches`, `coast_run`, `ribbon_alpha`,
`paper_plate`, `label_geom`, `paint_hash`, `plates_dir`, `load_plates`,
`_crossfade`, and the brush tables `BRUSH_TREATMENTS`, `BRUSH_COLOURS`.
`geo.py`: `journal_layers`.

**Why.** `paint.py` is two modules in one file. The engine (sheet, noise,
brush, stamp, wash, pigment compositing, raster I/O) shares a file with a
470-line `paint()` that knows sea, lakes, cover classes, woods, rivers,
road bands and the route ribbon. That map half is why ink reaches upward:
all three `paint -> geo` lazy imports sit in it. The brush sheet ids
(`RIV1-a`, `MAJ2-a`, `LAN5-a`) are keyed by map feature class, so even the
brush catalogue carries maps vocabulary.

**Shape.** `ink` keeps the engine; its interface takes coverage arrays,
strokes, brushes and pigments. A maps-side plate painter owns layer order,
the cover and water rules, the ribbon trim and the class-to-brush table,
and calls ink. Brush ids lose their class prefixes or the class-to-id table
moves to maps.

**Gains.** Layer order and map rules in one maps module. Ink testable with
synthetic masks and no payload dict. No upward edge from ink.

```
BEFORE                                   AFTER
[paint.py ...........................]   [maps: plate painter]
|  Sheet Brush stamp wash composite  |     | layer order, cover, sea,
|  paint(): sea, cover, wood, rivers |     | ribbon, class -> brush
|  roads, ribbon, label_geom         |     v
|  paint_activity ==> geo            |   ~~~~~~~~~~~~~~~~~~~~~~~~~~
[....................................]   [ink: Sheet Brush stamp wash
        ^          ==>                     composite raster-io]
      geo.journal_layers
```

## A2. The hand writes settings, not labels

**Files.** `labels.py`: `Hand`, `Mark`, `hand()`, `draw_plate`,
`plate_key`, tables `KIND_INK`, `KIND_SLANT`, `KIND_TRACKING`,
`SPAN_INTENT_INK`, `HOME_GLYPH`, `NO_LEADER`. `paint.py`: `label_brushes`,
`_pen_profile`, `_dark_field`, `label_plate`, `_backing_wash`,
`labels_hash`. `outlinefont.py`: `OutlineFont`, `load`.

**Why.** Lettering is spread across three files and points the wrong way.
`Hand` reads `Label` and `Span` fields (tier, kind, intent, in_water,
leader, lift, window) and map tables, so the hand decides that a river is
slanted and blue, that a settlement gets an underline, that a span gets
ticks. `Hand._baseline` still picks a window for labels the placer skipped,
which is placement logic one layer too low. The raster half of lettering
(`label_plate`, the nib profile, the backing wash) lives in `paint.py`.
`OutlineFont` is already deep (three methods over about 800 lines) and
stays as it is.

**Shape.** `letters` owns the face, the trace, the hand and the nib raster.
Its input is a **setting**: a request to write some text at a size along a
line or from an anchor, with slant, tracking, ink token and seed. Its
output is marks, and a plate from marks. `maps` translates labels and
spans into settings and draws its own furniture (pins, leaders,
underlines, span lines, ticks, the home marker) as marks through the same
nib. Two interface shapes are to be drafted side by side before the code
moves (design it twice); the plan records the one chosen and why.

**Gains.** Removes the letters-to-maps dependency, the one cycle a pure
move cannot break. Map lettering policy in maps, letterform behaviour in
letters. One interface tested with a string and a line.

**Plan correction.** An earlier draft said `Hand` takes a plain `Mark`
sequence. `Mark` is what the hand produces. The input is the setting.

```
BEFORE                                   AFTER
[labels.Label/Span] <== [labels.Hand]    [maps: lettering] -- settings --> [letters: hand]
        kind, tier,       |  reads map            furniture marks ---------> |
        intent, lift      |  tables               ~~~~~~~~~~~~~~~~~~~~~~~~~~~
[outlinefont] <-- Hand    v                      [letters: face, trace, hand, nib plate]
[paint.label_plate, label_brushes, _pen_profile]           --> ink
```

## A3. Map lettering behind one `letter` module

**Files.** `mapcard.py`: `compose`. `labels.py`: `home_labels`,
`ground_labels`, `pick_roads`, `route_markers`, `journal_picks`,
`journal_heuristic`, `resolve_spans`, `place`, `place_spans`,
`road_lines`, `measure`, `_text_width`, and the no-caller shims
`_journal_picks`, `_journal_heuristic`, `_place_journal_labels`.

**Why.** The lettering pipeline is assembled by the caller. `compose` runs
eleven steps by hand. `place` has eight parameters and defaults to a flat
8 px advance measure that does not match the hand. Three text measures
exist (`labels.measure`, `labels._text_width`, `Hand.measure`). Three
shims have no callers.

**Shape.** One deep maps module behind D6's
`letter(plates, basemap, annotations, style) -> Lettering`. Picking,
anchoring, spans, placement and the plate sit behind it, and placement
always measures with the hand. The shims are deleted (deletion test:
nothing moves).

**Gains.** One call replaces eleven steps here and in the upstream
consumer's SVG page (D21). Placement bugs concentrate in one module. Tests
stop reaching private helpers.

## A4. Typed basemap and plates in one card frame

**Files.** `geo.py`: the `journal_layers` payload, `path_d`, `parse_path`,
`track_projection`. `paint.py`: `parse_d`, `label_geom`, the manifest
built in `paint`. `card.py`: `_Card`. `mapcard.py`: `compose`.
`labels.py`: `road_lines`.

**Why.** The seam between fetch, paint and lettering is an untyped dict
with short keys (`c`, `n`, `k`, `r`, `d`, `w`, `wn`, `wp`). Geometry is
written as SVG path strings and parsed back twice by two copies of the
same parser. The painter copies road, river and coast geometry into its
manifest (`label_geom`) only because the payload is thrown away, so
lettering reads map data through paint. `compose` projects the track a
second time and patches the drift with a `route0` offset. Metres, display
pixels and render pixels are converted in at least three places.

**Shape.** `Basemap` and `Plates` (D6, D21) are the typed seam. Geometry
stays as point lists in card metres. The projection is computed once and
carried. One **card** frame converts between metres, display pixels and
render pixels.

**Gains.** Frame and projection bugs in one module. The upstream SVG page
and `compose` read the same typed fields. One parser, `label_geom` and
the `route0` patch are deleted. Tests build a `Basemap` instead of a dict
with magic keys.

**Parity.** Removing the one-decimal round trip can move pixels. Inside the
regeneration window.

## A5. One polyline module under ink

**Files.** `geo.py`: `simplify`, `smooth`, `clip_line`, `join_ways`,
`join_strokes`, `_join_chains`, `_run`, `_point_to_seg`,
`_segments_cross`, `_normal_at`, `_eased`. `paint.py`: `chain_lines`,
`deform_line`, `parse_d`. `labels.py`: `_run`, `_cum`, `cumulative_m`,
`_joined`, `_seg_gap`, `_meet`, `_unit_normal`, `_offset_curve`,
`_spline`. `card.py`: `_tangent_at`, `_ease_along`. `outlinefont.py`:
`_normals`.

**Why.** Polyline helpers are copied across five files: five line-chaining
functions, two arc-length functions, two path parsers. The
`labels -> geo` and `labels -> paint` lazy imports exist only to borrow
`simplify` and `chain_lines`.

**Shape.** One polyline module at the bottom of the stack that every layer
may import. Move first, then merge duplicates one at a time, each merge
its own parity-checked commit.

**Caution.** `chain_lines` and `join_strokes` differ in tolerance handling;
merging them can change pixels. Inside the regeneration window.

## A6. Style grouped by layer

**Files.** `paint.py`: `PaintStyle`, `digest`, `from_style`,
`with_display`. `geo.py`: `GeoOptions`, `journal_geometry`. `style.py`:
`RouteInk`, `coerce_like`. The `getattr(pstyle, ...)` readers in
`labels.py` and `mapcard.py`.

**Why.** One dataclass of 173 fields carries ink, letters and maps
settings, plus fields only the upstream consumer's SVG renderer reads.
`geo` reads 20 of them for card size and ribbon, so maps depends on a type
defined in ink. `Hand` reads it with `getattr` and silent defaults. The
base-plate hash digests every field, so a lettering change invalidates the
paper and wash plates too.

**Shape.** Each layer owns its style group: ink (paper, wash, brush),
letters (face, nib, hand), maps (card, ribbon, cover, route, lettering
policy, basemap). The P3 `Style` model (D7) composes them. Consumer-only
fields go back to the upstream consumer.

**Gains.** A field lives next to the module that reads it. A lettering
change stops repainting base plates.

## A7. Caches keyed by what was painted

**Files.** `paint.py`: `plates_dir`, `load_plates`, `paint_hash`,
`labels_hash`, `paint_activity`. `labels.py`: `plate_key`, `draw_plate`.
`geo.py`: `overpass_path`, `elevation_path`, `landcover_path`.

**Why.** Freshness rules live in three hand-written key lists: the payload
keys in `paint_hash`, 27 style field names in `labels_hash`, and the label
rows in `plate_key`. A new field that changes pixels but is missing from a
list leaves a stale plate on disk. Plates and fetched payloads are still
found by the caller's key, which in practice was an external activity ID.

**Shape.** One cache module owns the fetch cache and the plate cache. Keys
derive from the typed inputs and the layer's style group (A6), never from
a hand-kept list. This brings the plate cache under D9, which already
says no cache is keyed by a caller's ID.

## A8. Candidates as a reusable facility; dead code deleted

**Files.** `geo.py`: `landmark_export`, `climbs`, `ground_climbs`,
`route_places`, `road_run`, `named_roads`, `read_gpx_elevation`,
`haversine`, `bearing`, `compass`, `cumulative`. Zero callers:
`mapcard.alphabet_sheet`, `mapcard.sport_from_gpx`, `paint.with_display`,
`labels._journal_picks`, `labels._journal_heuristic`,
`labels._place_journal_labels`.

**Why.** About 550 lines of `geo.py` compute climbs and landmark
candidates for an external picker. Nothing in the fetch, paint, letter or
compose path calls them. They inflate the module the maps split must cut
into seven parts. Six functions have no caller.

**Decision (D27).** The candidate logic stays in scope. It is split out of
`geo.py` and **generalised**: a `candidates` facility in maps that ranks
named roads, climbs and places for a track, usable by any later
annotation decision (which span to name, which road to number, what to
letter first), not a one-shot export. The six zero-caller functions are
deleted. `alphabet_sheet` is the exception if the docs (P7) want a
lettering specimen; keep it only if a caller appears there.

## Glossary additions

Settled with this plan: **card** (the main coordinate frame: card metres,
display pixels, render pixels), **manifest** (the plates' sidecar record),
**mark** (one stroke the hand produces), **setting** (the hand's input),
**candidate** (a ranked annotation option), **credit** (a provider's
attribution text and URL).

## Decisions this plan touches

D2, D5 (layers via `_port`), D6, D7, D9 (now covers the plate cache), D21,
D23 (one regeneration), D27 (all eight accepted). No D is reopened.
