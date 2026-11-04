# 007 diff review (fresh context)

**Verdict: FIX** (one item, PR metadata only; the branch content is ready)

Reviewed: `git diff origin/feat/006-one-public-surface...HEAD` at `2c455b8` (006 at `702c1b4`),
against `spec.md`, `plan.md` and `tasks.md`.

Verified locally:

- `uv run pytest -q tests/docs`: 167 passed.
- `uv run --locked --group docs mkdocs build --strict`: green, "Documentation built in 4.33 seconds" (limit 5 s).
- `ruff check` and `ty check` on `tests/docs tests/support`, and `lint-imports`: clean.
- `git diff --numstat`: no binary file changed, so no golden or docs image moved. `git diff --name-only`: no `src/` path.
- Every Meaning in the spec's "Canonical terms" table equals the `GLOSSARY.md` Meaning
  verbatim (35 rows, checked by script; `ink pad` sits in the contributor section).
- Mutations, each reverted straight after (tree clean afterwards). Each one failed the test named:
  - nib-angles caption `38` changed to `30` and `0.52` to `0.5` → `test_every_label_list_in_a_caption_is_a_tuple_of_its_script`
  - wash essay back to `wash(cover, sheet, base, pool)` → `test_a_quoted_signature_lists_every_parameter`
  - `WashOptions`, from `pyntpot.maps` → `test_every_from_claim_names_an_exported_name`
  - `--margin-m` dropped from the `cli.md` synopsis → `test_the_synopsis_is_the_parser_usage`
  - `WashStyle` from `pyntpot.maps`, and `, from` removed from the `RouteInkStyle` line → `test_every_group_line_names_its_dataclass`
  - a `GLOSSARY.md` edit with no regeneration → `test_the_glossary_page_is_generated`
  - "callout" added to a how-to → `test_no_page_or_example_uses_a_retired_word`
  - one line inserted into a quoted block on `pictures.md` → `test_every_marked_block_on_every_tutorial_page_is_verbatim[painting-with-python/pictures.md]`
  - one painting-with-python image removed from the gallery → `test_the_gallery_shows_every_registered_image_but_the_site_chrome`

## Must fix

