# 007 — tasks

Slices and their files are in `plan.md`. S1 to S6 run in parallel after S0; S7 after them;
S8 after feature 006 has merged. No slice edits `src/`; nothing under
`tests/architecture/` moves or changes before S8. The PR stays a draft until S8.

## S0 — Scaffold and site shape

- [x] `tests/docs/` package created; nothing under `tests/architecture/` touched (the two docs tests move in S8).
- [x] Red: `tests/docs/test_site_pages.py` for the helper API.
- [x] `tests/support/site_pages.py`: pages, exclusions, nav, fenced blocks (indented fences; marker is the nearest non-blank line above), prose, links, resolve, resolve_dotted.
- [x] Red: `tests/docs/test_nav.py` (section index order by exact section, first occurrence; performance log off the site; anchors validated before `nav:`; `includes/` excluded).
- [x] `mkdocs.yml`: Painting with Python and How-to nav order, no performance page, `includes/` excluded, `validation: anchors: warn`.
- [x] `performance.md` to `docs/runbooks/`; Explanation index, `docs/README.md`, `CONTRIBUTING.md` repointed.
- [x] prek `docs-tests` hook; time measured.
- [x] Gate and strict build green.

## S1 — Glossary (#65)

- [x] Red: `tests/docs/test_glossary.py` (parse; the real file: each Say instead ends in a term, every In-the-code name resolves, no `’` on site pages; generated files; mkdocs config).
- [x] `tests/support/glossary.py`: parse, plain, anchor, glossary page, abbreviations, main.
- [x] `GLOSSARY.md` in three sections with every row of the plan's table and the spec's Meanings; six retired words.
- [x] Generated `docs/reference/glossary.md` and `docs/includes/abbreviations.md` (a blank line between definitions).
- [x] `mkdocs.yml`: `abbr`, `pymdownx.snippets` auto_append, `content.tooltips`.
- [x] Generated page carries the GitHub link the existing pointer test checks (test file untouched); reference index line; `CONTRIBUTING.md` glossary paragraph.
- [x] "brush sheet", "style group" and "vector layers" rows keep `main`'s meaning (006's facts wait for S8).
- [x] Strict build green; tooltips render (glossary, a tutorial, the maps API page) and none inside code.
- [x] Strict build time measured before and after and stated in the commit message; after is under 5 s.

## S2 — Reference truth (#163)

- [ ] Red: `tests/docs/test_docs_imports.py` (imports, from claims, dotted paths).
- [ ] Red: `tests/docs/test_reference_values.py` (style-field rows, synopsis, pigments, brushes).
- [ ] Style-field group lines true on both sides of 006 (package only where exported today; `RouteInk`, `LetteringPolicy` as the code has them); reading-the-tables bullet; route ink `style` row; nib plate.
- [ ] Brush tables imported from `pyntpot.ink.brush` (S8 repoints).
- [ ] `cli.md` synopsis equals the parser's usage.
- [ ] Cache layout: nib plate, trace; manifest, pigments, brushes: map for the picture.
- [ ] Gate and strict build green.

## S3 — Gallery and captions (#162)

