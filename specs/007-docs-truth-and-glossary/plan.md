# 007 — plan

## Approach

Docs and docs tests only. No `src/` file changes here (feature 006 sweeps the docstrings
from the spec's "Canonical terms" table), no boundary change, no public-API change, so no
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

The existing docs tests `tests/architecture/test_tutorials.py` and
`tests/architecture/test_reference_pages.py` move to `tests/docs/` (they check prose, not
architecture), so this feature and 006 never edit the same test file.

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
once feature 006 has merged to `main`. Each slice is test-first: write the named tests,
run them, watch each fail for the reason given, then make them pass. Each slice commits
its own checkpoint on the feature branch. "Done" for every slice includes: its tests
green, `uv run pytest tests/docs tests/architecture -q` green, `uv run ruff check .`,
`uv run ruff format --check .` and `uv run ty check` clean, and no file over 400 lines.

B-dependency: S0 to S7 are **independent of 006**: every page they write is true whether
or not 006 exports the style groups, `WashOptions` or the provider protocols, and
whatever it renames `ink.wash`, `ink.stamp`, `maps.compose` and `maps.vector_layers` to.
S8 is **after 006 lands**.

### S0 — Scaffold and site shape (serial, first)

Owned files: `tests/docs/__init__.py` (new, empty docstring module like
`tests/architecture/__init__.py`), `tests/support/site_pages.py` (new),
`tests/docs/test_site_pages.py` (new), `tests/docs/test_nav.py` (new),
`tests/docs/test_tutorials.py` and `tests/docs/test_reference_pages.py` (moved),
`.pre-commit-config.yaml`, `mkdocs.yml`, `docs/explanation/performance.md` (moved to
`docs/runbooks/performance.md`), `docs/explanation/index.md`, `docs/README.md`,
`CONTRIBUTING.md`.

Steps:

1. `git mv tests/architecture/test_tutorials.py tests/docs/test_tutorials.py` and the same
   for `test_reference_pages.py`. Contents unchanged in this slice. If 006 has already
   edited either file on `main`, rebase first and move 006's version.
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
     fences; `marker` is the `<!-- ... -->` comment on the line before the fence.
   - `prose(text: str) -> str`: the text with fenced blocks removed.
   - `links(text: str) -> list[str]`: Markdown link targets, images excluded.
   - `resolve(page: Path, href: str) -> Path | None`: a relative `.md` link resolved
     against the page, fragment dropped; `None` for absolute URLs.
4. Write `tests/docs/test_nav.py`:
   - `test_every_section_index_lists_its_pages_in_nav_order`: for each nav section whose
     first entry is an `index.md`, the links on that index page that resolve to pages of
     the same section, in order, equal the section's other pages in nav order. Fails
     today: Painting with Python (nav has Vector drawing before Pictures) and How-to
     guides (nav order differs from `how-to/index.md`).
   - `test_the_performance_log_is_a_runbook_and_no_site_page_links_it`:
     `docs/runbooks/performance.md` exists, no nav entry and no site page link resolves
     to a `performance.md`. Fails today.
   - `test_the_strict_build_validates_anchors`: `mkdocs.yml` has
     `validation:` with `anchors: warn`. Fails today.
5. Make them pass:
   - `mkdocs.yml` nav: Painting with Python in the order Curves, Symmetry, Fractals,
     Pictures, Vector drawing; How-to guides in `how-to/index.md`'s order (write a theme,
     map from the command line, change the route ink, letter your own landmarks, work
     offline and reuse the cache, credit the map data, self-host providers, paint your
     own shapes); drop `explanation/performance.md`; add `includes/` to `exclude_docs`;
     add `validation:` / `  anchors: warn`.
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

Done: the three nav tests and the helper tests pass; the strict build passes with anchor
validation on; `tests/architecture` no longer holds the two moved files.

### S1 — Glossary (#65), parallel

