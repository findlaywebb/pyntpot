# Review 03: how-to guides and the examples they quote

Scope: `docs/how-to/*.md` (9 pages), `examples/how_to_own_shapes.py`, `examples/how_to_route_ink.py`,
`examples/route_map.py`, `examples/map_styles.py`, `examples/place_card.py`, `examples/places.toml`,
`examples/themes/*.toml`, `pyntpot map --help`.

What I ran, all offline (fixture caches copied to the scratchpad so no plates were written into
`tests/fixtures/`):

- `examples/how_to_own_shapes.py out/`: runs, 1.8 s.
- `pyntpot map ambleside/track.gpx -o out/route.png --cache ambleside/ --contact …`: runs, 28 s on the first paint.
- `examples/how_to_route_ink.py ambleside/track.gpx ambleside/ out/ …`: runs, 10 s, logs "plates … are current" as the page says.
- `examples/place_card.py y-fenni/track.gpx y-fenni/ out/ you@example.org --theme examples/themes/y-fenni.toml --place y-fenni`:
  runs **only** after copying `tests/fixtures/y-fenni` to `./y-fenni` (see finding 3).
- A trimmed theme loaded with `Style.from_toml`, plus a script comparing it with `Style.default()` (finding 1).

Findings are ordered by impact. Each has: where; what is wrong and how it hurts the user; cause; fix;
size; area; related note.

---

## 1. A trimmed theme loads without error but paints a different, flatter map

- **Where:** `docs/how-to/write-a-theme.md:24-25`, `:98-118`; `src/pyntpot/maps/style.py:126-142`.
- **What's wrong:** the page says `Style.from_toml` "needs every group, and it rejects a key that a
  group does not have". It does not say that a key left **out** of a group is accepted and quietly
  takes the *dataclass* default, not the default theme's value. I checked: 25 fields differ between
  the two. With a missing key, `wash.wet_bleed`, `blooms`, `flow_rim`, `fluid_pass`,
  `silhouette_deform`, `pigment_separation`, `sea_variation`, `brush.ink_starve`, `pen_starve`,
  `brush_organic`, `stroke_smooth`, `paper.km_glazing`, `paper.paper_fibre`, `basemap.landmarks`,
  `landmark_max`, `generalise` and others all take a different value. A theme made of the 13
  table headers plus `paper_hex` loads cleanly and paints a visibly different card. Someone who trims
  their 304-line copy down to what they changed (the obvious thing to do) gets a worse map with no
  error and no log line. The "When it goes wrong" list has no "my map looks plainer than the
  default" entry. `docs/reference/style-fields.md:9` mentions that "the two differ for some fields",
  but the how-to never links it.
- **Cause:** missing library feature (no "missing key" check, and no merge over the default theme),
  plus prose.
- **Fix:** short term, make `from_toml` reject a missing key the same way it rejects an unknown one,
  or log every key that falls back. Also add a "When it goes wrong" line. Long term, merge over the
  default theme (the overrides feature). Either way the dataclass defaults and the default theme
  should agree, or the dataclass defaults should go.
