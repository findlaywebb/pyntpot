"""Tests for the polyline helpers: simplify, clip and the length measures."""

from pyntpot.ink.polyline import clip_line, cumulative_length, length, simplify

#: A five-point line with two small wobbles and one real turn.
WOBBLY = [(0.0, 0.0), (1.0, 0.1), (2.0, -0.1), (3.0, 5.0), (4.0, 6.0)]
#: A 3-4-5 line split at its midpoint.
HYPOTENUSE = [(0.0, 0.0), (1.5, 2.0), (3.0, 4.0)]


class TestSimplify:
    """Douglas-Peucker on a pinned five-point line."""

    def test_keeps_the_pinned_points(self) -> None:
        """Simplifying drops only the wobble the tolerance covers."""
        assert simplify(WOBBLY, 0.5) == [(0.0, 0.0), (2.0, -0.1), (3.0, 5.0), (4.0, 6.0)]

    def test_keeps_both_endpoints(self) -> None:
        """The first and last point survive any tolerance."""
        kept = simplify(WOBBLY, 100.0)
        assert kept == [WOBBLY[0], WOBBLY[-1]]

    def test_is_idempotent(self) -> None:
        """Simplifying a simplified line changes nothing."""
        once = simplify(WOBBLY, 0.5)
        assert simplify(once, 0.5) == once


def test_clip_line_returns_the_pinned_pieces() -> None:
    """A line that leaves and re-enters a box comes back as its two inside pieces."""
    line = [(-5.0, 5.0), (2.0, 5.0), (8.0, 5.0), (15.0, 5.0), (8.0, 6.0), (5.0, 6.0)]
    assert clip_line(line, (0.0, 0.0, 10.0, 10.0)) == [
        [(2.0, 5.0), (8.0, 5.0)],
        [(8.0, 6.0), (5.0, 6.0)],
    ]


def test_a_three_four_five_line_is_five_long() -> None:
    """A 3-4-5 polyline is as long as its hypotenuse."""
    assert length(HYPOTENUSE) == 5.0


def test_cumulative_length_is_pinned() -> None:
    """At the default scale the cumulative length counts the distance covered at each point."""
    assert cumulative_length(HYPOTENUSE) == [0.0, 2.5, 5.0]


def test_cumulative_length_divides_by_the_scale() -> None:
    """Metres covered are the pixel distance over pixels per metre."""
    assert cumulative_length(HYPOTENUSE, 2.0) == [0.0, 1.25, 2.5]
