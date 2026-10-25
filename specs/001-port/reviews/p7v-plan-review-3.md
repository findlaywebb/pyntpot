# P7.V plan review 3

## Scope

This review covers "#### P7.V. Revision round 1" in `specs/001-port/plan.md` on
`p7-docs-release` at `4cbcb7a`, the revision after plan review 2. I read it against:

- `reviews/p7v-plan-review-{1,2}.md`;
- `p7-research.md` sections 10 to 10.5;
- the critique reports `causes.md` and `landmarks.md`;
- the source at this commit.

I checked out nothing and edited nothing beyond this file. I painted nothing.

## What I checked and found true

- **`route_pen_brush` is in the base digest.** `RouteStyle` (`style_groups.py:156-159`)
  is the `route` group, and `"route"` is in `BASE_GROUPS` (`style.py:56-65`). A second
  pen brush is therefore a second plate set.
- **`separate_strands` returns one list.** It returns one displaced polyline
  (`strands.py:41-43`), the same list when nothing doubles back.
- **The strand gap today.** `pipeline.paint` computes `route_ink().px *
  STRAND_GAP_WIDTHS` (`pipeline.py:123`).
- **The pen plate today.** `paint_route_pen` lays `job.layers.route`, the track
  simplified at `CARD_TRACK_EPS_M` = 3 m (`layers.py:72`, `:284`). `basemap.track` is
  the unsimplified `pts` (`layers.py:325`).
- **The two stale docstrings exist as quoted.** `style.py:171` and `pipeline.py:111`.
- **`cache-layout.md` and its test.**
  - The page's key table names `box` and `margin_m` (`cache-layout.md:42-43`).
  - `test_key_inputs_are_named` (`test_reference_pages.py:174-180`) checks the four
    names the plan says.
- **`make_track.py` has the options the plan builds on:**
  - `--list-ways`, `--ways` with `ID:FROM:TO`, and the `--via-node` checks;
  - `STEP_M = 20.0` at `:46`;
  - `chain` with the 5 m join rule.
- **Imports.** `tomllib` is in the standard library, so `place_card.py` may import it
  under `test_examples_import_only_public_names`.
- **`place_card.main`'s options and lettering.** It takes `theme` and `size` and has
  `# noqa: PLR0913` already. Ruff does not select `ARG`, so P7.V9a's not-yet-read `place`
  keyword lints clean. It letters with `letter(plates, basemap, None, style)`, so P7.V10
  has one call to change.
- **The `NibSurface(` lines.** All six are at the lines named. The signature
  (`canvas, scale, dark, gran_px`) takes the plan's scale-2 form, and `nib_plate`
  writes the plate at the canvas's size, so P7.V11's "twice the width" test holds.
- **Placement code.** `home, taken = home_labels(...)` is at `lettering/pipeline.py:106`.
  `_place_flat` (`placement_flat.py:136`) takes `Terms`, so `notes.py` can call it with
  the taken boxes.
- **Coordinates.** The coordinate gate scans `examples/` and `specs/` as well
  (`_text_scan.py:7`). The curated points in `places.toml` must therefore lie in a
  fixture box. Each one named does.
- **No unowned Keswick or Trotternish fixture consumer.** The consumer grep, widened to
  `places/keswick` and run over `src`, `.github` and `mkdocs.yml` as well, finds only
  P7.V12a's owners. Two residues are covered in S5.
- **ADR numbers.** 0036 to 0040 are free on every branch: `p7-docs-site` and
  `release-0.1.0` stop at 0035.
- **Budgets.** `docs/images/` holds 1.81 of its 7 MB. No `src/` file the round edits is
  near 400 lines except `placement.py`, whose split is planned.
- **The assumptions the reviser flagged.** Both are confirmed; see the end of this
  review.

## Round-2 findings: status

