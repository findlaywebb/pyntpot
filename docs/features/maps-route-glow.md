# The route could be drawn with a glow

GitHub issue: [#105](https://github.com/findlaywebb/pyntpot/issues/105)

**What exists today.** The model and the primitive are in. `pyntpot.ink.glow` takes a `Glow`
(spread, blur, strength) and a theme sets one on any line class, the route included, through
`line_effects` and `effect_presets` (`EffectStack` from `pyntpot.maps`; the built-in presets
are `cased`, `halo` and `lifted`). The route's stack is laid at compose. Every default is off,
so no theme paints a glow yet.

**What the feature would add.** A glow: a soft, blurred band round the route, lighter than
the ground, at a given width and opacity, drawn under the route.

**History.** Until ADR 0046 the theme's route ink carried `glow_px` and `glow_opacity` in a
free `effect` table that nothing read. The default, `sepia` and `winter` themes set
`glow_px = 2.5` and `glow_opacity = 0.8` on the ink that was drawn; the others set 0. The
P7 critique (`specs/001-port/research/p7/critique/maps.md`) read the default's route as
"glowing magenta" from its colour alone, so a painted glow may not suit a watercolour card;
weigh that before adding it.

**What remains.** Figures, the how-to guide and the reference, and any packaged theme that
turns a glow on (which moves that theme's pinned images and so needs its own golden
regeneration). The P7 critique's doubt, that a painted glow may not suit a watercolour card,
is still worth weighing before a packaged theme sets one. These come in the follow-up spec
(`specs/009a-line-effect-figures-and-galleries/`), which closes this issue.
