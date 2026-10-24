# P7 plan review 2

## Scope

I reviewed `specs/001-port/plan.md` on `p7-docs-release`. The brief named HEAD `b3e70c8`,
the revision after round 1. While I was reviewing, the maintainer's Y Fenni answer landed
as `ad54732`, which adds P7.3b, ADR row 0035, a `tasks.md` line and the order diagram. I
reviewed both commits. The parts I read:

- the section "### P7. Docs and first release";
- the ADR numbers table and the paragraph under it;
- the P7 section of `specs/001-port/tasks.md`, and P9's order line;
- `docs/features/maps-prefer-welsh-names.md`;
- the round-1 review, `reviews/p7-plan-review-1.md`.

Settled, and not reopened here:

- the round-1 maintainer choices;
- the Yr Wyddfa route;
- the Keswick, Trotternish, Oxford and Y Fenni routes;
- Keswick as the hero and tutorial fixture;
- the Y Fenni card reading "Y Fenni".

How P7.3b builds the last of these is reviewed.

I made no edits beyond this file. I ran three things:

- `uv run pytest -m golden` (exact, all 22 passed here);
- the plan's dash gate (exit 1, so it passes today);
- a scratch script that ran the seven ink and letters rungs and encoded their outputs, and
  `tests/golden/lynmouth/map.png`, at the plan's encodings, to test the budgets.

## What I checked

**The Welsh-name test edits (P7.2): every line number and length holds.**

- `test_font.py`: lines 13 to 15 hold Monmouth, Monmouth Castle and Abergavenny in
  `MAP_STRINGS`, and line 33 holds `"Abergavenny 12%"`.
- `test_hand.py:135` is the docstring "`Abergavenny` and `Wllllllllll`".
- `test_picks.py:85,86,91` hold the names.
- `test_placement.py:53` and `test_label.py:79` hold "Monmouth Castle".
- `test_placement_names.py:108 to 129` holds Monmouth (and its War Memorial) and
  Abergavenny.
- The lengths match: Machynlleth and Abergavenny are both 11, Trefynwy and Monmouth both
  8, and Trefynwy Castle and Monmouth Castle both 15.
- "Y" is not in `QUALIFIERS`, so `name_stem("Y Fenni")` stays whole. No test pins a
  measured width of these strings, so the re-pin rule will likely never fire.
- A repo-wide grep finds no other English Welsh place names outside `specs/`, apart from
  CONTRIBUTING.md and `spec.md` D26 (see m3).

**P7.1 against the code.**

- `KIND_TRACKING` is at `lettering_marks.py:51`. `box_size` is at `:94`, and `Measure` at
  `label.py:57`. `pipeline.py:102` and `:117` match the plan.
- `_place` measures `tw` once (`placement.py:161`) and uses it only for `place_along`.
  `best_flat` measures for itself, so the split between `measure_fn` and `measure_tracked`
  is clean.
- `PINNED_LABELS` holds ten names, two of them "East Lyn".
- The only callers of `place` are `pipeline.py:117` and eight sites in `test_placement.py`.
- The `make_golden.py` options match: `--compare`, `--require-identical NAME... | all`,
  `--require-hash`, `--require-labels-equal`, and `labels.txt` written outside the golden
  directory.
- The exact golden run is green here, so step 3 rewrites `paper`, `wash`, `pen` and
  `plates.json` byte-identical.

**The script contract against `test_route_map_example.py`.** The test copies the fixture
and builds both providers at `127.0.0.1:9` with `budget=0`. It then passes
`track=cache / "track.gpx"`, a **`Path`**, and `route_map.main` declares `track: Path`
(B2).

**The CI jobs.**

- `ci.yml` has `checks` (3.13 and 3.14, `-m "not golden and not benchmark" --cov
  --golden-tolerance`) and `prerelease` (3.15, `--no-dev`, a hand-picked `pip install`).
