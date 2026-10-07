# The `labels` switch also drops the attribution

`pyntpot.maps.style_groups.LetteringPolicy.labels` is read in two places, and
both open no hand when it is off. `pyntpot.maps.lettering.pipeline.letter`
returns an empty `Lettering` with no label plate, which is what a theme that
wants the painting bare asks for. `pyntpot.maps.attribution.draw_attribution`
then writes no attribution line either, even when `pyntpot.maps.pipeline.compose`
was called with `attribution=True`. A theme with `labels = false` therefore
loses the data credit the basemap's sources ask for, and the `attribution`
flag (the CLI's `--no-attribution`) is no longer the only thing that turns it
off.

Show it with `grep -rn "lettering.labels" src/pyntpot/maps --include=*.py`:
the readers are `attribution.py` and `lettering/pipeline.py`. Changing which
stages read the field is a code change, which P6 does not make.

Possible fix: have `draw_attribution` stop reading `labels`, so the attribution
is written whenever `compose` is asked for it, and add a unit test that a style
with `labels = false` still gets the attribution block. The goldens use the
default theme (`labels = true`), so the change moves no golden pixel.
