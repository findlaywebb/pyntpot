# P7 plan review 1

## Scope

I reviewed `specs/001-port/plan.md` on `p7-docs-release` at HEAD `dfe1773`. That is
`d2768e5` plus two maintainer amendments to the Yr Wyddfa fixture, which I reviewed as
their own item (M1):

- `053376c`: the track goes over Crib Goch, following OSM way geometry;
- `dfe1773`: the track goes on down the Llanberis Path to Llanberis, about 12 km, with a
  6 MB allowance.

The route itself is settled; how it is built is not. The parts I read:

- the section "### P7. Docs and first release" (5813 to about 6236);
- the ADR numbers table (513 to 547), including rows 0031 to 0034 and the 0013 to 0021
  row repointed to P7.11;
- the P7 section of `specs/001-port/tasks.md` (145 to 166) and P9's order line (192).

I read them against:

- `p7-research.md`, whose sections 7 to 9 are settled and which I did not reopen;
- the six notes under `research/p7/`;
- `docs/issues/maps-lettering-curved-name-window-and-flat-repeat.md`;
- the parked features in `docs/features/`;
- ADR 0025, and the P10 and P11 briefs and reviews for the house standard of a brief;
- the code.

Every check was read-only, and I ran no tests. Two network probes, one to
`overpass.private.coffee` and one to the mail.ru mirror, did not complete, so I have not
confirmed the plan's network facts.

## What I checked

**P7.1 against the lettering code.**

- `KIND_TRACKING` is at `maps/lettering_marks.py:51`.
- `box_size` (`:94`) calls `hand.measure(text, size)` with no tracking. `Hand.measure`
  takes `tracking: float = 0.0` (`letters/hand.py:63`).
- `pipeline.py:102` passes `partial(lettering_marks.box_size, hand)`.
- The import cycle the plan cites is real: `lettering_marks` imports `lettering_window`
  (`:38`), and `lettering_window` imports `placement` (`:25`).
- `label.py` imports nothing from `maps.lettering`, so `KIND_TRACKING` can live there.
- `Measure` is `Callable[[str, float], tuple[float, float]]` (`label.py:57`), and seven
  call sites use it:
  - `label.py:277` (`block_size`)
  - `picks.py:255`
  - `placement.py:161`
  - `placement_flat.py:101`
  - `span_ends.py:86`
  - `spans.py:230`
  - `attribution.py:69` (calls `box_size` directly)
- `tests/support/measure.py::flat_measure`, a two-argument `Measure`, is used by five
  lettering test modules.
- `PINNED_LABELS` holds ten names, two of them "East Lyn"
  (`test_pipeline_letter_compose.py:26`).
- `test_a_rivers_two_names_are_kept_apart_along_the_water_not_across_the_map` exists
  (`test_placement.py:180`).
- `make_golden.py` has `--require-identical NAME... | all`, `--max-fraction`,
  `--require-hash equal|differ` and `--require-labels-equal`. `OUTPUTS` are the four
  plates plus `map.png`. The manifest hash covers the plates' geometry and style, not
  the labels.
- The ADR 0025 shape is as the plan describes.

**The examples harness.**

- `support.examples.run_example(stem, out_dir, **options)` asserts that `main` returns
  one `Path`.
- `test_ink_examples.py` asserts that each rung writes exactly one file at a pinned
  size. Five of the rungs are 360 px wide, pigments is 720 px wide and composition is
  480 by 320.
- `test_examples.py` pins eight stems and keeps `_THIRD_PARTY = frozenset({"numpy",
  "PIL", "pyntpot"})` as a literal.
- `route_map.main` takes `track`, `cache_dir`, `features: OverpassFeatures` and
  `elevation: OpenTopoData`. Its test is `@pytest.mark.golden` and builds budget-0
  providers that point at `127.0.0.1:9`.
- The rung docstrings: `nib_line` is "Rung 4" and `pigments` is "Rung 5". No other rung
  names a rung number.