- `ci.yml` has no `workflow_dispatch`. `golden.yml` runs on `pull_request` and on pushes
  to `main` only.
- `publish.yml` only builds and publishes.

**The WebP encoder.** `ink/io.py:46,48` (`save_webp`) uses `method=5` for both lossless
and lossy, and `:109` and `:149` use `method=4`. The plan's "method 5" matches `save_webp`.

**The rung widths.** `test_ink_examples.py` and `test_letters_examples.py` pin five rungs
at 360 px, pigments at 720 by 240 and composition at 480 by 320, so the plan is right.
`route_map` writes the 900 px card. `lettering.py` and `composition.py` each write two
files: the plate and the finished image.

**The measured encodings.** These are file sizes in KB:

| Image | Lossless, method 5 | Lossy WebP, q90 | JPEG, q88 |
| --- | --- | --- | --- |
| paper | 51 | 3 | |
| wash | 54 | 4 | |
| brush_stroke | 57 | 5 | |
| nib_line | 59 | 7 | |
| lettering | 53 | 4 | |
| pigments (720 px) | 110 | 8 | |
| composition (480 px) | 101 | 8 | |
| map, 900 px | 549 | 66 | 99 |
| map, 720 px | 367 | 49 | |
| map, 360 px | 104 | 18 | |

A 1280 by 640 JPEG cut of the map is about 114 KB. The hero and preview budgets are
comfortable. The thumbnail budget is not (S4).

**The style digests (for P7.3b).**

- `_group_digest` hashes `dataclasses.asdict(group)`, which is every field (`style.py:217`).
- `plates.json`'s hash is the canonical layers text plus `-` plus `base_digest()`
  (`cache.py:181`). The committed value is `340a7f6e260ee1e2-e5a5f1b4b3ca2177`, and its
  suffix equals `BASE_DIGEST` in `test_style.py:74`.
- `test_style.py:73 to 75` pins `DIGEST`, `BASE_DIGEST` and `LETTERING_DIGEST`.
- `test_style_groups.py` pins each group's field names (`PINNED`), and
  `LetteringPolicy`'s default digest `252f33e095df0b01` (`SOURCED`, a provenance pin from
  the flat painter style). It also pins `BASEMAP_DEFAULTS`.

**Where the names are read.**

- OSM names are read only in `osm_elements.py`, at `:186`, `:226`, `:260`, `:297` and
  `:303`, as the plan says.
- They are read against `Scope.options: BasemapStyle`. The path is `layers.py:289` →
  `layers.basemap` → `osm.osm_layers` → `Scope`. The lettering group never reaches them.
- `candidates/places.py:91 to 105` and `candidates/roads.py:65` read `tags["name"]` on
  their own.
- `Basemap.canonical` includes the layers, and road, river and coast names are in them.

## Round-1 findings

