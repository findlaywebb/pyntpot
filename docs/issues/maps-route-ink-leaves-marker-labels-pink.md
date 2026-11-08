# Changing the route ink leaves the "start" and "finish" labels in the old pink

GitHub issue: [#159](https://github.com/findlaywebb/pyntpot/issues/159)

Area: maps (style), with letters (nib).

`Style.with_route_ink(colour=...)` in `src/pyntpot/maps/style.py` changes only
`route_ink.colour` and `route_ink.width_px`. The route markers that
`maps/lettering/picks.py` `route_markers` adds, "start" and "finish", are lettered in a
different field: `maps/lettering_marks.py` maps the `marker` kind to the `route` ink
(`KIND_INK`), and `letters/nib.py` resolves `route` to `NibStyle.label_route_ink`, which
is `#c22050`, the model default.

So a caller who follows `docs/how-to/change-the-route-ink.md` gets a violet route with a
pink "start" beside it. The how-to's own result image, `docs/images/how-to/route-ink.webp`,
shows exactly that. The page never mentions `label_route_ink`; a theme avoids the mismatch
only because its author also sets `nib.label_route_ink` by hand.

This is deliberate today. `with_route_ink`'s docstring promises that only `digest()`
moves, never `lettering_digest()`, so no plate is repainted; `nib` is in
`LETTERING_GROUPS`, so feeding the route colour into `label_route_ink` would move the
lettering digest and the lettering would be done again. ADR 0027 keeps `label_route_ink` independent of
the route ink (after ADR 0005). The defect is that one concept, the route's colour, lives in
two fields and the public way to change it changes only one.

Possible fix: decide in an ADR whether the route ink feeds the lettering. Either
`with_route_ink` also sets `nib.label_route_ink` (and the lettering digest moves), or the
markers are lettered apart from the other names and tinted with `route_ink.colour` when the
card is composed, so no digest but `digest()` moves. Until then,
add a "When it goes wrong" entry to the how-to naming `nib.label_route_ink`.
