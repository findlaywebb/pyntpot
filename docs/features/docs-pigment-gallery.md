# A gallery of every pigment

GitHub issue: [#70](https://github.com/findlaywebb/pyntpot/issues/70)

**What exists today.** The pigments are listed in `docs/reference/pigments.md` as tables
of names, hex values and transparencies, with a pigment card that paints a strip of each
over a bar. The painter's pigments added this round and the map roles sit in separate
tables, and no page shows them all side by side, nor how they mix.

**What the feature would add** (maintainer, 2026-10-25). A gallery of every pigment: a
swatch of each at a few strengths, labelled in the library's hand with its name and its
aliases, and a few glazes of common pairs so a reader sees how they mix. It pairs with
the one pigment registry (`ink-one-pigment-registry.md`), which gives the gallery one list
to paint, and with the brush id gallery (`docs-brush-id-gallery.md`).

**Why it is not a defect.** The pigments are documented and every one paints; the gap is
that the docs never show them all.

**Possible shape.** An example script painting the gallery from the registry, a reference
page, and a test that every registered pigment appears on it.
