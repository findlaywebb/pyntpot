# 05: Reference docs, explanation docs and the public API surface

Scope: `docs/reference/*`, `docs/explanation/*`, `mkdocs.yml` nav, and the four `__all__`
packages. Method: read the pages and inits, introspected the API with `inspect`, loaded it
with griffe, and **built the site** (`uv run --group docs mkdocs build` into the scratchpad)
to check what a reader actually sees on the API pages. No repo file was changed.

Public surface measured: 49 unique public names (ink 18, letters 9, maps 21, plus
`__version__`); the top level re-exports 17 of them.

Ordered by impact.

---

## 1. The API pages show no fields for the style groups, `Brush`, `Sheet`, `Canvas`, or the pigment tables

- **Where:** `src/pyntpot/ink/style.py:30` onward (`PaperStyle`, `WashStyle`), `src/pyntpot/ink/brush_style.py` (`BrushStyle`), `src/pyntpot/letters/style.py` (`NibStyle`), `src/pyntpot/ink/brush.py:168-213` (`Brush`), `src/pyntpot/ink/sheet.py:46,80` (`Canvas`, `Sheet`), `src/pyntpot/ink/pigment.py:20-103` (`PIGMENTS`, `TRANSPARENCY`, `PAINTERS_*`, `PigmentLayer`), `src/pyntpot/__init__.py:33` (`__version__`).
- **What's wrong:** field and constant docs are written as Sphinx `#:` comments, and `Brush` uses trailing `# ...` comments. griffe/mkdocstrings reads neither. In the built site:
  - `reference/ink/`: the `PaperStyle` entry has its class prose and **none of its 22 fields** (`plate_lossless`: absent). `BrushStyle` (45 fields) and `Brush` (43 fields) are the same. The 6 fields of `Canvas` (`x0..h`) have no description. `Sheet`'s 8 constructor arguments are undocumented, and its private `__post_init__` is rendered.
  - `reference/letters/`: the `NibStyle` entry shows **none of its 16 fields** (`label_ink`: absent).
  - The `PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS`, `PAINTERS_TRANSPARENCY` and `PigmentLayer` entries render as a raw value dump with no description. `__version__` is the same.
  - `help(PaperStyle)` and IDE hovers show nothing either.
  - griffe counts: PaperStyle 0/22 attributes with docstrings, BrushStyle 0/45, Brush 0/43, NibStyle 0/16, Sheet 0/13.
  - Some `Brush` fields have no comment at all (`pool_radius_frac`, `pool_gain`, `dir_elong`, `dir_mix`, `pen_thin`, `org_oct`, `org_lac`).
- **Who suffers:** anyone using the engine from Python, who meets `PaperStyle(km_glazing=True, paper_foxing=0.03)` in an example and cannot look up what a field does. `style-fields.md` covers the style fields, but only as TOML, and it does not cover `Brush` or `Sheet` at all.
- **Cause:** code (docstring format). A test gate checks that each name is *rendered* (`tests/architecture/test_site.py`) but not that what renders has content.
- **Fix:** move each `#:` block to an attribute docstring (a string literal under the field) or to an `Attributes:` section in the class docstring, which griffe parses (Basemap, Plates and VectorLayers already do this, and render well). Add a site test that every public dataclass field and module attribute has a parsed docstring. Optionally turn on `show_if_no_docstring` so gaps are at least visible.
- **Size:** M (mechanical, about 200 fields). **Area:** docs, ink, letters.
- **Related:** none. This is the root cause behind part of `docs-variable-effect-grids` (nobody can read what a variable does).

## 2. 34 private types appear in public signatures, so the API pages name types a reader cannot open or import

