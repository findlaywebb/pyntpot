# The route could be drawn with a glow

GitHub issue: [#105](https://github.com/findlaywebb/pyntpot/issues/105)

**What exists today.** The compose step lays the route ink through its mask with a `blend`
and an `opacity` (`pyntpot.maps.compose.route`). Nothing softens the ground round the route,
so on a dark or busy wash the line has no halo to lift it.

**What the feature would add.** A glow: a soft, blurred band round the route, lighter than
the ground, at a given width and opacity, drawn under the route.

**History.** Until ADR 0045 the theme's route ink carried `glow_px` and `glow_opacity` in a
free `effect` table that nothing read. The default, `sepia` and `winter` themes set
`glow_px = 2.5` and `glow_opacity = 0.8` on the ink that was drawn; the others set 0. The
P7 critique (`specs/001-port/research/p7/critique/maps.md`) read the default's route as
"glowing magenta" from its colour alone, so a painted glow may not suit a watercolour card;
weigh that before adding it.

**Possible shape.** Typed fields on `RouteInk` (`glow_px` in display pixels, `glow_opacity`
from 0 to 1, 0 for none); the compose step blurs the route's mask by `glow_px` and lays the
paper colour through it at `glow_opacity` before the route. Moves the goldens of any theme
that sets a glow.
