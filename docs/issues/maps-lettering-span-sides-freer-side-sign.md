# The free-paper side of a span is signed the opposite way to the side its mark is drawn on

`pyntpot.maps.lettering.span_sides._freer_side` probes each side of a span's
stretch along the normal `(-dy, dx)` and returns `+1` for the side that normal
points to, which in card pixels (y down) is the right of travel.
`pyntpot.maps.lettering.span_line.span_line`, through
`pyntpot.ink.curves.offset_curve`, draws a mark for `side=+1` on the left of
travel. `pyntpot.maps.lettering.spans.place_spans` passes the first straight
to the second (`base = free if span.ground else -free`), so a ground span's
mark starts on the darker side and a session span's on the clearer one: the
opposite of what `place_spans` says ("the ground takes the side of the route
with more free paper").

The docstring used to say `_freer_side` returns "+1 for left", and the module
invariant said every side is signed towards `(-dy, dx)`. P6 rewrote both to
describe what the code does and changed no code: the goldens pin the current
placement, and `_curved_side` and `_drawn_side` can still move a span after
the free-paper choice, so the visible effect needs a render to judge.

To show it: an eastward route `[(100 + 5 i, 300) for i in range(100)]` on an
800 by 600 card, a 16 by 12 darkness grid solid above `y = 300` and clear
below, `Span(name="test", i0=10, i1=80)` and `cap_px=14`. `_freer_side`
returns `(1, 1.0)` (the clear side, below), and
`span_line(route, 10, 80, 1, 16.8)` draws its middle at `y = 283.2`, above
the route on the solid side.

Possible fix: probe along `(dy, -dx)` in `_freer_side` so its `+1` is the left
of travel, as `_side_at` and `offset_curve` sign it, then review the span
goldens: every span whose side came from free paper may move.
