# One glyph's change makes every later glyph in a name wander

GitHub issue: [#152](https://github.com/findlaywebb/pyntpot/issues/152)

PR #124 (#61) gave every ink stroke, ring and bloom its own generator keyed by the item
(`ink/keyed.py`, ADR 0049), so changing one item moves only that item. The letters layer still
draws a name's glyphs from one shared stream. `maps/lettering_marks.py` makes one generator per
name (`hand.generator(...)`, keyed by the name and its place), and `Hand.write` in
`letters/hand.py` passes it down `_along` or `_flat`, `_vary` and `Hand.stroke`. Each glyph
takes its draws (drift, then lean, scale, turn and nudge per stroke, then the wander on each
stroke) from where the last glyph left the stream.

So the draws a glyph receives depend on how many draws every glyph before it consumed. A change
to one glyph's strokes (more or fewer strokes, or points that change the length of a wander
draw) shifts the stream for every later glyph in the name. When PR #139 (#43, skeleton tails)
changed only `D`, `Q`, `3`, `8` and `X`, other glyphs in the same line wandered slightly, on the
glyph sheet and in map labels, and the image diffs showed movement nobody had asked for.

To show it: write one name twice with the shipped hand, once with a glyph's strokes altered
(for example by giving the font one extra stroke for that glyph), and compare the marks of the
glyphs after it. They differ, though nothing about them changed.

Possible fix: key each glyph's randomness by the glyph and its position in the name (the
character and its index in the row), or by its own geometry, the way `ink/keyed.py` keys a
stroke, so one glyph's change moves only that glyph. `Hand.write` would then make a generator
per glyph from the name's seed and the glyph's key, and `Hand.stroke` and `_vary` would draw
from that glyph's generator. The name-wide draws (`pen` and the flat block's `tilt`) keep the
name's own generator.

Golden impact: every lettered image changes once, because every glyph draws different values
from its new generator. It needs a regeneration window of its own and an ADR, since the
glyph's randomness key is a change to the hand's contract.

Test that proves it: perturb one glyph (change its strokes in a test font, or replace one
character of the name) and assert the marks of every other glyph in the name are byte-identical
to those from the unperturbed name. Add it with the fix, test first.
