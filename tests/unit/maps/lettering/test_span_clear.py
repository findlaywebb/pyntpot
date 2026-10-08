"""Keeping a span's mark and its end ticks clear of the route."""

import math

import pytest

from pyntpot.maps.lettering.label import TIER_SPAN, Span
from pyntpot.maps.lettering.span_clear import (
    SPAN_ALONG_MAX_BEARING_DEG,
    SPAN_CLEAR_CAPS,
    _nearest_on,
    _side_at,
    clear_of_route,
    span_bearing,
)
from pyntpot.maps.lettering.span_ends import _span_label, _span_ticks
from pyntpot.maps.lettering.span_line import span_line

from support.measure import flat_measure


def test_a_span_takes_its_name_along_it_only_when_it_runs_across_the_map():
    """The bearing rule, on three cases.

    The A39 drag and the climb out of Aviemore run across the card and read
    well with the name along them; the A361 climb runs down it and does not,
    because the letters stack and the reader has to tilt their head. The
    threshold is `SPAN_ALONG_MAX_BEARING_DEG` and it is a tunable, so the test
    is written against the tunable rather than against the number.
    """
    across = [(float(x), 100.0 + x * 0.15) for x in range(0, 300, 10)]  # ~9 deg
    slanted = [(float(x), 100.0 + x * 0.9) for x in range(0, 300, 10)]  # ~42 deg
    down = [(100.0 + y * 0.06, float(y)) for y in range(0, 300, 10)]  # ~87 deg
    assert span_bearing(across) < SPAN_ALONG_MAX_BEARING_DEG
    assert span_bearing(slanted) > SPAN_ALONG_MAX_BEARING_DEG
    assert span_bearing(down) > SPAN_ALONG_MAX_BEARING_DEG
    # And the label follows the rule rather than restating it.
    for line, along in ((across, True), (down, False)):
        span = Span(name="the long drag up the valley", kind="drag", i0=0, i1=2)
        span.line = list(line)
        label = _span_label(span, [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)], 14.0, flat_measure)
        assert bool(label.baseline) is along
        # Never a leader, either way: a name beside its own bracket needs none.
        assert label.tier == TIER_SPAN


def test_the_module_signs_a_side_one_way_and_the_mark_lands_on_it():
    """The sign bug: `_bracket` and `_side_at` disagreed, and one of them went.

    `_bracket` pushed off the chord's own normal and `_side_at` filtered the
    contour by a cross product with the opposite sense, so the two paths landed
    on opposite flanks of the same arc and anything reasoning about `side` from
    a normal was wrong on whichever half of the card took the fallback. There
    is one convention now, `_side_at`'s, and the drawn mark obeys it.
    """
    route = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    for side in (1, -1):
        line = span_line(route, 0, len(route) - 1, side, 20.0)
        assert line, f"side {side} drew nothing"
        votes = [_side_at(route, _nearest_on(route, p), p) for p in line]
        assert sum(votes) / len(votes) == side, (
            f"the mark asked for side {side} landed on the other one"
        )
    # And the two sides are the two sides: one above the lane, one below.
    left = span_line(route, 0, len(route) - 1, 1, 20.0)
    right = span_line(route, 0, len(route) - 1, -1, 20.0)
    assert (sum(y for _, y in left) < 150.0 * len(left)) != (
        sum(y for _, y in right) < 150.0 * len(right)
    )


def test_a_spans_end_tick_points_from_the_line_at_the_end_of_the_stretch():
    """The end tick replaces "square to the route".

    The end marks take their direction from the end of the line to the end of
    the segment, not perpendicular to the route's local bearing. So the direction is the vector from where the mark stops to where
    the span stops on the road. The route's own bearing at that index is a
    property of two GPS samples and is not what the reader is being shown.

    The lane here kinks in its last few samples, so the two rules point
    different ways and the test can tell them apart.
    """
    route = [(100.0 + i * 6.0, 200.0) for i in range(40)]
    route += [(334.0 + i * 2.0, 200.0 - i * 6.0) for i in range(1, 6)]
    span = Span(name="the long climb", i0=0, i1=len(route) - 1)
    span.line = [(100.0, 160.0), (300.0, 130.0)]
    ticks = _span_ticks(span, route, 14.0)
    assert len(ticks) == 2
    for tick, at in zip(ticks, (span.i0, span.i1), strict=True):
        (x0, y0), (x1, y1) = tick[0], tick[-1]
        assert (x0, y0) == pytest.approx(span.line[0] if at == span.i0 else span.line[-1]), (
            "the tick does not start at the end of the line"
        )
        want = math.atan2(route[at][1] - y0, route[at][0] - x0)
        got = math.atan2(y1 - y0, x1 - x0)
        assert abs(math.degrees(want - got)) < 1.0, (
            "the tick does not point at the end of the stretch"
        )
        assert math.hypot(x1 - x0, y1 - y0) > 0.0
    # The far tick is not square to the route's own kink, which is the whole
    # point: square to it would send the tick off to the north-east.
    (fx0, fy0), (fx1, fy1) = ticks[1][0], ticks[1][-1]
    assert fx1 > fx0 and fy1 > fy0, "the tick took the route's micro-bearing"
    # And a tick stops short of the road rather than touching it.
    for tick in ticks:
        assert clear_of_route(tick, route, 14.0 * SPAN_CLEAR_CAPS)
