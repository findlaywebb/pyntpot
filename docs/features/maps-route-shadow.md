# The route could cast a shadow

GitHub issue: [#106](https://github.com/findlaywebb/pyntpot/issues/106)

**What exists today.** The compose step lays the route ink through its mask with a `blend`
and an `opacity` (`pyntpot.maps.compose.route`). The route lies flat on the card; nothing
offsets a darker copy of it.

**What the feature would add.** A shadow: a darkened, blurred copy of the route's mask,
offset by a distance, drawn under the route so the line seems to sit above the paper.

**History.** Until ADR 0045 the theme's route ink carried `shadow_px` and `shadow_blur_px` in
a free `effect` table that nothing read. Every theme set both to 0, so no theme has asked
for a shadow yet.

**Possible shape.** Typed fields on `RouteInk` (`shadow_px`, the offset in display pixels,
and `shadow_blur_px`, 0 for none); the compose step offsets and blurs the route's mask and
multiplies a dark wash through it before the route. Moves the goldens of any theme that sets
one.
