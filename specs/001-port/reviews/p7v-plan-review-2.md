# P7.V plan review 2

## Scope

This review covers "#### P7.V. Revision round 1" in `specs/001-port/plan.md` on
`p7-docs-release`, as of `78cc5d7`. That is the `749c988` revision plus the amendment
recording the maintainer's two answers of 2026-10-25: the fern takes the new paper, and
Skye is accepted up to 12 MB after the 25 m re-trim. I read it against:

- `reviews/p7v-plan-review-1.md`;
- `p7-research.md` sections 10 to 10.5;
- the critique reports `causes.md` and `landmarks.md`;
- the source at this commit.

I made no edit beyond this file. I ran one scratch measurement of the Yr Wyddfa payload's
make-up, and one of the docs-image budget use, both under the session scratchpad.

## What I checked and found true

- **Code facts the revision added, all verified at this commit:**
  - `Cache.key` (`cache.py:95-124`) hashes `margin_m` only. `ensure` (`:210`) uses the
    constants, and `fetch` (`pipeline.py:61`) takes no margin.
  - The consumers are exactly `cli.py:76`, the four examples, `support/golden.py:53`,
    `test_places.py:138` and `record_fixture.py:57`.
  - `make_track.py:46` has `STEP_M = 20.0`.
  - `layers.py:286-298` clips to the card.
  - `journal_geometry` and `card_aspect_min` 1.12 are as stated.
  - `Track.bounding_box(margin_m)`, `Basemap.projection` and `Card.box` exist with the
    shapes P7.V9a's card-box check needs.
  - The water branch is `osm_elements.py:283-286`.
  - `rings_path(rings, holes)` already takes holes and winds them clockwise.
  - `fill_cov` is nonzero.
  - `paint_water` fills every lake ring in one `fill_cov`, so holes will cut.
  - `rivers._ring_at` (`:73-78`) and `_banks_at` exist.
  - `vector_layers.py:226` reads `water_area`.
  - `_seat_cost`, `_pair_cost` and `_swap_seats` are at `placement.py:272-308`.
    `placement.py` has 380 lines.
  - `RASTER_EM` is 128 and `FLANK_MIN` is 0.40.
  - `classify` runs the plaque rule, then `_RULES`, with `monument` ahead of
    `attraction` and `building`, as P7.V5 assumes. `landmark_rank` is in `landmarks.py`.
  - `deposit.py:168` has `span = int(r * 2)`.
  - `paint_route_pen` is at `pen.py:108-117` and uses `job.canvas.px` and `job.scale`.
  - `compose.route` tints the pen plate only when `ink.style == "pen"`.
  - `default.toml:254-257` has `route_pen = true` with `MAJ6-e`.
  - `blend = "normal"` is at `:266,281,296,311`.
  - `paper_plate` is as described. Its two `sheet.noise` draws are the only draws.
    `sheet.gran` exists and makes no draw at read time.
  - `fern.py:135` is the `PaperStyle` line.
  - `MINOR_ROADS` is at `providers/overpass.py:61`.
  - `relief_density` is at `painter/paper.py:20` and is called only from
    `painter/relief.py`.
  - `label_max` is at `style_groups.py:233`.
  - The six `NibSurface(` lines are exactly `lettering.py:80`, `word.py:115`,
    `composition.py:117`, `derwentwater.py:246`, `how_to_own_shapes.py:138` and
    `nib_stages.py:128`.
  - `paint-a-watercolour.md` quotes the `lettering.py` and `composition.py` lines
    (`:339`, `:415`).
  - `fractals.md` quotes no part of `fern.py`'s `main`.
  - ADR numbers 0036 to 0040 are free.
- **Test files named as owners exist:**
  - `test_example_themes.py`, with `THEME_NAMES` and the exact-directory check;
  - `test_reference_pages.py`, with the cli, style-field and `PIGMENTS` checks;
  - `test_style.py`, with three pinned digests;
  - `test_style_groups.py`, with its `PaperStyle` row and digest;
  - `painter/test_smoke.py`;
  - `benchmarks/test_ink.py`;
  - every `tests/examples/*` file named.

  The one exception is P7.V4's test path (S5).
