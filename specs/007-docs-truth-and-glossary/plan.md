# 007 — plan

## Approach

Docs and docs tests only. No `src/` file changes here, in any slice (feature 006's S9
makes the docstring changes the spec lists under "Docstring changes for 006's S9"), no
boundary change, no public-API change, so no
ADR: the docs-site mechanism is an addition inside ADR 0034's rule (source pages stay
plain Markdown; `mkdocs.yml` chooses what the site shows), and the one site-only file is
excluded from the site.

Three pieces of machinery, each generic and data-driven:

1. **The glossary.** `GLOSSARY.md` is restructured into three sections (reader terms,
   contributor terms, retired words). A stdlib-only generator,
   `tests/support/glossary.py`, writes two committed files from it:
   `docs/reference/glossary.md` (the site's glossary page, reader terms only, an anchor per
   term) and `docs/includes/abbreviations.md` (one `*[form]: meaning` line per Tooltip
   form). `pymdownx.snippets` appends the abbreviations file to every page, `abbr` turns
   each listed form into `<abbr title=...>`, and Material's `content.tooltips` styles it.
   Tests fail on any drift between `GLOSSARY.md` and either file, and print the command
   that regenerates them. Verified in a scratch build against the locked docs group
   (Markdown 3.11.2, pymdown-extensions 12.3, Material 9.8.0): `abbr` skips inline code
   and code blocks, applies in headings and tables, matches whole words and is
   case-sensitive with no plural matching (hence explicit forms); a raw
   `<span id="term-x">` is a valid anchor target for `validation: anchors: warn`; the real
   site builds clean with anchor validation on today.
2. **The docs-truth suite**, a new `tests/docs/` package. Pages come from `mkdocs.yml`
   (`docs_dir` minus `exclude_docs`), order from its nav, images from
   `tests/support/docs_images.py`, facts from the code. Every check runs over every page it
   applies to, so a new page, image, field or nav entry is covered with no test edit.
   Prototypes of every content check ran against `cb75c7b`: the style-field comparator
   matches all 206 rows; the import-claim check finds exactly #163's 8 claims; the caption
   checks find #162 and two wrong theme captions out of 119 captioned images; the
   signature check finds exactly the wash essay's `wash(cover, sheet, base, pool)`.
3. **Tutorial paths**: one nav-derived reading order, a `Next:` line per tutorial page,
   and a lead-on link from each tutorial page to a guide, reference or explanation page.

The existing docs-prose tests `tests/architecture/test_tutorials.py`,
`test_reference_pages.py`, `test_readme.py` and `test_docs_images.py` move to `tests/docs/`
(they check prose, not architecture) and `test_how_to_commands.py` is deleted as subsumed
by S7's commands test, but only in S8, after the rebase onto 006: 006 owns `tests/architecture/`
and edits `test_reference_pages.py` (S0a repoints its brush-table import), `test_site.py`
and `test_reference_keys.py`. Until then no 007 slice moves or edits any file under
`tests/architecture/`; every new test goes in `tests/docs/` from S0 on.

