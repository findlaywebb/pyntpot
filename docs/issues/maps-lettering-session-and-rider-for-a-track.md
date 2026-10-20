# Lettering says "session" and "rider" for a track

Area: `maps` lettering.

pyntpot has no notion of what a track records (ADR 0027), but sixteen `src` lines call
the track a "session" or the person on it a "rider". Eleven are docstrings and
comments. Five are `Label.why` values: `"where the session began"` and the other
session values in `maps/lettering/picks.py` and `picks_roads.py`, and
`"the rider's own place"` in `picks.py`. `Label.why` is text the upstream consumer
reads into its route chart, so changing a value changes what it shows; the choice is
policy, not a fact the code settles. `Label` is in no `__all__` (ADR 0026).

The rename of the other sport words in docstrings and comments ("run", "ride",
"rider", "runner") leaves these lines alone for that reason.

To show it: `grep -rnIwi session src/pyntpot` prints 15 lines, and
`grep -rnIw "rider's" src/pyntpot` prints the `why` value in `picks.py`.

Awaiting a maintainer decision. Readings: (1) reword all sixteen, the five `why` values
included, and tell the consumer what it will read; (2) reword the eleven docstring and
comment lines only, by the same rule as the other sport words, and keep the `why`
values as they are.
