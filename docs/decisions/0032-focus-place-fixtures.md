# 0032 — Focus-place fixtures and one coordinate box per fixture

Status: accepted

Amends D10 (the coordinate allowlist) and applies D16 (no personal content) to five new
fixtures.

## Context

Lynmouth is the test place behind every golden, and the coordinate gate
(`tests/architecture/test_coordinates.py`) held one box, Lynmouth's. The maintainer named
focus places for the docs and the gallery (2026-10-23): Keswick, the Quiraing on
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
  gate's own file is exempt too, since it holds the table. The run log, the plan, this ADR
  and every other file carry no coordinate.
- **Fixture rules, for every fixture.** The track is generated, never recorded: it follows
  public OpenStreetMap ways chosen by id and joined and resampled every 20 m by
  `tests/fixtures/make_track.py`, with no time, elevation or activity type. It marks no
  home and no personal route (D16). The payloads are recorded by
  `tests/fixtures/record_fixture.py` through the shipped providers, so their file names
  carry the default providers' cache key. Each README states the source (the Overpass
  mirror used, because `overpass-api.de` resets connections from the recording
  environment), the date, the boxes, the way ids and versions, the D16 statement, and the
  licences. `track.gpx` and the two Overpass payloads are ODbL-derived data and the README
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