- **Size:** S for the check or the warning; M to align the defaults. **Area:** maps.
- **Related:** `maps-themes-as-overrides` (#80). New evidence: it is not only that themes are full
  copies. Partial copies are already accepted silently and come out wrong. The note's "about 355
  lines" is also out of date (the default theme is 304 lines).

## 2. `with_route_ink` recolours the route but leaves its "start" and "finish" in the old pink

- **Where:** `docs/how-to/change-the-route-ink.md:14-22`, `:48-50`; `src/pyntpot/maps/lettering_marks.py:62`
  (`KIND_INK = {"marker": "route"}`); `src/pyntpot/letters/nib.py:277` (`"route": nib.label_route_ink`);
  `default.toml:182`.
- **What's wrong:** the route markers are lettered in `nib.label_route_ink`, which is a separate field
  hard-set to `#c22050`. `with_route_ink(colour=…)` changes only `route_ink.colour`. The guide's own
  result image, `docs/images/how-to/route-ink.webp`, shows a violet route with a **pink "start"**
  next to it. The page says "leave the rest of the map as it is", so a user following it gets a
  mismatch on the card. Themes avoid this only because their authors also edit `[nib]
  label_route_ink` by hand, and the page never mentions that field.
- **Cause:** library behaviour (two fields hold one concept). The prose does not warn about it.
- **Fix:** make `with_route_ink` also set `nib.label_route_ink`, or read the marker ink from
  `route_ink.colour` when lettering. Note: `label_route_ink` is in `LETTERING_GROUPS`, so the
  lettering digest would move. Decide in an ADR whether the route ink should feed the lettering
  digest. Until then, add a "When it goes wrong" entry: "the start label is still pink: set `[nib]
  label_route_ink`".
- **Size:** S to M. **Area:** maps / letters.
- **Related:** none. This is a new defect and should get a `docs/issues/` note.

## 3. The landmark guide's run command points at directories that don't exist, and `--theme` resolves against the repo root

- **Where:** `docs/how-to/letter-your-own-landmarks.md:79-81`; `examples/place_card.py:53-54,107-108,137-138`;
  `examples/how_to_route_ink.py:81-82,117-121,300-301`.
- **What's wrong:**
  (a) The command uses `y-fenni/track.gpx y-fenni/`. That data is in `tests/fixtures/y-fenni/`, and
  the page never says so. Pointing the cache at `tests/fixtures/y-fenni/` directly writes a
  `plates/` directory into the checkout's fixtures. The page should tell the user to copy the
  fixture first.
  (b) Both scripts resolve `--theme` as `REPO_ROOT / theme`, not relative to the current directory.
  `--theme my-theme.toml` from a user's own project directory fails with a `FileNotFoundError`
  inside the repo (an absolute path happens to work). This breaks the hand-off from "Write a theme"
  (which writes `my-theme.toml` in the cwd) to these scripts. `pyntpot map --style` resolves
  against the cwd, so the two behave differently.
- **Cause:** prose (a); code (b).
- **Fix:** (a) say "copy `tests/fixtures/y-fenni` to `y-fenni/`", or use that path and warn about the
  plates. (b) treat `--theme` as a normal path, `Path(theme)`, and drop `REPO_ROOT` (the docs
  build can pass repo-relative paths from the repo root).
- **Size:** S. **Area:** docs, examples.
- **Related:** `docs-examples-review` (#63).

## 4. Three of the eight map how-tos need a Python script because `pyntpot map` lacks an option

- **Where:** `change-the-route-ink.md:9-10` ("The command line has no route-ink option"),
  `letter-your-own-landmarks.md:9` ("no option for callouts"), `work-offline-and-reuse-the-cache.md:59-60`
  ("The command line has no such switch"); `pyntpot map --help`.
- **What's wrong:** the guides that most users will reach for each require copying a 50 to 300
  line example script. The missing `map` options are:
  - `--route-colour` / `--route-width`;
  - `--landmarks FILE` (the `places.toml` table shape already exists);
  - `--size` (`place_card.py --size` exists, the CLI does not have it);
  - `--offline` (today it means building providers with `budget=0` in Python).

  The offline case is the worst. The page promises "works with the network off", but the CLI then
  silently goes online if the cache key differs. The `place_card.py` script is effectively a
  second, richer CLI, kept in `examples/`.
- **Cause:** missing feature (CLI).
- **Fix:** add these options to `pyntpot map`, each a thin call into the existing API. Then rewrite
  the three guides with a one-line CLI path first and Python second.
- **Size:** M. **Area:** cli.
- **Related:** `cli-wider-commands` (#68). New evidence: that note is about *new commands*. This
  finding is about *options on `map`*, and three how-tos already tell the user the CLI can't do
  their task.

## 5. Every map script repeats the same five-line pipeline, passing the providers twice

- **Where:** `examples/route_map.py:243-249`, `map_styles.py:75-81`, `place_card.py:111-121`,
  `how_to_route_ink.py:133-137`, `src/pyntpot/maps/cli.py:76-86`, and quoted again in
  `change-the-route-ink.md:27-30`, `self-host-providers.md:48-56`, `work-offline…:52-56`.
- **What's wrong:** `plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))`
  appears in every map script. The providers go to `fetch` and again to `cache.key`, and the style
  is passed to all four stages. The how-tos have to explain this (`self-host-providers.md:44-45`:
  "they go to `fetch` and to `Cache.key`"). In `change-the-route-ink.md:108-109`, the failure "you
  passed the original `Style.default()` to a stage" exists only because the style is threaded by
  hand four times. `work-offline….md:96-99` warns about passing a different plates directory: a
  trap the API creates.
- **Cause:** API friction (missing convenience).
- **Fix:** carry the key on the basemap (`basemap.key`) or let `paint` take the `Cache`. Better still,
  add one public convenience, e.g. `map_card(track, cache, features, elevation, style, annotations=None, attribution=True) -> Image`,
  that the CLI and the examples call, keeping the four stages for callers who need them.
- **Size:** M (public API, needs an ADR). **Area:** maps.
- **Related:** none.

## 6. Laying lettering over your own picture takes about 15 lines of plumbing, copied between two examples

- **Where:** `docs/how-to/paint-your-own-shapes.md:55-57`; `examples/how_to_own_shapes.py:149-165`;
  `examples/how_to_route_ink.py:155-179`.
- **What's wrong:** step 3 of the guide hand-waves the hardest part ("stroke the marks onto a plate
  with `nib_plate` and lay the plate over the painting by its alpha, as the tutorial's lettering step
  does"). The script needs:
  - a second `Canvas` at `NIB_SCALE`;
  - a `NibSurface` with a `dark` array of zeros that nobody explains;
  - `GRAN_PX * NIB_SCALE`;
  - a `NibGroups` built from five style objects;
  - `nib_plate` **writing to a file**, then re-opening it, `.convert("RGBA")`, resizing with Lanczos,
    dividing by 255 and alpha-blending by hand.

  `how_to_route_ink._lettered` repeats it, and needs a `tempfile.TemporaryDirectory` because
  `nib_plate` can only write to disk. The two copies already differ: one converts through `"RGBa"`
  (premultiplied) before resizing, the other does not. The guide also never says why the plate is
  painted at twice the size.
- **Cause:** missing library feature, plus prose that skips the step.
- **Fix:** add a `letters` helper that returns the RGBA array, or lays marks over an `(h, w, 3)`
  painting (e.g. `nib_layer(marks, size, groups, scale=2) -> np.ndarray` and
  `lay_over(painting, rgba)`), with an optional `path`. Then show it in step 3.
- **Size:** M. **Area:** letters.
- **Related:** `docs-examples-review` (#63).

## 7. Switching the route to a pen stroke needs pydantic and dataclass surgery across two groups, and the guide teaches it with docs-image code

- **Where:** `docs/how-to/change-the-route-ink.md:63-99`; `examples/how_to_route_ink.py:144-152,193-207`;
  `default.toml:257-266`; `style_groups.py:157-167,259-280`.
- **What's wrong:**
  - **The page drifts into explanation.** "Try the treatments and the colours" quotes the `for`
    loop that builds the docs' 2×3 grid image. That loop is about a picture of the docs, not a
    user task. The actual change it depends on happens in `_row_style`, which the page does not
    show: `dataclasses.replace(small.route_ink, style="pen")` plus
    `small.model_copy(update={"route": dataclasses.replace(small.route, route_pen_brush=brush)})`.
  - **Two groups, three names.** The route's look is split between `[route]` (`route_pen`,
    `route_pen_brush`, `route_pen_width_px`) and `[route_ink]` (`style`, `px`, `colour`, `blend`,
    `opacity`). The width is called `px` in TOML, `width_px` in `with_route_ink` and `ink.px` on the
    value.
  - **The word "style" is overloaded.** The treatment key is called `style`, inside a `Style`, and
    the glossary calls it "treatment".
  - **`opacity` is undocumented.** It exists but is in neither `default.toml` nor the guide.
  - **Width can silently do nothing.** With a `pen` route, `width_px` changes nothing drawn. The
    page has to explain this twice (`:45-46`, `:110-114`).
- **Cause:** API friction and terminology; Diátaxis mixing in the prose.
- **Fix:**
  - Rename `route_ink.style` to `treatment` and `px` to `width_px`.
  - Let `with_route_ink` take `treatment`, `blend`, `opacity` and `pen_brush`.
  - Replace the grid section with a direct step: "To draw the route as a pen stroke: …".
  - Move the grid image to the gallery or an explanation page.
- **Size:** M (renames are breaking, ADR). **Area:** maps, docs.
- **Related:** `maps-route-casing` / `maps-route-glow` / `maps-route-shadow` touch the same group,
  so do the renames before adding fields.

## 8. "Write a theme" never mentions `pyntpot map --style`, never links the field reference, and its step 3 dead-ends

- **Where:** `docs/how-to/write-a-theme.md:38-50`.
- **What's wrong:** the quickest way to see a theme is `pyntpot map … --style my-theme.toml`, and the
  page doesn't mention it (only `map-from-the-command-line.md:53` does). Step 3 says "Pass `style` to
  `fetch`, `paint`, `letter` and `compose`, as `examples/route_map.py` does with the default", but
  `route_map.py` hard-codes `Style.default()` (`:245`) and has no theme option. The user has to edit
  the example. `docs/reference/style-fields.md`, the only place that explains about 230 field
  names such as `km_glazing`, `ribbon_k`, `gran_gamma` and `pen_pool_gain`, is not linked from the
  page.
- **Cause:** prose.
- **Fix:** make step 3 "Paint with it: `pyntpot map route.gpx -o out/map.png --cache cache/ --contact … --style my-theme.toml`",
  with Python as the alternative. Link the style fields reference in step 2. Add a short "most
  wanted changes" table: paper colour, cover pigments, route ink, `label_max`, `label_size_px`,
  `card.display_px`, `basemap.hillshade_mode`, `cover.relief`.
- **Size:** S. **Area:** docs.
- **Related:** `docs-glossary-in-place`, `docs-variable-effect-grids`.

## 9. Theme mistakes in colours and brush ids are caught only at paint time, after the fetch

- **Where:** `docs/how-to/write-a-theme.md:112-118`.
- **What's wrong:** the page admits "Loading does not check colours" and "does not check brush ids
  either". A typo such as `"cream"` or `"#fff"` therefore surfaces as
  `ValueError: invalid literal for int() with base 16` deep inside `paint`. That can come after a
  first-run fetch of a minute or two, and the error doesn't name the key. `with_route_ink`
  validates colours, so the theme loader is the odd one out.
- **Cause:** missing library validation.
- **Fix:** validate every `*_hex`, `*_ink`, `colour` and `[cover.pigments]` value as `#rrggbb`, and
  every `[brush.brushes]` and `*_brush` id against the brush sheet, in `Style.model_validate`. The
  error then names the table and key, as the other errors do. Drop the two "when you paint"
  entries from the page.
