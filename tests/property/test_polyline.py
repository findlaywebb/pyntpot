"""Properties of `simplify`, `normal_at` and `cut_line`.

`simplify` keeps the ends, returns a subsequence, settles and stays within tolerance;
`cut_line` keeps every piece in the box and cuts a piece's open ends on its edge.
"""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pyntpot.ink.cut import cut_line
from pyntpot.ink.polyline import Point, normal_at, simplify

from support.properties import UNTIMED

COORD = st.floats(-1000, 1000, allow_nan=False, allow_infinity=False)
POINTS = st.lists(st.tuples(COORD, COORD), min_size=0, max_size=60)
EPS = st.floats(0, 50, allow_nan=False, allow_infinity=False)


def _gap(p: Point, a: Point, b: Point) -> float:
    """Distance from p to the infinite line through a and b, or to a when they coincide."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    den = math.hypot(dx, dy)
    if den == 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    return abs(dx * (p[1] - a[1]) - dy * (p[0] - a[0])) / den


class TestSimplify:
    """Douglas-Peucker keeps the ends, drops only what lies within `eps`, and settles."""

    @UNTIMED
    @given(points=POINTS, eps=EPS)
    def test_the_ends_are_kept(self, points: list[Point], eps: float) -> None:
        """The first and last points survive; a line under three points comes back equal, its two ends by identity."""
        out = simplify(points, eps)
        if len(points) < 3:
            assert out == points
            if len(points) == 2:
                assert out[0] is points[0]
                assert out[1] is points[1]
        else:
            assert out[0] is points[0]
            assert out[-1] is points[-1]

    @UNTIMED
    @given(points=POINTS, eps=EPS)
    def test_the_output_is_an_ordered_subsequence(self, points: list[Point], eps: float) -> None:
        """Every kept point is an input point, in input order."""
        it = iter(points)
        assert all(any(p is q for q in it) for p in simplify(points, eps))

    @UNTIMED
    @given(points=POINTS, eps=EPS)
    def test_simplifying_twice_changes_nothing(self, points: list[Point], eps: float) -> None:
        """A simplified line is its own simplification."""
        once = simplify(points, eps)
        assert simplify(once, eps) == once

    @UNTIMED
    @given(points=POINTS, eps=EPS)
    def test_every_dropped_point_is_within_eps_of_its_kept_neighbours(
        self, points: list[Point], eps: float
    ) -> None:
        """A dropped point lies within eps of the line through the kept points either side."""
        out = simplify(points, eps)
        kept = {id(p) for p in out}
        previous = 0
        for i, p in enumerate(points):
            if id(p) in kept:
                previous = i
                continue
            nxt = next(j for j in range(i + 1, len(points)) if id(points[j]) in kept)
            assert _gap(p, points[previous], points[nxt]) <= eps + 1e-9


GRID = st.integers(-50, 50).map(float)
GRID_POINTS = st.lists(st.tuples(GRID, GRID), min_size=1, max_size=12)


class TestNormalAt:
    """`normal_at` is a unit vector left of, and square to, its neighbours' chord."""

    @UNTIMED
    @given(points=GRID_POINTS, data=st.data())
    def test_the_normal_is_unit_and_left_of_the_chord(
        self, points: list[Point], data: st.DataObject
    ) -> None:
        """Off a degenerate run the normal is unit length, square to the chord and on its left; on one it is (0, 1)."""
        i = data.draw(st.integers(0, len(points) - 1))
        a = points[max(i - 1, 0)]
        b = points[min(i + 1, len(points) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        nx, ny = normal_at(points, i)
        if a == b:
            assert (nx, ny) == (0.0, 1.0)
            return
        assert math.hypot(nx, ny) == pytest.approx(1.0)
        assert nx * dx + ny * dy == pytest.approx(0.0, abs=1e-9)
        assert dx * ny - dy * nx > 0


BOX = (-200.0, -150.0, 300.0, 250.0)


def _on_edge(p: Point) -> bool:
    """Whether a point lies on `BOX`'s boundary."""
    xmin, ymin, xmax, ymax = BOX
    return p[0] in (xmin, xmax) or p[1] in (ymin, ymax)


class TestCutLine:
    """Every piece lies in the box, and a piece's end that is not a point of the line is on its edge."""

    @UNTIMED
    @given(points=POINTS)
    def test_every_piece_lies_in_the_box_and_starts_and_ends_on_it(
        self, points: list[Point]
    ) -> None:
        """Each piece has two or more points, all inside the box; a cut end lies on the box's edge."""
        xmin, ymin, xmax, ymax = BOX
        for piece in cut_line(points, BOX):
            assert len(piece) > 1
            assert all(xmin <= x <= xmax and ymin <= y <= ymax for x, y in piece)
            for end in (piece[0], piece[-1]):
                assert end in points or _on_edge(end)
