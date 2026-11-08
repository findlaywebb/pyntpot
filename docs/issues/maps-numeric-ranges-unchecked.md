# A theme's numeric values are not range-checked at load

GitHub issue: [#206](https://github.com/findlaywebb/pyntpot/issues/206)

Area: maps (themes).

`Style.from_yaml`, `Style.named` and `Style.from_theme` check every key, every value's
type, the `Literal` choices, brush ids and colours at load, but not whether a number is in
a range its reader can use. A theme over `sepia` with `card.display_px: -5` and
`route_ink.opacity: 2.0` loads with no problem: the style holds `display_px=-5` and
`opacity=2.0`.

The bad value is found later, if at all. `route_ink.opacity` is refused when the route is
composed (`compose_steps.py`: "route opacity 2.0 is not in [0, 1]"), after the fetch and
the paint have run, and with no file or line. Other fields (`card.display_px`,
`card.supersample`, the `_px` widths, the shares and strengths meant to be in 0 to 1) have
no check at all, so a negative size or an out-of-range share fails deep in the painter or
paints something odd.

Possible fix: a range per numeric field, held once beside the model (for example in the
field's metadata), checked by `maps.theme_check` with the other value checks so the
problem names its file, key and line, and written into the schema as `minimum` and
`maximum` so an editor flags it too. The compose step's own check on `opacity` stays, for
a style built in Python.
