# Brushes and pigments could be declared as data

GitHub issue: [#71](https://github.com/findlaywebb/pyntpot/issues/71)

**What exists today.** Brushes are Python dictionaries in `ink/brush.py`
(`BRUSH_TREATMENTS`, `BRUSH_COLOURS`), and pigments are the `PIGMENTS`,
`TRANSPARENCY`, `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY` tables in
`ink/pigment.py`. Adding a brush or a colour means editing the package.

**What the feature would add.** Brushes and pigments declared in data files shipped with
the package (YAML, the theme format of `maps-themes-as-overrides.md`), loaded into the
registries at import, and extendable by a caller or a theme that declares its own brush or
pigment by name.

**Why it is not a defect.** The tables work and are tested; this is about how easily a
user adds to them.

**Possible shape.** `ink/data/pigments.yaml` and `ink/data/brushes.yaml`, read into the one
pigment registry (`ink-one-pigment-registry.md`) and a brush registry; a theme may carry a
`pigments:` and `brushes:` block that adds to them; a test that the shipped data reproduces
today's tables exactly, so no golden moves; the brush and pigment galleries
(`docs-brush-id-gallery.md`, `docs-pigment-gallery.md`) painted from the same data.
