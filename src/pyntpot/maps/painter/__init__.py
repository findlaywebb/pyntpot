"""The plate painter: the phases that lay a basemap down as plates.

Each module is one phase or one piece a phase needs. `job` holds the two values
that cross phases, `PaintJob` (what is painted, with what, and the seeded random
generators the phases share) and `PlateStack` (the arrays one phase writes and a
later one reads). `brushes` builds a plate's brushes, `water` fills the sea and
the lakes, `cover` paints the land cover, and `wood` paints the wood's texture and
dabs. `relief` lays the shaded relief, `fluid` runs the one shallow-water pass over every
trimmed layer, `pen` lays the watercourses, coast and roads as ink and writes the route's
own plate, `ribbon` trims the ground to the ribbon, and `paper` paints the card.
`plates` runs them all in order, writes the plates and the manifest, and is the one
entry point, `paint_plates`.

A phase is `paint_<phase>(job, stack)`: it reads its settings from the style
groups of `job.style` and writes into `stack`. Two return what they lay instead:
`paint_pen(job)` returns the ink layers and `paint_ribbon` the ground and its rim,
for `plates` to composite. This package does not draw labels, fetch anything or
import `maps.lettering`.
"""
