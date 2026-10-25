# Names are lettered under a river's stroke, a road, or a lake blob

Three placements overlap something that hides part of the name:

- A river name written along the water ("Cherwell" on the Oxford card) can sit on its own
  river's stroke, which paints over the first letter.
- "Magdalen Bridge" on the Oxford card is lettered across three roads, which a city theme
  with `roads = "all"` draws densely; the placer's road penalty is the same as in a
  village.
- "Afon Arddu" on the Yr Wyddfa card has its first letters covered by a small lake painted
  after the label's ground was chosen: small water polygons are not among the placer's
  obstacles.

Found by the round-2 map critique (2026-10-25).

To show it: paint the Oxford and Yr Wyddfa place cards from `tests/fixtures/` and look at
those three names.

Possible fix: offset an along-water label clear of its stroke width, include lakes in the
obstacle set, and scale the road penalty by how many roads the style draws.
