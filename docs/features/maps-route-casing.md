# The route could be drawn with a casing

GitHub issue: [#104](https://github.com/findlaywebb/pyntpot/issues/104)

**What exists today.** The compose step lays the route ink through its mask with a `blend`
and an `opacity` (`pyntpot.maps.compose.route`). Nothing draws a band of another colour
either side of the line, so a route over a wash of a similar colour has nothing to separate
it from the ground.

**What the feature would add.** A casing: a wider stroke under the route, in its own colour
and width, drawn before the route itself so the route sits inside it. A cream casing reads
as the paper showing through either side of the ink.

**History.** Until ADR 0046 the theme's route ink carried `casing_colour` and `casing_px` in a
free `effect` table that nothing read. The themes held, on the ink that was drawn:
`casing_colour = "cream"` everywhere, and `casing_px = 0.25` in the default, `sepia` and
`winter` themes, `1.2` in `bold`, `1.6` in `pen-and-ink`, `0` elsewhere. Those values were
never seen on a card, so they are a starting point, not a look to restore.

**Possible shape.** Typed fields on `RouteInk` (`casing_colour` as `#rrggbb`, `casing_px` in
display pixels, 0 for none), checked at load like any other key; the compose step draws the
casing from the same mask, dilated by `casing_px`, for the solid line and the pen route
alike. Moves the goldens of any theme that sets a non-zero casing, so it needs its own
golden regeneration.
