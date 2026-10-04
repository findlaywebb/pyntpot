"""Tests for the trace: the skeleton of each glyph is counted, and the strokes stay in the ink."""

from __future__ import annotations

import numpy as np
import pytest

from pyntpot.letters.font import OutlineFont, _Flatten, load
from pyntpot.letters.skeleton import RASTER_EM, _components, _crossings, _fill, thin

#: What each letter's own skeleton is made of: how many free ends it has, how
#: many junctions, and how many separate pieces of ink the glyph is drawn from.
#: An `H` is two stems and a crossbar, so four ends and two junctions; an `M`
#: is two stems and a bowl joining them, so the same four ends and two
#: junctions; an `i` is one stem and its tittle, so two ends, no junction and
#: two pieces. A test that only asked whether some strokes came back is what
#: let the card read `Honmouth` twice: the M's bowl was there, it had simply
#: lost its arms into the stems. These counts are the shape of the letter and
#: nothing else agrees with them by accident.
GLYPH_TOPOLOGY: dict[str, tuple[int, int, int]] = {
    "A": (2, 2, 1),
    "B": (0, 2, 1),
    "C": (2, 0, 1),
    "D": (1, 1, 1),
    "E": (3, 1, 1),
    "F": (4, 2, 1),
    "G": (3, 1, 1),
    "H": (4, 2, 1),
    "I": (2, 0, 1),
    "J": (2, 0, 1),
    "K": (4, 2, 1),
    "L": (2, 0, 1),
    "M": (4, 2, 1),
    "N": (4, 2, 1),
    "O": (0, 0, 1),
    "P": (1, 1, 1),
    "Q": (2, 2, 1),
    "R": (2, 2, 1),
    "S": (2, 0, 1),
    "T": (3, 1, 1),
    "U": (2, 0, 1),
    "V": (3, 1, 1),
    "W": (5, 3, 1),
    "X": (4, 2, 1),
    "Y": (3, 1, 1),
    "Z": (4, 2, 1),
    "a": (1, 1, 1),
    "b": (1, 1, 1),
    "c": (2, 0, 1),
    "d": (2, 2, 1),
    "e": (1, 1, 1),
    "f": (4, 1, 1),
    "g": (1, 1, 1),
    "h": (3, 1, 1),
    "i": (2, 0, 2),
    "j": (2, 0, 2),
    "k": (4, 2, 1),
    "l": (2, 0, 1),
    "m": (3, 1, 1),
    "n": (3, 1, 1),
    "o": (0, 0, 1),
    "p": (2, 2, 1),
    "q": (1, 1, 1),
    "r": (3, 1, 1),
    "s": (2, 0, 1),
    "t": (4, 2, 1),
    "u": (3, 1, 1),
    "v": (3, 1, 1),
    "w": (3, 1, 1),
    "x": (4, 2, 1),
    "y": (3, 1, 1),
    "z": (2, 0, 1),
    "0": (0, 0, 1),
    "1": (2, 0, 1),
    "2": (2, 0, 1),
    "3": (3, 1, 1),
    "4": (3, 1, 1),
    "5": (2, 0, 1),
    "6": (1, 1, 1),
    "7": (4, 2, 1),
    "8": (0, 2, 1),
    "9": (1, 1, 1),
    "-": (2, 0, 1),
    "'": (2, 0, 1),
    ".": (0, 0, 1),
}


@pytest.fixture(scope="module")
def face() -> OutlineFont:
    """The vendored face, loaded once."""
    return load()


def _bitmaps(face: OutlineFont, ch: str) -> tuple[np.ndarray, np.ndarray, float, float]:
    """One glyph's filled bitmap, its thinned skeleton and the fill's origin."""
    name = face._name_of(ch)
    assert name is not None
    rec = face._pen_cls(face._glyphs)
    face._glyphs[name].draw(rec)
    flat = _Flatten()
    rec.replay(flat)
    img, ox, oy = _fill(flat.contours, face.upem)
    return img, thin(img), ox, oy


def _raster(face: OutlineFont, ch: str, ox: float, oy: float) -> list[list[tuple[float, float]]]:
    """One glyph's drawn paths, back in the raster the fill was made on."""
    k = RASTER_EM / face.upem
    return [
        [((x * face.upem - ox) * k, (y * face.upem - oy) * k) for x, y in path]
        for path in face.glyph(ch).paths
    ]