**The coordinate gate.**

- `tests/architecture/test_coordinates.py` holds one box, `LAT_RANGE (51.19, 51.26)` and
  `LON_RANGE (-3.88, -3.80)`. That equals the Lynmouth README's "track points lie inside"
  box, rounded outward to 0.01.
- It pairs a latitude and a longitude that sit within 120 characters of each other.
- `_text_scan._SCANNED` includes `specs` and `examples`.

**Providers and the cache.**

- `OverpassFeatures.id = "overpass"`, with `DEFAULT_ENDPOINTS` = `overpass-api.de` and
  `overpass.private.coffee`.
- `Cache.key` hashes the box, the margin and both provider ids. The payload names are
  `<kind>-<key>.json`.
- `tests/support/paths.py` holds one Lynmouth `KEY`.

**Pytest, CI and the workflows.**

- Markers: `golden` and `benchmark`. `filterwarnings = ["error"]`.
- `ci.yml` runs `-m "not golden and not benchmark" --cov` on 3.13 and 3.14.
- A `prerelease` job runs `uv sync --locked --no-dev` plus a hand-picked
  `pip install`, then `-m "not golden"` on 3.15 (continue-on-error).
- `golden.yml` runs `-m golden --golden-tolerance` on `ubuntu-latest` and `macos-15`.
- `publish.yml` builds and publishes with no gates.

**Packaging and repo state.**

- The build backend is `uv_build`.
- `pyproject` is at 0.0.2 and has `Development Status :: 3 - Alpha`.
- The plates are written as lossless WebP, and `ink/io.py:28` explains why: "the lossy
  encoder ... replaces a stroke's ramp with two flats and a step".
- `README.md` has no Markdown links, and `CHANGELOG.md` has no dashes.
- The CodSpeed badge literal was in the outline that P7.0 deleted, and it is not in
  `p10-triage.md`.

## Findings

### Blocker

**B1. P7.1: `Measure` "takes a tracking argument, default 0.0" cannot be written, and
the owner list misses the files the change touches.**

- **Where:** P7.1, step 1, Green.
- **The problem:** `Measure` is a `Callable` alias, and a `Callable` type cannot carry a
  default. There are only two ways out, and both leave the owner list too small.
  - Change it to `Callable[[str, float, float], ...]`. Then every call site and
    `flat_measure` must pass three arguments. That touches `picks.py`,
    `placement_flat.py`, `span_ends.py`, `spans.py`, `label.py`'s `block_size` and
    `tests/support/measure.py`, and none of them is an owner file.
  - Or call `measure_fn(name, size, track)` in `placement.py` against the two-argument
    alias. ty fails that.
  - A `Protocol` with a defaulted `__call__` is not an option: the rule of three in
    `CLAUDE.md` bars it.
- **What follows:** an implementer will widen the owner list ad hoc or stall. If they
  pass the kind's tracking at every site, they also fix the flat-box defect that the plan
  says to file, not fix. That moves more pixels and turns the step 1 gate into
  guesswork.
- **Fix:** prescribe the mechanism.
  - Leave `Measure` alone. Add `MeasureTracked = Callable[[str, float, float],
    tuple[float, float]]` in `label.py`.
  - `pipeline.py` passes a second callable, `partial(lettering_marks.box_size, hand)`,
    with `box_size(hand, text, size, tracking=0.0)`.
  - Thread it only into `place` and `_place`, which measure the along-window with
    `KIND_TRACKING.get(lb.kind, 0.0)`.
  - Every other site keeps the untracked two-argument measure.
  - List the exact signature change for `place`. State that `attribution.py`,
    `flat_measure` and the five other call sites are left alone.
  - Name how the red tests build a hand-backed measure (`open_hand()` plus
    `partial(box_size, hand)`), because `test_placement.py` uses `flat_measure` today.

