# The wash essay says `wash` takes only a body and a pool

GitHub issue: [#TBD](https://github.com/findlaywebb/pyntpot/issues/TBD)

Area: docs (explanation).

`docs/explanation/how-the-wash-works.md`, under "What the figures leave out", says: "The
public `wash` takes a body and a pool and nothing else, so none has a figure here."

That is not what `wash` takes. Its signature is
`wash(cover, sheet, base, pool, options=None)`: a coverage mask, the sheet, the body's
density, the pool's density and an optional `WashOptions`. The options hold the edge's
wobble and dryness, the rim's width, the grain, the tooth, a shared wet area with its
bleed, the flow rim, pit granulation and backruns. Two of the four behaviours the section
then lists, backruns and bleed, are fields of `WashOptions`. The other two, pigment
separation and the shallow-water pass, are not `wash`'s at all: they are separate steps
(`separated` and `fluid_modulate`) that the map painter runs.

The same page also quotes the signature short, at the start of "The body":
"`wash(cover, sheet, base, pool)` takes the mask and returns a density."

And it ends the section with a link to the feature note
`docs/features/ink-public-wash-options.md` for "what exposing them would take", a roadmap
pointer on a page that should state what the code does.

Why it matters: a reader who looks at the API reference sees `options: WashOptions` in
the rendered signature and is told by the essay that it does not exist.

Possible fix: quote the full signature; say that backruns and bleed are fields of the
optional `WashOptions` the map painter builds from a theme's `[wash]` group, and that
pigment separation and the shallow-water pass are steps of the painter; drop the feature
note link. Word it so it stays true whether or not `pyntpot.ink` exports `WashOptions`.
