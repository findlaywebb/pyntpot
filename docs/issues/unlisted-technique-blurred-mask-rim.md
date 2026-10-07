# The blurred-mask rim is implemented but has no inventory row

`pyntpot.ink.wash.wash`, when a wash has no flow term, pools pigment at its
edge as the mask minus its own blur
(`rim = np.clip(a - blur(a, o.rim_px), 0.0, 1.0)`); its docstring says
"Pooling is the mask minus its own blur". `design-sources.md` credits this to
Zach Watson's Stamen *Watercolor process* ("rim darkening via blurred
mask"). The `edge-darkening` row covers the other branch,
`pyntpot.ink.wash.flow_edge`, the outward flow term, which is a different
construction.

The references inventory (`specs/001-port/p6-inventory.md`) has no row for
it: P6.1 admits only the seed rows and the decided terms the plan lists, and
the blurred-mask rim is in neither. Whether it is a technique or a single
elementary operation (one subtraction of a blur) is a decision the plan's
decided-terms table does not make, so it is filed here rather than decided
in the inventory step.

Possible fix: decide it in a follow-up to the references work: either add
it to the decided terms as elementary, or give it a row (key
`blurred-mask-rim`, site `pyntpot.ink.wash.wash`, the Stamen post as its
source).
