# Flat boxes are reserved without the tracking the name is drawn with

The placer reserves a flat name's box from `measure_fn`, which is `box_size` called with no
tracking, while the hand draws the name with its kind's `KIND_TRACKING` (0.05 em for a
settlement, 0.10 em for a road, 0.24 em for a river). The flat candidates in
`maps/lettering/placement_flat.py`, the span ends and spans (`span_ends.py`, `spans.py`), the
wrapped blocks in `label.py` (`block_size`), `picks.py` and the attribution line measure the
same way. Nothing is clipped, because a flat name is not cut to its box, but the box
understates the drawn width, so a flat settlement, road or a river's flat first name can sit
closer to a neighbour than the placer meant. Curved names were fixed in ADR 0031: `place` and
`_place` take `measure_tracked`; the flat paths were left on `Measure` on purpose.

To show it: place a settlement label with a real hand and compare `box_size(hand, name, size)`
with `hand.measure(name, size, KIND_TRACKING["settlement"])[0]`; the second is wider by
`size * 0.05 * (len(name) - 1)`.

Possible fix: pass the kind's tracking to the flat measure in the same way, either by giving
`Measure` the tracking argument everywhere or by measuring through `measure_tracked` in the
flat candidates, and regenerate the goldens in a window of their own, since flat boxes move
the placed positions of settlements and roads on the Lynmouth card.