**B2. The parallel group shares more files than the two it declares.**

- **Where:** "Order and parallelism", and P7.5 to P7.10.
- **The shared files the plan does not declare:**
  - `tests/examples/test_painting_with_python.py` is "new" in P7.6a, and P7.6b and P7.6c
    "append" to it. All three branch from the same head, so 6b and 6c have no file to
    append to, and the landing conflicts.
  - `docs/tutorials/painting-with-python/index.md` (P7.6a) must link pages that 6b and
    6c own. Either it links missing files, which fails the offline link check once
    P7.12 lands, or 6b and 6c edit a file they do not own.
  - `docs/how-to/index.md` (P7.8) must list `write-a-theme.md` (P7.7).
  - `docs/tutorials/index.md` (P7.5) must list the Painting with Python set (P7.6a).
  - `docs/gallery.md` and the gallery registry rows appear in both P7.4 and P7.13.
- **Fix:** add a "Shared files and their merge rules" table as P11 did. Either:
  - each of P7.6a, 6b and 6c owns its own test module
    (`test_painting_with_python_{curves,fractals,pictures}.py`); or
  - P7.4 creates every shared file as a stub (the index pages with their final link
    lists, the test module with a header), and each slice appends one block.

  Then:
  - Hand every index page to one integrator, the orchestrating session or P7.13, which
    writes the link lists after the group lands.
  - Take the gallery registry rows out of P7.13.

**B3. The registry and script contract is not prescribed, yet eight parallel slices
append to it.**

- **Where:** P7.4, `tests/support/docs_images.py` and `make_docs_images.py`. Also
  P7.6 to P7.10 and P7.13.
- **The problem:**
  - The plan lists the entry's fields loosely ("the options passed to its main, the
    fixture it reads if any").
  - Several planned scripts write more than one figure: `map_styles.py` paints four
    themes, `wash_stages.py` paints one figure per effect, and `curves.py` draws three
    curve families, as may `pigment_swatches.py`.
  - `run_example` requires `main` to return a single `Path`.
  - Fixture-reading scripts (`route_map`, `map_styles`, `social_preview`, the hero)
    need provider objects that a data registry cannot hold.
  - Each slice will invent its own answer.
- **Fix:** fix the shape in P7.4.
  - Give the frozen dataclass's field names and types, for example
    `image: str, stem: str, options: Mapping[str, str | int | float],
    fixture: str | None, width: int, kind: Literal["thumbnail", "page", "hero",
    "preview"], format: Literal["webp", "png"]`.
  - Rule: one `main` call writes one image. A script with several figures takes a
    keyword that selects one (`theme=`, `stage=`, `curve=`), and the registry holds one
    entry per figure.
  - Rule: when `fixture` is set, `make_docs_images.py` and the pin test copy
    `tests/fixtures/<fixture>/` to a temporary cache. They pass `track`, `cache_dir`
    and the budget-0 `OverpassFeatures` and `OpenTopoData` at `127.0.0.1:9`, exactly as
    `test_route_map_example.py` does, and every fixture-reading script takes those four
    keywords.
  - Put both rules in the module docstring.

**B4. Four of the five tracks cannot be made the way the table describes, and the loop
mode contradicts Q-P1.**

- **Where:** the focus places table, `make_track.py` in P7.3, and the D16 check.
- **The problem:** the maintainer's Q-P1 answer is "Each map's track is invented along a
  public path". The plan generates Keswick, Trotternish, Oxford and Y Fenni as loops
  from "a centre, a radius and a seed". A seeded loop of fixed radius cannot go "round
  the north of Derwentwater", stay "under the Quiraing" or run "through the centre" of
  Oxford. It will cross the lake, the escarpment, colleges and the Cherwell. The
  implementer will either ship a track over water or improvise a method.
