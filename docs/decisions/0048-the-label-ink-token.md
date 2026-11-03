# 0048 — The label ink token (amends 0008 and 0026)

Status: accepted

The maintainer approved this rename (the stop ADR 0026 requires) on 2026-11-03.

## Context

`letters` named its default ink `"map"`: `Setting.ink` and `Mark.ink` defaulted to it,
`nib_plate` resolved it to `NibStyle.label_ink`, and a mark whose ink was neither a named
token nor a `#rrggbb` colour fell back to it. `maps.lettering_marks` gave it to every label
kind without an ink of its own in `KIND_INK`. `letters` sits below `maps`
(`maps -> letters -> ink`) and knows no map; the glossary keeps "map" for the maps side
only (#41).

ADR 0026 made the four ink keys `"map"`, `"route"`, `"water"` and `"in_water"` tokens, part
of the public surface, and said a rename of `"map"` needs its own ADR. ADR 0008's table
records `Setting`'s signature with `ink="map"`.

## Decision

- The default ink token is `"label"`, named for the field it resolves to,
  `NibStyle.label_ink`. The four tokens are `"label"`, `"route"`, `"water"` and
  `"in_water"`.
- `Setting.ink` and `Mark.ink` default to `"label"`; `nib_plate` resolves `"label"` to
  `NibStyle.label_ink`; an ink nobody chose falls back to `"label"`; `maps` gives
  `"label"` to every kind without an ink in `KIND_INK`.
- There is no deprecation period and no alias. A caller that still passes `"map"` gets
  the label ink anyway, because `"map"` is now an ink nobody chose and so falls back to it:
  its marks paint exactly as before. Only a caller that reads `Setting.ink` or `Mark.ink`
  back and compares it with `"map"` sees the change.
- The string `"label"` that `nib_brushes` passes to `brush_from_id` is a
  `BrushStyle.brush_overrides` key, a separate namespace; the two do not collide.

No pixel moves: the token only names which colour a group of marks is stroked in, and the
colour, the grouping and the order the groups are stroked in are unchanged. The label
plate's cache key (`Cache.lettering_key`) hashes every mark's fields, `ink` among them, so
a label plate cached by an earlier release is stroked again once, to the same pixels.
`Style.digest()`, `base_digest` and `lettering_digest` do not move, and no golden, docs
image or pinned hash changes.

This amends ADR 0026's list of ink tokens and ADR 0008's `Setting` signature
(`ink="label"`). The boundary and the import-linter contracts are unchanged.

## Consequences

- `grep -rnIw '"map"' src/pyntpot/letters` prints nothing.
- A caller comparing `Mark.ink` or `Setting.ink` with `"map"` compares with `"label"`
  instead; one passing `"map"` needs no change, though `"label"` is the token to write.
- Lynmouth goldens and the lettering-heavy docs images repainted byte-identical; the
  pull request carries the compare logs.
