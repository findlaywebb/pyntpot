"""Strand merging: a stretch the route runs more than once is drawn as one stroke."""

from itertools import pairwise

from pyntpot.maps.strands import merge_strands

#: The merge reach the tests draw with, in display pixels.
REACH = 12.0


def _limb_rows(
    moved: list[tuple[float, float]], out_len: int, back_len: int
) -> tuple[float, float]:
    """The rows of the middle of the outward limb and of the middle of the return limb."""
    return moved[out_len // 2][1], moved[out_len + back_len // 2][1]


def test_an_out_and_back_on_one_path_is_one_stroke():
    """An out-and-back on the very same pixels is drawn where it ran, as one line.

    Pulled apart, the two limbs read as two parallel strokes with the road
    showing between them, which is how the Armadale leg on the Skye card read.
    """
    out = [(float(x), 100.0) for x in range(0, 400, 4)]
    back = [(float(x), 100.0) for x in range(400, 0, -4)]
    route = out + back
    assert merge_strands(route, REACH) == route


def test_a_return_a_few_pixels_off_the_way_out_is_drawn_on_it():
    """A return leg a few pixels beside the outward one meets it on one line between them.

    A track recorded on the other side of the road on the way back is still
    the same leg, and drawn on its own line it is a second stroke beside the
    first.
    """
    out = [(float(x), 100.0) for x in range(0, 400, 4)]
    back = [(float(x), 106.0) for x in range(400, 0, -4)]
    moved = merge_strands(out + back, REACH)
    assert len(moved) == len(out + back)
    a, b = _limb_rows(moved, len(out), len(back))
    assert abs(a - b) < 1.0, "the two limbs are still two strokes"
    assert abs(a - 103.0) < 1.0, "the limbs met somewhere other than between them"


def test_a_leg_run_three_times_is_one_stroke():
    """Out, back and out again, each a few pixels off the last, end on one line.

    The repeated retrace is where three near-parallel strokes came from.
    """
    out = [(float(x), 100.0) for x in range(0, 400, 4)]
    back = [(float(x), 104.0) for x in range(400, 0, -4)]
    again = [(float(x), 102.0) for x in range(0, 400, 4)]
    moved = merge_strands(out + back + again, REACH)
    column = [y for x, y in moved if abs(x - 200.0) < 2.0]
    assert len(column) >= 3
    assert max(column) - min(column) < 1.5, "the three passes are still apart"


def test_a_route_that_never_comes_back_is_left_where_it_is():
    """Nothing is moved on a route with no second pass on any of it."""
    line = [(float(x), 100.0) for x in range(0, 400, 4)]
    assert merge_strands(line, REACH) == line


def test_a_second_road_beyond_the_reach_is_its_own_stroke():
    """A pass further away than the reach is another road, and keeps its own line."""
    out = [(float(x), 100.0) for x in range(0, 400, 4)]
    back = [(float(x), 100.0 + REACH + 2.0) for x in range(400, 0, -4)]
    route = out + back
    assert merge_strands(route, REACH) == route


def test_a_bend_is_not_mistaken_for_a_second_pass():
    """A hairpin comes back to itself within a few of its own widths.

    The two sides of one corner are the same pass, and pulling them together
    would close a real bend.
    """
    corner = [(0.0, 0.0), (20.0, 0.0), (24.0, 4.0), (20.0, 8.0), (0.0, 8.0)]
    assert merge_strands(corner, REACH) == corner


def test_the_limbs_meet_and_part_as_a_curve():
    """No step where the pull starts: a kink is a fault in the line."""
    out = [(float(x), 100.0) for x in range(0, 600, 4)]
    back = [(float(x), 106.0) for x in range(600, 300, -4)]
    route = out + back
    moved = merge_strands(route, REACH)
    pull = [m[1] - r[1] for m, r in zip(moved, route, strict=True)]
    assert max(abs(p) for p in pull) > 2.0, "nothing was pulled"
    steps = [abs(b - a) for a, b in pairwise(pull)]
    assert max(steps) < 1.0, "the pull comes on as a step, not a ramp"
