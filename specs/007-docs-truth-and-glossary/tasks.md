# 007 — tasks

Slices and their files are in `plan.md`. S1 to S6 run in parallel after S0; S7 after them;
S8 after feature 006 has merged.

## S0 — Scaffold and site shape

- [ ] Move `test_tutorials.py` and `test_reference_pages.py` from `tests/architecture/` to `tests/docs/`.
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
- [ ] Glossary pointer test removed; reference index line; `CONTRIBUTING.md` glossary paragraph.
- [ ] Strict build green; tooltips render and none inside code.

## S2 — Reference truth (#163)

- [ ] Red: `tests/docs/test_docs_imports.py` (imports, from claims, dotted paths).
- [ ] Red: `tests/docs/test_reference_values.py` (style-field rows, synopsis, pigments, brushes).
- [ ] Style-field group lines in the B-neutral form; reading-the-tables bullet; route ink `style` row; nib plate.
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

- [ ] Red: every tutorial page's marked blocks verbatim; every python block marked.
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
- [ ] Gate, places golden test and strict build green; no golden moved.

## S6 — The wash essay (#TBD)

- [ ] Red: `tests/docs/test_docs_signatures.py`.
- [ ] Line 32 signature; the four behaviours stated truly; feature-note link gone.
- [ ] Gate and strict build green.

## S7 — Integration

- [ ] `tests/docs/test_retired_words.py` green over pages, README and examples.
- [ ] Notes for #162, #163, #65, #172 and the wash defect deleted; links to them repointed.
- [ ] Out-of-scope notes and issues filed; #174 note extended and commented.
- [ ] Full suite, `prek run --all-files` and strict build green; no golden moved.
- [ ] Diff reviewed against the plan; PR opened closing #65, #162, #163, #172 and the wash issue.

## S8 — After feature 006

- [ ] Rebase on `main` with 006; docs tests read what changed.
- [ ] Group lines name the exporting package and new dataclass names.
- [ ] Wash essay names `WashOptions`'s package if exported.
- [ ] Glossary cells use 006's exported names; files regenerated.
- [ ] Retired-word scan covers `src/`, green.
