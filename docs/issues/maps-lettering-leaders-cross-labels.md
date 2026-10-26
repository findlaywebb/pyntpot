# A leader line is drawn across other names and across the route

The placer in `maps/lettering/` places each callout's name and then draws a leader from the
name to its point. It checks a name's box against the other names' boxes, but it does not
check the leader: a leader may run through another name or across the route near its anchor.
On `docs/images/places/skye.webp` the Dunvegan journal note's leader cuts through "Coral", on
`docs/images/places/y-fenni.webp` several leaders cross one another and the route, and on
`docs/images/places/ambleside.webp` the "Bridge House" leader runs the length of the start
of the route. Nothing orders callouts or positions them to keep leaders short and apart.

Found by the round-2 map critique (2026-10-25). The theme-side changes that were possible
(a card framed on the tour, fewer callouts) were made and shorten the worst of them; the
rule itself is the library's.

To show it: paint any showcase place card from `tests/fixtures/` with its curated callouts
and look at where each leader's segment meets another name's box.

Possible fix: after a name is placed, reject a position whose leader segment meets another
placed name's box, or the route within a few pixels of its anchor, and try the next
candidate position. The lettered goldens and docs images move, so it needs a regeneration
window of its own with an ADR.
