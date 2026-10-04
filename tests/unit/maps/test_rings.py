"""Rings: winding, containment and clipping."""

import pytest

from pyntpot.ink.chains import join_chains
from pyntpot.maps.rings import clip_ring, orient, signed_area


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


def test_a_polygon_bigger_than_the_sheet_is_clipped_not_dropped():
    """A wood that covers everything is cut to the box, which is what shades it."""
    huge = [(-5000.0, -5000.0), (5000.0, -5000.0), (5000.0, 5000.0), (-5000.0, 5000.0)]
    cut = clip_ring(huge, (0.0, 0.0, 100.0, 50.0))
    assert abs(signed_area(cut)) == pytest.approx(10000.0)