Owned files: `GLOSSARY.md`, `tests/support/glossary.py` (new),
`tests/docs/test_glossary.py` (new), `docs/reference/glossary.md` (generated),
`docs/includes/abbreviations.md` (generated, new), `mkdocs.yml` (markdown extensions and
theme features only), `docs/reference/index.md`, `tests/docs/test_reference_pages.py`
(only the glossary pointer test), `CONTRIBUTING.md` (a glossary paragraph only).

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
backticked dotted names that resolve at runtime; it names an exported name
(`pyntpot.ink.Sheet`, `pyntpot.maps.Track`) where one exists, otherwise a private module
path, and never a path through `ink/wash.py`, `ink/stamp.py`, `maps/compose.py`,
`maps/vector_layers.py` or `ink/brush.py` (006 renames the first four and may split the
fifth); `pyntpot.ink.wash`, `pyntpot.maps.compose` and `pyntpot.maps.vector_layers` are
fine because they resolve to the exported functions either way. The Meaning column holds
no dotted code path; existing rows move theirs to "In the code".

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

- `Term` (frozen: `name`, `meaning`, `code`, `tooltip: tuple[str, ...]`,
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

  Every term these docs use, what it means and where it lives in the code. The docs use one name for each of these and no other. A term underlined on a page shows its meaning when you point at it.

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
  order, ending in one newline.
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
     every retired word is not a term, and every "Say instead" is a term.
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
4. Delete `TestEveryPageExists.test_glossary_page_points_to_the_glossary` from
   `tests/docs/test_reference_pages.py` and fix its class docstring (the glossary page is
   generated, and `test_glossary.py` proves it). `docs/reference/index.md`: the glossary
   line reads "Glossary: every term the docs use, and what it means".
   `CONTRIBUTING.md`: a short "Glossary" paragraph: add or change a term in `GLOSSARY.md`,
   then run the regenerate command; a Tooltip of `no` for an everyday word.
5. Gate: `uv run pytest tests/docs -q`, strict build. Open the built
   `reference/glossary.html` and one tutorial page in the build output and confirm by
   `grep -c '<abbr' ` that tooltips render and `grep '<code>[^<]*<abbr'` finds none.

Done: tests green; strict build green; no contributor term on the site page.

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
     (a trailing `(...)` dropped) resolves by importing the longest module prefix and
     `getattr` on the rest. Passes today (69 paths); it is the gate 006's renames must
     keep green.
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
   - `TestCliSynopsis.test_the_synopsis_is_the_parser_usage`: the fenced block under
     `## Synopsis` equals, line by line with whitespace runs collapsed, the
     `format_usage()` of `build_parser()` and of each subparser, `usage: ` removed. Fails
     today (`{map}` and `--margin-m`).
   - `TestPigmentTables`: rows of the table with columns Strip, Key, Colour, Transparency
     match `PIGMENTS[key]` and `float(cell) == TRANSPARENCY[key]`; rows of the table with
     columns Key, Colour, Transparency match `PAINTERS_PIGMENTS` and
     `PAINTERS_TRANSPARENCY`.
   - `TestBrushTables`: each treatment row's Darkness, Bristles, Gap, Dry and Texture
     equal `BRUSH_TREATMENTS[row]` (floats compared as floats, bristles as int) and Kind is
     `nib` exactly when the row is in `PEN_ROWS`; each prefix row's column letters and
     colours equal `BRUSH_COLOURS[prefix]`. Import these from `pyntpot.ink.brush`, as the
     moved test does.
3. Make them pass:
   - `style-fields.md`: every group line becomes, for example,
     `` `CardStyle`, read as `Style.default().card`. `` followed by the existing
     description sentence; a group whose dataclass its package exports today keeps the
     package: `` `PaperStyle`, from `pyntpot.ink`, read as `Style.default().paper`. ``
     (`PaperStyle`, `BrushStyle` from `pyntpot.ink`; `FaceStyle`, `NibStyle`, `HandStyle`
     from `pyntpot.letters`). The "Reading the tables" bullet reads: "The line under it
     names the group's dataclass, the package that exports it when one does, and how to
     read the group from a style." Line 267 (`style` of `route_ink`): "How the route is
     drawn: `"pen"` tints the pen plate when the `route` group painted one; any other value
     draws a solid line." Line 282: "draws no nib plate". The `route_ink` group line keeps
     "on the map" where it says "on the card".
   - `cli.md` synopsis: `pyntpot [-h] {map} ...` and
     `pyntpot map [-h] -o OUTPUT --cache CACHE --contact CONTACT [--style STYLE] [--margin-m MARGIN_M] [--no-attribution] track`;
     the sentence after it begins "`{map}` is the command, and `map` its one value." and
     keeps the word `command` (the moved test checks the subparser's `dest`). Where it
     says "letters the card" and "composes the PNG", it says "letters the map".
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
`![...](.../images/<path>)` after one blank line, on any site page.

Steps:

1. Write `tests/docs/test_captions.py`, over every captioned image on every site page:
   - `test_every_caption_names_the_script_that_paints_its_image`: the image is registered
     and the caption's stem is the entry's `stem`.
   - `test_every_caption_names_its_figure_and_theme`: when the entry has a `figure`
     option the caption contains `figure <v>` or `figure="<v>"`; when it has `theme`, the
     caption contains the theme's path. Fails today: `docs/index.md` (hero, says "the
     Ambleside theme") and `docs/explanation/data-policy.md` (`places/ambleside.webp`).
     With two registry entries for one image, one matching entry suffices.
   - `test_every_label_number_in_a_caption_is_a_literal_of_its_script`: every number in
     the sentence after "The labels read" is a numeric literal (unary minus included) in
     the script's AST.
   - `test_every_name_in_a_caption_is_written_by_its_script`: the name after "The name
     is" occurs in a string literal of the script. Fails today: nib-angles (#162).
2. Write `tests/docs/test_gallery.py`:
   - `test_the_gallery_shows_every_registered_image_but_the_site_chrome`: every
     `IMAGES` entry whose path does not start with `site/` is shown in `docs/gallery.md`.
     Fails today: `painting-with-python/svg-flat.webp`, `svg-washes.webp`, `svg-ink.webp`,
     `reference/glyph-sheet.webp`.
   - `test_the_gallery_lists_its_pages_in_nav_order`: the pages its `###` heading links
     resolve to are a subsequence, in order, of the nav.
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

Owned files: everything under `docs/tutorials/`, `tests/docs/test_tutorials.py`,
`tests/docs/test_tutorial_paths.py` (new), `examples/route_map.py` (module and `main`
docstrings only), `README.md` (line 40 only).

Steps:

1. Edit `tests/docs/test_tutorials.py`:
   - `_tutorial_pages()` returns `sorted((REPO_ROOT / "docs" / "tutorials").rglob("*.md"))`;
     its docstring and the module docstring say every tutorial page.
   - New `test_every_python_block_on_a_tutorial_page_is_marked`: each fenced `python` block
     on a tutorial page has a `from examples/` marker. Fails today: two blocks on
     `pictures.md`.
   - `test_the_first_map_quotes_the_route_map_script` docstring: "the first map's script"
     (not "the eighth rung").
   Run: the verbatim test may also fail on curves, symmetry or fractals blocks never
   checked before; each such failure is fixed by making the page's block the script's
   text, never by editing the script.
2. Write `tests/docs/test_tutorial_paths.py`, from `nav()`:
   - `test_every_tutorial_page_ends_with_the_next_page_in_nav_order`: the tutorial pages
     in nav order (section "Tutorials"); each page's last non-blank line matches
     `^Next: \[[^\]]+\]\((?P<href>[^)]+)\)` and `resolve(page, href)` is the next page; the
     last page's resolves to `docs/how-to/index.md`. Fails today on all nine.
   - `test_every_tutorial_page_but_an_index_leads_on_to_a_guide_reference_or_explanation`:
     each non-`index.md` tutorial page has a link resolving under `docs/how-to/`,
     `docs/reference/` or `docs/explanation/`. Fails today on all six.
3. Make them pass:
   - `pictures.md`: put a `<!-- from examples/derwentwater.py -->` marker before each of
     its two python blocks and make each block the script's exact text (the first now
     reads `& inside)` where `examples/derwentwater.py:189` reads `& scene.inside)`).
   - `Next:` lines, each the page's last line: tutorials index to Paint a watercolour;
     Paint a watercolour to First map; First map to Painting with Python; its index to
     Curves; Curves to Symmetry; Symmetry to Fractals; Fractals to Pictures; Pictures to
     Vector drawing; Vector drawing to the how-to guides (`../../how-to/index.md`). Form:
     `Next: [First map](first-map.md), a route map of Ambleside from recorded data.` (a
     short clause saying what the next page paints). `pictures.md` loses its "The next
     page, ..." sentence.
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
4. Gate: `uv run pytest tests/docs tests/examples/test_route_map_example.py -q`, strict
   build (it checks every new link and anchor).

Done: tests green; the 9 pages each end in `Next:`; no example's code changed.

### S5 — Terminology sweep: how-to pages, the places file, the hand and the nib (#65), parallel

Owned files: everything under `docs/how-to/`, `docs/explanation/the-hand-and-the-nib.md`,
`examples/places.toml`, `examples/place_card.py`, `examples/social_preview.py`
(docstrings only), `tests/golden/test_places.py`, `tests/unit/maps/test_example_themes.py`,
`tests/support/docs_images.py` (the `_place_card` docstring only).

Steps:

1. Red: in `tests/golden/test_places.py:194` and `tests/unit/maps/test_example_themes.py:70`,
   read the key `landmarks` instead of `callouts`, and say "landmarks" in their comments
   and docstrings. `uv run pytest tests/unit/maps/test_example_themes.py tests/golden/test_places.py --golden-tolerance -q`
   fails (the file still says `callouts`).
2. Green: `examples/places.toml`, each `callouts = [` to `landmarks = [` and the header
   comment says landmark; `examples/place_card.py:69` reads `entry.get("landmarks", [])`,
   and its docstrings and comments, `examples/social_preview.py`'s docstrings and the
   `_place_card` docstring say landmarks. The pinned label positions in `test_places.py`
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

Done: tests green; no `callout` left in `docs/how-to/` or `examples/`; no golden moved.

### S6 — The wash essay (#TBD), parallel

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
     besides a body and a pool, which the map painter builds from the theme; pigment
     separation and the shallow-water pass are steps of the map painter of their own. This
     page shows none of them as a figure."
   - Lines 140-142: "See [references](references.md) for each source." The feature-note
     link goes.
   No claim that `WashOptions` is or is not exported (S8 adds the package if 006 exports
   it).
3. Gate: `uv run pytest tests/docs -q`, strict build.

Done: test green; "nothing else" and the feature-note link are gone
(`grep -n "nothing else\|ink-public-wash-options" docs/explanation/how-the-wash-works.md`
prints nothing).

### S7 — Integration (after S0 to S6)

Owned files: `tests/docs/test_retired_words.py` (new), the notes listed below.

Steps:

1. Write `tests/docs/test_retired_words.py`:
   `test_no_page_or_example_uses_a_retired_word`: for each retired word of
   `parse(GLOSSARY.md)`, no site page, `README.md`, or `examples/**/*.{py,toml,md}`
   contains it, matched case-insensitively as a whole phrase, an optional plural `s`,
   spaces matching any whitespace run, after backticks are removed. It must pass on
   arrival if S1 to S6 swept correctly; any failure is fixed in the file it names (the
   integrator owns those fixes now that the parallel slices are merged).
2. Delete `docs/issues/docs-gallery-nib-angles-caption-wrong.md`,
   `docs/issues/docs-style-fields-imports-and-reference-checks.md`,
   `docs/features/docs-glossary-in-place.md`, `docs/features/docs-tutorials-lead-on.md`,
   `docs/issues/docs-wash-takes-options.md`. Search every remaining note for links to
   them and repoint or drop each (`grep -rn` for each file name under `docs/`).
3. File the spec's "Out of scope, filed separately" items: one note each (the CLAUDE.md
   shape: heading, `GitHub issue:` line, detail), and the matching issue with the note's
   heading as title, labels as CLAUDE.md lists; search open issues first. The #174 item
   is a paragraph appended to `docs/features/docs-examples-housekeeping.md` and a comment
   on #174, not a new issue.