- **Fix:** the amendment already adds a ways mode to `make_track.py`. Use it for all
  five.
  - Each row of the table names the public path or paths: for example the Derwentwater
    shore path between Keswick and Portinscale, the Quiraing path from the Staffin road
    car park, and in Oxford and Y Fenni a chain of named streets and footways.
  - Keep loop mode for nothing new, or drop it.

### Major

**M1. Yr Wyddfa (the two amendments): the route is settled, but how to build it is
left open, and the size budget now contradicts itself.**

- **Where:** the D16 paragraph (5836 to 5841), the table row, `make_track.py`, the
  Budgets bullet (6033), and the D16 check.
- **The gaps:**
  - **The budgets disagree.** Line 5841 allows this fixture 6 MB. The Budgets bullet
    (6033) still says "each fixture directory at most 4 MB", and its only remedy (shrink
    the loop) applies to urban fixtures. An agent meeting a 5 MB Yr Wyddfa directory has
    two contradicting rules and no remedy, because a settled route cannot shrink.

    Fix: the Budgets bullet names the exception ("`yr-wyddfa/` at most 6 MB"). Over
    budget there means stop and report, not shrink. The budget is pinned in the test
    (m2).
  - **The way chain is incomplete.** "The Pyg Track, the Crib Goch ridge path and the
    Llanberis Path" skips three things:
    - the ridge's continuation over Bwlch Coch and Crib y Ddysgl (Garnedd Ugain) to Bwlch
      Glas;
    - the shared final section to the summit;
    - the stretch where the descent first retraces the ground near Bwlch Glas beside the
      railway.

    State the full order: Pen-y-Pass, the Pyg Track to Bwlch y Moch, Crib Goch, Bwlch
    Coch, Crib y Ddysgl, Bwlch Glas, the summit, then the Llanberis Path to its foot.
    Also say that the track may run close to itself near the summit, and that this is
    expected.
  - **The end point is unnamed.** "To Llanberis" could mean the path's foot at the
    village road, the village centre or the station. Name it as an OSM node id, for
    example where the Llanberis Path meets the public road. Use an id, not coordinates,
    because of the coordinate gate. Check that the start lies within 150 m of the
    Pen-y-Pass car park node, that the track passes within 30 m of the summit trig
    node, and that the length is 11 to 13 km.
  - **Selection is unprescribed.** "Named OSM ways" may not exist as names; ridge and
    path segments are often unnamed `highway=path` with `sac_scale`. Prescribe how the
    ways are found: an Overpass query by box and tags, then manual id selection recorded
    in the README.
  - **The join rule is unprescribed.** Chain by shared end node ids, reverse a way when
    needed, and fail if any join gap exceeds 5 m or a branch is ambiguous.
  - **The resampling spacing is unnamed.** Lynmouth is 400 points over 8 km, which is
    20 m. Name a figure: 20 m gives about 600 points.
  - **The fetch is unprescribed.** `OverpassFeatures` sends only its fixed queries, so the
    ways fetch is raw `httpx` with the provider's User-Agent. The contact comes from a
    `--contact` argument (no `os.environ`). The raw response is not committed; the way
    ids and their OSM versions go in the README.
  - **Licensing is unstated.** A track resampled from OSM geometry is ODbL-derived data.
    The README's licence section must list `track.gpx` under the ODbL beside the two
    Overpass payloads.
  - **Box and size risk.** The route runs about 7 km from Pen-y-Pass to Llanberis. With
    the 2600 m land cover margin, the box takes in Llanberis, Llyn Padarn and the
    Dinorwig quarry land use, which is polygon-heavy. "It is rural, so it is expected
    under that" is a guess. Measure the payloads before committing, and record the sizes
    in the run log.
  - **One-way behaviour is untested.** The pipeline has only painted a loop. State the
    expected start and finish marks, and that a fixture which paints wrongly is parked by
    the stop rule.

**M2. svgelements: decide before the fan-out, and the fallback writes files P7.6c does
not own.**

