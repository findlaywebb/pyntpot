# The per-bristle ink reservoir is implemented but has no inventory row

`pyntpot.ink.deposit.spend` spends a per-bristle load along a stroke: ink is
spent in proportion to what is laid down, a heavy bristle empties first, and
`Brush.dip_px` is the reload, whose seam is what makes a long line look
drawn. `Brush.starve` and `Brush.pen_starve` switch it on. `design-sources.md`
names this as a technique from two sources: Chu, Tai (MoXi, 2005) for ink
starvation and the brush reservoir, and Baxter, Lin (2004) for a per-bristle
ink reservoir with reload.

The references inventory (`specs/001-port/p6-inventory.md`) has no row for
it: P6.1 admits only the seed rows and the decided terms the plan lists, and
the reservoir is in neither. The `bristle-brush` row's site,
`pyntpot.ink.stamp.stamp`, reaches it through `channels`, but the split rule
gives a technique with its own site its own row, so it is filed here rather
than folded into that row.

Possible fix: decide whether the reservoir earns its own row (key
`ink-reservoir`, site `pyntpot.ink.deposit.spend`) in a follow-up to the
references work, with Baxter, Lin 2004 or MoXi as its canonical source, or
record that it is part of the bristle brush and cite it there.
