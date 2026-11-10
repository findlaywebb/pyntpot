# The route could cast a shadow

GitHub issue: [#106](https://github.com/findlaywebb/pyntpot/issues/106)

**What exists today.** The model and the primitive are in. `pyntpot.ink.shadow` takes a
`Shadow` (offset, blur, strength, colour) and a theme sets one on any line class, the route
included, through `line_effects` and `effect_presets` (`EffectStack` from `pyntpot.maps`; the
built-in presets are `cased`, `halo` and `lifted`). The route's stack is laid at compose.
Every default is off, so no theme paints a shadow yet.

**What the feature would add.** A shadow: a darkened, blurred copy of the route's mask,
offset by a distance, drawn under the route so the line seems to sit above the paper.

**History.** Until ADR 0046 the theme's route ink carried `shadow_px` and `shadow_blur_px` in
a free `effect` table that nothing read. Every theme set both to 0, so no theme has asked
for a shadow yet.

**What remains.** Figures, the how-to guide and the reference, and any packaged theme that
turns a shadow on (which moves that theme's pinned images and so needs its own golden
regeneration). These come in the follow-up spec
(`specs/009a-line-effect-figures-and-galleries/`), which closes this issue.
