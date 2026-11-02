# Themes could ship inside the package and be chosen by name

GitHub issue: [#77](https://github.com/findlaywebb/pyntpot/issues/77)

**What exists today.** The package ships one theme, `maps/themes/default.toml`,
which `Style.default()` loads. Any other look is a TOML file the caller writes
and loads with `Style.from_toml(path)`, which needs every group present.

**What the feature would add.** A few further themes in the package (for
example pen-and-ink only, faded sepia, bold and bright, winter), chosen by
name from Python and from the `pyntpot map` command line.

**Why it is not a defect.** One default theme is the shipped design. At 0.1 the
other looks are example theme files shown in the gallery and the theme guide
(maintainer, 2026-10-23, P7 research Q-P7), which needs no API change.

**Possible shape.** A `Style.theme(name)` class method and a `--theme` option,
reading `maps/themes/<name>.toml`; a test that every shipped theme loads and
paints the Lynmouth card. An ADR for the public name.
