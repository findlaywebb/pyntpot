"""Tests for the traced strokes of the letters that were drawn twice: each is written once, whole."""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import pytest

from pyntpot.letters.font import OutlineFont, _Flatten, load
from pyntpot.letters.skeleton import RASTER_EM, fill, thin

#: How wide the shipped hand's stem is, in em: twice the median half-width the
#: trace measures on its 128 pixel grid (about five pixels). It sets how close
#: two strokes may sit and still be one pen line.
STROKE_EM = 0.085

#: What each listed glyph is made of: how many connected pieces its strokes form.
PIECES: dict[str, int] = {
    "K": 1,
    "k": 1,
    "e": 1,
    "m": 1,
    "n": 1,
    "d": 1,
    "o": 1,
    "a": 1,
    "g": 1,
}

#: The glyphs whose junctions, strokes and ends are checked besides the ones above:
#: every letter and figure but D, Q, 3 and 8, whose own terminal tails and crossing
#: bridge are a separate fault.
JOINED = "ABCEFGHIJKLMNOPRSTUVWXYZabcdefghklmnopqrstuvwxyz01245679"

#: How far, in em, a skeleton pixel may be from the nearest stroke: under this the
#: stroke is on it, over it a stem end or a branch has been left undrawn.
REACH_EM = 0.03

#: How far two strokes may lie alongside each other, in em: the arms at a junction
#: lie side by side for about a stroke width and a half before they part, and a
#: stem drawn twice lies alongside for its length, three times that and more.
ALONGSIDE_EM = 1.5 * STROKE_EM

#: The sample spacing along a stroke when it is walked for the parallel check, in em.
STEP = 0.004


def _paths(face: OutlineFont, ch: str) -> list[list[tuple[float, float]]]:
    """One glyph's traced strokes, in em."""
    return [path for path in face.glyph(ch).paths if len(path) > 1]


def _samples(path: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """A stroke resampled every `STEP`, so lengths can be counted by points."""
    out = [path[0]]
    for a, b in pairwise(path):
        n = max(int(math.dist(a, b) / STEP), 1)
        out.extend(
            (a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n) for t in range(1, n + 1)
        )
    return out


def _gap(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    """The least distance between two sampled strokes."""
    return min(math.dist(p, q) for p in a for q in b)


def _pieces(paths: list[list[tuple[float, float]]]) -> int:
    """How many connected pieces strokes form, two touching when within one stroke width."""
    samples = [_samples(p) for p in paths]
    todo = set(range(len(paths)))
    pieces = 0
    while todo:
        pieces += 1
        stack = [todo.pop()]
        while stack:
            i = stack.pop()
            joined = {j for j in todo if _gap(samples[i], samples[j]) <= STROKE_EM}
            todo -= joined
            stack.extend(joined)
    return pieces


def _alongside(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    """How much of stroke `a`, in em, runs within half a stroke width of stroke `b`."""
    near = sum(1 for p in a if min(math.dist(p, q) for q in b) <= STROKE_EM / 2)
    return near * STEP


@pytest.fixture(scope="module")
def face() -> OutlineFont:
    """The vendored face, loaded once."""
    return load()


class TestDrawnOnce:
    """A letter's strokes join into one piece and none is laid along another."""

    @pytest.mark.parametrize("ch", list(PIECES), ids=list(PIECES))
    def test_the_strokes_form_the_expected_pieces(self, face: OutlineFont, ch: str) -> None:
        """A listed letter is one connected piece, not a stem and a stray."""
        assert _pieces(_paths(face, ch)) == PIECES[ch]

    @pytest.mark.parametrize("ch", list(PIECES), ids=list(PIECES))
    def test_no_two_strokes_run_parallel(self, face: OutlineFont, ch: str) -> None:
        """No stroke lies along another for more than a stroke width and a half: a stem is drawn once."""
        samples = [_samples(p) for p in _paths(face, ch)]
        for i, a in enumerate(samples):
            for j, b in enumerate(samples):
                if i != j:
                    assert _alongside(a, b) <= ALONGSIDE_EM, (
                        f"{ch!r}: stroke {i} doubles stroke {j}"
                    )

    def test_the_o_is_one_ring(self, face: OutlineFont) -> None:
        """The o is a single closed stroke, with no speck drawn inside its ring."""
        paths = _paths(face, "o")
        assert len(paths) == 1
        assert math.dist(paths[0][0], paths[0][-1]) < STROKE_EM / 4


def _skeleton_em(face: OutlineFont, ch: str) -> list[tuple[float, float]]:
    """One glyph's one pixel skeleton, as points in em."""
    name = face._name_of(ch)
    assert name is not None
    rec = face._pen_cls(face._glyphs)
    face._glyphs[name].draw(rec)
    flat = _Flatten()
    rec.replay(flat)
    img, ox, oy = fill(flat.contours, face.upem)
    k = RASTER_EM / face.upem
    return [
        ((c + 0.5) / k / face.upem + ox / face.upem, (r + 0.5) / k / face.upem + oy / face.upem)
        for r, c in zip(*np.nonzero(thin(img)), strict=True)
    ]


class TestJoined:
    """Strokes meet where the glyph's own ink does, and nothing is left short or loose."""

    @pytest.mark.parametrize("ch", list(JOINED), ids=list(JOINED))
    def test_every_skeleton_pixel_has_a_stroke_on_it(self, face: OutlineFont, ch: str) -> None:
        """No junction or stem end is left undrawn: the d keeps its foot, the n its stem top."""
        drawn = [p for path in _paths(face, ch) for p in _samples(path)]
        for x, y in _skeleton_em(face, ch):
            gap = min(math.dist((x, y), q) for q in drawn)
            assert gap <= REACH_EM, (
                f"{ch!r}: skeleton at ({x:.3f}, {y:.3f}) is {gap:.3f} em from any stroke"
            )

    @pytest.mark.parametrize("ch", list(JOINED), ids=list(JOINED))
    def test_no_stroke_is_shorter_than_a_stroke_width(self, face: OutlineFont, ch: str) -> None:
        """A stroke shorter than the pen is wide is a dot beside the letter, as the stray one after an a."""
        for path in _paths(face, ch):
            length = sum(math.dist(a, b) for a, b in pairwise(path))
            assert length >= STROKE_EM, f"{ch!r} has a stroke {length:.3f} em long"

    @pytest.mark.parametrize("ch", list(JOINED), ids=list(JOINED))
    def test_a_stroke_ends_on_another_or_on_a_free_end(self, face: OutlineFont, ch: str) -> None:
        """The pieces of a letter are one piece: nothing is drawn clear of the rest."""
        assert _pieces(_paths(face, ch)) == 1

    def test_a_cross_is_a_stem_and_a_bar(self, face: OutlineFont) -> None:
        """The t is two strokes, each written through the crossing, not four that meet in it."""
        assert len(_paths(face, "t")) == 2