- **Where:** P7.4 (dependency, ADR list, `_THIRD_PARTY`) and P7.6c (Stop).
- **The problem:**
  - The fallback ("the ADR 0033 list drops the package") edits ADR 0033,
    `pyproject.toml`, `uv.lock` and `test_examples.py`, all of which belong to P7.4.
  - The `prerelease` job runs `--no-dev` with a hand-picked `pip install` list, so a test
    that imports `svgelements` fails there with `ModuleNotFoundError`, and nobody owns
    that line of `ci.yml`.
- **Fix:**
  - Move the decision into P7.4 as a spike step: add the package, then run
    `uv run python -W error -c "import svgelements"` and `uv run ty check` on a ten-line
    use. Record the result in ADR 0033. If it fails, use the `xml.etree` M/L/C/Z subset
    from the start and add no package.
  - If the package stays, P7.4 also owns adding it to the `prerelease` job's
    `pip install` line. The vector page tells readers to `pip install svgelements`.
  - Make `_THIRD_PARTY` a literal in `test_examples.py` that the ADR mirrors. A test
    parsing an ADR's Markdown is fragile, and "read from the ADR's list" will be built
    two ways.

**M3. Test markers and CI time are not prescribed.**

- **Where:** P7.3 (`test_places.py`), P7.4 (`test_docs_images.py`), P7.6 (the
  per-script tests), P7.7 (the theme test), P7.9 (the swatch scripts).
- **The problem:** only two of these are marked `golden`. The rest land in `ci.yml`'s
  coverage run on 3.13 and 3.14, and in the 3.15 prerelease run, unmarked.
- **The cost:**
  - P7.7 alone paints Keswick four times, on the order of 60 to 80 s, by the plan's own
    12 to 19 s per card at line 7721.
  - The docs pin re-paints every registered image on both golden OSes: about 15 to 25
    map paints plus the P7.6 scripts at up to 20 s each.
  - No total budget is set.
- **Fix:**
  - Every test that paints a fixture card, and every docs-image pin, is
    `@pytest.mark.golden`, as `test_route_map_example.py` is.
  - The non-golden per-script tests call `main` at a small size option and stay under
    2 s each, measured locally.
  - Set a budget for the golden job's growth (for example at most 6 minutes added on
    `ubuntu-latest`). Record the measured time in the P7 run log at P7.4, P7.7 and
    P7.13, and stop if the budget is exceeded.

**M4. The hero, the first-map fixture and the social preview are left to the
implementer.**

- **Where:** P7.5 (`first-map.md`: "a focus-place fixture") and P7.13 (the hero, the
  social preview).
- **The decisions left open:**
  - **Which place the hero shows.** The research fixed the East Lyn label before 0.1.0
    because the Lynmouth card "is the obvious hero image". The conventions say "focus
    places for new figures".
  - **Which fixture the tutorial uses.**
  - **What format the preview is.** It is a "1280 by 640 PNG". A painted map PNG at that
    size will be around 1.5 to 2 MB (the 900 by 728 `map.png` is 2.7 MB). That breaks
    GitHub's 1 MB social-preview limit and most of the 4 MB `docs/images/` budget.
    The preview also has no budget class.
- **Fix:**
  - Name the hero's place and fixture (Lynmouth with the fixed label, or Keswick) and
    the tutorial's fixture.
  - Make the preview a JPEG or lossy WebP under 1 MB, stored outside `docs/images/`, or
    in it with its own budget class.

**M5. The CodSpeed badge literal was deleted.**

- **Where:** P7.13, "CodSpeed in the form Q13 fixed".
- **The problem:** the exact markup was in the outline text that P7.0 replaced, and
  `p10-triage.md` does not hold it.
- **Fix:** restore it in P7.13 verbatim:
  `[![CodSpeed](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/findlaywebb/pyntpot)`.
  Name the other four badges' exact URLs too.

**M6. "Welsh names for Welsh places everywhere" (Q-P4) is only partly applied, and the
carve-out is vague.**