- **The fixture-reference grep of P7.V12a now passes.** It hits only
  `test_places.py`, `test_map_styles.py`, `support/paths.py`,
  `support/docs_images.py`, `test_coordinates.py`, `first-map.md` and `gallery.md`, plus
  `data-policy.md` by its image path. All of them are P7.V12a's owners.
- **The CI fallback is real.** `golden.yml` triggers on `pull_request` with no path
  filter, so a push to PR #28 starts the run.
- **The parallel group P7.V8, P7.V8b and P7.V9b owns disjoint `src/` files.** The only
  overlaps are `test_public_api.py`, `GLOSSARY.md` and the ADR index, and all three have
  shared-file rows. `pyntpot/__init__.py` re-exports none of the new names, so it is not
  a hidden fourth overlap.

## Round-1 findings: status

| Finding | Status |
| --- | --- |
| B1 (the fern) | Resolved, and overtaken by the maintainer's decision. The fern takes the new paper; `"classic"` stays as an option the Stretch-the-paper grid shows. |
| B2 (the whole island) | Resolved. The route runs Kyleakin to Neist Point and Armadale to Uig. The invariant is stated and asserted, and the Sleat sentence is gone. My estimate of the rule's Skye margin is about 14 km, against an expected 15 to 19, which is within the 20 km stop. The card's south edge reaches about Sleat Point and its north edge Rubha Hunish. |
| B3 (the key) | Resolved. The key gains `landcover_margin_m` and omits it at the default. `place_card.py`, `test_places.Place`, the CLI and the registry pass the margins. One residue remains: `cache-layout.md` (S3). |
| B4 (tags) | Resolved. |
| B5 (golden and pin owners) | Resolved. |
| B6 (pen mechanism) | Resolved in mechanism. One residue: the gap mismatch and the stale docstrings (S2). |
| B7 (painter's pigments) | Resolved. |
| B8 (effect, reference pages) | Resolved. |
| B9 (P7.V11) | Resolved. The six scripts are verified. Two residues: `word.webp` and the thumbnail budget (S7). |
| B10 (docs group) | Resolved. One residue: the registry and README seams (S8). |
| B11 (notes) | Resolved, with one gap: the notes ignore the home glyph boxes (S6). |
| S1, S2, S3, S4, S5, S6, S7, S8, S10, S11 | Resolved as proposed. |
| S9 (CI time) | Not resolved. There is now one budget, but its checkpoints stop the round on growth that the round itself later removes (B2 below). |
| C1 | Declined with a reason, which is acceptable. |
| C2 | Taken, and it causes B1 below. |

## Findings

### Blocker

**B1. P7.V9a's new 6 MB fixture budget turns `keswick/`'s budget test red, and it stays
red until P7.V12a.**

- **The cause.** C2 leaves `keswick/` untrimmed: it is 6,663,743 bytes. P7.V9a sets
  "each fixture under 6 MB on disk".
- **The consequence.** `test_a_fixture_directory_is_within_its_budget[keswick]`
  (`test_coordinates.py:113-119`) fails in P7.V9a's own G-here. It would stay red
  through every engine slice until P7.V12a deletes the directory.
- **Fix.** P7.V9a adds `BUDGETS["keswick"] = 7_000_000` (its pre-round size, rounded
  up), with a comment that P7.V12a removes it. Alternatively, P7.V9a lowers
  `BUDGET_BYTES` only for the directories it records, and P7.V12a lowers the default
  when Keswick goes. Name the choice in P7.V9a and in P7.V12a's owners.

**B2. The CI budget's intermediate checkpoints will stop the round on growth that the
round itself removes later.**

- **The cost per card.** The golden job repaints every place card twice: once in
  `test_places.py`, and once in `test_docs_images.py`, which repaints every registered
  image. P7.3's five cards cost +4 minutes locally, about 48 s each.
- **The trajectory:**
  - P7.V9a adds Ambleside and Skye to `test_places.py`. Skye's card is the heaviest yet:
    about 10 MB of payload and a route of about 2,800 points.
  - P7.V10 adds `places/ambleside` and `places/skye` to the registry.
  - Keswick and Trotternish keep being painted in both places until P7.V12a.
  - So the P7.V10 and P7.V11 checkpoints run four or more extra card paints: about +4 to
    +6 minutes. "One over the budget stops the round."
- **The final checkpoint.** The P7.V12 group adds about 20 grid images. P7.V12a's
  route-ink grid (S4) could add up to 12 card paints if it is written naively. So even
  the final number is unbounded as written.
- **Fix:**
  - **When the budget binds.** It binds at the P7.V12-group checkpoint only. The
    earlier runs are recorded for the trajectory and stop the round only if they exceed
    the budget plus what P7.V12a will remove. That is the measured cost of the Keswick
    and Trotternish cards, which P7.V9a records from its baseline run.
  - **The route-ink grid** paints one plate set and composes all twelve cells (S4).
  - **The new grids** paint at the published width, never larger. The tree and fern
    families paint their nine cells at cell size, not at full size and then downsized.

### Should fix

**S1. Yr Wyddfa will land at about its new budget, with no fallback.**

- **The margin.** Under the default fields, P7.V9a's rule gives a 2.08 km overhang
  (grow 1.20 km plus pad 0.88 km). Adding 1 km of headroom gives 3.08 km, so the rule
  rounds up to 4 km.
- **The payload today:**
  - About 1 MB of the minified features is two constant relations, the national park
    (621 KB) and the SSSI (357 KB). The rest scales with area: 2.35 times for the
    features, 1.54 times for the land cover.
  - The review-1 trimmed figures were 2.45 MB of features and 3.53 MB of land cover.
- **The estimate.** That gives about 4.7 MB of features and 5.4 MB of land cover:
  about 10.1 MB against a budget P7.V9a lowers from 12 MB to 10 MB. Simplification is
  reserved for Skye.
- **Fix.** Keep `BUDGETS["yr-wyddfa"]` at its current 12,000,000. P7.V9a widens the
  fixture, so it has no reason to tighten the budget. Or give Yr Wyddfa Skye's rule:
  accept up to 12 MB and set the budget to the measured size. State it beside Skye's
  amended rule.

**S2. P7.V7: the pen strands and the lettering strands use different gaps, and two
public docstrings go stale.**

- **The two gaps.**
  - After the fix, the pen is separated with gap `route_pen_width_px × scale × 2.5`
    (render pixels, along `job.layers.route`, the simplified track).
  - `pipeline.paint`'s strands, which the lettering avoids, keep `route_ink().px × 2.5`
    (display pixels, along `basemap.track`).
  - Under a showcase theme the route drawn is the pen plate. If `ride.px` (5.4 by
    default) is not `route_pen_width_px` (3.0 by default), the labels avoid a line that
    sits a few pixels off the one painted.
- **"One stroke per strand" is wrong.** `separate_strands` returns one displaced
  polyline, not a list of strands. P7.V7 lays that one polyline.
- **The stale docstrings.** `Style.with_route_ink`'s docstring ("the fed width only
  respaces the strands") and `pipeline.paint`'s docstring ("its route ink sets the gap
  between strands") become false. `style.py` is not one of P7.V7's owners.
- **Fix:**
  - When the ride ink's style is `"pen"` and `route_pen` is on, `pipeline.paint` takes
    its gap from `route_pen_width_px`. Put the rule in one helper in `strands.py`, used
    by both sides.
  - Or P7.V10 sets `ride.px = route_pen_width_px` in every showcase theme, and says so.
  - Add `style.py` (docstring only) to P7.V7's owners. It is sequential before P7.V8.

**S3. P7.V1b leaves `docs/reference/cache-layout.md` describing the old key.**
`test_key_inputs_are_named` (`test_reference_pages.py:174-180`) checks only the four
inputs `box`, `margin_m`, `features` and `elevation`, so it stays green while the page
is wrong. Fix: add `cache-layout.md` (the key table) to P7.V1b's owners. Add
`landcover_margin_m` to that test's tuple, noting that it is omitted at the default.

**S4. P7.V12a's route-ink grid is unspecified, and one of its likely treatments renders
nothing different.**

- **What is missing.** The plan names no script, no figure, no image path, no registry
  entry and no list of the "three treatments".
- **Why it matters.**
  - `compose.route` reads only `"pen"` against everything else. `"dotted"` is drawn
    solid (causes report, item 5), so an agent that picks solid, dotted and pen ships a
    grid with two identical columns.
  - A pen plate depends on `route_pen_brush`, which is part of the base digest.
    Varying the brush per cell repaints the card.
- **Fix.** Prescribe:
  - the figure: `examples/how_to_route_ink.py`, `figure="grid"`;
  - the image: `how-to/route-ink-grid.webp`, 720, page, lossy, in the `"P7.V12a"`
    block;
  - the cells: one `paint` (Ambleside, the Ambleside theme), then twelve `compose`
    calls via `Style.with_route_ink(colour=...)` and a ride-ink replacement;
  - the treatments: solid with `blend="normal"`, solid with `"multiply"`, and pen with
    `"multiply"`.

**S5. P7.V4's test path does not exist.** Letters tests live in `tests/unit/letters/`,
a package with `__init__.py`. `tests/letters/` does not exist. Fix:
`tests/unit/letters/test_skeleton_glyphs.py`.

**S6. P7.V9b seats notes against each other only, not against the boxes already
taken.**

- **The gap.** `letter` computes `home, taken = home_labels(...)` before `place`
  (`lettering/pipeline.py:106`). As written, a note can land on the home glyph.
- **The places module.** P7.V10's `examples/places.py` cannot be imported by
  `place_card.py`. `test_examples_import_only_public_names` rejects any import whose
  top level is not the standard library, numpy, PIL or `pyntpot`, so `from places import
  ...` fails.
- **No place option.** `place_card.main` has no option that says which place's
  callouts to use. The pin copies the fixture to a temporary directory, so the
  directory name cannot be relied on.
- **Fix:**
  - Notes are seated against `taken` plus the notes already seated.
  - The curated data is `examples/places.toml` (callouts with optional `lat` and `lng`,
    and the Skye notes), read with `tomllib` by `place_card.py` and by `test_places.py`.
  - `place_card.main` gains `place: str | None = None`. The registry rows pass
    `("place", "<fixture>")`.

**S7. Two of P7.V11's budget calls are fragile or inconsistent.**

- **`word.webp`.** It is a mixed figure: a washed disc with lettering over it. The
  plan's own rule keeps mixed figures (composition, Derwentwater, own shapes) lossy, yet
  it moves `word.webp` to lossless. Pick one, and say why.
- **`gallery/lettering.webp`.** It is lossless at 55.2 KB against the 60 KB thumbnail
  budget. P7.V7b adds specks and P7.V11 sharpens the strokes, so "over budget stops,
  the width may not shrink" is a likely stop. Allow the registry's own rule, a smaller
  width (320), for that one thumbnail.
- **P7.V7b has no budget rule at all.** It regenerates every image, and P7.10's share
  is already at 437 of 500 KB. Give it the same rule: a kind or share overrun stops
  and reports.

**S8. The docs group's registry and README seams are narrower than the edits.**

- **The registry row.** It says "one block each", but P7.V12a, b and c also edit or
  delete entries in older blocks:
  - P7.V12a: P7.4 (`gallery/route-map`), P7.5 (`tutorials/route-map`), P7.7, P7.8
    and P7.13;
  - P7.V12b: P7.9 and P7.10;
  - P7.V12c: P7.6b (the gasket).
- **The README.** Its owner is "the hero image and its caption only". The strip cell for
  `gallery/route-map.webp` (README `:48`) has the alt text "A hand-painted map of
  Keswick", which goes false when P7.V12a repaints it on Ambleside.
- **Fix:** list the edited old entries per slice in the shared-file row. Add "the
  route-map cell's alt text in the README strip" to P7.V12a's owners.

**S9. P7.V12d's "sync test" is not named.** `test_tutorials.py`'s marker regex
matches only `examples/<stem>.py` (`:32`). Fix: P7.V12d owns `test_tutorials.py`,
which gains a `<!-- from examples/drawings/<name>.svg -->` form. No other P7.V12 slice
edits that file.

**S10. P7.V10's 60% painted-land target on Skye may conflict with the card-box
invariant, and the plan does not say what happens then.**

- **The lever that works.** `ribbon_mult` widens the painted ribbon without moving the
  card: the card grows by `fitted × card_grow_mult`, not by `ribbon_mult`.
- **The levers that do not.** `ribbon_max_m`, `card_grow_mult` and `card_pad_frac`
  grow the card past the 1 km headroom.
- **What counts as painted.** By the plan's definition the sea counts as "painted
  land". On Skye that is most of the score.
- **Fix:**
  - Name `ribbon_mult` as the first lever for Skye and Yr Wyddfa.
  - Rename the measure "painted area".
  - If 60% is unreachable within the invariant, record the best value and continue.
    P7.V13 judges the result.

**S11. Assembling the Skye track by hand is the hard part of P7.V9a, and the plan
skates over it.**

- **The scale of the job.** About 280 km on roads that OSM splits into several hundred
  ways. Junctions such as A851 by A87 fall mid-way, which needs `ID:FROM:TO` with node
  ids. The track has seven spurs or legs. `make_track.py` has no routing.
- **Fix.** The slice may write an uncommitted scratch helper that orders the listed
  ways by `ref` between the via nodes and emits the `--ways` argument. The ordered id
  list goes in the README, as it does today. Or give `make_track.py` a
  `--chain-ref REF` option.

**S12. P7.V7b's speck threshold is defined on an undefined sheet, over a field whose
scale changes with the caller.**

- **The field's scale varies.** `sheet.gran` is min-max normalised fBm at the caller's
  `gran_px`:
  - 3 px in `lettering` and `composition`;
  - 8 px in most examples;
  - 18 render px or more on a card, from `gran_m`;
  - 60 px on `wash_stages`' slow sheet.
- **What follows.** "`FOX_SPECK_LEVEL` set on the default sheet" names no sheet. A fixed
  level gives a different coverage and speck size per figure. On the 60 px sheet it
  gives rust blobs of tens of pixels until P7.V12b turns foxing off there. The
  small-sheet test cannot see any of this.
- **Fix:**
  - Threshold by rank, with no constant to tune and no draw:
    `level = np.quantile(sheet.gran, 1 - FOX_SPECK_AREA)`, where `FOX_SPECK_AREA` is
    0.003.
  - Run the coverage and speck-size assertions on two named sheets: the Lynmouth card's
    job sheet, and a 360 by 240 sheet at `gran_px` 3.
  - Move "foxing 0 in the reference and explanation figures" from P7.V12b into P7.V7b,
    so those figures are not regenerated twice and never ship the blobs.

### Consider

- **C1. The Compose-the-painting grid repeats the Mix-two-pigments grid.** `km_glazing`
  off and on is already the mixing rung's multiply row against its Kubelka-Munk row.
  A grid about composition would vary what composing adds: the name's backing wash
  off and on, by two hand seeds, or the order of the brush stroke and the wash. The
  Stretch-the-paper grid (`paper_tooth` by `paper_edge`) is good. It is now the
  showcase for `"classic"`.
- **C2. Name where `NIB_SCALE` lives.** It could be one constant per example, or the
  same literal in all six. Also say that P7.V12b's new lettered figures (the "Letter a
  name" grid, the nib grid and the hand-seed sheet) use P7.V11's scale-2 pattern.
  `lettering.py` has no `size` option, so P7.V11's test "at a small size" runs at 360
  px, or the slice adds the option.

## The reviser's open points

- **Workflow dispatch fallback.** It is sound: `golden.yml` has `pull_request` with no
  path filter, so the PR run stands in. Two things need saying:
  - **The measure:** the `ubuntu-latest` golden job's duration.
  - **The baseline:** the run of the PR head at the base commit.
- **The speck threshold, 0.8% of the width.** It is a fine upper bound in principle, but
  only if it is measured on real sheets and the level is a quantile (S12).
- **The two grids.** Stretch-the-paper is right. Compose-the-painting duplicates the
  mixing rung (C1).

## Verdict

**BLOCK.**

- **B1** turns a gate red from P7.V9a to P7.V12a, in slices that cannot fix it.
- **B2** makes the round's own CI rule stop it at P7.V10 on growth that P7.V12a
  removes, and leaves the final cost unbounded.

Both blockers are small to fix in the plan text. S1, S2, S4 and S6 are the should-fix
items most likely to cause a stop or a wrong result if left. Everything else round 1
raised is resolved.
