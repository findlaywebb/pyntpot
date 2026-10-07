# Pigment separation is implemented but has no inventory row

`pyntpot.ink.wash.separated` splits one wash into two pigment layers, a
light one and a heavy one that settles into the paper's pits
(`Sheet.pits(style.separation_gamma)`), with the total density kept. Its
docstring calls it "Curtis' pigment separation", and `WashStyle` carries the
`pigment_separation` switch and its `separation_*` settings. Curtis et al.
1997 is in `design-sources.md`, so this is a technique with a published
originating description and a code site of its own.

The references inventory (`specs/001-port/p6-inventory.md`) has no row for
it: P6.1 admits only the seed rows and the decided terms the plan lists, and
pigment separation is in neither, so the inventory step files it here rather
than adding a row.

Possible fix: decide whether pigment separation earns its own row (key
`pigment-separation`, site `pyntpot.ink.wash.separated`, canonical source
Curtis et al. 1997, `10.1145/258734.258896`) in a follow-up to the
references work, and if so add it to `references.md` with a citation line
in `separated`'s docstring.
