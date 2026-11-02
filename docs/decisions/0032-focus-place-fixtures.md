# 0032 — Focus-place fixtures and one coordinate box per fixture

Status: accepted

Amends D10 (the coordinate allowlist) for five new fixtures.

## Context

Lynmouth is the test place behind every golden, and the coordinate gate
(`tests/architecture/test_coordinates.py`) held one box, Lynmouth's. The docs and the
gallery use five focus places: Keswick, the Quiraing on
Trotternish, Yr Wyddfa by Crib Goch, central Oxford and Y Fenni. Each needs a recorded
fixture, a track and the three provider payloads, so a card paints from the cache alone.
Their coordinates lie far outside Lynmouth's box, and a fixture's payloads and README
carry coordinates by design.

## Decision

- **One box per fixture.** The gate holds a table of boxes, one per fixture directory, each
  the track's box rounded outward to 0.01 degree, as Lynmouth's is. A synthetic coordinate
  pair in `src/`, `tests/`, `examples/`, `docs/` and `specs/` must lie in one box: its
  latitude and its longitude in the same fixture's box. A latitude from one box beside a
  longitude from another fails.
- **Exempt files.** Each fixture's three payloads and its README are exempt, because
  Overpass returns whole ways touching a box and the README documents the margin boxes. The
  gate's own file is exempt too, since it holds the table. The plan, this ADR and every
  other file carry no coordinate.
- **Fixture rules, for every fixture.** The track is generated:
  `tests/fixtures/make_track.py` builds it from OpenStreetMap ways chosen by id, joined and
  resampled every 20 m. The payloads are recorded by
  `tests/fixtures/record_fixture.py` through the shipped providers, so their file names
  carry the default providers' cache key. Each README states the source (the Overpass
  mirror used, because `overpass-api.de` resets connections from the recording
  environment), the date, the boxes, the way ids and versions, and the licences. `track.gpx` and the two Overpass payloads are ODbL-derived data and the README
  licenses them so.
- **Budget, in bytes on disk.** A fixture directory's files sum to at most 10 MB, and
  `yr-wyddfa/` to at most 12 MB (MB is 1,000,000 bytes). `tests/` is in neither the sdist
  nor the wheel, and git stores the payloads at about a sixth of their raw size, so these
  cost the repository roughly 1.7 MB and 2 MB at most. The payloads are committed byte for
  byte as recorded; none is minified. A test in `test_coordinates.py` enforces it. Over
  budget is a stop: the slice reports the sizes and the routes are not shortened.
- **A card per fixture.** `tests/golden/test_places.py` paints each fixture from a copy of
  its directory with providers that cannot reach a network, calls `fetch`, `paint` and
  `letter` directly, and pins that no request is made, that the card paints and the label
  names placed.

| Fixture (every file, README included) | Bytes | Gzip bytes, for scale | Budget |
| --- | --- | --- | --- |
| `lynmouth/` | 3,648,402 | 562,762 | 10,000,000 |
| `keswick/` | 6,663,743 | 1,055,797 | 10,000,000 |
| `trotternish/` | 1,118,471 | 184,804 | 10,000,000 |
| `yr-wyddfa/` | 10,593,606 | 1,687,086 | 12,000,000 |
| `oxford/` | 8,827,848 | 1,462,704 | 10,000,000 |
| `y-fenni/` | 3,873,009 | 619,210 | 10,000,000 |

## Alternatives rejected

- Budgets on raw size at 4 MB and 6 MB, the plan's first figures: Keswick, Oxford and Yr
  Wyddfa measure 6.7, 8.8 and 10.6 MB raw, with routes the maintainer settled.
- Budgets on gzip size (1.5 MB, 2.5 MB), used for one night: the compressed size depends on
  the zlib build, and CI's Python measured Oxford at 1,506,991 bytes where the recording
  machine measured 1,462,704, so the test was not deterministic.
- Minifying the payloads. It would change bytes the cache and the key were recorded with
  and hide what the provider returned.
- One wide box over every fixture. It would let a Lynmouth latitude pair with a Quiraing
  longitude and so lose the gate's purpose.
