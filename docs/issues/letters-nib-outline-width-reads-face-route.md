# The nib narrows the outline route only when the face style names it

`pyntpot.letters.nib.nib_brushes` narrows the glyph nib by
`NibStyle.label_outline_width_frac` when `face.label_route == "outline"`. It
reads the route from the face style, not from the hand that wrote the marks.
`pyntpot.letters.hand.Hand` takes a `route` argument that overrides the face
style's, and `pyntpot.maps.lettering.pipeline.draw_plate` passes its own
`route` argument through `maps.lettering_marks.open_hand` to it while it
builds the `NibGroups` from `style.face` unchanged. So
`draw_plate(..., route="outline")` with the default style writes outline
glyphs (two strokes a stem) at the full centreline nib width, which is the
bolder letter the `label_outline_width_frac` comment says the finer nib exists
to prevent.

P6 does not fix it because the fix changes code: the docstring of
`nib_brushes` now says what the code does (the face style's `label_route`
decides).

How to show it: stroke the same setting written by
`Hand(FaceStyle(), HandStyle(), "outline")` through `nib.plate` once with
`NibGroups(face=FaceStyle())` and once with
`NibGroups(face=FaceStyle(label_route="outline"))`; the two plates differ.

Possible fix: have `draw_plate` build its `NibGroups` with
`dataclasses.replace(style.face, label_route=hand.route)`, or pass the route
to `nib_brushes` explicitly, and pin it with a test that the two calls above
write the same plate.
