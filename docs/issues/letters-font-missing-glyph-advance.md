# A character the face lacks advances 0.28 em, not the face's space

`pyntpot.letters.font.OutlineFont.glyph` returns `Glyph(ch, 0.28, [])` for a
character the face has no glyph for. Its docstring said such a character
"comes back with the advance of a space". The vendored Patrick Hand's space
advances 0.23 em (`hmtx` of the `space` glyph, 1000 units per em), so a
missing character is set about a fifth wider than a space.

P6 does not fix it because the fix changes a literal, which can move a label.
The docstring now says "a fixed advance of 0.28 em".

How to show it: `OutlineFont().glyph("\u4e00").advance` is 0.28 (the face
has no CJK glyphs) and `OutlineFont().glyph(" ").advance` is 0.23.

Possible fix: use the face's own space advance (`self.advance(" ")`, or a
fixed share of `upem` when the face has no space), with a golden check that
no placed label moves on the Lynmouth fixture.
