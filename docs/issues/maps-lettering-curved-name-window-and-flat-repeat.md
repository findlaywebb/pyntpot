# A curved name is cut short, and a river's repeat is set flat when it finds no water

The golden Lynmouth card letters the East Lyn twice: once flat, reading "East
Lyn", and once along the water, reading "East Lp". Two defects, one per symptom.

**The window is shorter than the written name.** The placer measures a name
without its kind's tracking (`lettering/pipeline.py` passes
`partial(lettering_marks.box_size, hand)`, and `box_size` calls `hand.measure`
with none), so `placement.py` cuts a window of the untracked width times 1.02.
The hand then writes the name with `KIND_TRACKING` (0.24 em for a river, 0.10 em
for a road). For "East Lyn" at 18 px the window is 65.0 px and the written name
85.0 px; the glyph centres of "y" and "n" fall past the walk's end, `Hand._along`
clamps both to the end point, and the "y" descender over the "n" reads as "p".
Every curved river and road name is affected.

**A river's repeat falls back to flat paper.** The water runs 652 px, so the
river takes `MAJOR_RIVER_LABELS` (two). Every window on the water that passes
the shape test lies within the repeat guard of the first name, so `place_along`
returns nothing, and `placement._place` sets the repeat on the cheapest flat
paper about 70 px from the first name. Nothing drops a repeat that cannot go on
its water, although the placer's docstring says a name that repeats another's
place is dropped.

Reproduced offline, byte-identical to the golden; both fixes tried in memory
(P7 research, 2026-10-23).

Possible fix: measure the window with the kind's tracking (`KIND_TRACKING` moves
to `lettering/label.py`, as `placement` cannot import `lettering_marks`), and drop
a river's repeat when it cannot go on its water; the first name keeps its flat
fallback. Tests, red first: a curved name's window is as long as the hand writes
it; every glyph of a placed name sits inside its window; a river's second name
with no water left is dropped. The labels plate and the card move (about 1.7% of
pixels, past `MAX_DIFFERING_FRACTION`), so the fix lands in a golden regeneration
window under ADR 0006's procedure, with its own ADR. With both fixes "B3234"
is set flat beside Lynton: its correctly sized window now costs more than the
flat seat.

Separate, smaller: flat boxes for kinds with tracking (settlements, roads, a
river's flat first name) are reserved without it, so they understate the drawn
width. Nothing is clipped, but they can crowd a neighbour.