| Finding | Status |
| --- | --- |
| B1 (Keswick's budget) | Resolved. P7.V9a sets `BUDGETS["keswick"] = 7_000_000`, and P7.V12a's owners remove it. |
| B2 (CI checkpoints) | Resolved. The budget binds at the P7.V12-group checkpoint only. The earlier runs are recorded with the Keswick and Trotternish allowance. Grids paint at their published size. |
| S1 (Yr Wyddfa's size) | Resolved for the budget. The new fallback simplifies a walking map; see B3. |
| S2 (one strand gap) | Resolved for the lettering. The helper as written makes a base plate read the route ink; see B1. |
| S3 (`cache-layout.md`) | Resolved. |
| S4 (route-ink grid) | Resolved in substance. Residues remain: the owner row, the plates directory and the row strands (S1). |
| S5 (P7.V4's test path) | Resolved. |
| S6 (notes against `taken`; places data; `place` option) | Resolved. |
| S7 (encodings) | Resolved in intent. The quality mechanism is unowned where P7.V11 needs it (S3). |
| S8 (registry and README seams) | Resolved. |
| S9 (sync test) | Named, but it checks nothing as written (S4). |
| S10 (Skye's painted area) | Resolved. |
| S11 (Skye's track) | Taken as `--ref`. Ordering, the box and forks are unspecified (S6). |
| S12 (speck threshold) | Resolved. The golden check that follows it is wrong (B2). |
| C1, C2 | Taken. |

Round-1 spot checks: B3 (the key), B6 (the pen mechanism), B9 (the six scripts) and B10
(the consumer table) still hold at this commit.

## Findings

### Blocker

**B1. P7.V7's helper makes the pen plate, a base plate, read the route ink, which the
base digest does not cover.**

- **The contract.** ADR 0005 (":137, changing an ink repaints no plate") and ADR 0027
  (":104-105, a fed route ink repaints no plate") make the route inks part of `digest()`
  only. `paint` reuses plates whose manifest carries `Cache.base_key`, which is the
  basemap hash plus `base_digest()` (`cache.py:168-181`).
- **The defect.** P7.V7 has `paint_route_pen` call `strand_gap_px(style)`. That helper
  reads `route_inks.ride.style` and, for a non-pen ride, `route_inks.ride.px`, so the
  pen plate now depends on the route ink. Two styles with equal base digests then paint
  different pen plates, and the cache hands back whichever was painted first.
- **Where it shows.**
  - **Solid then pen, same base groups.** The pen plate is painted with the solid gap,
    13.5 px for the default 5.4 px ride. Compose then tints that stale plate, while
    `plates.strands` uses the pen gap of 7.5 px. The labels avoid a line a few pixels off
    the painted one, which is the fault S2 set out to fix.
  - **A fed width on a solid ride.** `with_route_ink(width_px=...)` changes what a fresh
    pen plate would be, and `test_a_fed_width_respaces_the_strands_without_repainting`
    still passes. No test catches the inconsistency.
- **Fix.**
  - The pen plate's gap is `route.route_pen_width_px * STRAND_GAP_WIDTHS * job.scale`
    always. It reads base-group fields only, and the pen plate is drawn on a card only
    when the ride is a pen, where this is exactly the helper's value.
  - `strand_gap_px(style)` stays as the one rule for `pipeline.paint`.
  - Add a test: a solid-ride style and a pen-ride style with the same base groups
    paint byte-identical pen plates.
  - State the invariant in `pen.py`'s docstring.

**B2. P7.V7b's golden check states a false fact, so the slice will stop on its own
verification.**

- **The claim.** "Away from the edge band (a tenth of the width) the change is the
  foxing only: the run log records the largest channel change there and confirms it sits
  on specks."
- **Why it is false.** The classic vignette is `exp(-edge_px / (w * 0.34))` at strength
  0.05 (`paper.py:53-54`). It darkens deep into the sheet: 3.7% at a tenth of the width
  in, and 1.9% at the centre of a 3:2 sheet. The warm decay `w * 0.08 * (0.5 + n26)`
  falls to between 0.4% and 2.2% at a tenth in, and to 0.3% or less at the centre. So
  every image's interior brightens by about 1.5 to 3.5%, which is 4 to 9 of 255,
  smoothly and everywhere.
- **The smudges.** The classic foxing smudges (`noise(120)` above 0.80) disappear, and
  they are not specks either.
- **What follows.** The largest interior change will not sit on specks. Under the plan's
  "stops and reports if a fact here no longer holds", the slice stops.
- **Fix.**
  - Replace the check with a unit test on one seeded sheet. With `paper_vignette=0.0`
    and `paper_foxing=0.0`, the `"warm"` and `"classic"` plates are equal (to 1e-6) more
    than a tenth of the width in. That proves the draws and the tooth are unchanged.
  - The run log records the interior change on the goldens as the vignette's narrowing,
    the smudges removed and the specks added. Nothing else is expected.
  - Drop the same sentence from decision 3's fern paragraph ("its change is foxing
    only").

**B3. The Yr Wyddfa fallback simplifies a walking map by about two display pixels,
against decision 6.**

- **The decision.** Decision 6 says "no coordinate rounding for the walking maps … the
  Skye fixture is simplified to its card's scale".
- **The rule as written.** P7.V9a applies Skye's rule to Yr Wyddfa: "if over 10 MB,
  re-trim at `--simplify-m 25`".
- **Why it fires.** Review 2's estimate was 10.1 MB, so the rule is likely to trigger.
- **Why the justification does not transfer.**
  - "Both under half a display pixel at the 720 px card" is true for Skye, at about
    110 to 140 m per display pixel.
  - It is not true for Yr Wyddfa. Today's Lynmouth card is 6.2 m per display pixel at
    900 px. Yr Wyddfa's wider card will be roughly 10 to 15 m per pixel at 720 px, so
    25 m is about 2 px of error.
  - The error falls on the Crib Goch ridge paths and the lake shores that the map's idea
    rests on.
- **Fix.** Yr Wyddfa is never simplified. Its budget is the measured trimmed size,
  rounded up to the next 0.5 MB, up to 12 MB (its budget today). Over 12 MB stops and
  reports. Simplification stays Skye's alone, with the slice recording `mpp_display` as
  planned.

### Should fix

**S1. P7.V12a's route-ink grid: the owner row forbids the code, the two plate sets would
overwrite each other, and the solid row's strands use the pen gap.**

- **The owner row.** It lists `examples/how_to_route_ink.py` for "their docstrings and
  help text naming Keswick" only. The grid needs new code: a `figure` keyword and a
  `theme` keyword (`main` has neither today), and the grid loop. Add "the `figure` and
  `theme` options and the grid figure" to the row.
- **The plates directory.** It is one directory per payload key
  (`cache.py:138-140`), and the file names are fixed (`paper.webp`, `wash.webp`,
  `pen.webp`). A second `paint` into `cache.plates_dir(key)` under `MAJ3-e` overwrites
  the `MAJ1-e` set. Prescribe one directory per pen brush, for example
  `cache.plates_dir(key) / brush_id`.
- **The row strands.** Each row's strands come from `paint`'s style (`pipeline.py:123`).
  Have each row call `paint(basemap, row_style, its_set_dir)`. The plates are current,
  so nothing repaints, and the solid row's strands then use its own gap.
- **Lettering.** State that the cells are unlettered (`Lettering((), (), None)`, public in
  `pyntpot.maps`). At 180 px, the hand's display-pixel sizes would swamp a cell.

**S2. P7.V10: the lat and lng rule misses the Y Fenni stops, and the plan does not say
what to pin when the placer drops a curated name.**

- **Callouts that will be skipped.** A name-only callout is skipped silently when no
  candidate matches. The plan names only Glaslyn and Llyn Llydaw as needing coordinates,
  and checks names against candidates "for Ambleside". These will also be skipped:
  - **Angel Bakery.** `landmarks.md`'s Payload? column says "No (shops are not
    queried)".
  - **Bean & Bread, Rate of Rise and Shepherd's.** These are shops too, and after P7.V5
    shops are never offered anyway.
  - **Castell y Fenni.** OSM's name is "Castell Y Fenni"; the matching is exact.
- **Callouts the placer drops.** `landmarks.md`'s own six-callout run on Y Fenni dropped
  one for space. The test "pins … every curated name" then fails, and the plan gives no
  rule.
- **Fix:**
  - Every callout carries `lat` and `lng` from its OSM element, unless the slice has
    matched its exact lettered name in `basemap.candidates`. Apply this at every place,
    not only Ambleside.
  - Order each place's callouts by priority, with Tŷ Melin and the castle first on
    Y Fenni (decision 8).
  - If the placer drops a curated name, pin what is lettered, record the dropped name,
    and continue, unless the dropped name is Tŷ Melin, which stops and reports.

**S3. The per-entry quality is created "only under the budget rule" in P7.V7b, but
P7.V11 relies on it and owns neither file it needs.**

- **The gap.** If P7.V7b never overruns, `DocsImage` has no quality field and
  `make_docs_images.py` has no per-entry quality. Today's lossy quality is a literal 90
  (`make_docs_images.py:63`).
- **Not owned.** P7.V11's owners include the registry but not `make_docs_images.py`.
- **Upward only.** "Lossy WebP at quality 95" makes an already-lossy (q90) entry larger.
  The fallback helps lossless entries only, and the plan does not say what happens to a
  lossy entry over budget.
- **Fix:**
  - P7.V7b always adds `DocsImage.quality: int | None = None`, meaning today's
    per-encoding default, and threads it through `_encode`. It is a field, not an
    `options` pair, since options are passed to `main`.
  - State that the q95 fallback is for lossless entries.
  - A lossy entry over budget stops and reports.

**S4. P7.V12d's `.svg` marker form checks nothing as written.** `test_tutorials.py`'s
sync runs over `_tutorial_pages()`, which returns only `paint-a-watercolour.md` and
`first-map.md` (`:45-47`). A new marker regex form never sees `vector-drawing.md`. Fix:
P7.V12d also adds `docs/tutorials/painting-with-python/vector-drawing.md` to
`_tutorial_pages()`, and only that page. `curves.md` and `fractals.md` are unsynced
today, and pulling them in would collide with P7.V12c.

**S5. P7.V12a: two Keswick residues the grep cannot see.**

- **The coordinate gate's self-test.** `test_a_pair_split_across_two_boxes_is_caught`
  (`test_coordinates.py:108-111`) asserts that `"lat 54.60 lon -3.15"` (the Keswick box)
  is in a box, and pairs it with Trotternish's longitude. It goes red when the two boxes
  are deleted, and the owner text says "the two entries" only. Name it: it is rewritten
  with Ambleside's and Skye's values.
- **The tutorials index.** `docs/tutorials/index.md:8` says "paint a route map from the
  Keswick track". It is not owned by any slice. Add that line to P7.V12a's owners.

**S6. P7.V9a's `--ref` is underspecified at three points the Skye track will hit.**

- **Order.** The rule "the chained pieces join `--ways` pieces in the order given"
  cannot hold with two argparse options: each appends to its own list. The Skye route
  interleaves refs and named ways (the Glen Brittle road between the B8009 legs).
- **The box.** "Every highway way in the given box" names no box argument for `--ways`
  mode.
- **Forks and closed ways.** Roundabouts and dual or split carriageways sharing a ref
  give a fork, or a closed way, that `chain`'s rules reject only as "joins at both
  ends". The plan's tests cover gaps only.
- **Fix:**
  - One ordered list: a `--ways` item may be `ref=REF` or `ref=REF:FROM:TO`, beside `ID`
    and `ID:FROM:TO`.
  - A `--box S,W,N,E` argument, on the command line only, as `--list-ways` does.
  - A ref whose ways fork, or that include a closed way, fails naming the way ids. The
    slice then lists that stretch's ids explicitly.
  - Add one test: a fork fails.

### Consider

- **C1. P7.V7's pen and strands lay different inputs.** The pen is laid along the 3 m
  simplified track, the strands along the full track. At Lynmouth's 6.2 m per display
  pixel this is a fraction of a pixel, so the "within a pixel" test should hold. If it
  fails, separate `card.xy` of `basemap.track` for the pen too, scaled by `job.scale`.
  The two are then the same line by construction.
- **C2. Name the "Lynmouth job sheet" call.**
  - The call is `PaintJob.begin(fetch(...), Style.default(), tmp).sheet`.
  - Build it in a module-scoped fixture: the sheet is immutable, at 1800 by 1457 render
    pixels with `gran_px` 22.4, so 0.8% of the width is 14.4 px.
  - `tests/unit/maps/painter/jobs.py` already builds jobs this way. Put the check beside
    it, for example in the owned `test_smoke.py`, rather than in `tests/unit/ink/`,
    where no test imports `maps` today.
  - Run the 2% edge check with `paper_tooth=0`. The tooth alone is ±4%.

## The reviser's assumptions

- **Rebuilding the job sheet "as `paint_plates` builds it": confirmed.**
  - `paint_plates` calls `PaintJob.begin(basemap, style, out_dir)` (`plates.py:99`).
    That builds the sheet from the card's render size, `gran_m / mpp` and the paper
    fields, with no other input.
  - A test can fetch the Lynmouth basemap from the fixture with `FixtureFeatures` and
    `FixtureElevation`, as `test_route_ink.py` does, and call `PaintJob.begin`. Nothing
    is mocked and nothing is painted.
- **MAJ3-e reading as dry: acceptable.**
  - Row 3 is drier than row 1 on every dry-brush term (`brush.py:28-66`):

    | Term | Row 1 | Row 3 |
    | --- | --- | --- |
    | `dry` | 0.15 | 0.42 |
    | `gap` | 0.03 | 0.14 |
    | `texture` | 0.32 | 0.55 |
    | `bristles` | 26 | 16 |
    | `bleed` | 1.5 | 0.9 |

    That fits the investigation's "distinct, finer line".
  - The sheet's plainly dry row is 4 (`dry` 0.72, `gap` 0.28).
  - If P7.V13's critique says the dry cell does not read as dry, the fix is to change
    `MAJ3-e` to `MAJ4-e` in the grid: one constant, the same two paints. Say so in
    P7.V12a.

## Verdict

**BLOCK.**

- **B1:** a base plate reads a non-base field. That breaks the recorded contract of
  ADRs 0005 and 0027 and lets the plate cache serve a stale pen plate.
- **B2:** P7.V7b's done-check is false and will stop the slice.
- **B3:** Yr Wyddfa's fallback simplifies a walking map against decision 6.

All three are a sentence or two in the plan. S1 and S2 are the should-fix items most
likely to cause a wrong image or a red pin.
