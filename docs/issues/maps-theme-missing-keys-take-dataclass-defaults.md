# A theme that leaves out a key paints with the dataclass default, not the default theme

GitHub issue: [#158](https://github.com/findlaywebb/pyntpot/issues/158)

Area: maps (style), with the ink style groups.

`Style.from_toml` in `src/pyntpot/maps/style.py` reads the TOML and hands it to
`model_validate`. The `_reject_unknown_group_keys` validator rejects a key a group does not
have, and a missing group fails validation, but a key left out of a group is accepted
without a word: the group's dataclass fills it from its own field default. Those defaults
are not the packaged default theme's values.

Comparing each group's no-argument dataclass with `Style.default()`, 25 fields differ:

- `paper` (`PaperStyle`, `ink/style.py`): `km_glazing`, `paper_fibre`.
- `wash` (`WashStyle`, `ink/style.py`): 14 fields, among them `wet_bleed`, `flow_rim`,
  `blooms`, `pigment_separation` and `fluid_pass`.
- `brush` (`BrushStyle`, `ink/brush_style.py`): `ink_starve`, `dry_directional`,
  `pen_starve`, `brush_organic`, `ink_joins`, `stroke_smooth`.
- `basemap` (`BasemapStyle`, `maps/style_groups.py`): `landmarks`, `landmark_max`,
  `generalise`.

`RouteInkStyle()` cannot be built with no arguments at all. The other groups agree.

So a user who trims their copy of `default.toml` to the keys they changed gets a flatter
map (no blooms, no wet bleed, no Kubelka-Munk glazing) with no error and no log line. The
how-to `docs/how-to/write-a-theme.md` says only that `from_toml` "needs every group, and it
rejects a key that a group does not have"; `docs/reference/style-fields.md` says the two
defaults "differ for some fields" without naming them.

The same split reaches engine users: `PaperStyle()`, `BrushStyle()` and `WashStyle()` do not
give the house look, so `composite(..., PaperStyle())` multiplies where a map glazes. The
`NibGroups` docstring in `letters/style.py` suggests building it from no-argument groups.

Evidence: deleting `wash.blooms` and `paper.km_glazing` from a copy of the default theme
validates cleanly and gives `blooms=False`, `km_glazing=False`; the default theme has
`blooms=True`.

Possible fix: one source of defaults. Either merge a theme over the default theme (the
overrides feature, #80) or reject a missing key as `from_toml` rejects an unknown one; and
make the dataclass defaults equal the default theme, or document each one that differs.
