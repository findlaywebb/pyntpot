# The route ink's `effect` table is read by nothing

`RouteInk.effect` (`src/pyntpot/maps/style_groups.py`) holds casing, glow, shadow, blend
and adaptive-percentage keys. The route drawer in `maps/compose.py` reads the ink's
`style`, `colour` and `px` only, so no casing, glow or shadow is painted whatever the
table says. The example themes set `casing_px` in `route_inks.ride.effect` and the cards
do not change.

The reader docs list the table under "Fields with no reader" in
`docs/reference/style-fields.md` and do not describe a casing.

Found by the P7 docs review (2026-10-24).
