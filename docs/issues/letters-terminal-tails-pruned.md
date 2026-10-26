# The skeleton prunes the terminal tails of D, Q and 3, and 8 keeps a bridge

`letters/skeleton.py` prunes short spurs from the thinned glyph before `letters/trace.py`
turns it into strokes. P7.V4 made every stroke draw once, and strokes that run on through a
junction one stroke (`letters/junction.py`, `skeleton.prune` keeping a spur that carries on
from another branch). Four glyphs are still wrong:

- `D`, `Q` and `3` lose their terminal tails: the pruning still reads the tail as a spur and
  removes it, so the traced glyph stops short of the drawn outline's end.
- `8` keeps a bridge of 0.047 em that `junction.join_through` does not drop.

`tests/unit/letters/test_skeleton_glyphs.py`, class `TestJoined`, checks every letter and
figure but these four ("every skeleton pixel is within 0.03 em of a stroke", "no stroke is
shorter than a stroke width", "the glyph is one piece"). They are the ones it leaves out.

To show it: trace `D`, `Q`, `3` and `8` with the shipped hand at 64 px, overlay the traced
strokes on the glyph's skeleton and run the `TestJoined` checks on them; the first three leave
skeleton pixels farther than 0.03 em from any stroke, and the fourth keeps the short bridge.

Possible fix: keep a spur that ends a stroke of the outline, not only one that carries on from
another branch, and drop a bridge shorter than a stroke width inside a junction, then add the
four glyphs to `TestJoined`. The lettered goldens and docs images move, so it needs a
regeneration window of its own with an ADR.