4. Full gates: `uv run pytest -n auto --dist loadgroup --golden-tolerance`,
   `prek run --all-files`, the strict build.
5. Mutation testing: the diff changes no `ink` or `letters` function, so ADR 0012's run is
   not required; say so in the PR description.
6. Review the diff against this plan, then open the PR with the spec's title, its
   Changelog lines, and `Closes #65`, `Closes #162`, `Closes #163`, `Closes #172`,
   `Closes #<wash issue>`.

Done: every acceptance criterion in the spec ticked except S8's; CI green.

### S8 — After feature 006 lands

Owned files: `docs/reference/style-fields.md` (group lines only),
`docs/explanation/how-the-wash-works.md` (one sentence), `GLOSSARY.md` ("In the code"
cells only) and the two generated files, `tests/docs/test_retired_words.py`.

Steps:

1. Rebase on `main` with 006 merged. Run `uv run pytest tests/docs -q`; the generic tests
   say what 006 changed that the docs now contradict (a renamed dataclass in a group line,
   a moved path in a glossary cell).
2. For each style group whose dataclass 006 exported, add `, from `<package>`` to its
   group line; for each renamed dataclass, use the new name.
3. If 006 exported `WashOptions`, the essay's line 32 sentence reads "`options`, a
   `WashOptions` from `pyntpot.ink`, is optional".
