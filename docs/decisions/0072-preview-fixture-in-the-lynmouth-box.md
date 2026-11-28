# 0072 — A preview fixture in the Lynmouth box

Status: accepted

Spec: `specs/008a-theme-preview-card/`. Issue: #79. Amends ADR 0032 for one new fixture
directory, `tests/fixtures/preview/`, and for it only.

## Context

A theme is judged on real place cards, and each holds only what its place has. The
interactions a theme gets wrong (a name on a dark wash, a road over a river, a route doubling
back beside a stream, an island in a lake) are scattered across the places or missing. A card
that holds all of them cannot be recorded, because no real place has them in one frame, so
the preview is made up. ADR 0032's "Fixture rules, for every fixture" assume a recorded
place: a track built from OpenStreetMap ways, payloads recorded through the shipped providers
and licensed ODbL, and the exempt-files rule, "the plan, this ADR and every other file carry
no coordinate". The preview breaks the first two on purpose and departs from the third: its generator
holds the layout's centre as a coordinate pair, inside the box, and its test imports the
gate's `BOXES` table from `architecture.test_coordinates` rather than carrying a box of its
own, so the box has one source.

## Decision

For `tests/fixtures/preview/` only, ADR 0032 changes as follows; everything else in it stands.

- **Made up, not built or recorded.** The track and the three payloads are made by
  `tests/fixtures/make_preview.py` (and its `preview_payloads.py`), not by `make_track.py`
  or `record_fixture.py`. They hold no OpenStreetMap data, so they are not ODbL data; the
  payloads say so in their `osm3s` block and the README says so. The generator is
  deterministic: its output is committed, and a test runs it into a temporary directory and
  compares every file byte for byte.
- **One box, Lynmouth's.** `tests/architecture/test_coordinates.py` gets a `preview` entry
  holding the same box as `lynmouth`. Every coordinate in the payloads, the elevation grid
  and the GPX lies inside it, and the generator holds its own centre inside it, as the
  scanned source of a fixture generator must. The payloads and the README are exempt as for
  every fixture, by the entry's key.
- **A README of its own kind.** The README names the generator in place of the source, date
  and way ids, and the data is under the repository's licence.
- **Real names at made-up places, by design.** Every name on the fixture is a real place or
  feature of the Lynmouth area (Lynmouth, Lynton, East Lyn River, West Lyn River,
  Countisbury, Watersmeet, Foreland Point), standing where the layout needs it, not where it
  is. Features with no real name there carry no name tag. This is the one place CLAUDE.md's
  "never invented" rule for places gives way: the coordinates are invented, the names are
  not, and the README says so.
- **The default margins.** The preview is cached under `Cache(dir)` and `FetchMargins()`, so
  its features fetch box is the track's box and 1500 m. The track's box is 1.5 km east to
  west by 1.6 km north to south, which puts that fetch box (about 4.5 by 4.6 km) inside the
  Lynmouth box and every theme's card inside the fetch box. The land cover is written only
  inside it.
- **Budget.** 600,000 bytes on disk, a `BUDGETS` entry beside the other overrides.
- **Its card test is `tests/golden/test_theme_preview.py`**, not `test_places.py`: it paints
  every packaged and example theme on the fixture and pins each card's mean colour and the
  label names placed. The fixture's own test, `tests/fixtures/test_make_preview.py`, checks the
  bytes, the box, the names and the way the features meet.

## Alternatives rejected

- A recorded place that holds everything: none exists in one frame, and a stretched box would
  leave the recorded tracks of the other fixtures behind.
- Hand-writing the payload files: the layout would not be reproducible, and the box, the
  names and the key could drift from the track.
- Widening `lynmouth/` with the preview's elements: its goldens pin the recorded payloads
  byte for byte.

## Consequences

- The fixture's cache key is a pinned literal, `PREVIEW_KEY` in `tests/support/paths.py`,
  and the fixture test asserts it equals the key computed from the committed track.
- A change to the layout is a change to the generator and to the committed files together.
