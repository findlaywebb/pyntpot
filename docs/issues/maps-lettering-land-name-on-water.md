# A land callout can be lettered on a lake

GitHub issue: [#50](https://github.com/findlaywebb/pyntpot/issues/50)

A curated callout for a place on land (a cave, a bridge, a hamlet) is placed on the best free
ground the placer finds, and a water polygon counts as free ground for a name that is not a
water name. On the Ambleside card at 720 pixels a callout for Rydal Cave was lettered inside
Rydal Water, under the lake's own leader, so the lake read as "Rydal Cave". The example's
callouts no longer include it, so the published card does not show the fault, but any theme
that curates a land name near a lake can.

Found by the round-2 map critique (2026-10-25).

To show it: add `{ name = "Rydal Cave", lat = 54.4431789, lng = -2.9965662 }` to
`[ambleside].callouts` in `examples/places.toml` and paint the Ambleside card at 720 pixels
in `examples/themes/ambleside.toml`.

Possible fix: forbid a land name's box on a water polygon, and a water name's box on land,
unless no other position fits; a name that has to go on water takes the water ink.