- **Where:** the rendered `reference/maps/`, `reference/ink/` and `reference/letters/` pages (signature cross-refs and attribute types). Sources: `src/pyntpot/maps/annotations.py:31,64` (`Landmark`, `SpanRequest`), `src/pyntpot/maps/pipeline.py:62` (`Features`, `Elevation`), `src/pyntpot/maps/style.py:81` (the eight group types), `src/pyntpot/ink/wash.py` (`WashOptions`).
- **What's wrong:** the public pages name these private types, with no page to link to: `Align, BasemapStyle, BoundingBox, Box, Card, CardStyle, CoverStyle, Credit, DEFAULT_ENDPOINTS, Elevation, ElevationGrid, Features, HillshadeBand, HillshadeImage, Label, Landmark, Layers, LetteringPolicy, Line, MAX_NOTES, MAX_NOTE_CHARS, Manifest, PUBLIC, Projection, Pt, RibbonStyle, RouteInk, RouteStyle, Span, SpanRequest, VectorArea, VectorLine, WashOptions, WashStyle`. The ones a user actually has to *build* are:
  - `Annotations.landmarks: tuple[Landmark | str]` and `spans: tuple[SpanRequest]`. The only documented way in is `Annotations.model_validate({...})` with dicts (how-to `letter-your-own-landmarks.md:36`), and the dict keys are documented only on the private classes.
  - `fetch(..., features: Features, elevation: Elevation)` and `Cache.key/ensure`.
  - `wash(..., options: WashOptions)`.
  - `Basemap.card: Card`, `Plates.manifest: Manifest`, `Basemap.credits: Credit`. Users read these fields; the how-to `credit-the-map-data.md` walks `basemap.credits`.
