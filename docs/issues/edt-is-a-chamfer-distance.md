# `edt` is named for a Euclidean transform but computes a chamfer distance

`pyntpot.ink.noise.edt` reads as "Euclidean distance transform", and
`design-sources.md` lists a "Euclidean distance transform" among the
techniques named in the code. Its body is a two-pass chamfer distance: a
forward and a backward sweep over the rows, each taking the minimum over the
row above (or below) at weight 1 straight and 1.41421356 diagonally, and a
running minimum along the row at weight 1. That is not the exact Euclidean
distance: along directions between the axes and the diagonals it overstates
it by up to about 8 per cent. Its docstring already says "Chamfer distance in
pixels to the nearest True cell", and the module docstring calls it "a chamfer
distance transform", so the text is right and only the name is not.

The references inventory (`specs/001-port/p6-inventory.md`) names the
technique by what the body does, `chamfer-distance`, with `edt` as its site.
P6 does not rename it: a rename changes an identifier that nine `src/`
modules and six test modules import, which the docs pass forbids.

Possible fix: rename `edt` to `chamfer_distance` (or `distance_field`) in one
refactor slice, repointing every importer and test, with G-self proving no
pixel moved. Keep the name `edt` out of `GLOSSARY.md`.
