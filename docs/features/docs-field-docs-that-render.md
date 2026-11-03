# Field docs could render where readers look

GitHub issue: [#169](https://github.com/findlaywebb/pyntpot/issues/169)

**What exists today.** The fields of the public engine types are documented with Sphinx `#:`
comments above each field, or, on `Brush`, trailing `# ...` comments. mkdocstrings (griffe),
`help()` and editor hovers read neither, so the API reference shows the class prose and no
field text at all:

| Type | Fields | Documented as |
|---|---|---|
| `PaperStyle` (`src/pyntpot/ink/style.py`) | 22 | `#:` |
| `BrushStyle` (`src/pyntpot/ink/brush_style.py`) | 45 | `#:` |
| `Brush` (`src/pyntpot/ink/brush.py`) | 43 | trailing `#` |
| `NibStyle` (`src/pyntpot/letters/style.py`) | 16 | `#:` |
| `Sheet` (`src/pyntpot/ink/sheet.py`) | 13 | `#:` |

None of the five has an `Attributes:` section. Some `#:` blocks cover several fields at
once (`plate_lossless`, `webp_quality` and `paper_quality` share one), and some `Brush`
fields have no comment. Types that use `Attributes:` (`Basemap`, `Plates`, `NibSurface`,
`NibGroups`) render well. The site test (`tests/architecture/test_site.py`) checks that each
public name is rendered, not that what renders has text. The same `#:` style documents
`WashStyle` (44 fields, beside `PaperStyle`) and the maps style groups
(`src/pyntpot/maps/style_groups.py`, 79 `#:` lines).

**What the feature would add.** Every field of a public type described on its reference
page, in `help()` and in an editor, and a test that keeps it so.

**Possible shape.** A suggestion: move each `#:` block into the class docstring's
`Attributes:` section (or an attribute docstring under the field, which griffe also reads),
one entry per field, splitting shared blocks; then a site test that every field of every
public dataclass has parsed, non-empty text. Docstrings only, so no ADR, no golden and no
docs-image change; the reference pages grow. `src/pyntpot/ink/brush.py` is at 391 of its
400 lines, so giving each `Brush` field a full entry may mean splitting that file first.

**Related.** `docs-variable-effect-grids` (#67): a reader cannot see what a field does
today, in words or in pictures. `maps-public-signature-types` would export the maps style
groups, whose field docs this sweep would then need to cover too.
