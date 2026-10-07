# The route-coloured lettering ink does not follow the route's ink

The comment on `pyntpot.letters.style.NibStyle.label_route_ink` said "The
caller fills it from the sport's route ink". No code does: the field is read
from the theme like every other (`label_route_ink = "#c22050"` in
`maps/themes/default.toml`), and `pyntpot.maps.style.Style.route_ink` (the
ride ink the route is drawn in) is never copied into it. A theme that changes
the route's colour leaves names in the "route" ink at the old colour unless it
also sets `label_route_ink`.

P6 does not fix it because the fix changes code. The comment now says the
field is read from the theme and its default is the default route ink.

Possible fix: build the `NibStyle` handed to `nib.plate` with
`dataclasses.replace(style.nib, label_route_ink=style.route_ink().colour)`
in `maps.lettering.pipeline.draw_plate`, or drop the claim and keep the two
inks independent by design, recording which in the theme's comments.
