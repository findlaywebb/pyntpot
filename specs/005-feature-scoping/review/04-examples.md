# Review 04: the example scripts and the gallery

Slice: `docs/gallery.md`, all 28 `examples/*.py` (5 578 lines), `tests/examples/`, and the
docs image registry `tests/support/docs_images.py`. Read-only review; nothing edited.

**Headline numbers**

- Private imports: **none**. Every `pyntpot` import in `examples/` is a name in a public
  package's `__all__` (checked by AST against `pyntpot.ink`, `.letters`, `.maps` `__all__`),
  and `tests/architecture/test_examples.py` enforces it. The cost shows up elsewhere: a
  private table is copied as a literal (`brush_sheet.BRUSH_IDS`), and private behaviour is
  rebuilt by hand (the nib-plate round trip, F1).
- Runs (all offline, all exit 0): paper 0.6 s · lettering 1.1 s · kaleidoscope 1.4 s · word
  2.2 s · brush_sheet `--figure sheet` 2.3 s · derwentwater 3.4 s · glyph_sheet 3.7 s ·
  tutorial_grids `--figure composition` 3.8 s · fern_family 3.8 s · pigment_swatches 4.0 s ·
  trees `--figure family` 16.4 s · place_card (Ambleside fixture copied as cache, ambleside
  theme, size 720, the CLI with a dummy contact, cache hit so nothing fetched) 18.6 s.
- Boilerplate counts across `examples/`:
  - `Canvas(0, 0, …)` identity canvases: 47.
  - `paper_plate(` calls: 33, in 25 files.
  - `np.random.default_rng(`: 25.
  - `acc = np.zeros` + `stamp` + `ink_density(acc …)`: 16.
  - `brush_from_id(…, 1.0, BrushStyle())`: 15, in 11 files.
  - `NibGroups(…)` built in full: 13 files.
  - Nib-plate write → reopen → Lanczos → alpha-blend: 14 copies, in 13 files.
  - `np.mgrid` disc or mask: 11.
  - `rgb(*PIGMENTS[…])`: 18 files.
  - `*TRANSPARENCY[…]`: 18 lookups.
  - `wash(…)` with bare positional densities: 26 of 30 calls.
  - `argparse` + `logging.basicConfig` + `main(out_dir…)`: all 28 scripts.

Findings are ordered by impact: how much a newcomer copies, then how wrong it is.

---

## F1. The nib-plate round trip is hand-rolled in 13 scripts (14 copies)

- **Where:**
  - `examples/brush_sheet.py:138-162`
  - `composition.py:119-135`
  - `derwentwater.py:~245-260`
  - `glyph_sheet.py:134-153`
  - `how_to_own_shapes.py:~150-166`
  - `how_to_route_ink.py:155-180`
  - `lettering.py:78-95`
  - `nib_stages.py:154-167` and again at `195-218`
  - `pigment_swatches.py:75-105`
  - `social_preview.py:86-106`
  - `tutorial_grids.py:119-154`
  - `wash_stages.py:99-124`
  - `word.py:113-133`
- **What's wrong:** Lettering over a picture always takes the same 15 to 25 lines:
  1. Build a `Canvas` at `NIB_SCALE` times the size, with `NIB_SCALE = 2` redefined in 13
     files.
  2. Build a zero `dark` array and a `NibSurface`.
  3. Build all five `NibGroups` fields. `NibGroups` "holds no defaults", and `face` and
     `hand_style` are passed both to `Hand(…)` and to `NibGroups(…)`.
  4. Call `nib_plate`, which only *writes a file*: a lossy WebP by default, at
     `PaperStyle.paper_quality`.
  5. Re-open the file with PIL, `resize(…, LANCZOS)`, divide by 255 and blend by alpha.

  The copies have drifted apart:
  - 6 copies convert `"RGBa"` before resizing and 8 convert `"RGBA"`. Pillow 13.0's `resize`
    premultiplies RGBA itself, so the two give the same result, but the explicit `RGBa` is
    unexplained noise a reader will think matters.
  - 9 copies write the plate to a `tempfile.TemporaryDirectory`. 5 (composition,
    derwentwater, how_to_own_shapes, lettering, word) leave `<stem>-plate.webp` in the
    caller's `out_dir`, and `tests/examples/test_letters_examples.py:121` pins that side
    file as behaviour.
  - Each copy's `gran_px` is worked out differently (`GRAN_PX * NIB_SCALE`,
    `SLOW_GRAN_PX * w / DESIGN_W`, `6.0 * NIB_SCALE`, `GRAN_PX * NIB_SCALE * w / GRID_W`).
  - A lossy encode and decode sits in the middle of every lettered image.
