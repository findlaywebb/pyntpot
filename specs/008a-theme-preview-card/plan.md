# 008a — plan

Written ahead of 008's merge; slice P0 re-checks every path and name below against
`main` with 008 merged before anything is built. Gates as in `specs/008-themes-as-data/plan.md`
"Running the gates".

## Slices

### P0 — Check and decide (serial)

1. Confirm on `main`: `Style.named`, `Style.themes()`, `Style.from_theme(theme,
   relative_to=...)` (public, taking a name or a `.yaml` path), `.yaml` themes,
   `examples/place_card.py`'s
   offline path (it paints from a cache that already holds the payloads, so the providers
   are never called). If any differs, update this plan first.
2. Write ADR 0070, "A preview fixture in the Lynmouth box" (amends 0032): one new fixture
   directory, `preview`, synthetic, inside the Lynmouth box, budget 600,000 bytes; why
   synthetic (every interaction on one card) and why that box (a real coast, a real
   river and real names to letter; the coordinate gate needs a real box). Index row.

### P1 — The fixture (serial)

**Owned.** `tests/fixtures/make_preview.py`, `tests/fixtures/test_make_preview.py`,
`tests/fixtures/preview/*`, `tests/architecture/test_coordinates.py` (one `BOXES` and one
`BUDGETS` entry), `tests/support/paths.py` (`PREVIEW_KEY`, `PREVIEW_DIR`).

1. Red: `tests/fixtures/test_make_preview.py`: the generator's output is byte-identical on
   two runs; every node lies in the box; the payloads load through `vector_layers` with
   `Style()` and the layers hold at least one of each: sea, coastline, lake with an
   island hole, river with a split, stream, major road, minor road, each of the five
   cover classes, a cover patch smaller than `min_patch_px` at 900 px, a settlement node,
   a named landmark node; the track doubles back (some pair of non-adjacent track points
   within 30 m) beside a road and beside the river.
2. Green: the generator builds the features in card metres on a 3 km square around
   (51.225, -3.84), projects them to latitude and longitude with the library's own
   projection, and writes `overpass-<key>.json`, `landcover-<key>.json` and
   `elevation-<key>.json` in the providers' formats (copy the shape of
   `tests/fixtures/lynmouth/`), `track.gpx`, and `README.md` listing each feature and the
   interaction it tests. `<key>` is `Cache(...).key(track, OverpassFeatures("t"),
   OpenTopoData("t"))` with the library's default margins. Names only from the spec's
   list. Elevation: one smooth hill (a Gaussian, 300 m above a 20 m floor) so relief
   shows.

### P2 — The example and its test (serial)

**Owned.** `examples/theme_preview.py`, `tests/golden/test_theme_preview.py`,
`tests/architecture/test_examples.py` (only if it pins the example list).

1. Red: `test_theme_preview.py` (golden-marked), parametrized over `Style.themes()` and the
   `examples/themes/*.yaml` paths, ids the names: the script's `main(theme=..., out=...)`
   writes a 600 px wide PNG; mean RGB pinned per theme (measured once, then literals);
   the placed label names pinned for `default`.
2. Green: `examples/theme_preview.py` (public imports only), modelled on `place_card.py`:
   `--theme` by 008's rule, loaded with `Style.from_theme(theme, relative_to=REPO_ROOT)`
   (no branching on the value in the script), the fixture cache, `display_px` 600, the journal note
   "High tide at Lynmouth" on the route, `Annotations` with the landmark "Foreland
   Point". Docstring with the run command.

### P3 — Docs images and pages (serial)

**Owned.** `tests/support/docs_images.py` (five entries), `docs/images/preview/*`,
`tests/golden/docs/preview/*`, `docs/how-to/write-a-theme.md`, `docs/gallery.md`,
`docs/features/maps-theme-preview-card.md` (deleted).

Register the five images, paint them with `make_docs_images.py`, show them in the theme
how-to under each packaged theme and in the gallery, with captions the captions test
accepts (`*Painted by examples/theme_preview.py with theme="sepia".*`). Delete the note.

### P4 — Review and PR

Fresh-context diff review; full gates; PR `feat(maps): a theme preview card ...` with
`Closes #79`. No mutation run is needed unless an `ink` or `letters` function changed.