def _inner_edge(face: OutlineFont, ch: str, frac: float, tol: float = 0.05) -> float:
    """How far in from the left the letter's own ink reaches, at one height.

    Measured as a share of the letter's width, over the ink in the left half
    only, so it is the inside face of the left-hand stroke: the boundary of
    the white the reader sees inside the letter.
    """
    pts = [p for path in face.glyph(ch).paths for p in path]
    lo, hi = min(x for x, _y in pts), max(x for x, _y in pts)
    cap = max(y for _x, y in pts)
    band = [
        (x - lo) / (hi - lo)
        for x, y in pts
        if abs(y / cap - frac) <= tol and (x - lo) / (hi - lo) < 0.5
    ]
    return max(band) if band else 0.0


class TestSkeleton:
    """Each glyph's skeleton is counted, not merely produced."""

    @pytest.mark.parametrize("ch", list(GLYPH_TOPOLOGY), ids=list(GLYPH_TOPOLOGY))
    def test_a_letter_has_the_free_ends_junctions_and_pieces_it_should(
        self, face: OutlineFont, ch: str
    ) -> None:
        """Free ends, junctions and separate pieces of ink match the pinned shape of the letter."""
        img, skel, _ox, _oy = _bitmaps(face, ch)
        on = {(int(r), int(c)) for r, c in zip(*np.nonzero(skel), strict=True)}
        cross = {p: _crossings(p, on) for p in on}
        got = (
            sum(1 for p in on if cross[p] == 1),
            sum(1 for p in on if cross[p] >= 3),
            len(_components(img)),
        )
        assert got == GLYPH_TOPOLOGY[ch]

    @pytest.mark.parametrize("ch", list(GLYPH_TOPOLOGY), ids=list(GLYPH_TOPOLOGY))
    def test_no_piece_of_a_letter_is_left_undrawn(self, face: OutlineFont, ch: str) -> None:
        """A blob of ink with no stroke through it is a letter missing a part."""
        img, _skel, ox, oy = _bitmaps(face, ch)
        drawn = [p for path in _raster(face, ch, ox, oy) for p in path]
        for blob in _components(img):
            rows = [r for r, _c in blob]
            cols = [c for _r, c in blob]
            near = any(
                min(cols) - 2 <= x <= max(cols) + 2 and min(rows) - 2 <= y <= max(rows) + 2
                for x, y in drawn
            )
            assert near, f"{ch!r} has a piece of ink nothing is drawn through"

    @pytest.mark.parametrize("ch", list(GLYPH_TOPOLOGY), ids=list(GLYPH_TOPOLOGY))
    def test_no_stroke_of_a_letter_is_drawn_outside_its_own_ink(
        self, face: OutlineFont, ch: str
    ) -> None:
        """A pen that leaves the letter has been thrown there, so the M and the W grow no star."""
        img, _skel, ox, oy = _bitmaps(face, ch)
        h, w = img.shape
        for path in _raster(face, ch, ox, oy):
            for x, y in path:
                c, r = round(x), round(y)
                inside = (
                    0 <= r < h
                    and 0 <= c < w
                    and img[max(r - 2, 0) : r + 3, max(c - 2, 0) : c + 3].any()
                )
                assert inside, f"{ch!r} draws at ({c}, {r}), outside its own ink"


class TestFlanks:
    """A stroke that thinning merged into another comes back."""

    def test_the_capital_m_is_not_written_as_an_h(self, face: OutlineFont) -> None:
        """The M's bowl keeps its arms, told from an H by the white inside each."""
        m_low, m_high = _inner_edge(face, "M", 0.60), _inner_edge(face, "M", 0.70)
        h_low, h_high = _inner_edge(face, "H", 0.60), _inner_edge(face, "H", 0.70)
        assert m_low > 0.3, "the M has no bowl"
        assert m_high > 0.08, "the M's bowl has no arms: it is an H with a dip"
        assert h_high < 0.06, "the H has grown something above its crossbar"
        assert m_high > h_high * 2.5, "an M and an H are drawn the same"
        assert h_low < 0.2, "the H's crossbar is not a crossbar"