- Writing the boxes as whole numbers so the scanner skips them. That hides the table from
  the gate by trick; exempting the gate's own file says so openly.

## Consequences

- A new fixture adds a row to the box table and the key table, a key constant in
  `tests/support/paths.py`, and its payloads and README to the exempt list by name.
- Lettering reads OSM's `name` tag, which in Wales is often the English name; the Y Fenni
  card reads "Abergavenny" until the style names the tags lettering reads.
- The golden job grows by about four minutes, the five cards painting at full size.

## Amendment: the showcase fixtures (P7.V9a, 2026-10-25)

The showcase round (decision 2 of the plan's P7.V section) adds `ambleside/` and `skye/`,
re-records `oxford/` and `y-fenni/` on new routes and `yr-wyddfa/` wider, and replaces
`keswick/` and `trotternish/` (P7.V12a removes them). What changes in the decision above:

- **Payloads are trimmed.** From P7.V1 the recorder trims the feature and land cover payloads
  (`tests/fixtures/trim_fixture.py`: minified, only the fields and tags the code reads), so
  "committed byte for byte as recorded" no longer holds for a recording made since. `keswick/`
  stays untrimmed until it is removed.
- **Budgets by fixture.** The default is 6,000,000 bytes on disk for a directory. Yr Wyddfa's is
  8,000,000 (7,715,942 measured, rounded up to the next half megabyte). `keswick/` is 7,000,000
  (6,663,743, untrimmed; removed by P7.V12a). `ambleside/` is 7,000,000: its land cover alone is
  4.87 MB trimmed and unsimplified, and the walking maps are never simplified, so it measured
  6,571,595 against the default (the coordinator accepted it as a deliberate per-fixture budget, like
  Keswick's, not a loosening of a contract). Over budget is still a stop.
- **Recorded wider.** A recording may take fetch margins other than the defaults
  (`record_fixture.py --margin-m`, `--landcover-margin-m`; ADR 0040). The rule: project the
  recorded track, compute the card box with `journal_geometry` under the default ribbon fields as
  the basemap does, and take the smallest whole kilometre that covers the card box's largest
  overhang beyond the track's box, plus 1 km of headroom for a theme; the land cover margin equals
  it (at least the default). Yr Wyddfa's overhang is 1,957 m, so its margins are 3,000 m. The card
  box lies inside the fetched feature box, which `test_places.py` asserts for a place recorded
  with margins; the three default-margin places (Ambleside, Oxford, Y Fenni) also have it inside
  their default box, recorded in the run log and not asserted. Margins over 20,000 m stop the slice.
- **Skye is the one simplified fixture.** `--simplify-m` applies to its payloads alone (the 720 px
  card is about 106 m per display pixel); the walking maps are never simplified. Its payloads are
  not committed: at 25 m the directory measured 16.7 MB, over the 12 MB limit. `trim_fixture.py`
  gained two scale-aware drops, used for Skye only (orchestrator decision): `--drop-minor-roads`
  (ways of the minor road classes and the footpath classes: the pen paints the minor and path bands
  only below `minor_roads_mppd`, 8 display metres per pixel, and Skye's card is 106.4) and
  `--min-area-m2 A` (closed ways and multipolygons whose outer area is under A, with A the square of
  the card's `mpp_display`, 11,326 m2; natural water and coast, places and named areas are kept).
  With both the directory measures 12,511,755 bytes, over the 12 MB limit. The orchestrator, applying
  the maintainer's instruction of 2026-10-25 not to stop Skye for a slight overrun, accepted it
  as it is: `skye/`'s budget is 13,000,000 (the measured size rounded up to the next half megabyte).

| Fixture | Bytes (every file) | Budget |
| --- | --- | --- |
| `ambleside/` | 6,571,595 | 7,000,000 |
| `oxford/` | 4,850,357 | 6,000,000 |
| `y-fenni/` | 2,171,023 | 6,000,000 |
| `yr-wyddfa/` | 7,715,942 | 8,000,000 |
| `skye/` | 12,511,755 | 13,000,000 |
| `keswick/` | 6,663,743 | 7,000,000 |