4. In `GLOSSARY.md`, replace a private path with the exported name wherever 006 exported
   one (`Card`, `Manifest`, `ElevationGrid`, `Credit`, `SpanRequest`, the provider
   protocols); regenerate.
5. Extend `test_no_page_or_example_uses_a_retired_word` with `src/**/*.py`; it passes once
   006's sweep is in. A failure is a line 006 missed: fix it in this slice as a docstring
   edit (006 has landed, so the file is free).

Done: `uv run pytest tests/docs -q` green with 006 in; strict build green.

## Parallelism

| Wave | Slices | Shared files |
| --- | --- | --- |
| 1 | S0 | none (alone) |
| 2 | S1, S2, S3, S4, S5, S6 | none: each owns its files above; `mkdocs.yml` and `CONTRIBUTING.md` are S0's then S1's, never concurrent |
| 3 | S7 | merges wave 2 |
| 4 | S8 | after 006 |

Cross-slice contracts inside wave 2: S4's first-map caption follows S3's caption rule
(prescribed above, so it passes S3's test); S1's glossary page passes S2's dotted-path test
(all its paths checked); every slice sweeps the retired words in the files it owns, and S7
proves it.

## Files to touch

`GLOSSARY.md`; `mkdocs.yml`; `.pre-commit-config.yaml`; `CONTRIBUTING.md`; `README.md`
(line 40); `docs/index.md`; `docs/gallery.md`; `docs/README.md`; everything under
`docs/tutorials/` and `docs/how-to/`; `docs/reference/{index,glossary,style-fields,cli,cache-layout,manifest,pigments,brushes}.md`;
`docs/includes/abbreviations.md` (new); `docs/explanation/{index,how-the-wash-works,the-hand-and-the-nib,data-policy}.md`;
`docs/explanation/performance.md` moved to `docs/runbooks/performance.md`;
`examples/route_map.py` (docstrings), `examples/places.toml`, `examples/place_card.py`,
`examples/social_preview.py` (docstrings); `tests/support/site_pages.py` and
`tests/support/glossary.py` (new); `tests/support/docs_images.py` (one docstring);
`tests/docs/` (new package; two files moved in from `tests/architecture/`);
`tests/golden/test_places.py`, `tests/unit/maps/test_example_themes.py` (the key);
the notes S7 deletes and files.

## Files to leave alone

- `src/**`: 006 owns it and executes the spec's src changes; this feature changes no code
  and no docstring there, even where a retired word sits (S8 checks after 006).
- `tests/architecture/**` other than moving the two docs tests out: 006 owns it,
  including `test_site.py` and `test_reference_keys.py`.
- `docs/reference/{pyntpot,ink,letters,maps}.md` and `docs/explanation/references.md`:
  006 fixes their dotted paths with its renames.
- `docs/features/ink-public-wash-options.md` (#73) and every other note not named above.
- Every example's code lines, `tests/golden/**` pins and masters,
  `tests/golden/make_docs_images.py`, the image registry's entries: no image moves or is
  added.
- `docs/decisions/**`: no ADR changes; accepted ADRs are history.
- `specs/001` to `specs/006`.
- `CHANGELOG.md`: drafted at release from the squash subject and Changelog lines.

## Risks

- **Every-use underline.** `abbr` marks every occurrence, not the first; only distinctive
  forms get a tooltip, and the everyday-word list guards it.
- **Concurrent edits with 006** on `tests/architecture/test_tutorials.py` or
  `test_reference_pages.py`: S0 rebases before moving them.
- **Hidden drift in quoted blocks** on curves, symmetry and fractals, unchecked until
  now: fixed by copying the script's text into the page, never the reverse.
- **Snippets path**: `auto_append` resolves from the working directory, so the build runs
  from the repo root, as CI does; `check_paths: true` fails loudly otherwise.
