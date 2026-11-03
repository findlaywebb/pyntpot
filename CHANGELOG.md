# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-11-03

Mostly fixes from the round of map critiques after 0.1.0: names keep off the water and the
route, rivers and coasts run cleanly to the card edge, retraced legs and small cover
patches no longer clutter a map, and painting is about twice as fast. Every painted image
differs from 0.1.0.

### Breaking changes

- Every painted image differs from 0.1.0. Each ring, stroke and bloom draws from a random
  generator of its own, keyed to what it paints, so changing one mark no longer moves the
  others; the map fixes below move pixels and label positions too.
- A route has one ink. `Style.route_inks` and the `route_ink()` method are replaced by the
  field `Style.route_ink`, which holds only the keys the compose step reads. A theme that
  names a route casing, glow, shadow or an `effect` table is rejected when it loads.
- The default ink token "map" is renamed "label". A caller's "map" token still paints in the
  label ink.
- A retraced leg of the route is drawn as one stroke, not two lines side by side (ADR 0057).
  `strand_gap_px` is now `strand_merge_px`, and `separate_strands` is now `merge_strands`.

### Added

- A theme's `[cover] min_patch_px` folds cover patches smaller than it into their largest
  painted neighbour, so a map is not speckled with slivers of wood and field (ADR 0054).
- A leader's pin is an open ring facing its leader, so the ring and its line read as one
  mark rather than a dot with a line attached (ADR 0067).

### Changed

- Painting skips the work on empty pixels: the Lynmouth card paints in 22 s instead of 56 s
  and peaks at 926 MB instead of 1688 MB, with the same pixels.
- Opaque lossless plates are written at WebP method 1: the same pixels, slightly smaller
  files at map size (ADR 0043).

### Fixed

- Names keep off the water. A flat name is measured with its kind's letter spacing, a river
  or road name with no room on the paper is dropped, and flat names, the leader swap and
  names set along a river are all priced for the water under their letters.
- A leader is priced for crossing the route past its pin, so leaders no longer cut across
  the route.
- A landmark name too long to letter ranks after the names that fit.
- The backing wash behind a name fades out from the letters, with no pale box round it.
- The letters D, Q and 3 keep their tails, and 8 is written through its waist.
- A glyph's width no longer flickers along a name, because the nib's direction is smoothed.
- A reloaded nib swells back instead of stepping, and a pen lays its set-down blot only on
  its own stroke. A thin pen keeps its blot, fading out as the pen widens past 2.5 px.
- An organic brush's drift no longer shifts a short stroke sideways, so a small "o" keeps
  its counter open.
- Blooms spread over a wash instead of sitting along its rim.
- Rivers run to the card edge without a blot where they come in, and a stroke that enters
  at the plate's edge is not set down with a load and a blot.
- The coast is cut where it crosses the card edge, so a mainland whose coast points are far
  apart (beside Skye) is land, not sea.
- Each land cover class is filled as the union of its rings, so an inner ring wound against
  its outer one (Christ Church Meadow) no longer cuts a hole.
- Colleges and other education land are painted as built ground, with their quads and
  gardens kept green.
- Streams are kept whole, unnamed ways that continue each other are joined before being kept
  or dropped, and short loose strokes are dropped (ADR 0058).

## [0.1.0] - 2026-10-26

The first release meant for general use. pyntpot paints hand-drawn watercolour and
pen-and-ink pictures in Python: paper, washes, brushes, nibs, pigments and hand lettering,
and, built on those, a route map from a GPX track, OpenStreetMap data and elevation. This
release adds the documentation (tutorials, how-to guides, reference and essays, also built
as a site), example themes and place fixtures, and fixes how names are lettered on a map.
0.0.1 and 0.0.2 were candidates for one consumer and are not for general use.

### Breaking changes

- Maps paint differently from 0.0.2. A name set along a curve is now cut a window as long
  as the hand writes it, with its kind's letter spacing, so river, road and settlement
  names sit and break differently (the Lynmouth card letters "East Lyn" once, along the
  water, where it lettered it twice). A river's repeat that finds no window on its water
  is dropped instead of set flat. A stroke at the card's edge and a mark on a finer ink
  grid also paint differently (see Fixed). Pixels, label positions and `Lettering.labels`
  differ from 0.0.2; the fetch cache keys do not change.
