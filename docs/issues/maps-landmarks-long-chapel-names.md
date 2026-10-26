# The landmark heuristic offers chapels with names forty characters long

With `landmarks = "all"`, the default, the candidates for a callout are ranked by class and
nearness, and a place of worship ranks beside a museum. On the Lynmouth command-line card
that offers "Living Waters Lynton United Reformed Church", "Saint Mary the Virgin" and
"Lynton and Exmoor Museum", three long names whose leaders converge on the coast, and the
town's own name is not lettered.

Found by the round-2 map critique (2026-10-25).

To show it: paint `docs/images/how-to/command-line.webp` from `tests/fixtures/lynmouth/`.

Possible fix: drop candidate names over about 25 characters, rank places of worship below
landmarks, and always letter the place the route starts in. The landmark picks and the
goldens that carry them move, so it needs a regeneration window of its own with an ADR.
