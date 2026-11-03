# 007 — tasks

Slices and their files are in `plan.md`. S1 to S6 run in parallel after S0; S7 after them;
S8 after feature 006 has merged. No slice edits `src/`; nothing under
`tests/architecture/` moves or changes before S8. The PR stays a draft until S8.

## S0 — Scaffold and site shape

- [ ] `tests/docs/` package created; nothing under `tests/architecture/` touched (the two docs tests move in S8).
- [ ] Red: `tests/docs/test_site_pages.py` for the helper API.
- [ ] `tests/support/site_pages.py`: pages, exclusions, nav, fenced blocks, prose, links, resolve.
- [ ] Red: `tests/docs/test_nav.py` (section index order, performance log off the site, anchors validated).
- [ ] `mkdocs.yml`: Painting with Python and How-to nav order, no performance page, `includes/` excluded, `validation: anchors: warn`.
- [ ] `performance.md` to `docs/runbooks/`; Explanation index, `docs/README.md`, `CONTRIBUTING.md` repointed.
- [ ] prek `docs-tests` hook; time measured.
- [ ] Gate and strict build green.

## S1 — Glossary (#65)

- [ ] Red: `tests/docs/test_glossary.py` (parse, the real file, generated files, mkdocs config).
- [ ] `tests/support/glossary.py`: parse, plain, anchor, glossary page, abbreviations, main.
- [ ] `GLOSSARY.md` in three sections with every row of the plan's table and the spec's Meanings; six retired words.
- [ ] Generated `docs/reference/glossary.md` and `docs/includes/abbreviations.md`.
- [ ] `mkdocs.yml`: `abbr`, `pymdownx.snippets` auto_append, `content.tooltips`.
- [ ] Generated page carries the GitHub link the existing pointer test checks (test file untouched); reference index line; `CONTRIBUTING.md` glossary paragraph.
- [ ] "brush sheet", "style group" and "vector layers" rows keep `main`'s meaning (006's facts wait for S8).
- [ ] Strict build green; tooltips render and none inside code.

## S2 — Reference truth (#163)

- [ ] Red: `tests/docs/test_docs_imports.py` (imports, from claims, dotted paths).
- [ ] Red: `tests/docs/test_reference_values.py` (style-field rows, synopsis, pigments, brushes).
- [ ] Style-field group lines true on both sides of 006 (package only where exported today; `RouteInk`, `LetteringPolicy` as the code has them); reading-the-tables bullet; route ink `style` row; nib plate.
- [ ] Brush tables imported from `pyntpot.ink.brush` (S8 repoints).
- [ ] `cli.md` synopsis equals the parser's usage.
- [ ] Cache layout: nib plate, trace; manifest, pigments, brushes: map for the picture.
- [ ] Gate and strict build green.

## S3 — Gallery and captions (#162)

- [ ] Red: `tests/docs/test_captions.py` (script, figure and theme, label numbers, names).
- [ ] Red: `tests/docs/test_gallery.py` (every registered image shown, nav order).
- [ ] Nib-angles caption corrected (#162).
- [ ] Three vector-drawing stages and the glyph sheet added to the gallery.
- [ ] Landing-page and data-policy captions name their themes.
- [ ] Landmark and map wording in the three files.
- [ ] Gate and strict build green.

## S4 — Tutorials (#172)

- [ ] Red: `tests/docs/test_tutorial_quotes.py` (every tutorial page's marked blocks verbatim; every python block marked); `tests/architecture/test_tutorials.py` untouched and green.
- [ ] Red: `tests/docs/test_tutorial_paths.py` (Next lines, lead-on links).
- [ ] `pictures.md` blocks marked and verbatim; any drift on curves, symmetry, fractals fixed in the page.
- [ ] `Next:` line on all nine pages.
- [ ] Lead-on links on the six non-index pages; rung references link their rungs.
- [ ] Ambleside in the watercolour tutorial's Where next; "seven rungs"; README line 40.
- [ ] First map's "Paint it in the Ambleside theme" section with the registered image.
- [ ] `examples/route_map.py` docstrings and the quoted block in step.
- [ ] Gate and strict build green.

## S5 — Terminology sweep

- [ ] Red: places tests read the `landmarks` key.
- [ ] `examples/places.toml` key, `place_card.py`, docstrings and comments say landmarks.
- [ ] How-to pages: landmark, route ink style, map for the picture, track.
- [ ] The hand and the nib: centreline trace.
- [ ] `self-host-providers.md` protocols sentence and the landmarks how-to's import sentence left for S8.
- [ ] Gate, places golden test and strict build green; no golden moved.

## S6 — The wash essay (#176)

- [ ] Red: `tests/docs/test_docs_signatures.py`.
- [ ] Line 32 signature; the four behaviours stated truly with no export claim or module path; feature-note link gone.
- [ ] Gate and strict build green.

## S7 — Integration

- [ ] `tests/docs/test_retired_words.py` green over pages, README and examples.
- [ ] Notes for #162, #163, #65, #172 and #176 deleted; links to them repointed, except in `docs-missing-how-tos.md` and `docs-examples-housekeeping.md` (S8).
- [ ] Out-of-scope notes and issues filed (the #174 paragraph and comment are S8's).
- [ ] Full suite, `prek run --all-files` and strict build green; no golden moved.
- [ ] Diff reviewed against the plan; draft PR opened closing #65, #162, #163, #172 and #176.

## S8 — After feature 006

- [ ] Rebase on `main` with 006; `GLOSSARY.md` conflict resolved; only the expected reds (route ink and lettering group lines).
- [ ] `test_tutorials.py` and `test_reference_pages.py` moved to `tests/docs/`; subsumed verbatim test dropped; "eighth rung" and "label plate" docstrings fixed; `examples/brush_sheet.py` docstring repointed.
- [ ] `test_reference_values.py` imports the brush tables from `pyntpot.ink.brush_sheet`.
- [ ] Red: group line requires `, from` an exporting package (#163). Green: `WashStyle` from `pyntpot.ink`, seven map groups from `pyntpot.maps`, `RouteInkStyle`, `LetteringStyle`; bullet and keyword-only sentence.
- [ ] Wash essay (#176): `WashOptions`, `separated`, `fluid_modulate` from `pyntpot.ink`; from-claim test shown to guard them.
- [ ] Red: glossary cells name the exported name where there is one. Green: cells swapped; 006's three rows in the new format; files regenerated.
- [ ] Red: repository links name files on the branch. Green: `self-host-providers.md` protocols; landmarks how-to names `Landmark`; `docs/architecture.md` states ADR 0068's rule.
- [ ] `docs-missing-how-tos.md` and `docs-examples-housekeeping.md` drop the lead-on note; #174 paragraph and comment.
- [ ] Red: retired-word scan over `src/` and `tests/`. Green: test docstrings and one test name fixed; any `src/` miss reported to 006, not edited.
- [ ] Full gates green; PR marked ready.