- The paper browns at its edge and foxes in small rust specks by default
  (`paper_edge = "warm"`), and letters are stroked once at their junctions, so every
  painted image differs from 0.0.2 (ADR 0036).
- The data credit on a map is sized in display pixels: 13 px on a 720 px card, growing with
  the card and never under 12, and a long credit wraps at its " · " (ADR 0041).
- `pyntpot.maps.fetch` and `Cache.ensure` raise `FetchError` when a provider cannot
  answer, with the provider's error as its cause. Catch `FetchError`, not the provider's
  error.
- The reasons the start, finish, home and road labels carry (`Label.why`) say track, not
  session or rider: "where the track began", "where the track ended", "home" and "road the
  track was on".

### Added

- `BasemapStyle.name_tags`, the tags a name is read from, first one present wins (default
  `("name",)`); a style that leaves it alone keeps its digest. `examples/themes/y-fenni.toml`
  reads `name:cy` first, so the Y Fenni card letters Y Fenni, Llan-ffwyst and Afon Wysg.
- `pyntpot.maps.ProviderError` and `pyntpot.maps.ProviderBudgetExceededError`, the
  errors the shipped providers raise when they cannot answer or their budget is spent
  (ADR 0029).
- Documentation: a README, two tutorial series, how-to guides, reference pages, essays, a
  gallery, and a docs site built with MkDocs Material (ADRs 0013 to 0021, 0033, 0034).
- Example themes (`examples/themes/`: pen-and-ink, sepia, bold, winter, y-fenni) and
  example scripts that paint every image in the docs from `examples/`.
- Recorded place fixtures for Ambleside, Skye, Yr Wyddfa, Oxford and Y Fenni, with
  `make_track.py` and `record_fixture.py` to make more.
- `pyntpot.maps.FetchMargins` and `Cache(directory, margins=...)`: how far beyond the track
  the features and land cover are fetched; `pyntpot map --margin-m` (ADR 0040).
- `pyntpot.maps.JournalNote` and `Annotations.notes`: short notes written on the map at a
  point, seated before any other name (ADR 0038).
- Style fields `basemap.minor_road_classes` and `cover.relief_strength`, and a route ink's
  `blend` and `opacity` effects (ADR 0037).
- `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY` in `pyntpot.ink`: ten painter's
  pigments by their tube names (ADR 0039).
- The sea is painted from closed coastline rings, so an island card has water round it.
- `draw_attribution` takes the card's render `scale`.
- A bug report form for issues.

### Fixed

- A curved name's window is measured with its kind's letter spacing, so a long name no
  longer overruns the water it is set along.
- A stroke that reaches or crosses the card's edge no longer piles its off-card ink
  onto the edge pixels (`ink.deposit`).
- Name-only landmarks beyond the cap are dropped, and a cap of 0 picks none
  (`journal_picks`).
- Span labels go on the side with more free paper for the ground span, and the other
  span on the opposite side; the side sign was reversed.
- A river or stream tagged `tunnel=no` is drawn instead of dropped.
- A mark painted on a finer ink grid (`ink_ss` above 1; the default theme's 3) is
  centred on the plate's pixels; it sat a third of a pixel up and left (ADR 0025).
- Water areas keep their islands.
- A leader line no longer crosses a name already placed.
- Landmarks leave shops out and rank recorded places first.
- The nib's touch-down has no square edge, and the pen route keeps its legs apart.

## [0.0.2] - 2026-10-09

A second pre-release candidate for the upstream consumer's migration: the candidate export, the vector layers and a fed route ink become public (ADR 0027). Not for general use; 0.1.0 is the first release.

### Added

- `pyntpot.maps.vector_layers` and `VectorLayers`: the basemap's layers as SVG path data,
  read from the fetch cache, for a caller that draws its own map.
- `pyntpot.maps.candidate_export`: what a track passes, read from the fetch cache under
  the track's key (was the private `landmark_export`).

### Changed

- `Style.with_route_ink`: a caller feeds the route's colour and width; the default route
  ink is unchanged.

## [0.0.1] - 2026-10-09

A pre-release candidate for the upstream consumer's migration (P8 of the port plan). Not
for general use; 0.1.0 is the first release.

[0.2.0]: https://github.com/findlaywebb/pyntpot/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/findlaywebb/pyntpot/compare/v0.0.2...v0.1.0
[0.0.2]: https://github.com/findlaywebb/pyntpot/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/findlaywebb/pyntpot/releases/tag/v0.0.1