| Finding | Status | Why |
| --- | --- | --- |
| B1 `Measure` | Resolved | `MeasureTracked`, `box_size(..., tracking=0.0)`, a keyword-only `measure_tracked` on `place` and `_place`, and the leave-alone list all fit the code. One wrinkle, in S7. |
| B2 shared files | Resolved for the group | Each 6x slice has its own test module, P7.4 owns the index stubs and the lychee exclusion, and the shared-files table exists. New collisions outside the group are in S3. |
| B3 registry and contract | Partly | `DocsImage` fields, one image per call, `figure=` and the fixture recipe are prescribed. But the recipe contradicts `route_map.main` and has no style input, which is B2 below. "Exactly one image per call" is untrue of two rungs (S10). |
| B4 tracks on public ways | Resolved | Ways mode is used for all five, loop mode is gone, and the D16 wording is right. |
| M1 Yr Wyddfa build | Partly | The budget, full chain, end node, join rule, 20 m spacing, raw fetch, ODbL and sizes are all fixed. The selection query and the 150 m, 30 m and length checks have no tool (S6). |
| M2 svgelements | Resolved | A spike in P7.4, the `prerelease` line, and the `_THIRD_PARTY` literal mirrored by the ADR. |
| M3 markers and CI time | Resolved | |
| M4 hero, tutorial, preview | Resolved | Keswick, a JPEG under 900 KB, and a `preview` kind. |
| M5 CodSpeed badge | Resolved | Verbatim, matching `6d34c8a:plan.md:5821`. The other four badges are named. |
| M6 Welsh names | Resolved | The edits are verified above. Minor leftovers are in m3. |
| M7 brief standard | Partly | P7.14 and P7.R now have owners, gates and done lines. P7.6b and P7.6c inherit from 6a, which has no leave-alone. P7.8 to P7.10 have no gate or done line, P7.10 has no test-first, and no group slice has a "touch nothing else" rule (S9). |
| M8 thumbnail widths | Resolved | "Own widths, never enlarged". The route map's width is not named (S4). |
| M9 lossy WebP | Resolved | Lossless for ink, the compare decodes, and a two-OS run gates the fan-out. The encoding classes are incomplete (S4). |
| M10 budget shares | Resolved | The shares sum to 5.2 MB of 5.5 MB, leaving 0.3 MB slack. |
| M11 stop rules | Resolved | The new remedy collides with the routes being settled (S5). |
| m1 | Resolved | The pin is read from the parser's actions. `build_parser()` exists at `cli.py:38`. |
| m2 | Resolved | |
| m3 | Resolved | A nit: `diff` also prints a `Nd M` line and exits 1. |
| m4 | Resolved | The table is sorted, 0024 is unused, the paragraph is repointed and 0035 is appended. |
| m5, m6, m7, m8, m9 | Resolved | |
| m10 | Resolved | `; test $? -eq 1` is used, and the gate exits 1 on today's tree. |

## Findings

### Blocker

**B1. P7.3b: the style field is in the wrong group, and either way a stop is certain to
fire.**

- **Where:** P7.3b.
- **The group:** the plan puts `name_tags` on "the `lettering` style group". That group's
  class is `LetteringPolicy`.
- **The plumbing:** the names are read in `osm_elements` against `Scope.options`, which is
  the `BasemapStyle`. Getting `LetteringPolicy` there means threading it through
  `layers.py` (`build_basemap`, then `basemap()`), `osm.osm_layers` and `Scope`. That is
  three modules against the plan's "at most two; more stops and reports".
- **The meaning:** it also makes `LETTERING_GROUPS`, documented as "the groups only the
  lettering reads", false.
- **The digests:** a new field in any group moves that group's digest, because
  `_group_digest` hashes `asdict()`, which is every field. Then:
  - In `lettering`: `LETTERING_DIGEST` and `DIGEST` (`test_style.py:73,75`) move, and so
    do the `PINNED` row and the `SOURCED` provenance digest of `LetteringPolicy`
    (`test_style_groups.py`). None of these files is an owner.
  - In `basemap`: `BASE_DIGEST` moves, and it is the suffix of `plates.json`'s hash. The
    golden manifest test fails, and so does the plan's `--require-hash equal`.
