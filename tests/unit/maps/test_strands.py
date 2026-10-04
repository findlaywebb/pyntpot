"""Strand separation: the two limbs of a doubled-back route are drawn beside each other."""

from itertools import pairwise

from pyntpot.maps.strands import separate_strands


def test_a_doubled_back_stretch_is_drawn_as_two_strands():
    """An out-and-back on one path is two lines with paper between them.

    Drawn on its own true line the second pass lands in the first one's gaps
    and the reader cannot tell an out-and-back from a single pass, which is
    what happened along a shared path.
    """
    out = [(float(x), 100.0) for x in range(0, 400, 4)]
    back = [(float(x), 100.0) for x in range(400, 0, -4)]
    moved = separate_strands(out + back, 12.0)
    assert len(moved) == len(out + back)
    # The middle of each limb, well clear of the ends where the two rejoin.
    a = moved[len(out) // 2]
    b = moved[len(out) + len(back) // 2]
    assert abs(a[1] - b[1]) > 8.0, "the two limbs are still on one line"
    # And neither has wandered further off the ground than half the gap.
    assert all(abs(y - 100.0) <= 6.01 for _x, y in moved)


def test_a_route_that_never_doubles_back_is_left_where_it_is():
    """Nothing is displaced on a route with no second pass on any of it."""
    line = [(float(x), 100.0) for x in range(0, 400, 4)]
    assert separate_strands(line, 12.0) == line


def test_a_bend_is_not_mistaken_for_a_second_strand():
    """A hairpin comes back to itself within a few of its own widths.

    The two sides of one corner are the same pass, and pushing them apart
    would straighten a real bend.
    """
    corner = [(0.0, 0.0), (20.0, 0.0), (24.0, 4.0), (20.0, 8.0), (0.0, 8.0)]
    assert separate_strands(corner, 12.0) == corner


def test_the_strands_part_and_rejoin_as_a_curve():
    """No step where the displacement starts: a kink is a fault in the line."""
    out = [(float(x), 100.0) for x in range(0, 600, 4)]
    back = [(float(x), 100.0) for x in range(600, 300, -4)]
    moved = separate_strands(out + back, 12.0)
    steps = [abs(b[1] - a[1]) for a, b in pairwise(moved)]
    assert max(steps) < 1.0, "the displacement comes on as a step, not a ramp"
