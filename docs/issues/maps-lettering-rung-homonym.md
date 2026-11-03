# The lettering's offset ladder calls its steps rungs, as the tutorial does

GitHub issue: [#TBD](https://github.com/findlaywebb/pyntpot/issues/TBD)

Area: maps (lettering).

`GLOSSARY.md` defines a rung as one step of the watercolour tutorial. The span lettering
uses the same word for something else: each side of the route carries a ladder of offsets,
and a span takes the nearest free "rung" (`maps/lettering/spans.py`, "Choose a side and a
rung for every span"; `span_line.py`, "How far off the route a span's first rung sits";
`placement_water.py`, "a name moves a rung further out"). The `rails` parameter counts
them.

One word with two meanings breaks the glossary's one-name-per-concept rule, and a reader
of the lettering code who has read the tutorial meets a false friend.

Possible fix: give the offset step its own glossary term (for example offset step, or
rail, matching the `rails` parameter) and use it in those docstrings and comments. No
behaviour changes.