- **Size:** S to M. **Area:** maps.
- **Related:** none.

## 10. Changing one style field from Python means `model_copy(update={…: dataclasses.replace(…)})`

- **Where:** `examples/place_card.py:110`, `examples/how_to_route_ink.py:146-152,193-207`.
- **What's wrong:** a very common task, "make the card bigger" (`card.display_px`), takes
  `base.model_copy(update={"card": replace(base.card, display_px=size)})`. That leaks pydantic and
  dataclasses into user code. No how-to shows it, so users meet it only by reading example
  internals. `with_route_ink` is the only friendly setter.
- **Cause:** API friction (missing feature).
- **Fix:** add a general `Style.with_(group, **fields)` or `Style.replace({"card": {"display_px": 1200}})`,
  validated like `from_toml` and sharing its merge code with the theme-overrides feature.
- **Size:** M. **Area:** maps.
- **Related:** `maps-themes-as-overrides` (#80). It is the same merge, from Python.

## 11. Landmarks: "callout" vs `landmarks`, a non-public `Landmark` type, and steps that leave code out

- **Where:** `docs/how-to/letter-your-own-landmarks.md:13-43,63-65,85-86`; `src/pyntpot/maps/__init__.py`
  (exports `Annotations`, `JournalNote`; not `Landmark` or `SpanRequest`); `examples/places.toml`.
- **What's wrong:**
  - **Three names for one thing.** The page's term "callout" is not in GLOSSARY.md. The API field
    is `landmarks`, the TOML key is `callouts`, and the style has `pick_landmarks`.
  - **No public type.** `Landmark` is not public, so the only way to build one is
    `Annotations.model_validate({"landmarks": [...]})`, which is pydantic leaking into user code.
  - **Missing code.** Step 2 says "`callouts` is the list of tables from the file, read with
    `tomllib`" and leaves out the three lines that read it.
  - **Missing syntax.** The by-name lookup (`:63-65`) is described but not shown: a bare string,
    `"landmarks": ["Castell y Fenni"]`.
  - **Overloaded "places".** It means three things here: the `places.toml` file, `fetch(places=…)`
    (places of interest), and `Annotations.places` (settlement names).
  - **Separator noise.** `places.toml` carries 128-character dashed separator lines (`:23-24`, …).
- **Cause:** terminology, API surface, prose.
- **Fix:**
  - Pick one term: "landmark" fits the API. Rename the TOML key and the page, or add "callout" to
    the glossary as the canonical term and rename the field.
  - Export `Landmark`, so `Annotations(landmarks=(Landmark(name=…, lat=…, lng=…),))` works.
  - Show the `tomllib` read and the bare-string form.
- **Size:** S to M. **Area:** maps, docs.
- **Related:** `docs-glossary-in-place`, `maps-lettering-pin-icons`.

## 12. `label_max` is described as a cap on all names but limits landmarks only

- **Where:** `docs/how-to/letter-your-own-landmarks.md:29-31,87-90`; `style_groups.py:240-243`;
  `lettering/pipeline.py:158-163`.
- **What's wrong:** the page says "`label_max` caps how many names the card letters". It is the
  landmark cap only. Settlements, rivers, road numbers and the start marker come on top, and
  journal notes don't count. The Y Fenni caption says "six names" over a card that letters more
  than ten. A user raising `label_max` to fit more street names would see nothing change.
- **Cause:** prose.
- **Fix:** "`label_max` caps how many landmarks, yours or the map's, are lettered. Settlements,
  rivers, road numbers and the start marker are not counted."
- **Size:** S. **Area:** docs.
- **Related:** none.

## 13. Landmarks that are dropped are dropped silently, so the troubleshooting can't be followed

- **Where:** `letter-your-own-landmarks.md:87-92`; `lettering/pipeline.py:158-182` (off-card entries
  are skipped with no log); no log for the `label_max` cut or a by-name lookup that misses.
- **What's wrong:** "A callout is missing from the card" has four causes:
  - over the cap;
  - off the card;
  - the placer couldn't seat it;
  - a by-name lookup found nothing.

  None of them logs. The page can only say "check the latitude and longitude". The placer logs
  other drops (`placement_names.py:161,172`), so this gap is inconsistent.
- **Cause:** missing library logging.
- **Fix:** `log.info` each dropped landmark with its reason. Then turn the "When it goes wrong" entry
  into "find the line `dropped landmark 'X': off the card` in the log".
- **Size:** S. **Area:** maps.
- **Related:** none.

## 14. The elevation credit says "NASA SRTM" whatever dataset is used, and the only fix is to turn the credit off

- **Where:** `credit-the-map-data.md:69-72`; `self-host-providers.md:105-107`;
  `providers/opentopodata.py:60-63` (class-level `Credit`).
- **What's wrong:** `OpenTopoData(contact, endpoint, dataset)` takes any dataset, including the
  public server's non-SRTM ones such as `eudem25m` or `aster30m`, but the credit is fixed on the
  class. The guide's only remedy is `--no-attribution` / `attribution=False` plus a caption, so the
  user loses the on-card credit. `Credit` is not exported from `pyntpot.maps` either.
- **Cause:** missing library feature.
- **Fix:** give the providers a `credit=` keyword, or derive the credit from the dataset, and
  export `Credit`. Then rewrite both "When it goes wrong" entries.
- **Size:** S. **Area:** maps.
- **Related:** `maps-public-provider-protocols` (#78), which is adjacent.

## 15. CLI errors are full Python tracebacks, and the troubleshooting is keyed on exception class names

- **Where:** `docs/how-to/map-from-the-command-line.md:66-78`; `src/pyntpot/maps/cli.py:74-90`.
- **What's wrong:** `pyntpot map missing.gpx …` prints a 15-line traceback ending in
  `FileNotFoundError` (checked). The guide is aimed at users with "No Python needed" (`:4`), yet its
  error list quotes `xml.etree.ElementTree.ParseError`,
  `pydantic_core._pydantic_core.ValidationError: ... for Style` and so on. `main` catches nothing,
  so every user error ends in a stack trace and exit status 1.
- **Cause:** CLI code.
- **Fix:** catch `FileNotFoundError`, `ParseError`, `ValueError`, `pydantic.ValidationError`,
  `tomllib.TOMLDecodeError` and `FetchError` in `main`. Print `pyntpot map: error: <message>` and
  exit with status 2 or 1. Then shorten the guide's list to those messages.
- **Size:** S. **Area:** cli.
- **Related:** `cli-wider-commands`, which is adjacent.

## 16. `--margin-m` appears in `--help` but in no how-to, and `--help` shows no defaults

- **Where:** `map-from-the-command-line.md` (absent); `work-offline-and-reuse-the-cache.md:32-35`;
  `pyntpot map --help`.
- **What's wrong:** for a long or remote route the default 1 500 m margin can leave paper bare. The
  Skye card is recorded at 18 000 m (`tests/golden/test_places.py:110`), and nothing tells the user
  when to raise it. The margin is also part of the cache key, so the offline guide's "run the same
  command" should say "with the same `--margin-m`". `--help` shows neither the default (1500) nor
  that land cover uses at least 2600.
- **Cause:** prose; CLI help text.
- **Fix:** use `ArgumentDefaultsHelpFormatter` or write the defaults into the help text. Add a
  "Fetch a wider area" step or how-to, and add a margin note to the offline guide.
- **Size:** S. **Area:** cli, docs.
- **Related:** none.

## 17. Snippets in "Paint your own shapes" have unexplained positional numbers and undefined names

- **Where:** `docs/how-to/paint-your-own-shapes.md:17-38,52`; `examples/how_to_own_shapes.py:63-76,138-143`.
- **What's wrong:**
  - **Bare numbers.** `wash(mask, sheet, 0.6, 0.3)` gives `base` and `pool` as bare positionals,
    and `brush_from_id("MAJ6-e", 3.0, 1.0, BrushStyle())` gives the display width and the
    render-per-display scale the same way. The page explains none of them, so the user cannot tell
    which number to turn for a "paler wash" or a "thicker line".
  - **Undefined names.** The snippets use `W`, `H`, `corners`, `line`, `paper`, `sheet` and `SEED`
    without defining them, and show no imports.
  - **Seed hunting.** `HAND_SEED = 2`, "chosen so that the name has even spacing", suggests the user
    may have to try seeds to get acceptable lettering, and the page doesn't say so.
  - **Wrong attribution of the error.** The "When it goes wrong" entry blames `wash` for a size
    mismatch ("`wash` is refusing"). It is a raw numpy broadcast error; `wash` does no check
    (verified).
- **Cause:** prose plus API friction.
- **Fix:**
  - Use keyword arguments in both the snippets and the script: `wash(mask, sheet, base=0.6, pool=0.3)`,
    `brush_from_id("MAJ6-e", width_display_px=3.0, scale=1.0, style=BrushStyle())`.
  - Say in a line what each does.
  - Have `wash` raise `ValueError("mask is (100, 100), sheet is (320, 480)")`.
  - Mention trying another `hand.generator` seed if the spacing looks off.
- **Size:** S. **Area:** ink, docs.
- **Related:** `ink-public-wash-options`, `docs-variable-effect-grids`, `docs-brush-id-gallery`.

## 18. A card with no lettering needs `Lettering((), (), None)`

- **Where:** `examples/how_to_route_ink.py:210`.
- **What's wrong:** to compose without names the example builds a `Lettering` value from three
  positional nobodies. The script's docstring claims it "introduces none beyond
  `Style.with_route_ink`", so this goes unremarked.
- **Cause:** API friction.
- **Fix:** let `compose(..., lettering=None)` or add `Lettering.empty()`. Alternatively, document
  `[lettering] labels = false`, which already letters nothing.
- **Size:** S. **Area:** maps.
- **Related:** none.

## 19. The fetch margins are worked out by hand in two places

- **Where:** `src/pyntpot/maps/cli.py:78`; `examples/place_card.py:112-117`.
- **What's wrong:** both repeat `FetchMargins(m, max(LANDCOVER_MARGIN_M, m))`, the rule that land
  cover is fetched at least as wide as the features. A user who builds `FetchMargins(5000)` by hand
  gets a land cover margin of… whatever the second default is. It is easy to get a different
  cache key from the CLI.
- **Cause:** API friction.
- **Fix:** add `FetchMargins.around(margin_m)` (or make the constructor apply the max) and use it in
  both places.
- **Size:** S. **Area:** maps.
- **Related:** none.

## 20. "Four example themes" tells the user to diff 300-line files themselves

- **Where:** `docs/how-to/write-a-theme.md:52-57`.
- **What's wrong:** "Read the files beside the pictures to see what changed". Each example theme is
  299 to 305 lines and differs from the default in 52 to 105 lines. The prose summaries say which
  tables changed but not the values, so a user can't copy "the sepia paper" without diffing.
- **Cause:** prose; the underlying cause is that themes are full copies.
- **Fix:** under each picture, show the changed tables only, as a TOML block, generated from a diff
  against `default.toml`, so the docs can't drift.
- **Size:** S. **Area:** docs.
- **Related:** `maps-themes-as-overrides`, `maps-theme-preview-card`, `maps-named-themes`.

## 21. None of the how-tos say the repository ships offline caches to try them on

- **Where:** "Before you start" in `map-from-the-command-line.md:6-7`, `change-the-route-ink.md:7-10`,
  `letter-your-own-landmarks.md:7-9`, `work-offline….md:7-8`.
- **What's wrong:** `tests/fixtures/{ambleside,lynmouth,y-fenni,oxford,skye,yr-wyddfa}` each hold a
  `track.gpx` and all three payloads. Copied to a scratch directory, every map how-to runs with no
  network and no contact traffic (verified for Ambleside and Y Fenni). The guides send everyone to
  the public servers first, and the landmark guide already half-relies on a fixture without saying
  so (finding 3).
- **Cause:** prose.
- **Fix:** add one line under "Before you start" on each map guide: "From a checkout you can try it
  offline: `cp -r tests/fixtures/ambleside ambleside` and use `ambleside/track.gpx` with
  `--cache ambleside/`."
- **Size:** S. **Area:** docs.
- **Related:** `tests-retire-lynmouth`. Note that the CLI guide uses Lynmouth while the others use
  Ambleside.

## 22. The offline guide's Python block stops at `fetch` and has no imports

- **Where:** `docs/how-to/work-offline-and-reuse-the-cache.md:52-57`.
- **What's wrong:** the block that "guarantees nothing reaches the network" ends at `basemap = fetch(...)`.
  The user then has to assemble `paint`/`letter`/`compose` and the imports from another page.
  `self-host-providers.md:59-60` lists the imports in prose instead of code.
- **Cause:** prose.
- **Fix:** show the full block with imports, once; or, with finding 4, `pyntpot map --offline`.
- **Size:** S. **Area:** docs.
- **Related:** none.

## 23. The how-to index is an ungrouped list with uneven titles

- **Where:** `docs/how-to/index.md:3-12`.
- **What's wrong:** "Each guide … assumes you have done the tutorials", but "Paint your own shapes"
  needs the watercolour tutorial and the map guides need First map. The list mixes the two without
  grouping. One title carries its own steps ("Write a theme: copy the default, change a group and
  load it"), unlike the others. "Paint your own shapes" is the only guide that isn't a map task, so
  the `ink`/`letters` half of the library has one how-to.
- **Cause:** prose.
- **Fix:** group as "Maps: from the command line", "Maps: from Python" and "Painting and lettering
  without a map". Use plain titles and name the prerequisite tutorial per group.
- **Size:** S. **Area:** docs.
- **Related:** none.

## 24. The grid caption names a theme that the run command doesn't pass

- **Where:** `docs/how-to/change-the-route-ink.md:56-58,72`.
- **What's wrong:** the caption says the grid is painted "in `examples/themes/ambleside.toml`" with
  `figure="grid"`. The only command shown runs the violet card with the default theme. A user who
  wants to reproduce the grid has to find the `--figure grid --theme examples/themes/ambleside.toml`
  flags in the script.
- **Cause:** prose.
- **Fix:** give the grid's command, or drop the grid section (finding 7).
- **Size:** S. **Area:** docs.
- **Related:** none.

---

## Missing how-tos

These are tasks a user plausibly has, with no guide today. "API" marks the ones that also need a
library change first.

1. **Change the card's size or resolution, for print or the web.** `card.display_px` and
   `supersample` need `model_copy` + `dataclasses.replace` (finding 10), and the CLI has no `--size`.
   Very common. API.
2. **Mark a stretch of the route** (a climb, a café stop, a bad section): `Annotations.spans`,
   `SpanRequest` by index, km or seconds. The machinery is substantial (`lettering/spans.py`), but
   `SpanRequest` is not exported and nothing documents it. API.
3. **Pin journal notes to the map.** `Annotations.notes` / `JournalNote` is exported and the Skye
   card uses four, but there is no guide. The 60-character and 6-note limits are only in the
   glossary.
4. **Always letter a settlement, or pick roads.** `Annotations.places`, `[basemap] pick_roads` and
   `pick_places`.
5. **Choose names from the candidate export.** `candidate_export` → pick → `Annotations`. The
   glossary describes it; no guide uses it.
6. **Draw your own map from the vector layers** (SVG, a plotter, a web map): `vector_layers` /
   `VectorLayers`.
7. **Fetch a wider area or map a long route** (`--margin-m`, `FetchMargins`, blank paper at the
   edges): finding 16.
8. **Map a planned route, or a track that isn't GPX** (FIT, GeoJSON, a list of points).
   `Track(lat=…, lng=…)` already works. The CLI guide only says "export the recorded track
   instead".
9. **Add relief: contours, hachures or hillshade** (`[basemap] hillshade_mode`,
   `contour_interval`), and turn land cover or relief off.
10. **Use another font for the lettering** (`[face] label_face` takes a `.ttf` path; it is
    mentioned nowhere in the how-tos).
11. **Get a different variation of the same map** (seeds: `sheet_seed`, `label_seed`, `bloom_seed`,
    …), e.g. when a name lands badly.
12. **Letter a title or caption on your own picture** without a path, or on a map card. Only the
    path case is covered, inside "Paint your own shapes". `examples/word.py` and
    `examples/lettering.py` have no how-to.
13. **Map many tracks in one go**, sharing a cache, within the providers' daily budgets.
14. **Handle fetch failures in a script** (`FetchError`, `ProviderBudgetExceededError`, retries).
    These are exported but undocumented.
15. **Change a wash or ink colour in your own painting** (`PIGMENTS` vs `PAINTERS_PIGMENTS`,
    `rgb`). Related: `docs-pigment-gallery`, `ink-one-pigment-registry`.
16. **Export a transparent or plate-by-plate image** (the plates are on disk as WebP; nothing
    tells a user they can lay them in another tool). See `reference/cache-layout.md`.

---

Count: 24 findings plus 16 missing how-tos.