- [ ] Red: `tests/docs/test_captions.py` (script, figure and theme, label lists equal a tuple of the script, names).
- [ ] Red: `tests/docs/test_gallery.py` (every registered image shown, nav order).
- [ ] Nib-angles caption corrected (#162).
- [ ] Gallery's "Map from the command line" moved to after "Write a theme" (nav order).
- [ ] Three vector-drawing stages and the glyph sheet added to the gallery.
- [ ] Landing-page and data-policy captions name their themes.
- [ ] Landmark and map wording in the three files.
- [ ] Gate and strict build green.

## S4 — Tutorials (#172)

- [ ] Red: `tests/docs/test_tutorial_quotes.py` (every tutorial page's marked blocks verbatim; every python block marked); `tests/architecture/test_tutorials.py` untouched and green.
- [ ] Red: `tests/docs/test_tutorial_paths.py` (Next lines, lead-on links).
- [ ] `pictures.md` blocks marked and verbatim (`scene.inside`, `scene.sheet`, 8-space indent, prose says `scene.inside`); any drift on curves, symmetry, fractals fixed in the page.
- [ ] `Next:` line on all nine pages.
- [ ] Lead-on links on the seven non-index pages; rung references link their rungs.
- [ ] Ambleside in the watercolour tutorial's Where next; "seven rungs"; README line 40.
- [ ] First map's "Paint it in the Ambleside theme" section with the registered image.
- [ ] `examples/route_map.py` docstrings and the quoted block in step.
- [ ] Gate and strict build green.

## S5 — Terminology sweep

- [ ] Red: places tests read the `landmarks` key (the two `"callouts"` key strings only; 006's S9 owns their comments, docstrings, test name and local).
- [ ] `examples/places.toml` key, `place_card.py` and `social_preview.py` docstrings and comments say landmarks; `tests/support/docs_images.py` untouched.
- [ ] How-to pages: landmark, route ink style, map for the picture, track.
- [ ] The hand and the nib: centreline trace.
- [ ] `self-host-providers.md` protocols sentence left for S8; no sentence about importing `Landmark` (S8 adds it).
- [ ] Gate, places golden test and strict build green; no golden moved.

## S6 — The wash essay (#176)

- [ ] Red: `tests/docs/test_docs_signatures.py`.
- [ ] Line 32 signature; the four behaviours stated truly with no export claim or module path; feature-note link gone.
- [ ] Gate and strict build green.

## S7 — Integration

- [ ] S1 to S6 merged; every red the merge raises fixed in the page it names and listed in the PR.
- [ ] `tests/docs/test_retired_words.py` green over pages, README and examples.
- [ ] `tests/docs/test_docs_commands.py`: fenced commands and inline `uv run python examples/` spans; every `pyntpot` command parses; every example command's options are the script's; extractor helper tests and non-vacuity assertions.
- [ ] Remaining `card` on site pages listed in the PR and checked against the glossary.
- [ ] Notes for #162, #163, #65, #172 and #176 deleted; links to them repointed, except in `docs-missing-how-tos.md` and `docs-examples-housekeeping.md` (S8).
- [ ] Out-of-scope notes and issues filed (the #174 paragraph and comment are S8's).
- [ ] Full suite, `prek run --all-files` and strict build green; no golden moved.
- [ ] Diff reviewed against the plan; draft PR opened closing #65, #162, #163, #172 and #176.

## S8 — After feature 006

- [ ] Rebase on `main` with 006 (plan reconciled at `a7d664d`); `GLOSSARY.md`, `test_example_themes.py:70` and any `test_places.py` hunk resolved as S8 step 1 says; only the expected reds (route ink and lettering group lines).
- [ ] `test_tutorials.py`, `test_reference_pages.py`, `test_readme.py` and `test_docs_images.py` moved to `tests/docs/`; `test_how_to_commands.py` deleted; subsumed verbatim test and `test_every_run_command_names_an_existing_script` dropped; "eighth rung" docstring fixed; nib plate test renamed; `examples/brush_sheet.py` and `tests/support/docs_images.py` docstrings repointed; path grep clean outside `specs/`, `docs/issues/`, `docs/decisions/`.
- [ ] `test_reference_values.py` imports the brush tables from `pyntpot.ink.brush_sheet`.
- [ ] Red: group line requires `, from` an exporting package (#163). Green: `WashStyle` from `pyntpot.ink`, seven map groups from `pyntpot.maps`, `RouteInkStyle`, `LetteringStyle`; bullet and keyword-only sentence.
- [ ] Wash essay (#176): `WashOptions`, `separated`, `fluid_modulate` from `pyntpot.ink`; from-claim test shown to guard them.
- [ ] Red: glossary cells name the exported name where there is one. Green: cells swapped; 006's three rows in the new format; files regenerated.
- [ ] Red: repository links (`blob/main/` files, `tree/main/` directories) exist on the branch. Green: `self-host-providers.md` protocols; landmarks how-to names `Landmark`; `docs/architecture.md` states ADR 0068's rule.
- [ ] `docs-missing-how-tos.md` and `docs-examples-housekeeping.md` drop the lead-on note; #174 paragraph and comment.
- [ ] Retired-word scan extended to `src/` and `tests/`, green on arrival after 006's S9 (non-vacuity shown); any `tests/` miss fixed here; any `src/` miss reported to 006, not edited.
- [ ] Full gates green; PR marked ready.
