"""Rings: winding, containment and clipping."""

import pytest

from pyntpot.ink.chains import join_chains
from pyntpot.maps.rings import clip_ring, cut_line, orient, signed_area


def test_rings_are_wound_so_overlapping_fills_never_stack():
    """Two overlapping woods fill once: outer rings share a winding direction."""
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    overlap = [(5.0, 5.0), (15.0, 5.0), (15.0, 15.0), (5.0, 15.0)]
    assert signed_area(orient(square, counter_clockwise=True)) > 0
    assert signed_area(orient(list(reversed(overlap)), counter_clockwise=True)) > 0
    assert signed_area(orient(square, counter_clockwise=False)) < 0


def test_a_relation_split_across_ways_is_joined_into_one_ring():
    """The Ilkley Moor is one boundary cut into pieces; the pieces are chained."""
    chains = join_chains(
        [
            [(0.0, 0.0), (10.0, 0.0)],
            [(10.0, 0.0), (10.0, 10.0)],
            [(10.0, 10.0), (0.0, 10.0), (0.0, 0.0)],
        ],
        tol=1.0,
    )
    rings = [c for c in chains if len(c) > 3]
    assert len(rings) == 1
    assert abs(signed_area(rings[0])) == pytest.approx(200.0)


def test_a_polygon_bigger_than_the_map_is_clipped_not_dropped():
    """A wood that covers everything is cut to the box, which is what shades it."""
    huge = [(-5000.0, -5000.0), (5000.0, -5000.0), (5000.0, 5000.0), (-5000.0, 5000.0)]
    cut = clip_ring(huge, (0.0, 0.0, 100.0, 50.0))
    assert abs(signed_area(cut)) == pytest.approx(10000.0)


class TestCutLine:
    """A line is cut where it crosses the box's edge, so its runs end on the edge."""

    BOX = (0.0, 0.0, 100.0, 100.0)

    def test_a_line_crossing_the_box_ends_where_it_crosses_the_edge(self):
        """The runs end on the edge, not at the last vertex inside, and keep the inner vertices."""
        line = [(-50.0, 40.0), (30.0, 40.0), (70.0, 60.0), (250.0, 60.0)]
        assert cut_line(line, self.BOX) == [
            [(0.0, 40.0), (30.0, 40.0), (70.0, 60.0), (100.0, 60.0)]
        ]

    def test_a_segment_through_a_corner_gives_a_run_of_its_two_crossings(self):
        """A long segment with both ends outside still leaves the piece of it inside the box."""
        assert cut_line([(-10.0, 50.0), (50.0, -10.0)], self.BOX) == [[(0.0, 40.0), (40.0, 0.0)]]

    def test_a_line_that_leaves_and_comes_back_is_two_runs(self):
        """Each pass through the box is its own run, cut at both crossings."""
        line = [(20.0, 50.0), (20.0, 150.0), (80.0, 150.0), (80.0, 50.0)]
        assert cut_line(line, self.BOX) == [
            [(20.0, 50.0), (20.0, 100.0)],
            [(80.0, 100.0), (80.0, 50.0)],
        ]

    def test_a_line_inside_is_kept_whole_and_one_outside_is_dropped(self):
        """No crossing means no cut: the line is returned as it is, or not at all."""
        inside = [(10.0, 10.0), (20.0, 30.0), (90.0, 90.0)]
        assert cut_line(inside, self.BOX) == [inside]
        assert cut_line([(-10.0, -10.0), (-5.0, 200.0)], self.BOX) == []

    def test_a_line_that_only_grazes_a_corner_leaves_no_run(self):
        """A line that only grazes a corner has no length inside, so no run is kept."""
        assert cut_line([(-10.0, 10.0), (10.0, -10.0)], self.BOX) == []
