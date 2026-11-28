# 008a — plan

Revision 2 (2026-11-28), after the plan review (`review-plan.md`, verdict BLOCK, 8 blocking
and 6 should-fix findings, all accepted). Checked against `main` at `3817978`. Where this
plan says "review finding N", the fix that finding prescribes is part of this plan, word for
word; this file states the decisions and where each one is used.

Gates: `uv run ruff format --check . && uv run ruff check .`, `uv run ty check`,
`uv run lint-imports`, `uv run pytest -n auto --dist loadgroup --golden-tolerance` (the golden
tests run with `-m golden`, as `specs/008-themes-as-data/plan.md` "Running the gates" says).

## Approach

A synthetic fixture, `tests/fixtures/preview/`, made by a committed generator, lies inside
the Lynmouth box and holds every feature and meeting a theme can get wrong. An example script
paints it in any theme; a golden test paints it in every theme. No library code changes: this
is fixtures, an example, tests and docs. No `ink` or `letters` function changes, so no
mutation run.

## Decisions

1. **The card is framed from the track, not the fetch box** (review finding 1). The track's
   box is 1.5 km east to west by 1.6 km north to south (each within 50 m), centred on
   (51.225, -3.84). Margins are the library's defaults (`Cache(dir)`, `FetchMargins()`):
   the features fetch box `track.bounding_box(MARGIN_M)` is then about 4.5 x 4.6 km, inside
   the Lynmouth box, and contains every theme's card. No `PREVIEW_MARGINS`.
2. **Data region.** Every element lies inside the features fetch box, rounded inward by 1 m.
   The coast, the major road, the river and the minor road run to that box's edge. Every
   listed feature lies within 350 m of the track's box (inside the smallest, y-fenni, card).
   Land cover is written only inside the features fetch box; the README says so.
3. **Elements:** the table in review finding 5, verbatim, ids 1, 2, 3, ... in writing order,
   unique across both Overpass payloads; relation members carry `type`, `ref`, `role`,
   `geometry`. No road `ref`. Names only from the spec's list.
4. **Small patches** (finding 4): threshold 400 display px² at a 900 px display width; one
   `meadow` and one `heath` patch, each 50 x 50 m, each against a larger patch of another
   class.
