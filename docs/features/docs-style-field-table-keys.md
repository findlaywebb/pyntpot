# The style-fields page could list the keys of its table fields

GitHub issue: [#TBD](https://github.com/findlaywebb/pyntpot/issues/TBD)

**What exists today.** `docs/reference/style-fields.md` shows eight fields only as
`table`, with "Its keys and values are in `src/pyntpot/maps/themes/default.toml`":
`pigment_transparency`, `separation_pigments`, `river_curve`, `brushes`,
`brush_width_px`, `brush_overrides`, `cover_cfg` and `pigments`. A theme author has to
open the default theme to learn which keys a table takes.

**What the feature would add.** Each table field's keys (line or cover classes, pigment
keys) and their default values on the page, as a nested list or a sub-table.

**Possible shape.** The docs tests already compare each row with the code; the same check
would compare each listed key and value with the default style, so the page cannot drift
from `default.toml`.

**Related.** `maps-theme-missing-keys-take-dataclass-defaults.md` (#158).
