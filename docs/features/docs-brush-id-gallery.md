# A gallery of every brush id

**What exists today.** A brush id names one cell of the brush sheet: a three-letter prefix
and a colour column (`BRUSH_COLOURS`: `RIV`, `STR`, `LAN` with one column each, `MAJ` with
five, `TRK` with six) and a treatment row (`BRUSH_TREATMENTS`, rows 1 to 8, of which 5, 6
and 8 are nibs). That is 112 ids. The reference page `docs/reference/brushes.md` lists them
in tables, and the brush sheet image paints a treatment by width grid in a few colours, so
most ids are never seen painted.

**What the feature would add.** A gallery page that paints every brush id: one swatch
stroke per id, grouped by prefix and colour, rows for the eight treatments, each lettered
with its id in the library's hand, at a size where wet, dry, gritty and nib strokes can be
told apart. It would let a theme author choose an id by eye instead of by name.

**Why it is not a defect.** The ids are documented and every one paints; the gap is only
that the docs do not show them all (maintainer, 2026-10-25: a future feature).

**Possible shape.** An `examples/brush_gallery.py` with `figure=` per prefix, one registry
entry per figure under the docs image budgets, and a `docs/reference/brush-gallery.md`
page linked from the brushes reference; a test that every id in `BRUSH_COLOURS` by
`BRUSH_TREATMENTS` appears on the page, so a new id cannot go unpainted.
