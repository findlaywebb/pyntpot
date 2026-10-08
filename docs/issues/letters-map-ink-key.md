# The letters layer keys an ink as "map"

`pyntpot.letters.nib` (three sites) and `pyntpot.letters.setting` (two sites) use the
string `"map"` as an ink key: the ink a mark is stroked in when it belongs to the map
furniture rather than to a route or a label. `letters` sits below `maps` and knows no map
(`maps -> letters -> ink`), and the maintainer's answer to the sheet and map question
keeps "map" for the maps side only. The docs pass reworded every "map" in `ink` and
`letters` prose but left this value: it is executable, so changing it is a code change,
and the key may cross the public surface on `Mark`, where an upstream caller could read
it.

To show it: `grep -rnIw '"map"' src/pyntpot/letters` prints five lines.

Possible fix: rename the key to what `letters` sees (for example the furniture ink), in
`letters` and in every `maps` module and test that writes or reads it, with G-self
proving no pixel moved; after P8 records what the upstream reads.