- **Where:** P7.2.
- **The problem:**
  - "Abergavenny kept only where a test needs its length", combined with "Leave alone
    `tests/**`", keeps Abergavenny in all four tests that use it: `test_font.py:15,33`,
    `test_hand.py:135`, `test_picks.py:85,91` and `test_placement_names.py:128`. None of
    them needs its length.
  - The list keeps Brecon, Crickhowell and Monmouth, and the river Usk.
- **Fix:** state the exact list edits:
  - Brecon to Aberhonddu;
  - Crickhowell to Crucywel;
  - Monmouth to Trefynwy;
  - Snowdon to Yr Wyddfa.

  Then add the four test files to the owner list, with the replacements named. For a
  same-length string use Machynlleth (11 letters) for Abergavenny, and Y Fenni where
  length does not matter. Alternatively, if the maintainer's "everywhere" excludes test
  strings, the plan should say so as a recorded reading, not as a carve-out that leaves
  the implementer to judge.

**M7. Most P7 briefs fall below the house standard of a slice brief.**

- **Where:** P7.2, P7.4 to P7.14, P7.R.
- **What P7.1 and the P10/P11 briefs carry:**
  - a predecessor;
  - a "check first";
  - named red tests;
  - a size;
  - a gate beyond G-here;
  - a commit message;
  - a done line.
- **What is missing in P7:**
  - Only P7.1 and P7.3 come close.
  - P7.14 has no owner list at all: no `mkdocs.yml` or `zensical.toml`, no Pages
    workflow file, no `docs` dependency group, no leave-alone list, no done line.
  - P7.R has no gate and no done line.
  - P7.5 to P7.10 name no tests besides P7.5's sync test and P7.9's pins.
  - P7.11 cites neither where D2 to D24 are defined nor the pointer map at plan 543 to
    547, which still says "P7.3's list".
- **Fix:** give each slice those fields.
  - At minimum: owner files, leave-alone, test first (named), gate, done, and a commit
    message.
  - P7.14: the config file, the workflow, the dependency group, and the engine rule as
    already written.

**M8. The gallery thumbnails at 480 px wide would upscale five of the eight rungs.**

- **Where:** P7.4.
- **The problem:** paper, wash, brush, nib and lettering are 360 px wide, so a 480 px
  thumbnail enlarges them. The plan's "downsizes to the entry's size" is then false.
- **Fix:** make the thumbnails 360 px wide, or "at most 480 px, never enlarged".

**M9. Lossy WebP for the docs images goes against the repo's own reasoning, and nothing
proves the pin holds across platforms.**

- **Where:** P7.4 ("WebP at quality 85, method 6").
- **The problem:**
  - `ink/io.py:28` documents why the plates are lossless: the lossy encoder flattens
    stroke ramps and grain.
  - A lossy encode of a fresh paint that differs by a last bit (ADR 0030) can move whole
    4 by 4 blocks. That can exceed `MAX_CHANNEL_DELTA = 2` on `macos-15`.
  - The repo uses `method=5` everywhere.
- **Fix:**
  - Use lossless WebP for pen-and-ink figures. Use lossy only for washes and maps, and
    say which per entry.
  - Make a green `golden.yml` run on both OSes, over the P7.4 gallery pins, a done
    criterion of P7.4 before the fan-out.
  - State that the tolerance compare decodes both images.

**M10. The `docs/images/` total budget is not allocated, so the slice that tips it fails
at landing.**

- **Where:** P7.4 budgets.
- **The problem:** about 30 page images at up to 250 KB each, plus the hero, the gallery
  and the swatches, can pass 4 MB. Each parallel slice passes alone, and the combination
  fails at the orchestrator's landing or in P7.13.
- **Fix:** give each slice a share of the 4 MB in P7.4, and record each slice's total in
  the run log.

**M11. Two stop rules an agent cannot follow.**