5. **Elevation** (finding 10): 0 m at every grid point on the sea side of the coast (the
   island's ring is land); elsewhere a 20 m floor plus a Gaussian 300 m high, sigma 500 m,
   centred inside the smallest card on the land side, at least 400 m from the coast; whole
   metres. Grid `n = 80` (`ELEVATION_SAMPLES`), box `track.bounding_box(MARGIN_M)`.
6. **The track doubles back** (finding 13): some two points at least 400 m apart along the
   track lie within 30 m of each other; one retraced stretch runs within 20 m of the minor
   road for at least 300 m, another within 40 m of the `East Lyn River` for at least 300 m;
   it crosses the `West Lyn River` stream once. Sampled every 20 m.
7. **Generator order and the key** (finding 6): build the track in metres; convert through
   one `Projection(lat0=51.225, lat_ref=51.225, lng_ref=-3.84)` `.inverse`; write
   `track.gpx` at six decimals in the Lynmouth `track.gpx` layout, no times; read it back
   with `Track.from_gpx`; `key = Cache(out_dir).key(track, OverpassFeatures(CONTACT),
   OpenTopoData(CONTACT))`; lay the features out through the same projection; write the
   elevation as `ElevationGrid(...).to_json()`. `PREVIEW_KEY` in `tests/support/paths.py` is
   the pinned literal; the fixture test asserts it equals the computed key.
8. **Deterministic bytes** (finding 9): coordinates rounded to seven decimals, elevation to
   whole metres, `json.dumps(..., separators=(",", ":"))` plus a trailing newline;
   `"generator": "tests/fixtures/make_preview.py"`; `osm3s` is
   `{"timestamp_osm_base": "2026-11-28T00:00:00Z", "copyright": "Synthetic data made by
   tests/fixtures/make_preview.py; not OpenStreetMap data."}`. The generator takes an output
   directory; its test writes to `tmp_path` and asserts byte equality with the committed files.
9. **Generator split** (finding 15): `tests/fixtures/make_preview.py` (layout in metres, the
   element table, `main(out_dir)`) and `tests/fixtures/preview_payloads.py` (projection,
   rounding, the three payload writers, the GPX and README writers). Each under 400 lines.
10. **The example's interface** (finding 2), in `examples/theme_preview.py`:
    `preview(style, *, track, cache_dir, features, elevation) -> tuple[Image.Image, Lettering]`
    and `main(out_dir, *, track, cache_dir, features, elevation, theme="default") -> Path`.
    `main` always calls `Style.from_theme(theme, relative_to=REPO_ROOT)`, copies the style with
    `card.display_px = 600` as `place_card.py` does, calls `preview`, saves
    `out_dir / "preview.png"`. Annotations: `Landmark(name="Foreland Point")` with no
    coordinates; `JournalNote(text="High tide at Lynmouth", lat=route.lat[NOTE_POINT],
    lng=route.lng[NOTE_POINT])`, `NOTE_POINT` a named index the README records as the
    riverside stretch. No coordinate literal in the example. The `__main__` block takes
    `--theme` and `out_dir`, copies `tests/fixtures/preview/` into a
    `tempfile.TemporaryDirectory()`, and builds both providers with `budget=0` at
    `http://127.0.0.1:9`. Public imports only; no use of the retired word "callout".
11. **Golden test** (finding 7): `CARD_SIZE` a measured literal (width 1200: a 600 px card is
    a 1200 px PNG at supersample 2); mean RGB literals within 1.5; the set of distinct label
    names pinned for every theme, read from `preview(...)`'s `Lettering`; parametrized over
    `list(MEAN_RGB)` with ids. A non-golden test asserts
    `set(MEAN_RGB) == set(Style.themes()) | {example theme paths}`.
12. **ADR 0072** (finding 11), "A preview fixture in the Lynmouth box", amends 0032 for
    `preview/` only: track and payloads made up by `make_preview.py`, not built or recorded,
    not ODbL; the generator holds its centre inside the box; real names stand at made-up
    places by design; default margins; budget 600,000 bytes; its card test is
    `tests/golden/test_theme_preview.py`. Index row in `docs/decisions/README.md`.
13. **Docs registration** (finding 8): three edits to `tests/support/docs_images.py` (import,
    `**SHARES_008A` in `SLICE_SHARE_BYTES`, `IMAGES += IMAGES_008A`); five entries
    `DocsImage(f"preview/{name}.webp", "theme_preview", (("theme", name),), "preview", 600,
    "page", "webp-lossy", "008a-preview")` for default, pen-and-ink, sepia, bold, winter;
    `SHARES_008A = {"008a-preview": <measured total, rounded up to 50 kB>}`. Captions
    ``*Painted by `examples/theme_preview.py` with `theme="sepia"`.*``. Placement in the how-to
    and the gallery as finding 8 says.
14. **The credit** reads "© OpenStreetMap contributors" over synthetic data because it is the
    provider's credit; kept, and said in the fixture README (finding 16).

## Files to touch

- `docs/decisions/0072-preview-fixture-in-the-lynmouth-box.md` (new), `docs/decisions/README.md` (row)
- `tests/fixtures/make_preview.py`, `tests/fixtures/preview_payloads.py` (new)
- `tests/fixtures/test_make_preview.py` (new; non-golden)
- `tests/fixtures/preview/` (new: `track.gpx`, three payloads, `README.md`)
- `tests/support/paths.py` (`PREVIEW_KEY` only)
- `tests/architecture/test_coordinates.py` (`BOXES`, `KEYS`, `BUDGETS` entries and the import)
- `examples/theme_preview.py` (new)
- `tests/golden/test_theme_preview.py` (new; golden) and the non-golden theme-set test (in
  `tests/fixtures/test_make_preview.py`)
- `tests/support/docs_images_008a.py` (new), `tests/support/docs_images.py` (three edits)
- `docs/images/preview/*.webp`, `tests/golden/docs/preview/*` (painted by `make_docs_images.py`)
- `docs/how-to/write-a-theme.md`, `docs/gallery.md`
- `docs/features/maps-theme-preview-card.md` (deleted)
- `specs/008a-theme-preview-card/tasks.md`, `spec.md` (ticks)

## Files to leave alone

- Everything under `src/`: the preview needs no library change. If a fixture feature is not
  painted, fix the fixture, not the painter.
- `tests/fixtures/make_track.py`, `record_fixture.py`: the preview has its own generator.
- `tests/architecture/test_examples.py`: it pins only the rung scripts.
- The rest of `tests/support/docs_images.py`: over budget (#212), three edits only.
- `examples/place_card.py`, `examples/map_styles.py`: models, not callers.

## Test plan

| Acceptance criterion | Test |
|---|---|
| Fixture, generator, deterministic, README | `test_make_preview.py`: generator to `tmp_path` byte-equal to committed files; `PREVIEW_KEY` equals the computed key |
| Coordinates in the box; budget | `test_make_preview.py` checks every lat/lon in all payloads, the elevation bbox/lats/lons and the GPX against `BOXES["preview"]`; `test_coordinates.py` with the new entries |
| Features meet each other | `test_make_preview.py` on `fetch(...)`'s `Basemap` with `Style()` (finding 3's assertions); small-patch areas at 900 px (finding 4); doubling back (decision 6); per theme, card inside the fetch box and lanes painted (all but `ambleside-hero`) (finding 1) |
| Real names only | `test_make_preview.py`: every `name` tag is in the spec's list |
| Example, offline, 15 s | golden test runs it through budget-0 providers; one timed CLI run recorded in the PR body |
| Golden over every theme | `tests/golden/test_theme_preview.py` (decision 11) and the non-golden theme-set test |
| Docs images | `make_docs_images.py`, `tests/docs/test_docs_images.py`, `test_captions.py` |
| Note deleted, `Closes #79` | PR body |

## Slices (serial; one agent per slice may be dispatched, files as owned)

- **P1 ADR and fixture.** Owns ADR 0072 and the index row, the two generator modules, the
  fixture dir, `test_make_preview.py` (fixture half), `paths.py`, `test_coordinates.py`.
  Red first: the fixture test against an empty dir. Then the generator, run once, commit its
  output.
- **P2 Example and goldens.** Owns `examples/theme_preview.py`,
  `tests/golden/test_theme_preview.py`, the per-theme frame checks and the theme-set test in
  `test_make_preview.py`. Measure `CARD_SIZE`, mean RGB and label sets once, pin literals.
  Timed CLI run.
- **P3 Docs.** Owns `docs_images_008a.py`, the three `docs_images.py` edits, the images and
  masters, the how-to, the gallery, the deleted note.
- **P4 Review and PR.** Fresh-context diff review against this plan; full gates; PR
  `feat(maps): a theme preview card that holds every feature and the awkward meetings between them`
  with `Closes #79`. Comment the branch on #79 at the start of P1.

## Delegation

The main context integrates: it runs the full gates after each slice and checks the seams
(the example reads the fixture P1 wrote; the docs runner calls the example's `main`). P1 and
P2 may go to a `plan-slice-implementer` each, serially. The diff review is a fresh-context
agent.
