# The wash options could be public

GitHub issue: [#73](https://github.com/findlaywebb/pyntpot/issues/73)

**What exists today.** `pyntpot.ink.wash.wash` takes a mask, a sheet, a body density, a pool
density and an optional `WashOptions`. The options carry the edge's width, the grain's
strength, the shared wet area and its bleed, the flow rim, granulation that follows the
paper's pits, and backruns. `pyntpot.ink` exports `wash` and not `WashOptions`, so a
caller who stays on public names reaches the body and the pool, and the size of the grain
through `Sheet`. The painter in `pyntpot.maps` sets the rest from the style's wash group
(`WashStyle`). Pigment separation (`pyntpot.ink.wash.separated`) and the shallow-water
pass (`fluid_modulate`) are also reachable only through the painter.

**What the feature would add.** A public way to ask for each of those from `pyntpot.ink`
alone: `WashOptions` and its parts exported, so a script can lay a wash with a flow rim,
bleed, pit granulation or backruns without a basemap. The essay
`docs/explanation/how-the-wash-works.md` could then show each as a figure from the same
seed.

**Why it is not a defect.** The options were written for the painter, and the public wash
is the smaller call the tutorial teaches. Exporting them widens the public API, which is
an ADR (`docs/decisions/0026-widen-the-public-api.md` is the last such).

**Possible shape.** Export `WashOptions`, `Blooms` and `Flow` from `pyntpot.ink` with
the docstrings the module already has, add a stage to `examples/wash_stages.py` for each
option the essay now describes in words, and register its figure.