- **Where:** P7.3.
- **The rules:**
  - "After three tries on two days": an autonomous session cannot wait a day.
  - "A defect that is not a quick fix": this has no time box.
- **Fix:**
  - On the third failure in one session, commit the fixtures that succeeded, log the
    failures, and stop and report. The orchestrator re-runs the slice on another day.
  - "Quick fix" means under 30 changed lines in `src/` with a red test. P7.3's leave-alone
    list bars `src/**`, so in practice any defect parks.

### Minor

- **m1. The `cli.md` pin against `pyntpot map --help` is fragile (P7.9).** argparse wraps
  to the terminal width (`COLUMNS`), and 3.13, 3.14 and 3.15 format differently (3.14
  adds colour). Fix: assert that every option string and help text from the parser's
  actions appears in `cli.md`, not that the output matches verbatim.
- **m2. The coordinate boxes (P7.3) need four more rules.**
  - Prescribe "the track's box rounded outward to 0.01°", as Lynmouth's is.
  - the P7 run log and `plan.md` are scanned, so neither may carry margin-box
    coordinates; only the exempt fixture READMEs can.
  - Pin the per-fixture budget in a test (4 MB, and 6 MB for `yr-wyddfa/`), or the
    budget is a note only.
  - `test_places.py` belongs in `tests/golden/` or `tests/unit/maps/`, not
    `tests/examples/`, which is for the example scripts.
- **m3. P7.1, step 2: "`labels.txt` differs by exactly that one line" has no command.**
  Fix: give one, for example `diff $SCRATCH/step-1/labels.txt $SCRATCH/step-2/labels.txt`,
  whose only output must be the deleted "East Lyn" line. Also name the step 0 command
  (`$MG` from the "Gate commands" paragraph). ADR 0031 should record that both steps
  passed the bound, under the one acceptance.
- **m4. The ADR table has three loose ends.**
  - It is out of numeric order (0031 to 0034 sit between 0021 and 0022).
  - Row 0024 still says "P10.5b, only if ...", although the plan now says it stays
    unused.
  - The paragraph at 543 says "P7.3's list".

  Fix: sort the rows, mark 0024 unused, and repoint the paragraph to P7.11.
- **m5. P7.R classifiers.** Add `Programming Language :: Python :: 3.14`, which CI
  tests. Keep `Typing :: Typed`.
- **m6. The README pinned to the tag needs a policy (P7.R).**
  - After 0.1.0, `main`'s README points at `v0.1.0` for good.
  - Between the PR 4 merge and the tag push, its images 404.
  - Fix: state in `docs/runbooks/release.md` that each release's branch repoints the
    README to its own tag, and that the tag is pushed right after the merge.
- **m7. P7.12 does not say how lychee is installed, and lychee is not in G-here.** Pin
  `lycheeverse/lychee-action` to a release, and give a local command for slices that
  add links.
- **m8. P7.6b: name the caps that keep the scripts under 20 s.** Fern: accumulate the
  iterated points into a density mask, then wash it, with dabs only for a few hundred
  sampled points. Gasket: a recursion depth cap, and a layer count kept low enough for
  KM glazing.
- **m9. P7.13 omits the accepted lede (G).** Add "Lay a wash, pull a brush, letter a
  name." to the README order.
- **m10. The `!` in front of the dash gate's `grep` also inverts grep's exit 2.** A
  missing path then passes silently. Use `grep -rnI ... ; test $? -eq 1`.

## Verdict

**BLOCK.** B1 to B4 must be fixed before P7.1 or the fan-out starts:

- B1: the `Measure` mechanism and its owner list.
- B2: the undeclared shared files in the parallel group.
- B3: the registry and script contract.
- B4: the tracks along public paths.

M1 to M11 should be fixed in the same pass. The fixes are local edits to the plan, not
a change of approach. The research synthesis, the slicing and P7.1's regeneration design
are sound.