- **The remedy the plan offers:** "excluded from the digest when it equals its default"
  needs `style.py` (`_group_digest`, and the module docstring's digest definition). That
  file is not an owner. The change also amends ADR 0005's digest rule, which 0035 does
  not say it does.
- **What follows:** the agent stops, or widens the owners ad hoc.
- **Fix:** prescribe it.
  - Put `name_tags: tuple[str, ...] = ("name",)` in `BasemapStyle`. It already reaches
    every read site through `scope.options`, so no plumbing is needed, and it is "what the
    basemap draws".
  - In `style.py`, `_group_digest` omits the fields named in a new
    `DIGEST_OMITS_AT_DEFAULT = ("name_tags",)` while they equal their default. The module
    docstring says so.
  - ADR 0035 amends 0005 with that rule.
  - Add owners:
    - `style.py`;
    - `style_groups.py`;
    - `test_style_groups.py` (the `BasemapStyle` row of `PINNED` and the `name_tags` entry
      of `BASEMAP_DEFAULTS`, written by hand);
    - `test_style.py`, with a new test that a non-default `name_tags` moves `base_digest()`
      and `digest()` while the default's three pins stay.
  - Then `BASE_DIGEST`, the manifest hash and every golden stay byte-identical, which is
    the maintainer's "no golden moves".
  - State that `candidates/places.py` and `candidates/roads.py` (the candidate export)
    keep reading `name`, so "every name the map reads" is scoped to `osm_elements`.
  - Mark `tests/unit/maps/test_osm_elements.py` as new.
- **The alternative:** accept the hash move as a fourth regeneration, with an ADR. That is
  heavier, and the maintainer has to choose it.

**B2. The script contract contradicts the code it says to copy, and it cannot carry a
theme.**

- **Where:** "The script contract", P7.3 (`test_places.py`), P7.3b, P7.7 and P7.13.
- **The contradiction:** the contract says to pass "`Track.from_gpx` of its track ...
  exactly as `test_route_map_example.py` does". That test passes `track=cache /
  "track.gpx"`, a `Path`, and `route_map.main(..., track: Path, ...)` reads the GPX
  itself.
  - `make_docs_images.py` is the one caller of `route_map`, `map_styles`, `hero`,
    `social_preview` and any `how_to_*` map script.
  - Parallel slices following the prose will type `track: Track`, while P7.4 (whose
    gallery includes `route_map`) must pass `Path`. One side breaks at landing.
- **The missing theme:** the contract has no way to choose a style, and `route_map.main`
  hard-codes `Style.default()`. P7.3b says `y-fenni.toml` is "used by every Y Fenni card
  in the docs and by `test_places.py`'s Y Fenni case". No script in the plan can take it,
  so those cards will letter "Abergavenny", which breaks the maintainer's settled
  requirement.
- **Fix:**
  - "`track` is the GPX `Path`".
  - Add an optional fifth keyword, `theme: str | None`, a path relative to the repo
    root that the script loads with `Style.from_toml`, defaulting to `Style.default()`.
    It fits the registry's `options` tuple as a string.
  - Say which script paints the Y Fenni docs card, or that none does in 0.1.0.
  - Say `test_places.py` does not go through `route_map.main`, which returns only a
    `Path` and so cannot expose the placed labels or marks the test pins. It calls
    `fetch`, `paint` and `letter` with the recipe's providers and the theme.

### Should fix

**S1. The README link rule rejects the badges P7.13 must write.**

- **The rule:** P7.4's `test_docs_images.py` requires "every README image and link an
  absolute URL on `raw.githubusercontent.com/findlaywebb/pyntpot/` or
  `github.com/findlaywebb/pyntpot/`".
- **The conflict:** P7.13's badges are `img.shields.io` images linking to `pypi.org` and
  `codspeed.io`.
- **What follows:** P7.13 goes red, or it edits P7.4's test.
- **Fix:** the rule applies to images and links *into the repo*, and no README link may be
  relative.

**S2. "G-here" is redefined, and P7.R puts exact goldens into `publish.yml`.**

- **The redefinition:** P7's "G-here: `uv run prek run --all-files && uv run pytest`"
  silently replaces the plan-wide G-here at `plan.md:556`. That one also runs `uv sync`
  and the tolerance pass.
- **The release risk:** P7.R's `publish.yml` must "run G-here's commands". On an Ubuntu
  runner, plain `uv run pytest` runs the goldens byte-exact. `golden.yml`'s own comment
  and ADR 0030 say that is not guaranteed there. A red publish job after the tag is pushed
  costs a re-tag.
- **Fix:**
  - Cite the plan-wide G-here, or call P7's variant G-P7.
  - Write `publish.yml`'s gate commands out: `uv sync --locked`, prek,
    `pytest -m "not golden and not benchmark" --golden-tolerance` and
    `pytest -m golden --golden-tolerance`.

**S3. P7.11 and P7.12 run "beside anything" but share files the table does not list, and
P7.12's done line cannot be met.**

- **The shared files:**
  - P7.12 and P7.4 both edit `pyproject.toml`'s `dev` group and `uv.lock` (twine and
    svgelements), as P7.14 later does with a `docs` group.
  - P7.12 (the `docs` job) and P7.4 (the `prerelease` line) both edit `ci.yml`.
  - `uv.lock` conflicts do not merge by hand.
- **The done line:** "the `docs` job green on a dispatched or PR run". But `ci.yml` has no
  `workflow_dispatch`, and PR 2 is not opened until P7.13.
- **Fix:**
  - Either put P7.12 before P7.4, or list `pyproject.toml`, `uv.lock` and `ci.yml` in the
    shared-files table with "re-lock after merge: `uv lock`, commit".
  - Give P7.12 a `workflow_dispatch` on `ci.yml`, or open PR 2 as a draft at P7.2.

**S4. The gallery and swatch entries break their budgets as classified.** This is from the
measurements above.

- **The thumbnails (60 KB):**
  - `route_map` "at its own width" is 900 px, about 66 KB even lossy. Name a width:
    720 px is 49 KB.
  - `composition` (480 px, nib and lettering) is 101 KB if lossless.
  - `nib_line` lossless is 59 KB, 1 KB under.
  - The encoding rule does not classify `paper`, `brush_stroke`, `composition` or the
    map's rung. P7.4's stop rule covers a red tolerance pin, not a budget overrun.
- **The swatch sheets:**
  - "Lossless for ... swatch figures" contradicts "lossy WebP for washes", because a
    pigment swatch is a wash. Lossless runs about 0.6 bytes a pixel, so a 15-pigment
    sheet nears the 250 KB page cap.
  - The brush sheet has 112 ids (8 rows by 14 colour columns), and `BRUSH_TREATMENTS` and
    `BRUSH_COLOURS` are not public. `examples/brush_sheet.py` cannot enumerate them under
    `test_examples.py`'s public-names rule.
- **Fix:**
  - In P7.4, give a per-entry table for the eight gallery rows: width, encoding, and
    fixture, Lynmouth or Keswick, for the map row.
  - Add the stop "over its kind's budget: lossy if a wash, else a smaller width; still
    over, stop".
  - Make the swatch sheets lossy.
  - Say the brush sheet lists its ids as a literal tuple, which the reference test checks
    against the private tables.

**S5. P7.3's budget remedy would change settled routes, and it does not work.**

- **The remedy:** "Over 4 MB, an urban loop shrinks to the bottom of its range". The
  Keswick, Oxford and Y Fenni routes are now settled.
- **Why it does not work:** the payload boxes are the track's extent plus
  `MARGIN_M = 1500` and `LANDCOVER_MARGIN_M = 2600` (`cache.py:54,58`). For a 3 km urban
  loop the margin dominates, so a shorter loop barely shrinks the payload.
- **Keswick:** Keswick now carries P7.5, P7.7 and P7.13. "Slices that would show it use
  Keswick instead" has no answer if Keswick itself parks.
- **Fix:**
  - Any fixture over its budget stops and reports with the payload sizes, which is the
    Yr Wyddfa rule.
  - If Keswick fails or parks, P7.4 and later do not start.

**S6. P7.3's way selection and route checks have no tool.**

- **The gap:** `make_track.py` takes only `--contact` and `--ways`. The plan does not say
  what runs:
  - the per-place `highway` query "in the route's box";
  - "within 150 m of the Pen-y-Pass car park node";
  - "within 30 m of the summit trig node";
  - "ends where the Llanberis Path meets the road";
  - the length ranges.
- **The box:** the route's box cannot be written in the plan or the run log, because of
  the coordinate gate. It must stay on a command line.
- **Fix:**
  - Give `make_track.py` `--start-node ID:M`, `--via-node ID:M`, `--end-node ID:M` and
    `--length-km MIN MAX`, failing on a miss, and say they print only distances.
  - Name the selection query as a `--list-ways S,W,N,E` mode that prints each way's id,
    name, `highway` and `sac_scale`, with the box passed on the command line only.

**S7. P7.1: switching existing `place` callers to a real hand changes green tests for no
reason.**

- **The instruction:** "Existing callers of `place` ... pass a tracked measure built ...
  from `open_hand()` where they place along water". That applies to four tests (`:34`,
  `:108`, `:180`, `:208`).
- **What follows:** those tests then measure along-windows with the real face and the
  0.24 river tracking, but flat boxes with `flat_measure`. Their geometry changes,
  including the two-"Lyn" test the plan says "stays green".
- **Fix:** every existing caller passes `lambda name, size, tracking: flat_measure(name,
  size)`. Only the three new red tests use the real hand.

**S8. The test_places recipe.** This is folded into B2.

**S9. The briefs in the parallel group still lack the bound that keeps worktrees
disjoint.**

- **The missing bound:** no group slice says "edit only the owner files and the
  shared-file blocks; anything else, stop and report".
- **The uneven briefs:**
  - P7.8, P7.9 and P7.10 have no gate or done line.
  - P7.10 has no test-first.
  - P7.6b and P7.6c inherit "rules as P7.6a", which has no leave-alone.
- **Fix:** one sentence under "Gates for every slice", plus "Gate: G-here and the dash
  gate; Done: the named tests green" on each.

**S10. "Exactly one image per call" is false for two rungs the gallery registers.**

- **The rungs:** `lettering.py` and `composition.py` write a plate and the finished image,
  and P7.5 leaves every rung's code alone.
- **Fix:** the rule is that `main` returns one image path, and the registry and the pin
  read that path only, ignoring any other file the script writes.

### Minor

- **m1. P7.1, step 3.** After `$MG tests/golden/lynmouth`, check that `git status
  --porcelain tests/golden/lynmouth` lists only `labels-centreline.webp` and `map.png`. The
  step rewrites the leave-alone `paper`, `wash`, `pen` and `plates.json` (byte-identical
  today), and nothing catches it if they move.
- **m2. The coordinate gate.** Say that a coordinate pair must lie in one box: its
  latitude and longitude both in the same fixture's box, not one from each.
- **m3. Welsh names.**
  - `spec.md` D26 still lists "Monmouth, Abergavenny" as the convention's examples. Either
    say it stays as history, or amend it.
  - CONTRIBUTING's rivers keep Dee and Severn (Dyfrdwy, Hafren). Record whether they are
    in or out.
- **m4. `docs/README.md` (P7.2) and lychee.** Its user-docs list will link pages that do
  not exist yet. That fails lychee once P7.12 lands, because only `docs/**/index.md` is
  excluded. Either exclude it too, or have P7.13 write that list.
- **m5. `first-map.md`'s "three named files".** The reader needs the track and the three
  payloads, which is four files.
- **m6. `test_placement.py`'s line budget.** The file is 295 lines, and three new tests
  approach the 400-line budget. Name a split target, for example
  `test_placement_windows.py`, if it passes.

## Verdict

**BLOCK.** Both blockers are local edits to the plan. They need no change of approach.

- B1: P7.3b's field goes in `BasemapStyle`, with a default-omitting digest rule in
  `style.py` amending ADR 0005, and the four test and source files added as owners.
- B2: the script contract's `track` is a `Path`, and it gains a `theme` keyword so a
  Y Fenni card can letter "Y Fenni".

Fix S1 to S10 in the same pass. S1, S2 and S4 will otherwise go red at P7.13, P7.R and
P7.4. Round 1's findings are otherwise resolved, and the research, the slicing, P7.1's
design and the shared-files discipline are sound.