- **Who suffers:** a Python user who follows a signature or attribute type to its definition and hits a dead end, or who cannot write a type annotation for their own code.
- **Cause:** missing public API.
- **Fix:** decide per type: export it (`Landmark`, `SpanRequest`, `Credit`, `Card`, `BoundingBox`, the style groups), or make the public signature stop naming it. Add a site test that public signatures name only public or third-party types.
- **Size:** M. **Area:** maps, ink.
- **Related:** `maps-public-provider-protocols` (#78) covers `Features` and `Elevation`; this adds 32 more types and an automated way to find them. `ink-public-wash-options` (#73) covers `WashOptions`.

## 3. `style-fields.md` says eight style groups come "from `pyntpot.maps`" or "`pyntpot.ink`", but none of the eight is importable from there

- **Where:** `docs/reference/style-fields.md:55` (`WashStyle`, "from `pyntpot.ink`"), and the `card`, `ribbon`, `cover`, `route`, `route_ink`, `lettering` and `basemap` sections at lines 196-287 ("from `pyntpot.maps`").
- **What's wrong:** only 5 of the 13 groups are exported (`PaperStyle` and `BrushStyle` from ink; `FaceStyle`, `NibStyle` and `HandStyle` from letters). `from pyntpot.maps import CardStyle` raises `ImportError`. The real homes are `pyntpot.ink.style` and `pyntpot.maps.style_groups`, both private. The same split leaves a caller who wants a style in Python (not TOML) unable to build the groups by name. Naming is also uneven: `LetteringPolicy` and `RouteInk` sit among twelve `*Style` names.
- **Who suffers:** a reader who trusts the page and writes the import.
- **Cause:** prose (a false claim) plus missing public API.
- **Fix:** either export all 13 groups from their layer's `__all__` (and consider `LetteringStyle` / `RouteInkStyle` names), or correct the page to "a group of `Style`, not importable on its own". Gate it: test that each "`X`, from `pyntpot.Y`" line on the page resolves.
- **Size:** S (prose) or M (export). **Area:** docs, maps, ink.
- **Related:** `maps-themes-as-overrides` (a Python-side override would need these types).

## 4. `PaperStyle()` and the other no-argument group constructors are not the default look: 25 fields differ from the default theme

- **Where:** `src/pyntpot/ink/style.py` (`PaperStyle`, `WashStyle`), `src/pyntpot/ink/brush_style.py`, `src/pyntpot/maps/style_groups.py`. Examples call `PaperStyle()` and `BrushStyle()` 30 or more times (`examples/nib_line.py:52,63`, `examples/word.py:104-122`, `examples/brush_sheet.py`, ...).
- **What's wrong:** the dataclass defaults differ from `Style.default()` in 25 fields:
  - paper: `km_glazing`, `paper_fibre`
  - wash: 14 fields, including `blooms`, `wet_bleed`, `fluid_pass` and `pigment_separation`
  - brush: 6 fields, including `ink_starve` and `brush_organic`
  - basemap: 3 fields
  - `RouteInk()` cannot be built with no arguments.

  So `composite(layers, paper, PaperStyle())` multiplies, where a map glazes by Kubelka-Munk. The examples work around this by hand (`PaperStyle(km_glazing=True, ...)` in `fern.py:135` and `trees.py:367`). `style-fields.md:9` mentions that the two defaults "differ for some fields" but does not say which. `NibGroups`'s docstring tells users to build `NibGroups(NibStyle(), FaceStyle(), HandStyle(), BrushStyle(), PaperStyle())`, and the maps side builds the same thing from `style.*` in two places (`maps/attribution.py:155`, `maps/lettering/pipeline.py:257`).
- **Who suffers:** an engine user whose picture does not match the gallery or the map, with no warning.
- **Cause:** code / API design.
- **Fix:** document the differing fields (a "differs from dataclass default" column in style-fields), and give engine users a one-liner to the house look: `Style.default().paper` is already there but never taught. Alternatively add `NibGroups.from_style(style)`, or make the dataclass defaults equal the theme (an ADR-sized change to goldens).
- **Size:** S (docs) / M (API). **Area:** ink, letters, docs.
- **Related:** `maps-themes-as-overrides`.

## 5. The reference gates check that names are present, not values: every type, default and table value on five pages is a hand copy

- **Where:** `tests/architecture/test_reference_pages.py:106-237`; `docs/reference/style-fields.md` (206 non-table defaults), `pigments.md:13-57` (25 colours and transparencies), `brushes.md:74-83` (8 treatment rows × 5 values) and `:125-133` (default ids), `cli.md:9` (synopsis).
- **What's wrong:** the tests assert that each field, key or id appears as code somewhere on the page. They never compare the Default, Type, Colour or Transparency cells, or the treatment numbers. All 206 defaults and all pigment values match today (checked), so this is latent drift. **It has already drifted once:** the `cli.md:9` synopsis omits `--margin-m`, which the parser's own usage line includes and line 68 of the same page documents. It passes because `--margin-m` appears elsewhere on the page.
- **Who suffers:** whoever reads the reference after the next default change.
- **Cause:** prose (hand-maintained tables).
- **Fix:** generate the tables at build time (an mkdocs hook or a small `gen-files` script reading `Style.default()`, `PIGMENTS`, `BRUSH_TREATMENTS` and `build_parser().format_usage()`), or strengthen the tests to parse each table row and compare the cells. Fix the synopsis now.
- **Size:** M. **Area:** docs, tests.
- **Related:** `ink-data-driven-brushes-and-pigments` (if the tables become data, generating them gets easier).

## 6. Four public functions shadow their own submodules, so `import pyntpot.ink.wash as w` gives you the function

- **Where:** `src/pyntpot/ink/__init__.py:29,31` (`stamp`, `wash`), `src/pyntpot/maps/__init__.py:18,25` (`compose`, `vector_layers`); hence `docs/reference/ink.md:40-42` and `maps.md:40,48` use the deep paths `pyntpot.ink.stamp.stamp`, `pyntpot.maps.pipeline.compose` and so on.
- **What's wrong:** `type(pyntpot.ink.wash)` is `function`, and `import pyntpot.ink.wash as w` also binds the function, so `w.WashOptions` raises `AttributeError`. `pyntpot.maps.compose` is `pipeline.compose`, while module `pyntpot.maps.compose` holds `painted_map` (cited in `explanation/references.md:22,59`: `pyntpot.maps.compose.painted_map` raises `AttributeError` at runtime). griffe resolves the same names to the *modules*, which is why the reference pages need the deep-path workaround, and why the rendered headings show module paths a user should not import.
- **Who suffers:** users exploring in a REPL; anyone following a `references.md` "Implemented in" path; tooling.
- **Cause:** code (naming).
- **Fix:** rename the modules (`ink/stamping.py`, `ink/washing.py`, `maps/compose_steps.py`, `maps/vector_layer_build.py`) so no public function shares a name with a sibling module. Add an architecture test for the collision.
- **Size:** S to M. **Area:** ink, maps.
- **Related:** none.

## 7. The pipeline makes every caller rebuild the cache key: `paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))`

- **Where:** `src/pyntpot/maps/pipeline.py:105` (`paint`), `src/pyntpot/maps/candidates/export.py:57`, `vector_layers`; repeated verbatim in `docs/tutorials/first-map.md:92`, `docs/how-to/change-the-route-ink.md:28` and five examples (`route_map.py:69`, `place_card.py:119`, `map_styles.py:79`, `how_to_route_ink.py:135,209`).
- **What's wrong:** `fetch` computes the key but drops it. The `Basemap` it returns does not carry it, so a caller passes the providers a second time just to rebuild the key for `paint`, `candidate_export` and `vector_layers`. The key also needs the private `Features` and `Elevation` protocols (finding 2). The CLI does the same internally (`maps/cli.py:82-84`), and there is no public one-call `render`.
- **Who suffers:** every map user, on line one of their script; the tutorial's most-read code line is plumbing.
- **Cause:** code / API design.
- **Fix:** have `fetch` put the key on `Basemap` (`basemap.key`), let `paint` take the cache (`paint(basemap, style, cache)`) or default `out_dir`, and have `candidate_export` and `vector_layers` accept a basemap or key-bearing value.
- **Size:** M. **Area:** maps.
- **Related:** `cli-wider-commands` (a shared pipeline helper would serve both).

## 8. Lettering a word with the engine means a disk round-trip and hand-written alpha compositing in Pillow

- **Where:** `src/pyntpot/letters/nib.py:284` (`nib_plate(..., path) -> Path | None`); `examples/word.py:118-130`, `examples/how_to_route_ink.py:169-170`, `examples/brush_sheet.py:152-153`.
- **What's wrong:** `nib_plate` only writes a file. To put a word on a painted array, the caller writes the WebP, opens it again with Pillow, resizes it with Lanczos, and does `washed * (1 - alpha) + rgba * alpha` by hand. Pillow is not part of the pyntpot API the docs teach. The caller also builds a second `Canvas` at `NIB_SCALE`, a zero `dark` array, and a `NibSurface` whose `canvas` is read only for `w` and `h`. Compare the ink side, which returns arrays and offers `save_image`. Maps `compose` returns a `PIL.Image` instead, which makes three output conventions across the layers.
- **Who suffers:** a tutorial reader of "Paint a watercolour" who reaches the lettering rung.
- **Cause:** missing public API.
- **Fix:** add an in-memory form (`nib_layer(...) -> np.ndarray` RGBA at the target size) plus a public "lay an RGBA plate over an image" helper, and keep `nib_plate` as the writer. Make `NibSurface` take `(w, h, scale)` directly. Pick one return convention (ndarray) and document it.
- **Size:** M. **Area:** letters, ink.
- **Related:** none. `letters-nib-follows-writing-line` is about stroke direction, not this.

## 9. Glossary terms are bent in public docstrings: `Track` is "a recorded route", the finished image is a "card", and `Canvas` (in `ink`) is "the card's metre box"

- **Where:** `src/pyntpot/maps/track.py:39` ("A recorded route."), `src/pyntpot/maps/pipeline.py:135` (`compose`: "one raster card"; "track: The route to map" in `fetch`), `src/pyntpot/ink/sheet.py:46` (`Canvas`: "The card's metre box"; `Canvas.px` "card's metres, north up"), and `docs/tutorials/first-map.md:89-93` (`route = Track.from_gpx(track)` and `card = compose(...)`, where `track` is a *path*). 11 `route = Track` or "track: The route" sites in src, examples and docs.
- **What's wrong:** GLOSSARY says track is the GPS path and route is the painted line. It also says card is the coordinate frame, a maps concept that `ink` "never uses", and map is the painted result. The flagship docstrings and the tutorial swap these. The ink docstring for `Canvas` leaks the maps vocabulary across the boundary.
- **Who suffers:** readers learning the vocabulary from the API, and agents reading docstrings as the contract.
- **Cause:** terminology.
- **Fix:** `Track`: "A recorded GPS track". `compose`: "into one map image". `Canvas`: "A world-unit box and the pixel grid it paints to" (the glossary's own words). Rename the tutorial variables to `track = Track.from_gpx(gpx_path)` and `image = compose(...)`. Consider an architecture test for maps words in `ink` docstrings.
- **Size:** S. **Area:** docs, ink, maps.
- **Related:** `docs-glossary-in-place`.

## 10. One argument name, several meanings: `scale` has three; colour has five spellings in two representations; `Sheet(h, w)` vs `Canvas(..., w, h)`

- **Where:**
  - `scale`: `Canvas.scale` (`src/pyntpot/ink/sheet.py:57`) is render px per metre; the `brush_from_id(..., scale)` and `NibSurface(scale)` arguments are render px per display px (the glossary's `render_scale`); `VectorLayers.scale` is "how much coarser than the reference span, 1 to 4".
  - Colour: `PaperStyle.paper_hex`, `NibStyle.label_ink` (hex), `Style.with_route_ink(colour=)`, `Mark.ink` / `Setting.ink` (a token or `#rrggbb`), and `rgb(hex_s)`. `composite` and `PigmentLayer` take a float RGB ndarray, but `brush_from_id` returns a hex string, so every stroke example does `rgb(ink_hex)`.
  - Order: `Sheet(h, w, gran_px, seed)` against `Canvas(x0, y0, x1, y1, w, h)`. Every example writes `Sheet(H, W, ...)` next to `Canvas(0, 0, W, H, W, H)`.
  - Units: `Setting.size`, `Mark.size` and `Hand.measure(size)` are display px with no suffix, while `NibStyle.label_size_px` has one. `Sheet(fibre_cell=)` is the same quantity as `PaperStyle.paper_fibre_cell_px`, with the `_px` dropped. `brush_from_id(width_display_px=)` against `with_route_ink(width_px=)` against `paper_plate(display_px=)`, which is a width.
  - Abbreviations in public signatures: `stamp(acc, pts, b, rng, aux, wprof)`, `ink_density(acc, b, ...)`, `Brush.thr`, `BrushStyle.minor_roads_mppd` and `ink_ss`.
- **Who suffers:** engine users, especially the swapped h and w (a silent transposition when the image is not square).
- **Cause:** code (naming).
- **Fix:** one canonical name each, recorded in GLOSSARY (`render_scale`, `px_per_m`, `colour` taking `str | RGB`), with `_px`/`_m` suffixes everywhere. Make `Sheet` keyword-only or `(w, h)`. Spell out `brush`, `points`, `accumulator` and `width_profile` (a breaking change, so an ADR, with deprecation shims).
- **Size:** M (breaking). **Area:** ink, letters, maps.
- **Related:** `ink-one-pigment-registry` (#72) for the colour-lookup half.

## 11. The engine's simplest calls need size and shape boilerplate, and positional magic numbers the docs never name

- **Where:** `src/pyntpot/ink/paper.py:41` (`paper_plate(sheet, canvas, style, display_px)`), `src/pyntpot/ink/brush.py:225` (`brush_from_id(id, width, scale, style)`), `src/pyntpot/ink/wash.py` (`wash(cover, sheet, base, pool)`); `examples/nib_line.py:48-60`.
- **What's wrong:**
  - `paper_plate` reads only `w` and `h` from `canvas`, which `sheet` already has, and then takes the width a third time as `display_px`. A pixel-unit picture needs `Canvas(0, 0, W, H, W, H)`.
  - Every example passes `brush_from_id("MAJ6-e", 3.0, 1.0, BrushStyle())`, where the `1.0` scale and the `BrushStyle()` are boilerplate, and `wash(mask, sheet, 0.6, 0.3)` takes two bare floats.
  - `paper_plate`'s docstring warns that "the result depends on how many fields were drawn from the sheet's generator before it": a hidden call-order coupling in a public function.
  - `stamp` requires an `rng` and refers to `aux` from `ink_aux`, which is private.
- **Who suffers:** new engine users and the tutorials, which spend lines on plumbing.
- **Cause:** code / API design.
- **Fix:** defaults (`scale=1.0`, `style=None` meaning the house style), keyword-only floats (`wash(mask, sheet, body=0.6, pool=0.3)`), a `Canvas.pixels(w, h)` constructor, `display_px` defaulting to the sheet width, and a keyed generator for `paper_plate` so call order stops mattering.
- **Size:** M. **Area:** ink.
- **Related:** `docs-examples-review`, which would see the line savings.

## 12. The top-level `pyntpot` re-exports are an unusable subset that no doc or example imports

- **Where:** `src/pyntpot/__init__.py:1-54`; `docs/reference/pyntpot.md:1-8`.
- **What's wrong:** there are 17 re-exports, and 0 uses of `from pyntpot import` in docs, README or examples. You cannot call most of them with top-level names alone:
  - `fetch` needs `Cache` and the providers.
  - `composite` needs `PaperStyle`.
  - `Hand` needs `FaceStyle`, `HandStyle` and `Setting`.
  - `stamp` needs `brush_from_id` and `ink_density`.

  The reference page for `pyntpot` shows the module prose and an undocumented `__version__`, with no links to the 17 names it lists (they render only on the layer pages).
- **Who suffers:** a newcomer who reads "Public API: ..." in `pyntpot.__doc__` and tries `import pyntpot`.
- **Cause:** missing public API / design.
- **Fix:** either drop the re-exports and say "import from the layer packages", or make the top level a complete "map in five names" set (`Track, Style, Cache, OverpassFeatures, OpenTopoData, fetch, paint, letter, compose`) and link each name on `pyntpot.md` to its layer page.
- **Size:** S. **Area:** docs, maps.
- **Related:** none.

## 13. `Annotations` has a public field that does nothing, and "places" means two different things

- **Where:** `src/pyntpot/maps/annotations.py:115,125` (`roads`: "Accepted and not read"); `src/pyntpot/maps/pipeline.py:62` (`fetch(..., places: Sequence[Mapping])`), `vector_layers(..., places=)`, and `Annotations.places`.
- **What's wrong:**
  - `Annotations.roads` is validated and documented, then ignored, so a caller can set it and see nothing happen.
  - `places` on `fetch` and `vector_layers` is an untyped list of `{name, lat, lng}` points of interest to mark. `Annotations.places` is a tuple of settlement *names* to always letter. The same word means two things, and neither is in GLOSSARY.
  - The how-to calls the landmark entries "callouts" (15 uses in `letter-your-own-landmarks.md`), a synonym the glossary does not have.
  - `candidate_export` returns `dict[str, Any]` with 30 or more keys documented only in docstring prose (no `TypedDict`).
- **Who suffers:** map users passing annotations.
- **Cause:** code + terminology.
- **Fix:** remove `roads` or make it raise. Rename `fetch`'s `places` to `points_of_interest` (or type it as a public `Landmark`-like model) and add `place` to GLOSSARY. Use "landmark" in the how-to. Type the export as a `TypedDict`.
- **Size:** S to M. **Area:** maps, docs.
- **Related:** `maps-letter-the-start-place`, `maps-lettering-pin-icons` (both touch what a place is).

## 14. `how-the-wash-works.md` says the public `wash` "takes a body and a pool and nothing else", but its signature takes `options: WashOptions`

- **Where:** `docs/explanation/how-the-wash-works.md:127-128`; `src/pyntpot/ink/wash.py` (`wash(cover, sheet, base, pool, options: WashOptions | None = None)`); the rendered `reference/ink/` shows `options: WashOptions` in the signature and in Args.
- **What's wrong:** the essay contradicts the reference page one click away. The truth is "takes options whose type is not public". The essay also links a maintainer feature note on GitHub (line 141), so a user page carries roadmap content, against CLAUDE.md's "state designed gaps as capability facts".
- **Who suffers:** readers trying the four behaviours the essay describes.
- **Cause:** prose drift.
- **Fix:** reword it to "`wash` accepts a `WashOptions`, which is not yet public; the painter sets it from the theme's `[wash]` group". Drop the feature-note link, or move it to a contributor page.
- **Size:** S. **Area:** docs.
- **Related:** `ink-public-wash-options` (#73). New evidence: the docs currently misstate the signature.

## 15. `explanation/performance.md` is a maintainer log on the user site

- **Where:** `docs/explanation/performance.md:1-125`; nav at `mkdocs.yml:111`.
- **What's wrong:** the page carries:
  - 9 references to specs, PRs and issues
  - before/after medians for a dated commit, with a CPU model
  - CI job wall times on GitHub runners
  - CodSpeed dashboard housekeeping ("removed on 2026-10-07 ... until they are archived")

  It does not explain anything, and it does not answer the user's questions: how long a map takes, how much memory it needs, and what makes it slower (card size, `render_scale`, `fluid_pass`, land cover). Its numbers go stale with every perf change.
- **Who suffers:** users who open "Performance" expecting guidance; maintainers keeping dated tables current.
- **Cause:** prose (mode mixing: a record presented as explanation).
- **Fix:** split it. Move the baselines and CI tables to `docs/runbooks/` or a decision record (excluded from the site). Keep a short explanation: where the time goes, which style fields cost what, and expected time and memory for a default card.
- **Size:** S. **Area:** docs.
- **Related:** none.

## 16. Terms the docs lean on are missing from GLOSSARY, and two names compete for the lettering plate

- **Where:** `GLOSSARY.md`; usage counts across `docs/reference`, `docs/explanation`, `docs/tutorials` and `docs/how-to`.
- **What's wrong:**
  - Frequent terms with no glossary row: label (89 uses), tip (80), glazing/Kubelka-Munk (47 + 15), face (33), ribbon (25; also a style group and a manifest key), tooth (20), bloom (19), glyph (18), treatment (17; the brush-sheet row), digest (11), backing wash (11), granulation (10), skeleton (6), accumulator (6), leader (5), line class and cover class (3 + 4), ink pad (2).
  - Synonyms: the glossary says **nib plate**, but `cache-layout.md` (4 uses), `style-fields.md:282` and the `maps/pipeline.py` and `lettering/pipeline.py` docstrings (9 uses) say **label plate**.
  - 20 of 53 glossary rows point only at private dotted paths (`maps.card.Card.xy`, `maps.annotations.SpanRequest`, `ink.keyed.keyed_rng`, ...).
  - The glossary mixes in test-tooling terms (review image, diff image, crop image).
- **Who suffers:** readers of the explanation essays; agents trying to honour "one canonical name".
- **Cause:** terminology.
- **Fix:**
  - Add rows for the top dozen terms.
  - Pick nib plate or label plate and sweep the other.
  - Split test-tooling terms into a contributor section.
  - Point rows at public names where they exist.
- **Size:** S to M. **Area:** docs.
- **Related:** `docs-glossary-in-place` (#65). The reference page `glossary.md` is a 3-line pointer off-site; this finding adds the coverage gaps.

## 17. Table-typed style fields list "table" as their default, and their legal keys are listed nowhere on the site

- **Where:** `docs/reference/style-fields.md:44,92,111,118,119,129,240,241` (8 fields whose Default cell reads "table"), notably `brush_overrides` (`:129`); `docs/reference/brushes.md:74-85`.
- **What's wrong:** the reader is told to open `src/pyntpot/maps/themes/default.toml`, which is not on the site. Gaps:
  - `brush_overrides` takes "a table of values that replace the shared geometry and a row's treatment", but `brushes.md` shows only 5 of each treatment's 12 keys (`name_wet`, `thr`, `press`, `load`, `pool`, `bleed` and `lift` are missing), and the shared-geometry keys are not listed at all.
  - The line classes that `brushes` and `brush_width_px` accept appear only incidentally, in "Ids the default style uses".
  - The cover classes for `cover_cfg` and `separation_pigments` are not enumerated.
- **Who suffers:** theme authors (the `write-a-theme` how-to readers).
- **Cause:** prose (incomplete reference).
- **Fix:** render each table default inline, collapsed or as a sub-table, generated from `Style.default()` (see finding 5). List the legal keys for each table-typed field. Show all 12 treatment keys.
- **Size:** S to M. **Area:** docs.
- **Related:** `docs-brush-id-gallery`, `maps-named-themes`.

## 18. The API pages are flat alphabetical lists with no grouping, and the top-level page links nowhere

- **Where:** `docs/reference/ink.md:8-42` (18 directives in a row), `letters.md:14-30`, `maps.md:8-48`, `pyntpot.md`.
- **What's wrong:** constants, then classes, then functions, alphabetically, with no headings or prose between them. A reader looking for "how do I lay a wash" gets `PIGMENTS ... Brush ... BrushStyle ... Canvas` first. The `ink` and `maps` package docstrings already group names by task ("To build a mark ...", "To colour and lay pigment ..."), but the page does not follow those groups. The reference index (`docs/reference/index.md`) has no table of all 49 public names.
- **Who suffers:** users scanning the reference.
- **Cause:** prose / structure.
- **Fix:** add `##` sections on each API page that mirror the package docstring's task groups (paper, marks, pigment, output; for maps: pipeline stages, inputs, providers and cache, cache readers, errors). Add a one-table "every public name, one line each" on `reference/index.md`, generated from `__all__` and each name's summary line.
- **Size:** S. **Area:** docs.
- **Related:** none.

---

### Nav check

All 37 site pages are in the nav, with no orphans: every Markdown file outside the
excluded maintainer folders is listed, and `README.md` is excluded on purpose. Nav gaps are
covered by findings 15, 16 and 18.
