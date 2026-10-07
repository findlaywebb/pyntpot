# Three route constants in the style groups have no reader

`pyntpot.maps.style_groups` defines `ROUTE_INK`, `ROUTE_EFFECT_OFF` and
`ROUTE_SHADOW`, and no module or test reads any of them. The comment on
`ROUTE_EFFECT_OFF` said it was "everything `basemap_route_effect`
understands" and that a theme's missing effect keys "are filled in from
here"; no `basemap_route_effect` exists in the package, and nothing fills in
a key. A theme whose `[route_inks.<sport>.effect]` table leaves out
`casing_colour` builds, and `RouteInk.casing`, which nothing calls,
would then raise `KeyError`. The
packaged default theme names every key, so the shipped path never meets it.

Show it with
`grep -rn "ROUTE_INK\b\|ROUTE_EFFECT_OFF\|ROUTE_SHADOW" src tests`: each name
appears only at its definition. The docs pass rewrote the comments to say
what the code does; deleting the names or adding the fill is a code change,
which P6 does not make.

Possible fix: either fill each route ink's `effect` from `ROUTE_EFFECT_OFF`
when the style is built (a `Style` validator), with a test that a theme
naming only `glow_px` gets every other key at its off value, or delete the
three constants. `ROUTE_INK` duplicates the colour every route ink in the
default theme carries, so it can go either way.