ADR 0068 is fact for this plan (see the spec's "True on both sides of 006"). The
"Handed to session A" list in 006's plan is this feature's S8.

## Running the gates

- Tests: `uv run pytest -n auto --dist loadgroup --golden-tolerance` (`--golden-tolerance`
  off the pinning machine; the golden-marked tests run by default).
- One slice's tests: `uv run pytest tests/docs -q`.
- Everything the commit hook runs: `prek run --all-files`.
- The strict docs build, from the repo root (the snippets path is relative to the working
  directory), writing outside the tree:
  `NO_MKDOCS_2_WARNING=1 uv run --locked --group docs mkdocs build --strict -d "$SCRATCH/site"`
  where `$SCRATCH` is your scratchpad. The first run installs the docs group into `.venv`.
  This is exactly CI's `.github/workflows/docs-site.yml` command plus an output directory.
- Regenerate the glossary files: `PYTHONPATH=tests uv run python -m support.glossary`.

## Slices

Order: **S0**, then **S1 to S6 in parallel** (disjoint files), then **S7**, then **S8**
once feature 006 has merged to `main`. S7 opens the PR as a draft; it is marked ready, and
merged, only after S8. Each slice is test-first: write the named tests,
run them, watch each fail for the reason given, then make them pass. Each slice commits
its own checkpoint on the feature branch. "Done" for every slice includes: its tests
green, `uv run pytest tests/docs tests/architecture -q` green, `uv run ruff check .`,
`uv run ruff format --check .` and `uv run ty check` clean, and no file over 400 lines.

006-dependency: S0 to S7 run **before 006 merges** and touch no file 006's plan edits:
every sentence they write is true at this branch's base and stays true once ADR 0068's
changes land (`WashOptions`, `WashStyle`, `separated` and `fluid_modulate` exported from
`pyntpot.ink`; the seven map style groups, the provider protocols, `Card`, `Credit`,
`Manifest`, `Label`, `Landmark` and the rest from `pyntpot.maps`; `LetteringPolicy` to
`LetteringStyle`, `RouteInk` to `RouteInkStyle`, `Pt` to `Point`, `Anchor` to `Align`;
`ink/stamping.py`, `ink/washing.py`, `maps/compose_steps.py`, `maps/vector_layer_build.py`,
`ink/brush_sheet.py`). A statement that cannot be true on both sides waits for **S8,
after 006 lands**.

Files both plans name, and where each edit went (checked by grepping both plans' owned
lists and the files themselves). This plan is reconciled against 006's plan at **`a7d664d`**
(`/home/user/pyntpot`, branch `feat/006-one-public-surface`); an earlier copy is not the
reference. 006's plan may still move, so S8 step 1 reruns the check against 006's merged
diff on `main`.

**Who owns retired words in code and tests.** 006's S9 owns every retired-word edit under
`src/**` and `tests/**`: docstrings, comments, test names and locals. 007 changes a line
under `tests/` only where the `examples/places.toml` key rename (`callouts` to
`landmarks`) strictly requires it: the two `"callouts"` key strings 006 leaves because
`examples/` is outside its scope.

| File | 006 edits | 007 edit | Resolution |
| --- | --- | --- | --- |
| `tests/architecture/test_reference_pages.py` | S0a: brush-table import line | S0 move; S1 glossary pointer test; S2's brush import | Move in S8. S1 keeps the pointer test green instead (the generated page carries the link it checks). S2's new tests import from `pyntpot.ink.brush`; S8 repoints to `pyntpot.ink.brush_sheet`. |
| `tests/architecture/test_tutorials.py` | none, but 006 owns `tests/architecture/` | S0 move; S4 widening | Move in S8. S4 writes its checks in a new `tests/docs/test_tutorial_quotes.py`; S8 drops the narrower test it subsumes. |
| `GLOSSARY.md` | S8: "brush sheet", "style group", "vector layers" rows | S1 restructure | S1 keeps those three rows' meaning as on `main`; S8 resolves the conflict and writes 006's three facts in the new format. |
| `docs/features/docs-missing-how-tos.md`, `docs/features/docs-examples-housekeeping.md` | S8: fact and path edits (lines 38 to 45; line 22) | S7: repoint the mention of the deleted `docs-tutorials-lead-on.md`; the #174 paragraph | Both moved to S8. |
| `docs/issues/docs-style-fields-imports-and-reference-checks.md` (#163) | none (006 leaves it alone; its S8 grep over `docs/issues` would see `LetteringPolicy` in it) | S7 deletes it | Kept in S7. If 006 lands first, the note is still there for its grep; 006's plan names the note as session A's, so the deletion here settles it. |
| `tests/unit/maps/test_example_themes.py` | S9: docstrings `:53`, `:68`; test renamed at `:67` to `test_the_label_cap_is_the_landmark_count`; local `callouts` to `landmarks` at `:70`, `:73` | S5: the key string `"callouts"` to `"landmarks"` at `:70` only | Both change line 70: S8 step 1 resolves the expected conflict. |
| `tests/golden/test_places.py` | S9: comments `:45`, `:51`, `:89`, docstring `:188` | S5: the key string at `:194` only | 006's wording and 007's key; S8 step 1 resolves any hunk. |
| `tests/support/docs_images.py` | S9: the `_place_card` docstring `:351` | none in S5; S8: the module docstring `:40` (the moved `test_docs_images.py` path) | S5 drops the file; S8's edit is after 006, on a line 006 does not touch. |
| `tests/architecture/test_reference_pages.py:168`, `tests/unit/maps/lettering/test_draw_plate.py`, `test_placement_water.py`, `tests/unit/maps/test_cache.py`, `test_pipeline_letter_compose.py`, `test_route_ink.py` | S9: every retired word in their docstrings, and the `test_placement_water.py:89` test name | S8 moves `test_reference_pages.py` and renames its `test_label_plate_…` test (006's S9 grep does not match the underscore form); nothing else | S8 does not repeat 006's edits; S8 step 9 expects them done. |
| `docs/how-to/self-host-providers.md`, `docs/how-to/letter-your-own-landmarks.md`, `docs/explanation/how-the-wash-works.md`, `docs/reference/style-fields.md`, `docs/architecture.md` | none (006 hands them over) | S5, S6, S2 pre-006; the handed sentences | Pre-006 slices write only both-sides wording; the handed sentences are S8's. |

No other file is in both plans: `examples/**` (006 leaves it alone), `mkdocs.yml`,
`CONTRIBUTING.md`, `README.md`, `.pre-commit-config.yaml`, `docs/README.md`,
`docs/index.md`, `docs/gallery.md` and the other reference and explanation pages this plan
names are 007's alone.

### S0 — Scaffold and site shape (serial, first)

Owned files: `tests/docs/__init__.py` (new, empty docstring module like
`tests/architecture/__init__.py`), `tests/support/site_pages.py` (new),
`tests/docs/test_site_pages.py` (new), `tests/docs/test_nav.py` (new),
`.pre-commit-config.yaml`, `mkdocs.yml`, `docs/explanation/performance.md` (moved to
`docs/runbooks/performance.md`), `docs/explanation/index.md`, `docs/README.md`,
`CONTRIBUTING.md`.

Steps:

1. Create `tests/docs/` with its `__init__.py`. Nothing under `tests/architecture/` moves
   or changes in this slice (the two docs tests move in S8, after 006).
2. Write `tests/docs/test_site_pages.py` against the helper API below, using inline
   Markdown strings and a small `mkdocs.yml` text built by a factory function (no
   fixtures chains, no mocking). Tests fail: the module does not exist.
3. Write `tests/support/site_pages.py` (module docstring per CLAUDE.md: purpose, key
   names, what it does not do). API, all pure functions over `Path`/`str`:
   - `MKDOCS: Path`, `DOCS: Path`.
   - `excluded(text: str) -> tuple[str, ...]`: the `exclude_docs: |` block's entries.
   - `site_pages() -> list[Path]`: every `docs/**/*.md` not under an excluded directory
     entry and not an excluded file entry, sorted.
   - `NavEntry` (frozen dataclass: `path: str`, `sections: tuple[str, ...]`) and
     `nav(text: str) -> list[NavEntry]`: an indentation parser over the lines after
     `\nnav:\n`, reading `- Title: path.md`, `- path.md` and `- Section:`; no YAML
     library (PyYAML is not a declared dependency).
   - `Block` (frozen dataclass: `lang: str`, `code: str`, `marker: str | None`,
     `line: int`) and `fenced_blocks(text: str) -> list[Block]`: backtick or tilde
     fences, at the margin or indented (a fence inside a list item, as on
     `paint-your-own-shapes.md:16-51`, is indented three spaces); each code line is
     dedented by its opening fence's indent and no further, so a block quoting indented
     script lines keeps their indentation. `marker` is the nearest preceding non-blank
     line, stripped, when that line is an HTML comment `<!-- ... -->`, else `None`: the
     watercolour tutorial puts the marker on the line before the fence, while
     `curves.md` (7 blocks) and `fractals.md` (13 blocks) leave a blank line between,
     as `tests/architecture/test_tutorials.py:34`'s `-->\s*\n` allows. Helper tests pin
     both spacings, an indented fence and a block with no comment above it.
   - `prose(text: str) -> str`: the text with fenced blocks removed (indented fences
     included).
   - `links(text: str) -> list[str]`: Markdown link targets, images excluded, in page
     order, duplicates kept.
   - `resolve(page: Path, href: str) -> Path | None`: a relative `.md` link resolved
     against the page, fragment dropped; `None` for absolute URLs.
   - `resolve_dotted(path: str) -> object`: imports the longest importable module prefix
     of a dotted `pyntpot.…` path, then `getattr` on each remaining part; raises
     `LookupError` naming the path when a part is missing. The one resolver for S1's
     "In the code" check, S2's dotted-path test and S8 step 6. Module first is deliberate:
     `pyntpot.ink.wash`, `pyntpot.maps.compose` and `pyntpot.maps.vector_layers` resolve
     to the modules that shadow the exported functions of the same name (#164), and a
     helper test pins that `resolve_dotted("pyntpot.ink.wash")` returns a module, so that
     nobody "fixes" it to prefer the package attribute.
4. Write `tests/docs/test_nav.py`:
   - `test_every_section_index_lists_its_pages_in_nav_order`: for each nav section whose
     first entry is an `index.md`, the section's pages are the entries whose
     `NavEntry.sections` equals that section's tuple exactly (the index itself left out),
     plus the index entry of each direct subsection that opens with one, all in nav
     order. A subsection's other pages belong to the subsection's own index, not to the
     parent's. The index page's `links()`, resolved, filtered to those pages, with each
     page kept at its first occurrence only (so S4's `Next:` line, which repeats a page
     the list already links, changes nothing), must equal that list. Today this gives:
     Tutorials `[paint-a-watercolour, first-map, painting-with-python/index]` (passes);
     Painting with Python fails (nav has Vector drawing before Pictures); How-to guides
     fails (nav order differs from `how-to/index.md`); Reference passes (its API
     subsection opens with no index, so the API pages are nobody's); Explanation passes
     before and after S0 drops the performance page from both the nav and its index.
   - `test_the_performance_log_is_a_runbook_and_no_site_page_links_it`:
     `docs/runbooks/performance.md` exists, no nav entry and no site page link resolves
     to a `performance.md`. Fails today.
   - `test_the_strict_build_validates_anchors`: `mkdocs.yml` has
     `validation:` with `anchors: warn`, placed before `nav:`, and `nav:` is the file's
     last top-level key (`tests/architecture/test_site.py:103` and `nav()` both read
     everything after `"\nnav:\n"`). Fails today.
   - `test_the_includes_directory_is_not_a_site_page`: `excluded()` lists `includes/`
     and no `site_pages()` path is under `docs/includes/`. mkdocs reports a page left out
     of the nav only at INFO, so without this nothing fails if the exclusion is dropped
     and the abbreviations file becomes a page. Fails today.
5. Make them pass:
   - `mkdocs.yml` nav: Painting with Python in the order Curves, Symmetry, Fractals,
     Pictures, Vector drawing; How-to guides in `how-to/index.md`'s order (write a theme,
     map from the command line, change the route ink, letter your own landmarks, work
     offline and reuse the cache, credit the map data, self-host providers, paint your
     own shapes); drop `explanation/performance.md`; add `includes/` to `exclude_docs`;
     add `validation:` / `  anchors: warn` above `nav:`, which stays the last key.
   - `git mv docs/explanation/performance.md docs/runbooks/performance.md`, content
     unchanged (it has no relative links). Remove its line from
     `docs/explanation/index.md`. `docs/README.md`: drop "performance" from the
     `explanation/` line and add it to the `runbooks/` line ("performance baselines").
     `CONTRIBUTING.md:54`: point at `docs/runbooks/performance.md`.
   - `.pre-commit-config.yaml`: a new local hook after `architecture-tests`:
     `id: docs-tests`, `name: docs truth tests`, `entry: uv run pytest tests/docs`,
     `language: system`, `pass_filenames: false`, `files: '\.(py|md|toml|yml)$'`.
     Measure `prek run docs-tests --all-files`; the header asks for the full run under
     5 s, so if the hook adds more than 2 s, report the time in the slice's commit message
     (do not drop the hook).
6. Gate: `uv run pytest tests/docs tests/architecture -q`, strict build.

Done: the four nav tests and the helper tests pass; the strict build passes with anchor
validation on; `git diff --stat` shows nothing under `tests/architecture/`.

### S1 — Glossary (#65), parallel

Owned files: `GLOSSARY.md`, `tests/support/glossary.py` (new),
`tests/docs/test_glossary.py` (new), `docs/reference/glossary.md` (generated),
`docs/includes/abbreviations.md` (generated, new), `mkdocs.yml` (markdown extensions and
theme features only), `docs/reference/index.md`, `CONTRIBUTING.md` (a glossary paragraph
only). Not `tests/architecture/test_reference_pages.py`: its glossary pointer test stays
and passes, because the generated page carries the link it checks.

The `GLOSSARY.md` format (prescribed):

```markdown
# Glossary

One canonical name per concept; no synonyms. Check here before introducing a term, and
add the term here when you coin one. <two sentences: what the three sections are, that the
site's glossary page and the in-page tooltips are generated from this file, and the
regenerate command>

## Terms a reader meets

### Painting

| Term | Meaning | In the code | Tooltip |
| --- | --- | --- | --- |
| tooth | The paper's height, ... | `pyntpot.ink.Sheet` | tooth, Tooth |

### Lettering
### Maps
### Reading the docs

## Terms a contributor meets

| Term | Meaning | In the code |
| --- | --- | --- |

## Retired words

| Retired | Say instead |
| --- | --- |
| label plate | nib plate |
```

A blank line separates every heading, paragraph and table (the current file lacks one
before its table). Cells hold no `|`. "In the code" is empty or a comma-separated list of
backticked dotted names that resolve at runtime on both sides of 006; it names an
exported name (`pyntpot.ink.Sheet`, `pyntpot.maps.Track`) where one exists today,
otherwise a private module path that 006 does not move, and never a path through
`ink/wash.py`, `ink/stamp.py`, `maps/compose.py`, `maps/vector_layers.py` or the brush
sheet tables of `ink/brush.py` (006 renames the first four to `ink/washing.py`,
`ink/stamping.py`, `maps/compose_steps.py` and `maps/vector_layer_build.py`, and moves the
tables to `ink/brush_sheet.py`; neither old nor new path resolves on both sides).
`pyntpot.ink.wash`, `pyntpot.maps.compose` and `pyntpot.maps.vector_layers` are fine
because they resolve on both sides: `resolve_dotted` imports the longest module prefix,
so at the base each resolves to the module that shadows the function (#164), and after
006 renames the modules each resolves to the exported function. Either way it resolves,
and S8 step 6 skips modules. A cell never names `Pt`,
`Anchor`, `LetteringPolicy` or `RouteInk`. The private paths to names ADR 0068 exports
(`pyntpot.maps.card.Card`, `pyntpot.maps.plates.Manifest` and the rest) still resolve
after 006; S8 swaps them for the exported names. The Meaning column holds no module path
(`pyntpot.…`, `ink.x.Y`); existing rows move theirs to "In the code". Attribute references
stay in Meaning as the spec writes them (`Style.route_ink`, `Style.with_route_ink`,
`PaperStyle.km_glazing`, `PaperStyle.paper_foxing`, `Setting.wash`).

Three rows are also edited by 006's S8: "brush sheet", "style group" and "vector
layers". S1 keeps their Meaning as it is on `main`, minus the dotted path moved to "In
the code" (the vector layers' `maps.vector_layers.VectorLayers` becomes the exported
`pyntpot.maps.VectorLayers`; the brush sheet's `ink.brush.BRUSH_TREATMENTS`, `PEN_ROWS`,
`BRUSH_COLOURS` is dropped for `pyntpot.ink.brush_from_id`, since the tables' module
changes in 006), and adds nothing of 006's: "keyword-only", `<Group>Style` and
`brush_sheet` are S8's.

Rows (Meaning for new and changed rows is the spec's "Canonical terms" text; unchanged
rows keep their Meaning, minus the dotted path):

| Section | Term | In the code | Tooltip |
| --- | --- | --- | --- |
| Painting | sheet | `pyntpot.ink.Sheet` | no |
| Painting | tooth | `pyntpot.ink.Sheet` | tooth, Tooth |
| Painting | granulation | `pyntpot.ink.Sheet` | granulation, Granulation |
| Painting | foxing | `pyntpot.ink.paper_plate`, `pyntpot.ink.PaperStyle` | foxing, Foxing |
| Painting | canvas | `pyntpot.ink.Canvas` | no |
| Painting | wash | `pyntpot.ink.wash` | no |
| Painting | coverage mask | `pyntpot.ink.wash` | coverage mask, coverage masks |
| Painting | body | `pyntpot.ink.wash` | no |
| Painting | pool | `pyntpot.ink.wash` | edge darkening, Edge darkening |
| Painting | backrun | `pyntpot.ink.bloom.bloom` | backrun, backruns, Backruns |
| Painting | glaze | `pyntpot.ink.composite`, `pyntpot.ink.PaperStyle` | glaze, glazes, glazed, glazing, Glazing, Kubelka-Munk |
| Painting | pigment | `pyntpot.ink.PIGMENTS`, `pyntpot.ink.TRANSPARENCY` | no |
| Painting | painter's pigment | `pyntpot.ink.PAINTERS_PIGMENTS`, `pyntpot.ink.PAINTERS_TRANSPARENCY` | painter's pigment, painter's pigments |
| Painting | pigment layer | `pyntpot.ink.PigmentLayer` | pigment layer, pigment layers |
| Painting | density | `pyntpot.ink.ink_density` | no |
| Painting | brush | `pyntpot.ink.Brush` | no |
| Painting | tip | `pyntpot.ink.Brush` | no |
| Painting | brush sheet | `pyntpot.ink.brush_from_id` | brush sheet |
| Painting | treatment | `pyntpot.ink.brush_from_id` | treatment, treatments |
| Painting | dab | | dab, dabs |
| Painting | accumulator | `pyntpot.ink.ink_density` | accumulator, accumulators |
| Painting | line class | `pyntpot.ink.BrushStyle` | line class, line classes |
| Lettering | hand | `pyntpot.letters.Hand` | no |
| Lettering | face | `pyntpot.letters.FaceStyle` | no |
| Lettering | glyph | `pyntpot.letters.Hand` | glyph, glyphs |
| Lettering | trace | `pyntpot.letters.FaceStyle` | no |
| Lettering | skeleton | `pyntpot.letters.skeleton` | skeleton, skeletons |
| Lettering | setting | `pyntpot.letters.Setting` | no |
| Lettering | mark | `pyntpot.letters.Mark` | no |
| Lettering | backing wash | `pyntpot.letters.Setting` | backing wash, backing washes, Backing wash |
| Lettering | nib plate | `pyntpot.letters.nib_plate`, `pyntpot.letters.NibSurface` | nib plate, nib plates, Nib plate |
| Lettering | leader | | leader, leaders |
| Maps | track | `pyntpot.maps.Track` | no |
| Maps | route | | no |
| Maps | map | `pyntpot.maps.compose` | no |
| Maps | card | `pyntpot.maps.card.Card` | no |
| Maps | display pixels | `pyntpot.maps.card.Card` | display pixels |
| Maps | render pixels | `pyntpot.maps.card.Card` | render pixels |
| Maps | plate | | no |
| Maps | plates | `pyntpot.maps.Plates` | no |
| Maps | manifest | `pyntpot.maps.plates.Manifest` | no |
| Maps | basemap | `pyntpot.maps.Basemap`, `pyntpot.maps.fetch` | basemap, basemaps |
| Maps | ribbon | `pyntpot.maps.Style` | ribbon |
| Maps | cover class | `pyntpot.maps.Style` | cover class, cover classes |
| Maps | cover patch | `pyntpot.maps.painter.patches.patches` | cover patch, cover patches |
| Maps | dark grid | `pyntpot.maps.plates.DarkGrid` | dark grid |
| Maps | elevation grid | `pyntpot.maps.providers.base.ElevationGrid` | elevation grid, elevation grids |
| Maps | lettering | `pyntpot.maps.Lettering`, `pyntpot.maps.letter` | no |
| Maps | label | `pyntpot.maps.lettering.label.Label` | no |
| Maps | annotations | `pyntpot.maps.Annotations` | no |
| Maps | landmark | `pyntpot.maps.Annotations` | no |
| Maps | place | `pyntpot.maps.Annotations` | no |
| Maps | journal note | `pyntpot.maps.JournalNote` | journal note, journal notes |
| Maps | span | `pyntpot.maps.lettering.label.Span` | no |
| Maps | span request | `pyntpot.maps.annotations.SpanRequest` | span request, span requests |
| Maps | candidate | `pyntpot.maps.candidates.candidate.Candidate` | no |
| Maps | candidate export | `pyntpot.maps.candidate_export` | candidate export |
| Maps | vector layers | `pyntpot.maps.VectorLayers`, `pyntpot.maps.vector_layers` | vector layers |
| Maps | style | `pyntpot.maps.Style` | no |
| Maps | style group | `pyntpot.maps.Style` | style group, style groups |
| Maps | theme | `pyntpot.maps.Style` | no |
| Maps | digest | `pyntpot.maps.Style` | no |
| Maps | route ink | `pyntpot.maps.Style` | route ink |
| Maps | credit | `pyntpot.maps.credit.Credit` | no |
| Maps | fetch cache | `pyntpot.maps.Cache` | fetch cache |
| Maps | fetch margins | `pyntpot.maps.FetchMargins` | fetch margins |
| Maps | provider | `pyntpot.maps.OverpassFeatures`, `pyntpot.maps.OpenTopoData` | no |
| Reading the docs | rung | | rung, rungs |
| Reading the docs | reference | | no |
| Contributor | keyed generator | `pyntpot.ink.keyed.keyed_rng` | |
| Contributor | ink pad | `pyntpot.ink.pad.InkPad` | |
| Contributor | layers | `pyntpot.maps.basemap.Layers` | |
| Contributor | elevation patch | `pyntpot.maps.basemap.ElevationPatch` | |
| Contributor | backdrop | `pyntpot.maps.lettering.placement_costs.Backdrop` | |
| Contributor | terms | `pyntpot.maps.lettering.placement_costs.Terms` | |
| Contributor | water | `pyntpot.maps.lettering.placement_water.Water` | |
| Contributor | review image | | |
| Contributor | diff image | | |
| Contributor | crop image | | |

All 25 private paths above were checked to resolve at runtime at `cb75c7b`. The retired
words are the spec's six. The three contributor review-image rows keep their test-tooling
file names in Meaning as plain words (`diff_images.py` stays backticked as a file name,
which the dotted check ignores because it does not start with `pyntpot.`).

Generator, `tests/support/glossary.py` (stdlib only; module docstring states it is the
one reader of `GLOSSARY.md`'s format and writes the two files, and that it does not build
the site):

- `Term` (frozen: `name`, `meaning`, `code: tuple[str, ...]` (the "In the code" cell's
  bare dotted names, backticks stripped, in cell order; empty for an empty cell),
  `tooltip: tuple[str, ...]`,
  `audience: Literal["reader", "contributor"]`, `group: str`), `Retired` (frozen:
  `word`, `instead`), `Glossary` (frozen: `terms`, `retired`).
- `parse(text: str) -> Glossary`: raises `ValueError` naming the line for an unknown
  `##` section, a table header other than the prescribed one, a row with the wrong
  number of cells, a reader row whose Tooltip is empty, or a `### ` group outside the
  reader section.
- `plain(markdown: str) -> str`: backticks dropped, `[text](href)` to `text`, `**`/`*`
  emphasis dropped, whitespace collapsed.
- `anchor(term: str) -> str`: `"term-"` plus the lowercased term with every run of
  characters outside `[a-z0-9]` replaced by `-`, stripped of `-`.
- `glossary_page(glossary: Glossary) -> str`: exactly
  ```text
  <!-- Generated from GLOSSARY.md by tests/support/glossary.py. Edit GLOSSARY.md, then run: PYTHONPATH=tests uv run python -m support.glossary -->
  # Glossary

  Every term these docs use, what it means and where it lives in the code. The docs use one name for each of these and no other. A term underlined on a page shows its meaning when you point at it. The source is [GLOSSARY.md](https://github.com/findlaywebb/pyntpot/blob/main/GLOSSARY.md) in the repository.

  ## Painting

  | Term | Meaning | In the code |
  | --- | --- | --- |
  | <span id="term-tooth"></span>tooth | <Meaning> | <In the code> |
  ```
  then one `##` section per reader group in file order, rows in file order, one blank
  line between blocks, ending in exactly one newline. Contributor rows and retired words
  are not on the page.
- `abbreviations(glossary: Glossary) -> str`: the same comment line, then one line
  `*[<form>]: <plain(meaning)>` per Tooltip form, terms in file order and forms in cell
  order, with exactly one blank line between consecutive definitions (and after the
  comment line), ending in one newline. The blank line is for build time, not looks:
  mkdocstrings converts each of the API pages' roughly 355 docstrings with the site's
  Markdown extensions, so `auto_append` runs on every one of them too, and `abbr`'s
  block parser is roughly quadratic over a dense run of definitions. The review measured
  a 117-line file on the real site: 2.3 s today, 27 s with the definitions dense, 4.0 s
  with a blank line between them.
- `main() -> None` writes both files under `support.REPO_ROOT` and logs each path at
  INFO; `if __name__ == "__main__":` sets `logging.basicConfig(level=logging.INFO)` and
  calls it. No `print`.

Steps:

1. Write `tests/docs/test_glossary.py` (classes grouping behaviour families; each test a
   one-line docstring):
   - `TestParse` on inline strings: the three sections parse; each malformed shape above
     raises `ValueError`; `plain` and `anchor` on pinned literal inputs and outputs; one
     Hypothesis property: `anchor` output always matches `term-[a-z0-9]+(-[a-z0-9]+)*`
     for any non-empty term with at least one ASCII letter.
   - `TestTheGlossary` on the real file: it parses; terms are unique case-insensitively
     across both sections; every Tooltip form is unique across the glossary and none is
     in `EVERYDAY_WORDS` (a module constant: map, maps, card, cards, route, routes, hand,
     wash, washes, track, tracks, plate, plates, style, theme, sheet, brush, span, water,
     mark, setting, terms, reference, label, labels, place, places, face, layers,
     density, pigment, credit, manifest, candidate, canvas, lettering, tip, body, pool,
     trace, landmark, landmarks, provider, annotations, edge, line, name, names);
     every retired word is not a term; every "Say instead" ends in a term as a whole
     word, matched case-insensitively (so "nib plate", "landmark", "map" and "track" are
     terms themselves, and "centreline trace" and "outline trace" end in the term
     "trace"; a qualifier before the term is allowed, a Say instead with no term is
     not); every name in every "In the code" cell resolves with
     `support.site_pages.resolve_dotted` (this is what checks the contributor rows,
     since `GLOSSARY.md` is not a site page and S2's dotted-path test never reads it);
     no site page contains a curly apostrophe `’` (a Tooltip form such as "painter's
     pigment" is written with `'`, and `abbr` would not underline the `’` spelling; none
     exists today).
   - `TestGeneratedFiles`: `docs/reference/glossary.md` equals
     `glossary_page(parse(...))` and `docs/includes/abbreviations.md` equals
     `abbreviations(parse(...))`, each failing with the regenerate command in the message;
     `mkdocs.yml` enables `abbr`, `pymdownx.snippets` with
     `auto_append: [docs/includes/abbreviations.md]` and `check_paths: true`, and the
     theme feature `content.tooltips` (static text checks, as `test_site.py` does).
   Fails today: the module and the files do not exist and `GLOSSARY.md` has the old shape.
2. Write the generator; rewrite `GLOSSARY.md` to the format and rows above; run the
   generator.
3. `mkdocs.yml`: add `content.tooltips` to `theme.features`; add markdown extensions
   `abbr` and `pymdownx.snippets` with `auto_append: [docs/includes/abbreviations.md]`
   and `check_paths: true` (default `base_path`, the working directory).
4. Leave `tests/architecture/test_reference_pages.py` alone (006 owns it):
   `test_glossary_page_points_to_the_glossary` passes because `glossary_page` writes the
   GitHub link to `GLOSSARY.md` it looks for, and `test_page_is_written` passes because
   the page is not empty. Run both. `docs/reference/index.md`: the glossary line reads "Glossary: every term the docs use, and what it means".
   `CONTRIBUTING.md`: a short "Glossary" paragraph: add or change a term in `GLOSSARY.md`,
   then run the regenerate command; a Tooltip of `no` for an everyday word.
5. Gate: `uv run pytest tests/docs -q`, strict build. Open the built
   `reference/glossary/index.html` (the site uses directory URLs), one tutorial page and
   `reference/maps/index.html` (API
   docstrings get tooltips too, because mkdocstrings converts them with the site's
   extensions) in the build output and confirm by `grep -c '<abbr'` that tooltips render
   in each, and that `grep '<code>[^<]*<abbr'` finds none.
6. Build time: run the strict build twice, before S1's changes and after, and take the
   "Documentation built in N seconds" line of the second run each time. At this plan's
   base it reads 2.29 s (2.7 s wall clock, measured in the plan's fix round). After S1 it
   must read under 5 s on the same machine. Over 5 s is a red gate: find the cause and
   fix it (for example, the definitions are not blank-line separated, or a form is
   pathological), never drop the tooltips or the API pages to get under.

Done: tests green; strict build green; no contributor term on the site page; the S1
commit message states the measured build time before and after (for example "strict
build 2.29 s to 3.9 s"), and after is under 5 s.

### S2 — Reference truth (#163), parallel

Owned files: `docs/reference/style-fields.md`, `docs/reference/cli.md`,
`docs/reference/cache-layout.md`, `docs/reference/manifest.md`,
`docs/reference/pigments.md`, `docs/reference/brushes.md`,
`tests/docs/test_reference_values.py` (new), `tests/docs/test_docs_imports.py` (new).

Steps:

1. Write `tests/docs/test_docs_imports.py`, over `site_pages()` plus `README.md`:
   - `test_every_import_in_a_code_block_resolves`: each `from pyntpot... import ...`
     statement in a fenced `python` block (parenthesised continuations joined, parsed with
     `ast`) names a module that imports and names attributes it has.
   - `test_every_from_claim_names_an_exported_name`: in prose, each
     `` `Name`, from `pyntpot.x` `` or `` `Name` from `pyntpot.x` `` names a module whose
     `__all__` holds `Name`. Fails today on the 8 claims of #163.
   - `test_every_dotted_pyntpot_path_resolves`: each backticked `pyntpot.a.b...` in prose
     (a trailing `(...)` dropped) resolves with S0's `support.site_pages.resolve_dotted`
     (no second resolver here). Passes today (69 paths). 006's branch does not have
     `tests/docs/`, so this is the check S8's rebase runs: it names any prose path 006's
     renames broke on a page this feature owns (none today outside the files 006 edits
     itself; the grep in S8 step 1 confirms).
2. Write `tests/docs/test_reference_values.py`:
   - `TestStyleFieldTables`: per `## \`group\`` section, the rows' field names equal the
     group dataclass's fields with no duplicate; each Default cell (backticks stripped)
     equals `toml_value(getattr(Style.default().<group>, field))` and each Type cell equals
     `toml_type(...)`, where `toml_value` renders bool as `true`/`false`, int and float
     with `repr`, str with `json.dumps(ensure_ascii=False)`, a dict, a dataclass or a
     non-empty sequence of dicts or dataclasses as `table`, and other sequences as
     `[a, b]` of rendered items; `toml_type` is boolean, integer, number, string, table or
     array, and a Type cell of quoted choices (`` `"classic"` or `"warm"` ``) is accepted
     for a string; each group's line matches
     `` ^`(?P<cls>\w+)`(?:, from `(?P<pkg>pyntpot[\w.]*)`)?, read as `Style\.default\(\)\.(?P<group>\w+)`\. ``
     with `cls` the group's dataclass name and `group` the section's group. Fails today on
     the line format.
   - `TestCliSynopsis.test_the_synopsis_is_the_parser_usage`: the parsers are
     `pyntpot.maps.cli.build_parser()` and then each subparser in its subparsers action's
     `choices` order. For each, take `format_usage()`, remove the leading `usage: `, and
     collapse every whitespace run, newlines included, to one space, then strip. The
     non-empty lines of the fenced block under `## Synopsis`, each with whitespace runs
     collapsed the same way, must equal that list, one line per parser. argparse wraps
     usage at the terminal width (at 80 columns, which xdist workers get, the `map` usage
     is three lines; at 200 it is one), and it wraps only between usage parts, so
     collapsing makes the comparison width-independent with no need to force `COLUMNS`
     (which would need a `src/` change or environment config this feature does not
     make). A helper test pins the collapse on the three-line 80-column form. Fails today
     (`{map}` and `--margin-m`).
   - `TestPigmentTables`: rows of the table with columns Strip, Key, Colour, Transparency
     match `PIGMENTS[key]` and `float(cell) == TRANSPARENCY[key]`; rows of the table with
     columns Key, Colour, Transparency match `PAINTERS_PIGMENTS` and
     `PAINTERS_TRANSPARENCY`.
   - `TestBrushTables`: each treatment row's Darkness, Bristles, Gap, Dry and Texture
     equal `BRUSH_TREATMENTS[row]` (floats compared as floats, bristles as int) and Kind is
     `nib` exactly when the row is in `PEN_ROWS`; each prefix row's column letters and
     colours equal `BRUSH_COLOURS[prefix]`. Import these from `pyntpot.ink.brush`, as
     `tests/architecture/test_reference_pages.py` does today. 006's S0a moves the tables
     to `ink/brush_sheet.py` and `brush.py` imports them back, so the import still
     resolves after 006; S8 repoints it to `pyntpot.ink.brush_sheet`.
3. Make them pass:
   - `style-fields.md` (006 does not edit it; its plan hands the page to this feature):
     every group line becomes, for example,
     `` `CardStyle`, read as `Style.default().card`. `` followed by the existing
     description sentence; a group whose dataclass its package exports today keeps the
     package: `` `PaperStyle`, from `pyntpot.ink`, read as `Style.default().paper`. ``
     (`PaperStyle`, `BrushStyle` from `pyntpot.ink`; `FaceStyle`, `NibStyle`, `HandStyle`
     from `pyntpot.letters`). The other eight groups (`WashStyle` and the seven map groups)
     drop their package here, because no `__all__` exports them before 006; S8 adds it
     back for all eight once ADR 0068 has exported them. The `route_ink` and `lettering`
     lines keep the class names the code has today, `RouteInk` and `LetteringPolicy`
     (the test checks the real dataclass name); S8 renames them. The "Reading the tables"
     bullet reads: "The line under it
     names the group's dataclass, the package that exports it when one does, and how to
     read the group from a style." Line 267 (`style` of `route_ink`): "How the route is
     drawn: `"pen"` tints the pen plate when the `route` group painted one; any other value
     draws a solid line." Line 282: "draws no nib plate". The `route_ink` group line keeps
     "on the map" where it says "on the card".
   - `cli.md` synopsis: `pyntpot [-h] {map} ...` and
     `pyntpot map [-h] -o OUTPUT --cache CACHE --contact CONTACT [--style STYLE] [--margin-m MARGIN_M] [--no-attribution] track`;
     the sentence after it begins "`{map}` is the command, and `map` its one value." and
     keeps the word `command` (`tests/architecture/test_reference_pages.py` checks the
     subparser's `dest`). Where it says "letters the card" and "composes the PNG", it says
     "letters the map".
   - `cache-layout.md`: heading "The nib plate"; "label plate" to "nib plate"
     (4 times); "The file name carries the trace the hand writes"; sidecar key `route`
     row: "The trace the hand wrote, `centreline` or `outline`."
   - `manifest.md`, `pigments.md`, `brushes.md`: "card" to "map" where it means the
     picture; no other change unless a test fails.
4. Gate: `uv run pytest tests/docs -q`, strict build.

Done: tests green; the 8 wrong claims gone; synopsis equals the parser.

### S3 — Gallery and captions (#162), parallel

Owned files: `docs/gallery.md`, `docs/index.md`, `docs/explanation/data-policy.md`,
`tests/docs/test_gallery.py` (new), `tests/docs/test_captions.py` (new).

A caption is the `*Painted by `examples/<stem>.py`...*` paragraph that follows an image
`![...](.../images/<path>)` after one blank line, on any site page. The paragraph runs to
its blank line, past the closing `*`: `brushes.md:7` puts "The labels read" outside the
italics, so the label check reads the whole paragraph.

Steps:

1. Write `tests/docs/test_captions.py`, over every captioned image on every site page:
   - `test_every_caption_names_the_script_that_paints_its_image`: the image is registered
     and the caption's stem is the entry's `stem`.
   - `test_every_caption_names_its_figure_and_theme`: when the entry has a `figure`
     option the caption contains `figure <v>` or `figure="<v>"`; when it has `theme`, the
     caption contains the theme's path. Fails today: `docs/index.md` (hero, says "the
     Ambleside theme") and `docs/explanation/data-policy.md` (`places/ambleside.webp`).
     With two registry entries for one image, one matching entry suffices.
   - `test_every_label_list_in_a_caption_is_a_tuple_of_its_script`: in the sentence after
     "The labels read", which ends at the first `.` followed by whitespace, `*` or the end
     of the line (so the `.` of `0.52` does not end it; a naive split would check one
     clause of the corrected nib caption instead of two), each clause ending in the word `across` or
     `down` runs from the sentence start or the previous `across`/`down` to that word.
     When a clause holds two or more numbers and no `to` range ("1 to 8"), its numbers in
     order, compared as floats, must equal the numeric elements, in order, of one tuple
     or list literal in the script's AST whose elements are all numeric constants (unary
     minus included). A clause with fewer than two numbers is skipped; words between the
     numbers are ignored ("seed 11 and seed 23" is `[11, 23]`, "3 px, 6 px and 12 px" is
     `[3, 6, 12]`); a number counts only when it is not part of a word (`RIV1-a` holds
     none). Prototyped against every
     current caption in the plan's fix round: 22 clauses, all pass except both clauses
     of `gallery.md:221` (`[-38, 0, 90]` and `[0.5, 0.85]`, no such tuple in
     `examples/nib_stages.py`); the corrected caption matches line 90's `ANGLES` and
     `THINS`. The looser rule of the first draft (each number is *some* literal of the
     script) passed #162's own wrong caption, since -38.0, 0.0, 90.0, 0.85 and `0.5 * w`
     all occur in it. Fails today: `gallery.md:221` (#162).
   - `test_every_name_in_a_caption_is_written_by_its_script`: the name after "The name
     is" occurs in a string literal of the script. Fails today: nib-angles (#162).
2. Write `tests/docs/test_gallery.py`:
   - `test_the_gallery_shows_every_registered_image_but_the_site_chrome`: every
     `IMAGES` entry whose path does not start with `site/` is shown in `docs/gallery.md`.
     Fails today: `painting-with-python/svg-flat.webp`, `svg-washes.webp`, `svg-ink.webp`,
     `reference/glyph-sheet.webp`.
   - `test_the_gallery_lists_its_pages_in_nav_order`: the pages its `###` heading links
     resolve to are a subsequence, in order, of the nav. Fails after S0's nav change:
     the gallery's How-to headings run Write a theme, Change the route ink, Letter your
     own landmarks, Paint your own shapes, Map from the command line
     (`gallery.md:125-165`), and the nav puts Map from the command line second.
3. Make them pass:
   - `gallery.md:221` caption: "*Painted by `examples/nib_stages.py` (seed 7, figure
     angles, size 840). The name is Keswick. The labels read -38, 0, 38 and 90 across, the
     nib's angle in degrees, and 0, 0.52 and 0.85 down, `label_pen_thin`.*"
   - Add the three vector-drawing stages after the `svg-drawing` image (gallery.md
     117-121), each with alt text describing it and the caption
     "*Painted by `examples/svg_drawing.py` (seed 5, figure <flat|washes|ink>).*" (copy
     the alt text and figure value from `docs/tutorials/painting-with-python/vector-drawing.md`,
     which shows them); add the glyph sheet under the Reference section after Brushes,
     with the alt text and caption `docs/reference/letters.md` uses.
   - Move the gallery's "Map from the command line" section (its heading, image and
     caption, `gallery.md:165` to the line before `## Reference`) to directly after the
     "Write a theme" section, unchanged.
   - `docs/index.md` hero caption: "*Painted by `examples/place_card.py` (size 1200,
     theme `examples/themes/ambleside-hero.toml`).*"
   - `data-policy.md` caption: name `examples/themes/ambleside.toml` as the gallery's
     caption for the same image does.
   - Terminology in the three files: "callout(s)" to "landmark(s)"; "card" to "map" where
     it means the picture (the gallery's "place card" stays only as the script name
     `place_card.py`).
4. Gate: `uv run pytest tests/docs -q`, strict build.

Done: tests green; no image added to the registry.

### S4 — Tutorials (#172), parallel

Owned files: everything under `docs/tutorials/`, `tests/docs/test_tutorial_quotes.py`
(new), `tests/docs/test_tutorial_paths.py` (new), `examples/route_map.py` (module and
`main` docstrings only), `README.md` (line 40 only). Not
`tests/architecture/test_tutorials.py`: it stays where it is, unchanged and green, until
S8 moves it.

Steps:

1. Write `tests/docs/test_tutorial_quotes.py`, over
   `sorted((DOCS / "tutorials").rglob("*.md"))` and `fenced_blocks` from
   `support.site_pages` (module docstring: every tutorial page's quoted code is the
   script's own text):
   - `test_every_marked_block_on_every_tutorial_page_is_verbatim`: each block whose marker
     is `<!-- from examples/<path> -->` is a verbatim part of that file, as
     `tests/architecture/test_tutorials.py`'s test checks today for three pages, now for
     all nine. Parametrize by page with `ids=` (the page's path under `docs/tutorials/`).
   - `test_every_python_block_on_a_tutorial_page_is_marked`: each fenced `python` block
     on a tutorial page has a `from examples/` marker. Fails today: two blocks on
     `pictures.md`.
   Run: the verbatim test may also fail on curves, symmetry or fractals blocks never
   checked before; each such failure is fixed by making the page's block the script's
   text, never by editing the script. The narrower test in
   `tests/architecture/test_tutorials.py` keeps passing; S8 removes it as subsumed and
   fixes that file's "the eighth rung" docstring.
2. Write `tests/docs/test_tutorial_paths.py`, from `nav()`:
   - `test_every_tutorial_page_ends_with_the_next_page_in_nav_order`: the tutorial pages
     in nav order (section "Tutorials"); each page's last non-blank line matches
     `^Next: \[[^\]]+\]\((?P<href>[^)]+)\)` and `resolve(page, href)` is the next page; the
     last page's resolves to `docs/how-to/index.md`. Fails today on all nine.
   - `test_every_tutorial_page_but_an_index_leads_on_to_a_guide_reference_or_explanation`:
     each non-`index.md` tutorial page has a link resolving under `docs/how-to/`,
     `docs/reference/` or `docs/explanation/`. Fails today on all seven.
3. Make them pass:
   - `pictures.md`: put a `<!-- from examples/derwentwater.py -->` marker before each of
     its two python blocks and make each block the script's exact text. The first block
     (`pictures.md:28-31`) differs twice: `& inside)` where `examples/derwentwater.py:189`
     reads `& scene.inside)`, and `wash(cover, sheet, ...` where `:190` reads
     `wash(cover, scene.sheet, ...`. The verbatim check is a raw substring check, so the
     two-line block keeps the script's 8-space indentation on both lines. The prose after
     it (`pictures.md:33`) then says "`scene.inside` is the picture less its side
     margins". The second block is one line and already a substring.
   - `Next:` lines, each the page's last line: tutorials index to Paint a watercolour;
     Paint a watercolour to First map; First map to Painting with Python; its index to
     Curves; Curves to Symmetry; Symmetry to Fractals; Fractals to Pictures; Pictures to
     Vector drawing; Vector drawing to the how-to guides (`../../how-to/index.md`). Form:
     `Next: [First map](first-map.md), a route map of Ambleside from recorded data.` (a
     short clause saying what the next page paints). `pictures.md` loses its "The next
     page, ..." sentence. The two index pages' `Next:` targets are pages their lists
     already link; S0's index-order test keeps each page's first occurrence only, so the
     repeat leaves it green (run `tests/docs/test_nav.py` in the gate to see it).
   - Lead-on links, in each page's last section (create "## Where next" where none):
     paint-a-watercolour: `../reference/brushes.md`, `../reference/pigments.md`,
     `../explanation/how-the-wash-works.md`, `../explanation/the-hand-and-the-nib.md`;
     first-map: `../how-to/write-a-theme.md`, `../how-to/letter-your-own-landmarks.md`,
     `../how-to/change-the-route-ink.md`, `../how-to/work-offline-and-reuse-the-cache.md`,
     `../how-to/map-from-the-command-line.md`, `../reference/style-fields.md`; curves:
     `../../explanation/the-hand-and-the-nib.md`, `../../reference/brushes.md`; symmetry:
     `../../explanation/how-the-wash-works.md`; fractals: `../../reference/brushes.md`;
     pictures: `../../how-to/paint-your-own-shapes.md`,
     `../../explanation/how-the-wash-works.md`; vector-drawing:
     `../../how-to/paint-your-own-shapes.md`, `../../reference/pigments.md`.
   - `paint-a-watercolour.md:709-710`: "a route round Ambleside". Do not touch any other
     "Keswick": it is the lettered word of rungs 6 and 7.
   - Rung references link their rung: `curves.md:203` "as in
     [Take up the pen](../paint-a-watercolour.md#take-up-the-pen)"; `pictures.md:68`
     "[Letter a name](../paint-a-watercolour.md#letter-a-name) again";
     `vector-drawing.md:76` "as [Lay a wash](../paint-a-watercolour.md#lay-a-wash) handed
     it a disc".
   - `tutorials/index.md`: "in seven rungs". `README.md:40`: "The first seven pictures are
     the rungs of the watercolour tutorial and the eighth is the first map; each links to
     its page."
   - `first-map.md`, a section "## Paint it in the Ambleside theme" before "Where next":
     the command
     `uv run python examples/place_card.py ambleside/track.gpx ambleside/ out/ you@example.org --theme examples/themes/ambleside.toml --place ambleside --size 720`;
     one paragraph saying the theme sets the look and `--place` letters the landmarks
     `examples/places.toml` holds for Ambleside, and that the README's picture is the
     same map at 1200 in `examples/themes/ambleside-hero.toml`; then the image
     `![<alt text copied from gallery.md for places/ambleside.webp>](../images/places/ambleside.webp)`
     and the caption
     "*Painted by `examples/place_card.py` in `examples/themes/ambleside.toml`, with the
     landmarks of `examples/places.toml`.*". Say "looks like the picture", not "the same
     pixels".
   - Terminology in tutorial prose: "`Track.from_gpx` reads the track"; "card" to "map"
     where it means the picture ("The result is a map: one painted picture of one walk");
     the backing wash flag is "backing wash" in prose. Code identifiers stay
     (`route = Track.from_gpx(track)`, `card = compose(...)`: filed under #174).
   - `examples/route_map.py`: module docstring line 1 "The first map's script: a route
     map, the engine's first application."; line 4 "reads the track"; line 9 "stacks them
     into one map"; `main` docstring "save the map", "The GPX file of the track.", "The
     path of the saved map"; then copy the changed `main` docstring lines into the quoted
     block of `first-map.md` so it stays verbatim. No code line changes.
4. Gate: `uv run pytest tests/docs tests/architecture/test_tutorials.py tests/examples/test_route_map_example.py -q`,
   strict build (it checks every new link and anchor).

Done: tests green; the 9 pages each end in `Next:`; no example's code changed.

### S5 — Terminology sweep: how-to pages, the places file, the hand and the nib (#65), parallel

Owned files: everything under `docs/how-to/`, `docs/explanation/the-hand-and-the-nib.md`,
`examples/places.toml`, `examples/place_card.py`, `examples/social_preview.py`
(docstrings only), and in two test files the key string only:
`tests/golden/test_places.py:194` and `tests/unit/maps/test_example_themes.py:70`.

006's S9 rewords the comments, docstrings, test name and local around those two lines
(overlap table), so S5 changes the `"callouts"` string literal on each line to
`"landmarks"` and nothing else in either file: not the comments, not the docstrings, not
the test name `test_the_label_cap_is_the_callout_count`, not the local `callouts`. Not
`tests/support/docs_images.py`: 006's S9 writes the same "curated landmarks" in its
`_place_card` docstring. `examples/**` is untouched by 006. In `docs/how-to/`, leave
`self-host-providers.md` lines 7 to 9 (the provider protocols) to S8: they become true
with 006. S5 adds no sentence about importing `Landmark`; S8 step 7 adds it.

Steps:

1. Red: in `tests/golden/test_places.py:194` and `tests/unit/maps/test_example_themes.py:70`,
   change the string `"callouts"` to `"landmarks"`; the lines become
   `{"landmarks": entry.get("landmarks", []), "notes": entry.get("notes", [])}` and
   `callouts = tomllib.load(handle)[name].get("landmarks", [])`. `uv run pytest tests/unit/maps/test_example_themes.py tests/golden/test_places.py --golden-tolerance -q`
   fails (the file still says `callouts`).
2. Green: `examples/places.toml`, each `callouts = [` to `landmarks = [` and the header
   comment says landmark; `examples/place_card.py:69` reads `entry.get("landmarks", [])`,
   and its docstrings and comments and `examples/social_preview.py`'s docstrings say
   landmarks. The pinned label positions in `test_places.py`
   do not move: the key's name is not read by the painter.
3. How-to prose: `letter-your-own-landmarks.md` says "landmark" for every "callout" and its
   code reads `landmarks = [...]` and `Annotations.model_validate({"landmarks": landmarks})`;
   `change-the-route-ink.md` says "style" for the route ink's treatment (lines 63, 65, 99,
   110: "Try the styles and the colours", "The ink also has a style", "any other style is
   a solid line", "the route ink's style is `pen`"); "card" to "map" where it means the
   picture across `docs/how-to/`; "`Track.from_gpx` reads the track" wherever it says the
   route. Code blocks that mirror `examples/route_map.py` keep its variable names.
   `the-hand-and-the-nib.md:32`: "That is the `centreline` trace".
4. Gate: `uv run pytest tests/docs tests/unit/maps/test_example_themes.py tests/examples -q`
   and `uv run pytest tests/golden/test_places.py --golden-tolerance -q`, strict build.

Done: tests green; no `callout` left in `docs/how-to/` or `examples/`; no golden moved;
`git diff --stat -- tests` shows exactly the two test files, one changed line each.

### S6 — The wash essay (#176), parallel

Owned files: `docs/explanation/how-the-wash-works.md`,
`tests/docs/test_docs_signatures.py` (new).

Steps:

1. Write `tests/docs/test_docs_signatures.py`:
   `test_a_quoted_signature_lists_every_parameter`: over prose of every site page and
   `README.md`, each backticked `name(a, b, ...)` (optionally dotted) where `name` is a
   callable in any public `__all__` and every argument is a bare identifier that is a
   parameter of it, lists all its parameters in order (`self` excluded). Fails today:
   `how-the-wash-works.md:32`.
2. Make it pass and fix the misstatement:
   - Line 32: "`wash(cover, sheet, base, pool, options)` takes the coverage mask and
     returns a density; `options`, a `WashOptions`, is optional, and this page leaves it
     out."
   - Lines 127-128: "Four more behaviours are in the wash code, and a theme's wash group
     turns each on. Backruns and bleed are fields of the `WashOptions` that `wash` takes
     besides a body and a pool, which the map painter builds from the theme. Pigment
     separation and the shallow-water pass are not: they act on what washes produce, one
     wash's density and then the whole stack of layers, and the map painter runs them
     after its washes. This page shows none of them as a figure."
   - Lines 140-142: "See [references](references.md) for each source." The feature-note
     link goes (006's S8 deletes `ink-public-wash-options.md`).
   No claim that `WashOptions`, `separated` or `fluid_modulate` is or is not exported,
   and no module path (`ink.wash` becomes `ink.washing` in 006): every sentence is true on
   both sides. S8 adds the exports ADR 0068 makes.
3. Gate: `uv run pytest tests/docs -q`, strict build.

Done: test green; "nothing else" and the feature-note link are gone
(`grep -n "nothing else\|ink-public-wash-options" docs/explanation/how-the-wash-works.md`
prints nothing).

### S7 — Integration (after S0 to S6)

Owned files: `tests/docs/test_retired_words.py` (new), `tests/docs/test_docs_commands.py`
(new), the notes listed below, and any site page, `README.md` line or example docstring
a red after the merge names. Not
`docs/features/docs-missing-how-tos.md` or `docs/features/docs-examples-housekeeping.md`:
006's S8 edits both, so this feature's edits to them are S8's.

S2's, S3's and S6's tests scan every site page, but each ran in its own worktree, so they
first meet S4's and S5's page edits here. The integrator owns every red that appears
after the merge, whichever slice's test raises it, and fixes it in the page the red
names (never by loosening the test, never in `src/`).

Steps:

0. Merge S1 to S6 and run `uv run pytest tests/docs tests/architecture -q` and the strict
   build. Fix each red as above and list each fix in the PR description under the test
   that raised it.
1. Write `tests/docs/test_retired_words.py`:
   `test_no_page_or_example_uses_a_retired_word`: for each retired word of
   `parse(GLOSSARY.md)`, no site page, `README.md`, or `examples/**/*.{py,toml,md}`
   contains it, matched case-insensitively as a whole phrase, an optional plural `s`,
   spaces matching any whitespace run, after backticks are removed. It must pass on
   arrival if S1 to S6 swept correctly; any failure is fixed in the file it names (the
   integrator owns those fixes now that the parallel slices are merged).
1a. Write `tests/docs/test_docs_commands.py`, over every site page and `README.md`. It
   reads commands from two sources:
   - the code of fenced `bash`, `console`, `shell`, `sh` and `text` blocks (via
     `fenced_blocks`), one command per line after joining `\` continuations and dropping
     a leading `$ ` and a leading `uv run `;
   - every backticked inline span in `prose()` that starts `uv run python examples/`,
     with `uv run ` dropped. Today that is `curves.md:14`
     (`uv run python examples/curves.py out/ --figure rose`) and `symmetry.md:12`
     (`uv run python examples/kaleidoscope.py out/`), which give their commands in prose.
     Inline spans that start `pyntpot ` are not read: on site pages they are the
     command's name (`pyntpot map`), an error message and `pyntpot map --help`, none of
     them a command to parse.

   The extractor is a pure function of a page's text in the test module itself,
   `commands(text) -> list[Command]`
   (`Command`: `line: int`, `text: str`), with helper tests on inline strings: a `\`
   continued line joined, a command in an indented fence, an inline example span read,
   and an output line in a `text` block (a line not starting `pyntpot ` or
   `python examples/`) yielding nothing. S7 reads `text` blocks on purpose; the old
   how-to test treated them as output.
   - `test_every_pyntpot_command_parses`: each command starting `pyntpot ` is split with
     `shlex` and `pyntpot.maps.cli.build_parser().parse_args(...)` accepts the rest
     (argparse's exit is caught as a failure naming the page and line). The usage lines of
     `cli.md`'s synopsis are skipped by the regex `^pyntpot (map )?\[`, and only by it.
     A helper test shows a misspelt option (`--margn-m`) is rejected. A non-vacuity
     assertion: `docs/how-to/map-from-the-command-line.md` yields at least one command.
     This covers the tutorial commands `first-map.md:131` and `:152`, which the
     how-to-only `tests/architecture/test_how_to_commands.py` never reads.
   - `test_every_example_command_names_a_script_and_its_options`: each command starting
     `python examples/<path>.py`, fenced or inline, names a file that exists, and every
     token starting `-` is an option string of one of that script's `add_argument` calls, read from its AST
     (the script is never run). This checks S4's new
     `place_card.py … --theme … --place ambleside --size 720` command beyond the script's
     existence. It takes over the job of
     `tests/architecture/test_tutorials.py::test_every_run_command_names_an_existing_script`
     (every tutorial run command names an existing script), which reads inline commands
     too; S8 step 2 deletes that test once this one is green. A non-vacuity assertion:
     the two inline spans above are among the commands read.
   Review 2 counted the fenced commands at the base: 7 `pyntpot` lines (2 of them the
   skipped usage lines) and 18 example commands, README's continued command included, all
   passing; with the two inline spans the test passes on arrival unless S4 or S5 wrote a
   wrong command; a red is fixed on the page.
1b. Review the remaining `\bcards?\b` on site pages: list each occurrence
   (`grep -rnwE 'cards?' docs --include=*.md` minus excluded paths) in the PR description,
   and check each against the glossary's definition of card (the frame, not the
   picture). Four parallel slices judged "card meaning the picture" separately; this
   puts one reader over all of it. Fix any that mean the picture.
2. Delete `docs/issues/docs-gallery-nib-angles-caption-wrong.md`,
   `docs/issues/docs-style-fields-imports-and-reference-checks.md`,
   `docs/features/docs-glossary-in-place.md`, `docs/features/docs-tutorials-lead-on.md`,
   `docs/issues/docs-wash-takes-options.md` (#176). Search every remaining note for links
   to them and repoint or drop each (`grep -rn` for each file name under `docs/`). Today
   the only mentions outside the deleted notes are in `docs-missing-how-tos.md:46` and
   `docs-examples-housekeeping.md:44` (each names `docs-tutorials-lead-on.md`); both wait
   for S8. A plain backticked file name breaks no gate in the meantime.
3. File the spec's "Out of scope, filed separately" items: one note each (the CLAUDE.md
   shape: heading, `GitHub issue:` line, detail), and the matching issue with the note's
   heading as title, labels as CLAUDE.md lists; search open issues first. The #174 item
   is a paragraph appended to `docs/features/docs-examples-housekeeping.md` and a comment
   on #174, not a new issue: both are S8's (006's S8 edits that note).
4. Full gates: `uv run pytest -n auto --dist loadgroup --golden-tolerance`,
   `prek run --all-files`, the strict build.
5. Mutation testing: the diff changes no `ink` or `letters` function, so ADR 0012's run is
   not required; say so in the PR description.
6. Review the diff against this plan, then open the PR **as a draft** with the spec's
   title, its Changelog lines, and `Closes #65`, `Closes #162`, `Closes #163`,
   `Closes #172`, `Closes #176`. Comment on #176 with the branch name if not already done.

Done: every acceptance criterion in the spec ticked except S8's; CI green; the PR is a
draft until S8.

### S8 — After feature 006 lands

Runs once 006 (`specs/006-one-public-surface/`, ADR 0068) has merged to `main`. It does
three things: the moves and edits held back from S0 to S7 because 006 owned the files;
the #163 style-group lines with the real public imports; and every item in the "Handed to
session A" list of 006's plan. Each change starts from a test that fails for the reason
given. No `src/` file is edited here either.

Owned files: `tests/architecture/test_tutorials.py`,
`tests/architecture/test_reference_pages.py`, `tests/architecture/test_readme.py` and
`tests/architecture/test_docs_images.py` (moved to `tests/docs/`),
`tests/architecture/test_how_to_commands.py` (deleted, subsumed),
`tests/docs/test_tutorial_quotes.py`, `tests/docs/test_reference_values.py` (the brush
import and the group-line check), `tests/docs/test_glossary.py` (one test),
`tests/docs/test_docs_links.py` (new), `tests/docs/test_retired_words.py`,
`docs/reference/style-fields.md` (group lines, the "Reading the tables" bullet, one
intro sentence), `docs/explanation/how-the-wash-works.md` (the two S6 passages),
`docs/how-to/self-host-providers.md` (lines 7 to 9),
`docs/how-to/letter-your-own-landmarks.md` (one sentence), `docs/architecture.md`
(lines 23 to 24), `GLOSSARY.md` and the two generated files,
`docs/features/docs-missing-how-tos.md` and `docs/features/docs-examples-housekeeping.md`
(the lines below only), `examples/brush_sheet.py` (one docstring sentence),
`tests/support/docs_images.py` (the module docstring's `test_docs_images.py` path, line 40
at `529753f`; after 006, which edits only line 351 of that file), and, under `tests/`, any
line step 9's red names that 006's S9 missed.

Steps:

1. **Rebase** on `main` with 006 merged. Expected conflicts, and their resolutions:
   - `GLOSSARY.md` (006's S8 edited three rows of the old format that S1 rewrote): take
     this branch's file whole, then apply 006's three facts in step 6.
   - `tests/unit/maps/test_example_themes.py:70`: 006 renamed the local, S5 changed the
     key. Resolve to
     `landmarks = tomllib.load(handle)[name].get("landmarks", [])`, keeping 006's version
     of every other line (`:53`, `:67`, `:68`, `:73`).
   - `tests/golden/test_places.py`: S5's `:194` is five lines from 006's `:188`
     docstring, so git may or may not report a hunk. Any hunk resolves to 006's wording
     with 007's key: `{"landmarks": entry.get("landmarks", []), "notes": entry.get("notes", [])}`.

   After resolving, `git grep -n -i callout -- 'tests/*.py'` finds nothing outside
   `tests/docs/` and `tests/support/glossary.py`. Any other conflict means a file both
   plans edit that the overlap table under "Slices" missed: stop and report it. Then rerun
   the overlap check against 006's merged diff:
   `git diff --name-only <merge-base>..main` against this plan's "Files to touch". Then run `uv run pytest tests/docs tests/architecture -q` and
   `grep -rnE 'pyntpot\.ink\.(wash|stamp)\.|pyntpot\.maps\.(compose|vector_layers)\.|\bPt\b|\bAnchor\b|LetteringPolicy|RouteInk\b' docs README.md GLOSSARY.md examples`
   outside `docs/features`, `docs/issues`, `docs/decisions`, the three API reference pages
   and `references.md`. Expected red, and nothing else: `TestStyleFieldTables`'s
   group-line check on `route_ink` and `lettering` (the page says `RouteInk` and
   `LetteringPolicy`; the code now says `RouteInkStyle` and `LetteringStyle`), and the
   grep finding those two lines. Anything else red is a 006 change this plan did not
   foresee: fix it in the page it names (never in `src/`) and list it in the PR.
2. **Move the two docs tests** (held from S0). `git mv tests/architecture/test_tutorials.py tests/docs/test_tutorials.py`
   and the same for `test_reference_pages.py`, 006's version (its brush import already
   reads `pyntpot.ink.brush_sheet`). Run `uv run pytest tests/docs -q`: both pass where
   they are (they import from `support`, not from `tests.architecture`). Then, in
   `tests/docs/test_tutorials.py`, delete `test_every_marked_block_is_a_verbatim_part_of_its_script`
   and its `_tutorial_pages` helper, which `test_tutorial_quotes.py` subsumes over all
   nine pages. Delete `test_every_run_command_names_an_existing_script` with them: it is
   the helper's other caller, and S7's `test_docs_commands.py` covers its job over every
   site page, inline commands included (run `tests/docs/test_docs_commands.py` first and
   see it green). Remove any import or constant (`_COMMAND`, `EXAMPLES_DIR`) the deletions
   leave unused, so ruff stays clean. Change `test_the_first_map_quotes_the_route_map_script`'s docstring to
   "the first map's script" (not "the eighth rung"). In
   `tests/docs/test_reference_pages.py`, `test_label_plate_files_and_sidecar_keys_are_named`
   becomes `test_nib_plate_files_and_sidecar_keys_are_named`; its docstring already says
   "Both nib plates" (006's S9). `examples/brush_sheet.py:16`'s docstring names
   `tests/docs/test_reference_pages.py`, and `tests/support/docs_images.py:40`'s module
   docstring names `tests/docs/test_docs_images.py`. The same reason ("they check prose, not
   architecture") moves two more, unchanged: `git mv` `test_readme.py` and
   `test_docs_images.py` to `tests/docs/` (both import only from `support`). Delete
   `tests/architecture/test_how_to_commands.py`: S7's `test_docs_commands.py` parses
   every `pyntpot` command on every site page, the how-to pages included, with the same
   parser. `tests/architecture/test_reference_keys.py` stays: it reads `src/` modules
   through `tests/architecture/_ast_checks.py` and checks that code's `Source:` citations
   against `references.md`'s keys, a code-side contract, and 006 edits it. Done when
   `tests/architecture/` holds none of the four moved or deleted files,
   `grep -rnE "architecture/test_(tutorials|reference_pages|readme|docs_images|how_to_commands)"`
   outside `specs/`, `docs/issues/` and `docs/decisions/` finds nothing (repoint any
   docstring or note that names them; ADR 0033's mention stays, accepted ADRs are
   history), and the moved files pass under the `docs-tests` hook.
3. **Repoint this suite's imports** to 006's modules: `tests/docs/test_reference_values.py`
   imports `BRUSH_TREATMENTS`, `BRUSH_COLOURS` and `PEN_ROWS` from
   `pyntpot.ink.brush_sheet`, as the moved `test_reference_pages.py` does. Green before
   and after (the old import still resolves); this keeps one import path per name.
4. **Style groups, the real public imports (#163).** Red: in `TestStyleFieldTables`,
   make the group line's `, from` part required and its package one of
   `pyntpot.ink`, `pyntpot.letters` or `pyntpot.maps`, and assert
   `cls in importlib.import_module(pkg).__all__`. It fails on the eight lines S2 wrote
   without a package (`WashStyle`, `CardStyle`, `RibbonStyle`, `CoverStyle`,
   `RouteStyle`, `BasemapStyle`, and the two below) and on the two renamed classes.
   Green: every group line names its package, with these exact lines for the groups that
   change:
   - `` `WashStyle`, from `pyntpot.ink`, read as `Style.default().wash`. ``
   - `` `CardStyle`, from `pyntpot.maps`, read as `Style.default().card`. ``, and the same
     form for `RibbonStyle` (`ribbon`), `CoverStyle` (`cover`), `RouteStyle` (`route`)
     and `BasemapStyle` (`basemap`).
   - `` `RouteInkStyle`, from `pyntpot.maps`, read as `Style.default().route_ink`. ``
   - `` `LetteringStyle`, from `pyntpot.maps`, read as `Style.default().lettering`. ``
   Each keeps the description sentence after it. The "Reading the tables" bullet reads:
   "The line under it names the group's dataclass, the package that exports it, and how
   to read the group from a style." The page's intro gains one sentence, ADR 0068's
   contract: "Every group is a frozen dataclass built by keyword: make a variant with
   `dataclasses.replace(group, field=value)`." `test_every_from_claim_names_an_exported_name`
   now checks all thirteen claims, and the spec's "names a package only when it exports
   it" still holds because every package does.
5. **The wash essay (#176), after 006.** ADR 0068 exports `WashOptions`, `separated` and
   `fluid_modulate` from `pyntpot.ink`. Write the claims, then prove the from-claim test
   guards them: name `pyntpot.letters` as the package in one claim, watch
   `test_every_from_claim_names_an_exported_name` fail naming that line, and put it back.
   - Line 32: "`wash(cover, sheet, base, pool, options)` takes the coverage mask and
     returns a density; `options`, a `WashOptions`, from `pyntpot.ink`, is optional, and
     this page leaves it out."
   - The S6 passage on the other two behaviours gains: "They are `separated` and
     `fluid_modulate`, from `pyntpot.ink`, and both read their settings from `WashStyle`,
     the theme's wash group, because those settings belong to a plate rather than to one
     wash."
   `test_a_quoted_signature_lists_every_parameter` stays green on line 32.
6. **The glossary, after 006.** Red: in `TestTheGlossary`, add
   `test_in_the_code_names_the_exported_name_where_there_is_one`: for each dotted path in
   an "In the code" cell that `resolve_dotted` resolves to a class, function or constant
   (not a module),
   if some layer package's `__all__` binds the same object, the cell must name it as
   `pyntpot.<layer>.<name>`. At the branch's base it passes; after the rebase it fails on
   the private paths to names ADR 0068 exports. Green, in `GLOSSARY.md`:
   - "In the code" cells: card, display pixels and render pixels to `pyntpot.maps.Card`;
     manifest to `pyntpot.maps.Manifest`; dark grid to `pyntpot.maps.DarkGrid`;
     elevation grid to `pyntpot.maps.ElevationGrid`; credit to `pyntpot.maps.Credit`;
     label to `pyntpot.maps.Label`; span to `pyntpot.maps.Span`; span request to
     `pyntpot.maps.SpanRequest`; layers to `pyntpot.maps.Layers`; elevation patch to
     `pyntpot.maps.ElevationPatch`; landmark to `pyntpot.maps.Annotations`,
     `pyntpot.maps.Landmark`; provider adds `pyntpot.maps.Features`,
     `pyntpot.maps.Elevation`; backrun to `pyntpot.ink.bloom.bloom`,
     `pyntpot.ink.Blooms`, `pyntpot.ink.WashOptions`; route ink adds
     `pyntpot.maps.RouteInkStyle`; ribbon adds `pyntpot.maps.RibbonStyle`; cover class
     adds `pyntpot.maps.CoverStyle`; lettering adds `pyntpot.maps.LetteringStyle`.
   - 006's three rows, in this format: "brush sheet" In the code
     `pyntpot.ink.brush_from_id`, `pyntpot.ink.brush_sheet` (the module that holds the
     tables); "style group" Meaning ends "Each is a frozen, keyword-only dataclass named
     `<Group>Style`." (ADR 0068's naming convention); "vector layers" keeps
     `pyntpot.maps.VectorLayers`, `pyntpot.maps.vector_layers`, the exported names of
     what 006 cited by its private path `maps.vector_layer_build.VectorLayers` (the new
     test requires the exported name).
   - The contributor rows "layers" and "elevation patch" stay contributor rows: who meets
     a term does not change with its export.
   Regenerate (`PYTHONPATH=tests uv run python -m support.glossary`); the generated-file
   tests and the dotted-path test pass.
7. **The rest of 006's handed prose.** Red: new
   `tests/docs/test_docs_links.py::test_every_repository_link_names_a_file_on_the_branch`:
   on every site page and `README.md`, each link to
   `https://github.com/findlaywebb/pyntpot/blob/main/<path>` (fragment dropped) names a
   file that exists under `REPO_ROOT`, and each link to `…/tree/main/<path>` names a
   directory that exists (the gallery's Places headings, `gallery.md:247-271`,
   `first-map.md:23` and `write-a-theme.md:54` link `tree/main/`). Every such link
   resolves at the branch's base;
   after the rebase it fails on `docs/how-to/self-host-providers.md:9`, whose note
   (`maps-public-provider-protocols.md`) 006 deleted. Green:
   - `self-host-providers.md` lines 7 to 9: "Writing a provider of your own works too:
     `fetch` and `Cache` take any provider that satisfies `Features`, from
     `pyntpot.maps`, or `Elevation`, from `pyntpot.maps`; this page covers only the
     two that ship." The link goes.
   - `letter-your-own-landmarks.md`, after the paragraph on `Annotations` refusing an
     unknown key: "`Annotations` checks each table as a `Landmark`, from
     `pyntpot.maps`." Prove the from-claim test guards it as in step 5.
   - `docs/architecture.md` lines 23 to 24, after "a name in no `__all__` is private.":
     "Every name a public signature reaches is itself public, exported from its layer
     package (ADR 0068, `tests/architecture/test_public_signatures.py`)."
   - The #163 note that names `LetteringPolicy` and `RouteInk` is already gone (S7).
8. **Notes held from S7.** In `docs/features/docs-missing-how-tos.md` and
   `docs/features/docs-examples-housekeeping.md`, drop `docs-tutorials-lead-on.md` from
   each "Related" list (lines 46 and 44 at `03cf136`; find them by the file name after
   006's edits). Append the #174 paragraph from the spec's "Out of scope" to
   `docs-examples-housekeeping.md` and comment on #174. Touch no line 006 changed.
9. **Retired words beyond the docs.** Red: extend
   `test_no_page_or_example_uses_a_retired_word` to `src/**/*.py` and to
   `tests/**/*.py` minus `tests/docs/` and `tests/support/glossary.py` (which quote
   retired words as data). It should pass on arrival: 006's S9 (plan `a7d664d`) reworded
   every retired word under `src/` and `tests/`, and step 1's resolution changed the last
   `"callouts"` key strings. Run the extension and watch it pass; there is no red to
   hunt. Prove it is not vacuous by adding "label plate" to one test docstring, watching
   the test fail naming that line, and reverting. A real failure is a line 006's S9
   missed: under `tests/`, fix it here and list it in the PR; under `src/`, do not edit
   it, report the lines to the orchestrator for a 006 follow-up, and commit the `src/`
   half of the extension only once it is green.
10. Gates: `uv run pytest -n auto --dist loadgroup --golden-tolerance`,
    `prek run --all-files`, the strict build. Tick S8 in `tasks.md`, then mark the PR
    ready.

Done: `uv run pytest tests/docs -q` green with 006 in; `tests/architecture/` holds no
docs-prose test (only `test_reference_keys.py`, a code-side contract, reads docs there); every group line names its package; the strict build green; the PR is ready
with `Closes #65`, `Closes #162`, `Closes #163`, `Closes #172`, `Closes #176`.

## Parallelism

| Wave | Slices | Shared files |
| --- | --- | --- |
| 1 | S0 | none (alone) |
| 2 | S1, S2, S3, S4, S5, S6 | none: each owns its files above; `mkdocs.yml` and `CONTRIBUTING.md` are S0's then S1's, never concurrent |
| 3 | S7 | merges wave 2; owns every red the merge raises, fixed in the page it names |
| 4 | S8 | after 006 merges; owns the files held back from S0, S1, S4 and S7 |

Cross-slice contracts inside wave 2: S4's first-map caption follows S3's caption rule
(prescribed above, so it passes S3's test); S1's glossary page passes S2's dotted-path test
(all its paths checked); every slice sweeps the retired words in the files it owns, and S7
proves it.

## Files to touch

Before 006 merges (S0 to S7): `GLOSSARY.md`; `mkdocs.yml`; `.pre-commit-config.yaml`;
`CONTRIBUTING.md`; `README.md` (line 40); `docs/index.md`; `docs/gallery.md`;
`docs/README.md`; everything under `docs/tutorials/` and `docs/how-to/`; `docs/reference/{index,glossary,style-fields,cli,cache-layout,manifest,pigments,brushes}.md`;
`docs/includes/abbreviations.md` (new); `docs/explanation/{index,how-the-wash-works,the-hand-and-the-nib,data-policy}.md`;
`docs/explanation/performance.md` moved to `docs/runbooks/performance.md`;
`examples/route_map.py` (docstrings), `examples/places.toml`, `examples/place_card.py`,
`examples/social_preview.py` (docstrings); `tests/support/site_pages.py` and
`tests/support/glossary.py` (new);
`tests/docs/` (new package, new files only);
`tests/golden/test_places.py:194` and `tests/unit/maps/test_example_themes.py:70` (the
key string only); the notes S7 deletes and files.

After 006 merges (S8): `tests/architecture/test_tutorials.py`,
`test_reference_pages.py`, `test_readme.py` and `test_docs_images.py` moved to
`tests/docs/`; `tests/architecture/test_how_to_commands.py` deleted; `docs/architecture.md` (one sentence);
`docs/features/docs-missing-how-tos.md` and `docs-examples-housekeeping.md` (one line
each, and the #174 paragraph); `examples/brush_sheet.py` (one docstring sentence);
`tests/support/docs_images.py` (the module docstring's test path); the rebase
resolutions of S8 step 1; any `tests/` line 006's S9 missed; and second edits to
`GLOSSARY.md`, `style-fields.md`, `how-the-wash-works.md`, `self-host-providers.md` and
`letter-your-own-landmarks.md`.

## Files to leave alone

- `src/**`, in every slice: 006 owns it and its S9 executes the spec's "Docstring changes
  for 006's S9"; this feature changes no code and no docstring there, even where a retired
  word sits. S8's scan reports a miss to the orchestrator rather than fixing it.
- `tests/architecture/**` before 006 merges, with no exception: 006 owns it and edits
  `test_reference_pages.py`, `test_site.py` and `test_reference_keys.py`. After it merges,
  S8 moves `test_tutorials.py`, `test_reference_pages.py`, `test_readme.py` and
  `test_docs_images.py` out, deletes `test_how_to_commands.py`, and touches nothing else
  there.
- `docs/reference/{pyntpot,ink,letters,maps}.md` (directives and dotted paths) and the
  "Implemented in" lines of `docs/explanation/references.md`: 006 fixes them with its
  renames and new exports.
- The three `GLOSSARY.md` rows 006 edits ("brush sheet", "style group", "vector layers"):
  S1 keeps their meaning as on `main`; only S8 adds 006's facts.
- The notes 006's S8 edits or deletes (its plan lists them), except the two lines and the
  #174 paragraph S8 adds after 006 has merged.
- `docs/features/ink-public-wash-options.md` (#73) and every other note not named above.
- Every example's code lines, with one exception: S5 changes `examples/place_card.py:69`
  to read the `landmarks` key (`entry.get("landmarks", [])`), together with the key
  in `examples/places.toml`; no picture changes, because the painter never reads the
  key's name. Also left alone: `tests/golden/**` pins and masters,
  `tests/golden/make_docs_images.py`, the image registry's entries: no image moves or is
  added.
- `docs/decisions/**`: no ADR changes; accepted ADRs are history.
- `specs/001` to `specs/006`.
- `CHANGELOG.md`: drafted at release from the squash subject and Changelog lines.

## Risks

- **Every-use underline.** `abbr` marks every occurrence, not the first; only distinctive
  forms get a tooltip, and the everyday-word list guards it.
- **Concurrent edits with 006.** Pre-006 slices edit a file 006's plan also edits only
  where the overlap table says so: `GLOSSARY.md` and S5's two key strings. S8 step 1
  names each expected conflict and its resolution. 006's plan is
  being rewritten in its own fix round while this one is reviewed, so S8 reruns the
  overlap grep against the merged 006 on `main` (its actual diff), not against any
  version of 006's plan.
- **006 slips or changes scope.** S0 to S7 stay true at the base whatever 006 does, but
  the PR stays a draft until S8. If ADR 0068 is amended (a name not exported, a different
  rename), S8's exact lines change with it; the S8 tests (the required `, from` part, the
  exported-name glossary check, the repository-link check) are generic and follow the
  code.
- **006's S9 misses a line.** S8 step 9 catches it: under `tests/` S8 fixes it, under
  `src/` the fix goes back to 006's owner, not into this diff.
- **Hidden drift in quoted blocks** on curves, symmetry and fractals, unchecked until
  now: fixed by copying the script's text into the page, never the reverse.
- **Snippets path**: `auto_append` resolves from the working directory, so the build runs
  from the repo root, as CI does; `check_paths: true` fails loudly otherwise.

## Response to review 1

Every finding was checked against the worktree at `7b61165` before the plan changed. None
was wrong. The blockers and should-fixes were confirmed as follows.

Blockers, all fixed:

1. **Index order and `Next:`.** Confirmed: `tutorials/index.md:8` and the series index's
   first bullet already link the pages S4's `Next:` lines name. S0's test now keeps each
   linked page at its first occurrence only. "Same section" now means an exact
   `NavEntry.sections` match, plus each direct subsection's index page, so a
   subsection's pages belong to its own index. This is stricter than the review's
   proposal: Tutorials must also list Painting with Python's index, which it does.
2. **Block marker.** Confirmed: `curves.md` (7 blocks) and `fractals.md` (13 blocks) leave
   a blank line between marker and fence. `marker` is now the nearest preceding non-blank
   line when that line is an HTML comment.
3. **CLI synopsis.** Confirmed at 80 and 200 columns. Each parser's usage, and each
   synopsis line, has every whitespace run (newlines included) collapsed to one space.
   That is width-independent, so the test forces no width: forcing one would need
   environment config or a `src/` change.
4. **Say instead.** Each "Say instead" now has to end in a term as a whole word, so the
   test and the data agree. The data stays as the spec words it ("centreline trace", not
   "trace (centreline trace)").
5. **#162 numbers.** Re-prototyped: 22 clauses across all current captions, and only both
   clauses of `gallery.md:221` fail. Adopted as the review proposes, with the clause
   boundaries written out. The spec's criterion now matches.

Should-fixes:

- Adopted: 1 (blank-line abbreviations, the API page in the `<abbr` check, and a measured
  build-time budget in S1's done criteria: 2.29 s today, under 5 s after); 2 (gallery
  reorder step); 3 (`resolve_dotted` in S0, contributor paths checked in S1,
  `Term.code` as bare names); 4 (example code carve-out); 5 (all three `pictures.md`
  details); 6 (`validation:` before `nav:`, asserted); 7 (indented fences dedented by
  the fence indent); 8 (S7 owns every post-merge red); 9 (`test_docs_commands.py` in
  S7, prototyped green on 23 commands; S8 deletes the how-to-only test); 10
  (`tree/main/`); 11 (`includes/` exclusion asserted); 12 (S8 moves
  `test_readme.py` and `test_docs_images.py` too).
- Partly adopted, 12: `test_reference_keys.py` stays in `tests/architecture/`. It reads
  `src/` through `_ast_checks.py` and checks code citations against `references.md`, a
  code-side contract, and 006 edits it.
- Consider items, all adopted: S7 lists and reviews every remaining `card`; S1 guards
  against `’` on site pages; "seven" non-index tutorial pages (plan and tasks); S8 reruns
  the overlap grep against the merged 006, not its plan.

## Response to review 2

Every finding was checked against the worktree at `529753f` and 006's plan at `a7d664d`
before the plan changed. None was wrong.

Blockers, all fixed:

1. **006's S9 edits S5's test lines.** Confirmed: 006's S9 (plan.md:948-975 at `a7d664d`)
   rewords `test_places.py:45, 51, 89, 188`, `docs_images.py:351`,
   `test_example_themes.py:53, 67, 68, 70, 73`, `test_reference_pages.py:168` and every
   test line S8 step 9 listed, and leaves only the two `"callouts"` key strings. Per the
   orchestrator's decision, 006's S9 owns every retired-word edit under `src/**` and
   `tests/**`. S5 now changes only those two key strings and drops `docs_images.py`. The
   overlap table has rows for `test_example_themes.py`, `test_places.py`,
   `docs_images.py` and the S9 test files, and states the pin to `a7d664d`. S8 step 1
   names the `test_example_themes.py:70` conflict and its exact resolution, and the
   possible `test_places.py` hunk. S8 step 2 keeps the test rename (006's grep does not
   match `label_plate`) and drops the `:168` docstring edit. S8 step 9 expects green on
   arrival, with a non-vacuity check, and fixes a `tests/` miss itself.
2. **The step 2 grep and ADR 0033.** Confirmed: `docs/decisions/0033-docs-images-and-examples.md:21`
   and `tests/support/docs_images.py:40` both match. The grep now excludes
   `docs/decisions/`, and S8 owns `docs_images.py`'s module docstring (line 40). That is
   after 006, which touches only line 351 of that file.
3. **`_tutorial_pages` has a second caller.** Confirmed: `test_tutorials.py:97`. S8 step
   2 also deletes `test_every_run_command_names_an_existing_script`, after S7's commands
   test is green, and the constants that leaves unused. S7's test now reads inline spans
   in prose that start `uv run python examples/` (`curves.md:14`, `symmetry.md:12`).
   - **Narrower than the review's fix:** inline spans that start `pyntpot ` are not read.
     On site pages they are `pyntpot map` (three times), an error message and
     `pyntpot map --help`. None parses as a command (`--help` exits, `map` alone lacks
     the required arguments), so reading them would make the test red at once.

Suggestions:

1. **Adopted.** The label sentence ends at a `.` followed by whitespace, `*` or the end
   of the line. The caption is the whole paragraph, past the closing `*` (confirmed at
   `brushes.md:7` and `gallery.md:183`).
2. **Adopted.** S7's extractor is a pure `commands(text)` with helper tests: a continued
   line, an indented fence, an inline span, an output line in a `text` block. The
   misspelt-option rejection and a non-vacuity assertion on
   `map-from-the-command-line.md` are carried over too. The usage-line skip is the regex
   `^pyntpot (map )?\[`.
3. **Adopted.** Confirmed: at `529753f` all three names resolve to modules. The S1
   sentence is corrected, and S0 adds a helper test pinning `resolve_dotted("pyntpot.ink.wash")`
   to a module.
4. **Adopted.** Confirmed: `letter-your-own-landmarks.md` has no import sentence. S5 now
   says it adds none, and S8 step 7 adds it (spec and tasks reworded to match).
5. **Adopted.** Meaning holds no module path (`pyntpot.…`, `ink.x.Y`); the spec's
   attribute references stay.

Skipped: none.