1. **The PR #187 body and title are stale and lack the `Closes` lines the spec requires.**
   The spec's "Whole feature" criterion says the body carries `Closes #65`, `Closes #162`,
   `Closes #163`, `Closes #172` and `Closes #176`. The body still reads "S8 waits for
   feature 006", "#163 (partly, finished in S8)" and "Closes: listed when it leaves draft",
   and it has no Changelog section. The title, "docs(docs): tell the truth in the docs and
   define terms where they are used", is not the spec's title,
   `docs(docs): one glossary shown in place, and docs tests that check what pages say`.
   Fix: before marking ready (tasks.md's last line), rewrite the body. List the five
   `Closes #N` lines. Paste the spec's nine Changelog lines under "Changelog". Add the gate
   results above (167 docs tests, strict build 4.33 s). List the remaining "card" uses on
   site pages, as S7 promised. Set the title to the spec's, or change the spec's title to
   match the PR, so the changelog draft and the spec agree. It also overstates one check:
   "every one shown is registered" holds only for captioned images, through
   `test_every_caption_names_the_script_that_paints_its_image`.

## Acceptance criteria

All met in the branch content. Evidence:

- Glossary layout, sections and Meanings: `GLOSSARY.md`; `tests/docs/test_glossary.py`
  `TestTheGlossary` and `TestParse`; verbatim Meanings checked by script (above).
- Tooltip forms are unique and none is an everyday word: `test_tooltip_forms_are_unique_and_not_everyday_words`.
- The generated page and abbreviations, with byte-for-byte drift checks:
  `TestGeneratedFiles::test_the_glossary_page_is_generated`, `test_the_abbreviations_are_generated`.
  `includes/` is excluded from the site: `tests/docs/test_nav.py::test_the_includes_directory_is_not_a_site_page`.
  The `mkdocs.yml` settings: `test_the_site_underlines_tooltip_forms`.
- Retired words across pages, README, examples, `src/` and `tests/`: `tests/docs/test_retired_words.py`.
- `validation: anchors: warn`: `test_nav.py::test_the_strict_build_validates_anchors`. The
  strict build finishes in 4.33 s, under 5 s.
- Style-field group lines (with `, from` required after S8), rows, defaults and types:
  `tests/docs/test_reference_values.py::TestStyleFieldTables`.
  The CLI synopsis: `TestCliSynopsis`. Pigment tables: `TestPigmentTables`. Brush tables: `TestBrushTables`.
- Imports, from-claims and dotted paths: `tests/docs/test_docs_imports.py`.
- Nib-angles caption: `docs/gallery.md:239`. Captions: `tests/docs/test_captions.py`.
  Gallery shows every image and follows nav order: `tests/docs/test_gallery.py`.
- Tutorial quotes are verbatim and every python block is marked: `tests/docs/test_tutorial_quotes.py`.
  `Next:` lines and lead-on links: `tests/docs/test_tutorial_paths.py`.
  Index order and nav order: `test_nav.py::test_every_section_index_lists_its_pages_in_nav_order`.
- Rung references link real headings (`pictures.md:70`, `vector-drawing.md:77`,
  `curves.md:204`), and the strict build validates the anchors. The watercolour tutorial's
  Where next names Ambleside (`paint-a-watercolour.md:710`).
- The Ambleside theme section: `first-map.md:171-189`. It shows the registered
  `images/places/ambleside.webp`, and the command's options are the script's options.
- Performance runbook: moved to `docs/runbooks/performance.md`, absent from the nav, and
  linked from no site page (`test_nav.py`); `CONTRIBUTING.md:54` points at it.
- Wash essay: `how-the-wash-works.md:33-34, 129-136`, checked against the code. `wash` has
  `options: WashOptions | None = None`. `blooms`, `wet` and `bleed_*` are `WashOptions`
  fields. `separated` and `fluid_modulate` take `style: WashStyle`. The feature-note link is gone.
- Commands: `tests/docs/test_docs_commands.py`. Repository links: `tests/docs/test_docs_links.py`.
- Text handed over from 006's plan: `self-host-providers.md`, `letter-your-own-landmarks.md`
  ("`Landmark`, from `pyntpot.maps`") and `docs/architecture.md`, which states ADR 0068's
  rule and cites `tests/architecture/test_public_signatures.py` (that file exists).
- Notes:
  - Deleted: #65 `docs-glossary-in-place.md`, #162, #163 and #172 `docs-tutorials-lead-on.md`.
    The #176 note was created and deleted on this branch, so the diff does not show it.
    No surviving reference to any of them outside `specs/`.
  - Ten follow-up notes (`docs/issues/*` x6, `docs/features/*` x4) link #177 to #186 on
    line 2. Each issue is open, has the same title as its note, and carries a "Full note:"
    link to the note on `main`.
  - The #174 paragraph is folded into `docs-examples-housekeeping.md`.

## Nice to have

1. `GLOSSARY.md`, the "map" row says "The maps side's word, which `ink` and `letters` never
   use". That is not quite true: `src/pyntpot/ink/io.py:47` ("a map's paper and wash"),
   `ink/noise.py:27` ("a map plate") and `ink/pigment.py:6,79` ("map roles", "map style")
   use it. The spec fixes the Meaning text, so either add these lines to
   `docs/issues/maps-card-means-the-frame.md` (#178) for a later `src/` sweep, or amend the
   spec and the row to "which `ink` and `letters` do not use for the picture".
2. `tests/docs/test_docs_commands.py:30`: `_USAGE = ^pyntpot (map )?\[` skips only the root
   and `map` usage lines. A second subcommand would put its synopsis line through the
   parser, and the test would fail spuriously. Use `^pyntpot (\w+ )?\[`.
3. `tests/docs/test_reference_pages.py:83`: the moved file's `parametrize` has no `ids=`,
   which CLAUDE.md requires. Its class docstring "The six reference pages and the glossary
   pointer" is stale: the glossary is now a full generated page. Both predate this branch,
   but the branch moved the file.
4. `tests/docs/test_glossary.py`: 18 test methods have no `-> None` or parameter
   annotations, unlike every other new test file.
5. `docs/how-to/self-host-providers.md`: "take any provider that satisfies `Features` …
   or `Elevation`" reads as if one provider will do. `fetch` takes one of each. Suggested
   wording: "a features provider that satisfies `Features` … and an elevation provider
   that satisfies `Elevation` …".
6. Painting with Python's order (Curves, Symmetry, Fractals, Pictures, Vector drawing) is
   enforced only as nav, index and gallery agreeing. Moving the nav and the index together
   would pass. If that order matters, pin it as a literal in `test_nav.py`.
7. The strict build takes 4.33 s against a 5 s budget. Note the margin in the PR, so the
   next site addition that adds snippet work measures it.
8. `test_docs_signatures.py` flags any backticked call with bare-identifier arguments, which
   is stricter than the spec's "whose arguments are all parameter names of it". That is
   fine, but the module docstring could say so.
