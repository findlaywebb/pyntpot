# The route could be drawn with a casing

GitHub issue: [#104](https://github.com/findlaywebb/pyntpot/issues/104)

**What exists today.** The model and the primitive are in. `pyntpot.ink.casing` takes a `Casing`
(width, colour, strength), and a theme sets a casing on any line class, the route included,
through `line_effects` and `effect_presets` (`EffectStack` from `pyntpot.maps`; the built-in
presets are `cased`, `halo` and `lifted`). The route's stack is laid at compose from the
route's mask, for the solid line and the pen route alike. Every default is off, so no theme
paints a casing yet.

**What the feature would add.** A casing: a wider stroke under the route, in its own colour
and width, drawn before the route itself so the route sits inside it. A cream casing reads
as the paper showing through either side of the ink.

**History.** Until ADR 0046 the theme's route ink carried `casing_colour` and `casing_px` in a
free `effect` table that nothing read. The themes held, on the ink that was drawn:
`casing_colour = "cream"` everywhere, and `casing_px = 0.25` in the default, `sepia` and
`winter` themes, `1.2` in `bold`, `1.6` in `pen-and-ink`, `0` elsewhere. Those values were
never seen on a card, so they are a starting point, not a look to restore.

**What remains.** Figures that show the route with and without a casing, the how-to guide and
the reference, and any packaged theme that turns one on (which moves that theme's pinned
images and so needs its own golden regeneration). These come in the follow-up spec
(`specs/009a-line-effect-figures-and-galleries/`), which closes this issue. The theme guide
([Write a theme](../how-to/write-a-theme.md)) names the keys.
