# Names are lettered under a river's stroke, a road, or a lake blob

GitHub issue: [#52](https://github.com/findlaywebb/pyntpot/issues/52)

Two placements overlap something that hides part of the name:

- A river name written along the water ("Cherwell" on the Oxford card) can sit on its own
  river's stroke, which paints over the first letter.
- "Magdalen Bridge" on the Oxford card is lettered across three roads, which a city theme
  with `roads = "all"` draws densely; the placer's road penalty is the same as in a
  village.

Found by the round-2 map critique (2026-10-25).

A third, "Afon Arddu" on the Yr Wyddfa card under a small lake, is fixed: a name set flat
is now priced on the lakes and watercourse strokes under it and its backing wash
(`maps.lettering.placement_water`), and a river's flat name may be seated beside any point
of its own course. A name set along a line is not priced on the water yet.

To show it: paint the Oxford place card from `tests/fixtures/` and look at those two names.

Possible fix: offset an along-water label clear of its stroke width, price the water for
a name set along a line as `water_cost` does for a flat one, and scale the road penalty by
how many roads the style draws.
