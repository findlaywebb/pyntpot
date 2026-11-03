# The style-fields page names import paths that fail, and the reference tests only check names

GitHub issue: [#163](https://github.com/findlaywebb/pyntpot/issues/163)

Area: docs (reference), with tests (architecture).

`docs/reference/style-fields.md` says, under each group's heading, which package the
group's dataclass comes from. For 8 of the 13 groups the import fails:

- `WashStyle`, "from `pyntpot.ink`": not exported (it lives in `pyntpot.ink.style`).
- `CardStyle`, `RibbonStyle`, `CoverStyle`, `RouteStyle`, `RouteInk`, `LetteringPolicy`
  and `BasemapStyle`, "from `pyntpot.maps`": none is exported. They live in
  `pyntpot.maps.style_groups`, so `from pyntpot.maps import CardStyle` raises
  `ImportError`.

Only `PaperStyle` and `BrushStyle` (from `pyntpot.ink`) and `FaceStyle`, `NibStyle` and
`HandStyle` (from `pyntpot.letters`) import as the page says.

The page passes its gate because `tests/architecture/test_reference_pages.py` checks that
names appear, not that what the page says about them is right. For style-fields it checks
that each field is named in backticks and each group has a heading; it never compares the
Type or Default cells or the import line. The same holds for `cli.md`: the test checks that
each option and help text appears somewhere on the page, so the synopsis line
`pyntpot map [-h] -o OUTPUT --cache CACHE --contact CONTACT [--style STYLE]
[--no-attribution] track` passes while omitting `--margin-m`, which the parser's own usage
line includes and the page's `--margin-m` section documents. The `pigments.md` and
`brushes.md` checks are presence checks too.

Possible fix: correct the import lines now (or export all 13 groups, an API change), and
the `cli.md` synopsis. Then make the tests check content: resolve each "`X`, from
`pyntpot.Y`" line, compare each table row's cells with `Style.default()`, and compare the
synopsis with `build_parser()`'s usage; or generate the tables at build time.
