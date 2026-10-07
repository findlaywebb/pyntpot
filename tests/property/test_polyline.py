"""Properties of `simplify`: ends kept, a subsequence, idempotent, within tolerance."""

import math

from hypothesis import given
from hypothesis import strategies as st

from pyntpot.ink.polyline import Pt, simplify

from support.properties import UNTIMED

COORD = st.floats(-1000, 1000, allow_nan=False, allow_infinity=False)
POINTS = st.lists(st.tuples(COORD, COORD), min_size=0, max_size=60)
EPS = st.floats(0, 50, allow_nan=False, allow_infinity=False)


def _gap(p: Pt, a: Pt, b: Pt) -> float:
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
    def test_the_ends_are_kept(self, points: list[Pt], eps: float) -> None:
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
    def test_the_output_is_an_ordered_subsequence(self, points: list[Pt], eps: float) -> None:
        """Every kept point is an input point, in input order."""
        it = iter(points)
        assert all(any(p is q for q in it) for p in simplify(points, eps))

    @UNTIMED
    @given(points=POINTS, eps=EPS)
    def test_simplifying_twice_changes_nothing(self, points: list[Pt], eps: float) -> None:
        """A simplified line is its own simplification."""
        once = simplify(points, eps)
        assert simplify(once, eps) == once

    @UNTIMED
    @given(points=POINTS, eps=EPS)
    def test_every_dropped_point_is_within_eps_of_its_kept_neighbours(
        self, points: list[Pt], eps: float
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
