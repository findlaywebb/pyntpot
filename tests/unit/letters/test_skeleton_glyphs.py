"""Tests for the traced strokes of the letters that were drawn twice: each is written once, whole."""

from __future__ import annotations

import math
from itertools import pairwise

import pytest

from pyntpot.letters.font import OutlineFont, load

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
        """No stroke lies along another for more than a stroke width: a stem is drawn once."""
        samples = [_samples(p) for p in _paths(face, ch)]
        for i, a in enumerate(samples):
            for j, b in enumerate(samples):
                if i != j:
                    assert _alongside(a, b) <= STROKE_EM, f"{ch!r}: stroke {i} doubles stroke {j}"

    def test_the_o_is_one_ring(self, face: OutlineFont) -> None:
        """The o is a single closed stroke, with no speck drawn inside its ring."""
        paths = _paths(face, "o")
        assert len(paths) == 1
        assert math.dist(paths[0][0], paths[0][-1]) < STROKE_EM / 4