- **Cause:** Missing library feature. `letters` has no in-memory plate and no "letter
  these settings over this image" call.
- **Suggested fix:** Two public calls in `letters`:
  - `nib_rgba(marks, surface, groups) -> (rgb, alpha)`, which `nib_plate` would then wrap to
    write the file.
  - A convenience `letter_over(image, settings, *, nib=NibStyle(), seed, scale=2,
    ground=None, gran_px=…)` that returns the blended image.

  Give `NibGroups` defaults, or a `NibGroups.default(nib=…)`, and let `NibSurface.dark`
  default to bare paper. This widens the public API, so it needs an ADR. Each example then
  drops to 2 to 3 lines. Re-pin the docs images, since the lossy step goes and the pixels
  move.
- **Size:** L (API + ADR + 13 scripts + re-pin). **Area:** letters (ink for any shared
  `lay_rgba`).
- **Related:** none tracked. This is the largest single gap behind `docs-examples-review`
  (#63).

## F2. The gallery's caption for `nib-angles` describes a different picture

- **Where:** `docs/gallery.md`, explanation section, under `explanation/nib-angles.webp`.
  Compare `examples/nib_stages.py:90,100`.
- **What's wrong:** The caption reads "The name is Ambleside. The labels read -38, 0 and 90
  across, and 0.5 and 0.85 down." The script writes **Keswick** (`NAME = "Keswick"`) at
  **four** angles (`-38, 0, 38, 90`) and **three** thinnings (`0, 0.52, 0.85`). The alt
  text above the caption is right ("Keswick … three rows of four"). The caption was copied
  from the `grid-nib` caption of `tutorial_grids.py`.
- **Cause:** Docs. No test checks a caption's labels against the script's constants.
- **Suggested fix:** Correct the caption. A cheap guard: have the caption name the
  constants (`ANGLES`, `THINS`) rather than restate them.
- **Size:** S. **Area:** docs. **Related:** `docs-examples-review`.

## F3. The map pipeline and style tweaks are re-derived in every map script

- **Where:**
  - `examples/route_map.py:172-178`
  - `map_styles.py:75-81`
  - `place_card.py:107-121`
  - `how_to_route_ink.py:~140, 189-207`
  - `social_preview.py:150`, which reaches `place_card.main` through `runpy`
  - The same steps in `src/pyntpot/maps/cli.py:84`, `docs/tutorials/first-map.md:92`,
    `docs/how-to/change-the-route-ink.md:28` and `docs/how-to/self-host-providers.md:52`.
- **What's wrong:**
  1. `paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))`
     appears in 5 examples, the CLI and 3 docs pages. A newcomer has to learn the cache's
     keying to paint a map.
  2. Changing one field of a style group takes
     `style.model_copy(update={"card": dataclasses.replace(style.card, display_px=…)})`:
     `place_card.py:110`, and 3 times in `how_to_route_ink._grid`, two levels deep. Only
     the route ink has a helper (`with_route_ink`).
  3. `place_card.py:112-117` re-implements the library's fetch-margin default rule ("land
     cover is the larger of its default and the features margin").
  4. `Style.from_toml(REPO_ROOT / theme) if theme is not None and theme != "" else
     Style.default()` is copied in `place_card.py:107` and `how_to_route_ink._base`.
- **Cause:** Missing library features.
- **Suggested fix:** One or more of:
  - `Cache.plates_dir_for(track, features, elevation)`, or `paint(basemap, style, cache)`.
  - A one-call `render_card(track, cache, features, elevation, style, annotations=None)`,
    which the CLI and the examples would share.
  - `Style.with_card(display_px=…)`, or a general `Style.with_(group, **fields)`.
  - `FetchMargins.around(features_m)`.
  - `Style.load(theme: Path | None)`.
- **Size:** M. **Area:** maps.
- **Related:** `cli-wider-commands` (#68), which could reuse a shared pipeline call, and
  `maps-themes-as-overrides` (#80), a different problem (theme files) that also fixes
  tweaking a style. New evidence: the 9 copies, and the margin rule duplicated outside the
  library.

## F4. Setting up blank paper is 3 calls and 6 redundant numbers

- **Where:** 47 × `Canvas(0, 0, w, h, w, h)` and 33 × `paper_plate(sheet, canvas, style, w)`,
  in 25 files. For example `examples/paper.py:32-34`, `pigment_swatches.py:126`,
  `tutorial_grids.py:102-105` (its own `_paper` helper), `nib_stages.py:241,270,304`.
- **What's wrong:**
  - Outside `maps`, a `Canvas`'s metre box means nothing, so every script passes `0, 0, w,
    h, w, h`.
  - `paper_plate` reads only `canvas.w/h` and then takes `display_px`, which is `w` again.
  - The order of `Sheet(h, w, …)`, height first, is the reverse of `Canvas(…, w, h)` and
    `PIL.resize((w, h))`, a trap for anyone copying the code.
  - The same goes for brush marks: `brush_from_id(id, width, 1.0, BrushStyle())` (15×)
    always passes `scale=1.0` and a default style. `acc = np.zeros((h, w)); stamp(acc, …,
    np.random.default_rng(SEED)); ink_density(acc, brush, sheet)` is the 3-step stroke
    (16×).
- **Cause:** API ergonomics: no defaults for the pixels-only case.
- **Suggested fix:**
  - Add `Canvas.pixels(w, h)`.
  - Default `paper_plate`'s `display_px` to `canvas.w`.
  - Default `brush_from_id`'s `scale=1.0` and `style=BrushStyle()`.
  - Possibly add a `stroke(sheet, lines, brush, rng) -> density` that wraps the
    accumulator, stamp and `ink_density` steps.

  These are small API widenings, one ADR.
- **Size:** M. **Area:** ink. **Related:** `docs-examples-review`.

## F5. Colour lookups are triple-indexed, and map-role pigments are used as paint colours

- **Where:** 18 files do `rgb(…PIGMENTS[key])`, with 18 `…TRANSPARENCY[key]` lookups beside
  them. For example `fern.py:143-158` makes 4 layers with 8 lookups, plus `word.py:107`,
  `trees.py:339-344` and `curves.py:149-151`.
- **What's wrong:**
  - The `ink-one-pigment-registry` note already covers the lookup cost.
  - New evidence: the non-map pictures pick colours by **map role**:
    - `fern.py` and `fern_family.py`: `"wood"`, `"scrub"`.
    - `kaleidoscope.py:98-103`: `"water"`, `"wetland"`, `"wood"`, `"heath"`.
    - `derwentwater.py:77-87`: `"wetland"`, `"rock"`, `"relief"`, `"scrub"`, `"heath"`,
      `"sand"`.
    - `word.py`: `"wood"`.
    - `curves.py:118`: a spirograph in `"wood"`, in a file whose docstring talks only of
      painter's pigments.
  - Meanwhile `pigments.py`, `trees.py` and `nib_stages.py` use `PAINTERS_PIGMENTS`. A
    newcomer learns that "wood" is a colour, against the GLOSSARY, which says the painter's
    pigments are for exactly this.
  - Rung 2 (`wash.py`) teaches `PIGMENTS["water"]` and rung 4 switches tables.
- **Cause:** Naming and design: two registries, and no rule on which an example uses.
- **Suggested fix:** Until the registry merges, make every non-map picture use
  `PAINTERS_PIGMENTS` (ferns: sap_green and hooker's green; derwentwater: ultramarine,
  burnt umber and so on). This changes pixels, so re-pin. State the rule in `CONTRIBUTING.md`.
- **Size:** M. **Area:** ink, docs.
- **Related:** `ink-one-pigment-registry` (#72), `docs-pigment-gallery`.

## F6. The labelled-grid figure is implemented five separate times

- **Where:**
  - `tutorial_grids.py:92-99,162-190` (`_layout`, `_labels`)
  - `nib_stages.py:221-262` (`_cells`, `_angles_grid`)
  - `brush_sheet.py:165-211` (`_grid`)
  - `wash_stages.py` (`_glaze_grid`, 52 lines)
  - `how_to_route_ink.py:180-247` (`_grid`, 68 lines, nesting 3)
- **What's wrong:**
  - Each has its own `LEFT/TOP/GAP/PAD` constants.
  - Each has the same magic label offsets: column labels at `top - 12` or `- 14`, row
    labels at `left - 12` and `y + h/2 + 7`.
  - Each has its own cell arithmetic and its own copy of the `_letter` round trip (F1).
- **Cause:** Missing shared helper.
- **Suggested fix:** This is exactly the helper `docs-variable-effect-grids` proposes ("one
  helper in `examples/` that paints a picture across a list of values"). The new evidence is
  that it would *replace five existing* layouts, not only enable new grids. Examples are
  scripts, not a package (see F9), so put the helper where scripts can import it, such as
  `examples/_grid.py` with an allow rule in `test_examples.py`. Otherwise grids stay copied.
- **Size:** M. **Area:** docs.
- **Related:** `docs-variable-effect-grids` (#67).

## F7. The gallery is not the complete index it claims to be, and some outputs are shown nowhere

- **Where:** `docs/gallery.md:3` ("Every picture in these docs is painted … Each picture is
  shown under the page it illustrates").
- **What's wrong:** Registry entries missing from the gallery:
  - `reference/glyph-sheet.webp` (`glyph_sheet.py`, shown in `docs/reference/letters.md`).
    The gallery has no Letters reference section at all.
  - `painting-with-python/svg-flat.webp`, `svg-washes.webp` and `svg-ink.webp`, the stage
    figures of `svg_drawing.py`.
  - `site/paper.webp`, `rule.webp` and `header.webp`. These are fine to leave out as site
    chrome, but the claim should say so.

  Outputs no docs page shows:
  - `brush_sheet.py --figure sheet` (every brush id) is painted and tested
    (`test_ink_examples.py:69`) but not registered.
  - `site_theme.py --figure palette` writes CSS, not an image.

  `tests/architecture/test_docs_images.py` checks the registry against Markdown, but not that
  the gallery is complete. `examples/` has no README or index, so the gallery is the only
  map of the scripts.
- **Cause:** Docs, plus a missing guard.
- **Suggested fix:**
  - Add the glyph sheet and the three SVG stages to the gallery.
  - Reword the claim to exclude site chrome.
  - Add an architecture test that every non-`site/` registry image appears in `gallery.md`.
  - Either register the brush id sheet or drop the figure (see the note).
- **Size:** S. **Area:** docs.
- **Related:** `docs-brush-id-gallery` (the `sheet` figure is the seed of that feature; the
  note proposes a new `examples/brush_gallery.py`, though `brush_sheet.py` already holds one
  figure of it), `docs-examples-review`.

## F8. Docs-build scripts sit beside the user examples and look like them

- **Where:**
  - `examples/site_theme.py` (359 lines, a 135-line CSS `Template` at 75-210, writes
    `pyntpot.css`).
  - `social_preview.py` (GitHub's social image; loads `place_card.py` with `runpy.run_path`
    at :150).
  - `glyph_sheet.py`, which exports test hooks `glyph_seed`, `line_seed`, `cell_box`,
    `line_box` and `paint` for `tests/examples/test_glyph_sheet.py`.
  - `brush_sheet.py:63-81`, whose 46-line `BRUSH_IDS` literal mirrors private tables "because
    the brush tables are private"; an architecture test keeps it in sync.
- **What's wrong:**
  - These are build tools for the site and README. A newcomer browsing `examples/` cannot
    tell them from teaching scripts.
  - `site_theme`'s `palette` figure breaks the registry contract "writes exactly one image
    per call".
  - `social_preview`'s `runpy` sibling import is a pattern no user should copy.
  - `BRUSH_IDS` exists only because `ink` does not export its brush ids.
- **Cause:** Code placement, and a missing feature (a public brush id list).
- **Suggested fix:**
  - Move `site_theme.py` and `social_preview.py` to a `docs/build/` or `tools/` directory the
    registry can also read, or at least add an `examples/README.md` that splits "teaching
    scripts" from "docs build scripts".
  - Export a public `BRUSH_IDS` (or `brush_ids()`) from `pyntpot.ink`, the glossary's
    `BRUSH_TREATMENTS`/`PEN_ROWS`/`BRUSH_COLOURS` made public, and delete the literal.
  - Move the CSS template into a `.css.tmpl` file.
- **Size:** M. **Area:** docs, ink.
- **Related:** `ink-data-driven-brushes-and-pigments`, `docs-brush-id-gallery`,
  `cli-wider-commands` ("painting the reference sheets").

## F9. Fern and fern family copy one another; tree and tree family share a script

- **Where:** `examples/fern.py:81-127` against `fern_family.py:99-148`, and `trees.py:347-386`.
- **What's wrong:** `fern_family.py` re-implements `fern_points`, `_count`, `_cover`,
  `_thicken` and `_dabs`, with diverging signatures (`fern_points(n, seed)` against
  `fern_points(maps, n, rng)`), and the same wash literals (`0.55, 0.25` / `0.75, 0.3`).
  `trees.py` does the single tree and the family of nine in one script with `figure=`.
  `fern_family.perturbed(maps, rng)` and `trees.perturbed(shape, rng)` share a name and
  differ in type. The two fractal pages teach the same "family" idea with two different
  code structures.
- **Cause:** Code. Scripts cannot import siblings without `runpy`.
- **Suggested fix:** Fold `fern_family.py` into `fern.py` as `figure="family"`, as `trees.py`
  does, and re-register `painting-with-python/fern-family.webp` with
  `("figure", "family")`. The pixels should not move if the seeds are kept.
- **Size:** S–M. **Area:** docs.
- **Related:** `docs-examples-review`.

## F10. Unnamed numbers in the picture code

- **Where:**
  - `trees.py:294-335` (`paint_tree`): about 25 literals, among them `0.22`, `0.07`,
    `0.075`, `0.05`, `0.3/0.15`, `0.4/0.3`, `0.025`, `0.007`, `0.004`, `0.55`, `0.45`,
    `0.7`, `2:12`, `10` and `12`. The file is also at exactly 400 lines, the soft budget.
  - `pigment_swatches.py:111,133,144`: offsets `12`, `-8` and `28`.
  - Grid label offsets `-12`, `-14` and `+7` in 5 files (F6).
  - `lettering.py:80`: type size `36.0`.
  - 26 of 30 `wash(...)` calls pass body and pool as bare positionals (`0.6, 0.3`); only
    `svg_drawing.py:240` and `wash_stages.py` name them.
  - `composition.py:61-67`, `lettering.py:44-49` and `how_to_own_shapes.py` lack the `#:`
    comments that `paper.py` and `wash.py` give `W, H, GRAN_PX, SEED`.
- **Cause:** Code.
- **Suggested fix:** Write `wash(mask, sheet, base=0.6, pool=0.3)` everywhere, or make those
  keyword-only in the API. Name `trees`' crown, foot and trunk fractions in `Shape` or a
  `Crown` dataclass. Add the missing `#:` comments.
- **Size:** S–M. **Area:** docs (ink for keyword-only `wash`).
- **Related:** `docs-examples-review` (its checklist), `ink-public-wash-options`.

## F11. Naming drift between scripts

- **What's wrong:**
  - The logger is `log` in the 5 map scripts and `logger` in the other 23.
  - `canvas2`/`dark2` appear in 6 files (composition, derwentwater, how_to_own_shapes,
    lettering, nib_stages, word). Names should say what a thing is: `nib_canvas`,
    `nib_ground`.
  - `_disc` returns a mask in pigments, tutorial_grids, wash_stages and word, but a polar
    outline in `kaleidoscope.py:87`.
  - `_cover` means a point-density threshold in fern and fern_family, and a polygon mask in
    curves and kaleidoscope.
  - `figure=` names a *theme* in `map_styles.py:51`.
  - "callout" is used in `examples/places.toml`, `place_card.py` and the gallery for what
    the API calls `landmarks` (`place_card.curated` remaps `callouts` to `landmarks` at :69).
    "callout" is not in `GLOSSARY.md`.
  - Output file names mix styles:
    - `brush_grid.png`, `route_ink_grid.png`, `pigment_swatches.png`, `glyph_sheet.png`;
    - against `grid-<figure>.png`, `nib-<figure>.png`, `trees-<figure>.png`,
      `fern-family.png`, `social-preview.png`.
  - `argparse` descriptions come from `__doc__.splitlines()[0]` in 8 scripts and a literal
    in 20.
  - `STEM` exists in 7 scripts only.
  - Figure validation varies: a `FIGURES` tuple in most, the `SIZES` dict keys in trees, the
    `_PAINTERS` dict in tutorial_grids.
  - The default figure varies: `sheet`, `angles`, `nib`, `paper`, `tree`, `violet`.
- **Cause:** Naming.
- **Suggested fix:**
  - One convention, written into `CONTRIBUTING.md`: `logger`, `FIGURES`, hyphenated output
    names `<stem>[-<figure>].png`, and a literal one-line description.
  - Rename `canvas2`/`dark2`.
  - Add "callout" to the glossary as the places file's word for a caller's landmark, or
    rename the TOML key to `landmarks`.
- **Size:** S. **Area:** docs.
- **Related:** `docs-glossary-in-place`, `docs-examples-review`.

## F12. `map_styles` and `place_card` write `map.png` whatever the figure or place

- **Where:** `examples/map_styles.py:83` and `place_card.py:123`.
- **What's wrong:** Running the four themes, or the five places, into one `out/` keeps only
  the last card. The docstring example (`map_styles.py winter … out/`) invites exactly that
  loop. Every other multi-figure script names its file by figure.
- **Cause:** Code.
- **Suggested fix:** Write `map-<figure>.png` and `<place or "map">.png`. The registry reads
  only the returned path, so no pin moves.
- **Size:** S. **Area:** maps.

## F13. Themes resolve against the repository root, so a copied script breaks

- **Where:** `examples/place_card.py:54,108` and `how_to_route_ink.py:82,124-127`.
  `map_styles.py:45` (`THEMES_DIR` beside the script) does it a third way.
- **What's wrong:** `--theme examples/themes/x.toml` is joined to `Path(__file__).parent.parent`.
  It works only inside a checkout: a newcomer who copies `place_card.py` into their own
  project, or passes a path relative to their working directory, gets a wrong path.
- **Cause:** Code, kept to fit the registry's "path relative to the repo root" contract.
- **Suggested fix:** Take a plain `Path` in `main`, resolved by the caller, and let the
  registry, `make_docs_images.py` and the pin test do the `REPO_ROOT /` join.
- **Size:** S. **Area:** maps, tests.

## F14. `Setting.path` forces a tuple-of-tuples conversion

- **Where:** 7 copies of `tuple((float(px), float(py)) for px, py in zip(x, y, strict=True))`:
  `composition.py:77`, `lettering.py:58`, `word.py:85`, `nib_stages.py:111,192`,
  `social_preview.py:93` and `how_to_own_shapes.py:~115`.
- **What's wrong:** Every path is built in numpy and then unpacked into Python floats,
  because `Setting.path` is typed `tuple[Pt, ...]`.
- **Cause:** API. A frozen hashable dataclass wants tuples.
- **Suggested fix:** Accept any `(N, 2)` array-like in `Setting.__post_init__` and convert
  it there. An ADR, since `Setting` is public.
- **Size:** S. **Area:** letters.

## F15. Some scripts have no fast test, and one CLI hides an option

- **Where:** `tests/examples/` and `examples/site_theme.py:322,353-359`.
- **What's wrong:**
  - `word`, `how_to_own_shapes`, `how_to_route_ink`, `place_card`, `social_preview` and
    `map_styles` have no test in `tests/examples/`. They run only through the
    `golden`-marked docs pins (`tests/golden/test_docs_images.py`, `test_places.py`,
    `test_map_styles.py`), which the main CI job excludes (`-m "not golden …"`); the
    separate golden workflow runs them.
  - `site_theme.main` takes `size`, but its CLI has no `--size`. It is the only script whose
    `main` options are not all on the command line.
- **Cause:** Tests, code.
- **Suggested fix:** One small-size smoke parametrize over the offline ink and letters
  scripts not yet covered (`word`, `how_to_own_shapes`). The map scripts can share the
  `tests-shared-lynmouth-paint` fixture. Add `--size` to `site_theme`.
- **Size:** S. **Area:** tests.
- **Related:** `tests-shared-lynmouth-paint`.
