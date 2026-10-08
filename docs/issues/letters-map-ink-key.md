# The letters layer keys an ink as "map"

`pyntpot.letters.nib` (three sites) and `pyntpot.letters.setting` (two sites) use the
string `"map"` as an ink key. It names the default label ink: `_ink_colour` in
`letters/nib.py` resolves `"map"` to `NibStyle.label_ink` ("The ink the lettering is
written in"), `Setting.ink` and `Mark.ink` default to it, an unknown ink that is not a hex
colour falls back to it, and `maps.lettering_marks._ink` gives it to every label kind
without an ink of its own in `KIND_INK` (everything but rivers and markers). `letters`
sits below `maps` and knows no map (`maps -> letters -> ink`), and the maintainer's answer
to the sheet and map question keeps "map" for the maps side only. The docs pass reworded
every "map" in `ink` and `letters` prose but left this value: it is executable, so
changing it is a code change, and the key may cross the public surface on `Mark`, where an
upstream caller could read it.

To show it: `grep -rnIw '"map"' src/pyntpot/letters` prints five lines.

Possible fix: rename the key to what it resolves to, for example `"label"`, matching
`NibStyle.label_ink`. No ink key is called `"label"` today (the named inks are `"map"`,
`"route"`, `"water"` and `"in_water"`); the string `"label"` at `letters/nib.py:127` is a
`brush_overrides` key passed to `brush_from_id`, a separate namespace, so the two do not
collide, though a grep for `"label"` finds both. Rename it in `letters` and in every
`maps` module and test that writes or reads it, with G-self proving no pixel moved; after
P8 records what the upstream reads.
