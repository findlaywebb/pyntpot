# A leg the route retraces is drawn as parallel strokes

GitHub issue: [#58](https://github.com/findlaywebb/pyntpot/issues/58)

When a route goes out along a road and comes back along it, `maps/strands.py` spaces the
strands apart so the two legs do not lie on one another. A route that retraces a leg more
than twice, or a leg a few metres off the road on the way back, ends as three near-parallel
strokes with the road showing between them. On the Skye card the Armadale leg is drawn three
times and the Dunvegan spur twice. The Oxford card's out-and-back to Magdalen Bridge reads
as one stroke, so the case is the repeated retrace, not the single one.

Found by the round-2 map critique (2026-10-25); the first critique round flagged parallel
lines in the same family.

To show it: paint `docs/images/places/skye.webp` from `tests/fixtures/skye/` and look at the
Armadale leg.

Possible fix: before spacing strands, merge segments of the route that lie within a few
pixels of one another and are walked more than once into one drawn stroke. The route
goldens and docs images move, so it needs a regeneration window of its own with an ADR.
