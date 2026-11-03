"""Tests for `cut_line`: the pieces of a line inside a box, cut where it crosses the edge."""

import pytest

from pyntpot.ink.cut import cut_line

#: A 10 by 10 box at the origin.
BOX = (0.0, 0.0, 10.0, 10.0)


def test_each_piece_is_cut_where_it_crosses_the_edge() -> None:
    """A line that leaves and re-enters a box comes back as two pieces that start and end on its edge."""
    line = [(-5.0, 5.0), (2.0, 5.0), (8.0, 5.0), (15.0, 5.0), (8.0, 6.0), (5.0, 6.0)]
    first, second = cut_line(line, BOX)
    assert first == [(0.0, 5.0), (2.0, 5.0), (8.0, 5.0), (10.0, 5.0)]
    assert second[0] == pytest.approx((10.0, 5.0 + 5.0 / 7.0))
    assert second[0][0] == 10.0
    assert second[1:] == [(8.0, 6.0), (5.0, 6.0)]


@pytest.mark.parametrize(
    ("line", "cut"),
    [
        ([(5.0, -5.0), (5.0, 5.0)], [(5.0, 0.0), (5.0, 5.0)]),
        ([(5.0, 15.0), (5.0, 5.0)], [(5.0, 10.0), (5.0, 5.0)]),
        ([(5.0, 5.0), (-5.0, 5.0)], [(5.0, 5.0), (0.0, 5.0)]),
        ([(5.0, 5.0), (15.0, 5.0)], [(5.0, 5.0), (10.0, 5.0)]),
    ],
    ids=["in-from-south", "in-from-north", "out-to-west", "out-to-east"],
)
def test_a_line_through_each_side_is_cut_on_it(
    line: list[tuple[float, float]], cut: list[tuple[float, float]]
) -> None:
    """A line crossing any one side, in or out, is cut exactly on that side."""
    assert cut_line(line, BOX) == [cut]


def test_a_corner_cut_with_no_point_inside_is_kept() -> None:
    """A segment that clips a box's corner with both its points outside is kept, cut at both edges."""
    (piece,) = cut_line([(-1.0, 5.0), (5.0, -1.0)], BOX)
    assert len(piece) == 2
    assert piece[0] == pytest.approx((0.0, 4.0))
    assert piece[1] == pytest.approx((4.0, 0.0))


def test_a_line_inside_is_one_piece_of_its_own_points() -> None:
    """A line wholly inside comes back whole, as its own points."""
    line = [(1.0, 1.0), (5.0, 2.0), (9.0, 9.0)]
    assert cut_line(line, BOX) == [line]


def test_a_line_that_only_touches_or_misses_the_box_has_no_piece() -> None:
    """A line that meets the box at one point, misses it, or is one point has no piece inside."""
    assert cut_line([(-5.0, 15.0), (5.0, 15.0)], BOX) == []
    assert cut_line([(-5.0, 5.0), (0.0, 0.0), (-5.0, -5.0)], BOX) == []
    assert cut_line([(1.0, 1.0)], BOX) == []


def test_a_line_that_starts_wholly_outside_is_cut_where_it_comes_in() -> None:
    """A first segment that misses the box is skipped, not the end of the line."""
    assert cut_line([(-10.0, 5.0), (-5.0, 5.0), (5.0, 5.0)], BOX) == [[(0.0, 5.0), (5.0, 5.0)]]


def test_a_two_point_piece_before_another_is_kept() -> None:
    """A line that crosses a corner and comes back gives both its pieces, the first of two points."""
    line = [(5.0, -5.0), (5.0, 5.0), (15.0, 5.0), (15.0, 8.0), (5.0, 8.0)]
    assert cut_line(line, BOX) == [
        [(5.0, 0.0), (5.0, 5.0), (10.0, 5.0)],
        [(10.0, 8.0), (5.0, 8.0)],
    ]
    assert cut_line([(5.0, -5.0), (5.0, 15.0), (8.0, 15.0), (8.0, 5.0)], BOX) == [
        [(5.0, 0.0), (5.0, 10.0)],
        [(8.0, 10.0), (8.0, 5.0)],
    ]


def test_a_box_off_the_origin_cuts_on_its_own_edges() -> None:
    """In a box from (2, 3) to (12, 13) a line through it is cut at x 2 and y 3."""
    box = (2.0, 3.0, 12.0, 13.0)
    assert cut_line([(-4.0, 8.0), (8.0, 8.0)], box) == [[(2.0, 8.0), (8.0, 8.0)]]
    assert cut_line([(8.0, -4.0), (8.0, 8.0)], box) == [[(8.0, 3.0), (8.0, 8.0)]]
    (west,) = cut_line([(-4.0, 2.0), (8.0, 14.0)], box)
    assert west[0] == pytest.approx((2.0, 8.0))
    (south,) = cut_line([(0.0, -3.0), (12.0, 9.0)], box)
    assert south[0] == pytest.approx((6.0, 3.0))


def test_a_line_along_or_just_inside_an_edge_is_kept() -> None:
    """A segment lying on the box's edge, or half a unit inside it, is inside."""
    assert cut_line([(0.0, 2.0), (0.0, 8.0)], BOX) == [[(0.0, 2.0), (0.0, 8.0)]]
    assert cut_line([(0.5, 2.0), (0.5, 8.0)], BOX) == [[(0.5, 2.0), (0.5, 8.0)]]


def test_a_short_segment_is_cut_like_a_long_one() -> None:
    """A segment under a unit long is kept inside and cut where it crosses an edge."""
    assert cut_line([(5.0, 5.0), (5.5, 5.0)], BOX) == [[(5.0, 5.0), (5.5, 5.0)]]
    (piece,) = cut_line([(9.8, 5.0), (10.3, 5.0)], BOX)
    assert piece == [(9.8, 5.0), (10.0, 5.0)]
