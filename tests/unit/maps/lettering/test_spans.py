"""Placing spans: sides, rungs, ticks and the drawn marks."""

import logging
import math

from pyntpot.ink.polyline import foot_on, length, simplify
from pyntpot.maps.annotations import Annotations, SpanRequest
from pyntpot.maps.lettering.label import Span
from pyntpot.maps.lettering.span_clear import SPAN_CLEAR_CAPS, clear_of_route
from pyntpot.maps.lettering.span_line import SPAN_OFFSET_CAPS
from pyntpot.maps.lettering.spans import (
    SPAN_MAX,
    SPAN_RUNG_CAPS,
    SpanSurroundings,
    place_spans,
    resolve_spans,
)

from support.lettering import arc, corners, crosses, flat_dark, shapes, sheet_card
from support.measure import flat_measure


def test_the_card_carries_no_more_spans_than_the_cap():
    """Four brackets made the map cluttered, so three is the cap.

    Dropped in the payload's own order, because the agent is asked for its best
    first and that ordering is the only judgement available here.
    """
    picks = Annotations(
        spans=tuple(
            SpanRequest(name=f"span {i}", from_km=float(i), to_km=float(i) + 0.5) for i in range(6)
        )
    )
    dist = [float(m) for m in range(0, 6000, 10)]
    got = resolve_spans(picks, [], dist)
    assert len(got) == SPAN_MAX == 3
    assert {s.name for s in got} == {"span 0", "span 1", "span 2"}


def test_a_span_on_a_bend_is_drawn_on_the_convex_side_of_the_route():
    """The whole term, through `place_spans`, on a map with nothing dark on it.

    With the dark grid flat the free-paper rule is a coin toss decided by a
    tie-break, so this is exactly the near-tie the bend is meant to settle. The
    bracket lands outboard of the arc, further from its centre than the route
    is, which is the intended geometry. With the term off it is a
    coin toss again and the assertion below is not guaranteed, which is the
    point of the switch.
    """
    card = sheet_card()
    centre = (200.0, 150.0)
    for turn, radius in ((45.0, 110.0), (-45.0, 110.0), (-80.0, 110.0)):
        route = arc(turn, r=radius)
        span = Span(name="the bend", kind="climb", i0=0, i1=len(route) - 1)
        assert place_spans(
            [span], SpanSurroundings(card, route, flat_dark()), flat_measure, cap_px=14.0
        )
        assert sum(math.dist(p, centre) for p in span.line) / len(span.line) > radius, (
            f"the {turn:+.0f} degree bend drew its bracket on the inside"
        )


def test_a_span_mark_never_crosses_any_piece_of_the_route():
    """The route rule, mechanically, on every shape the map has a case for.

    Span marks are never drawn over any other piece of route. Any piece, so the whole track is
    tested and not the stretch alone, and the ticks are tested with the line
    because a tick is part of the mark. Each of these routes carries the strand
    that used to be crossed: the returning leg of an out-and-back, the far side
    of a loop, the second limb of an S, and a lane that cuts across the corner
    the span ends in.
    """
    card = sheet_card()
    for name, route in shapes().items():
        span = Span(name=name, kind="climb", i0=0, i1=len(route) - 1)
        placed = place_spans(
            [span], SpanSurroundings(card, route, flat_dark()), flat_measure, cap_px=14.0
        )
        if not placed:  # a shape with no room for a mark says so, and stops
            continue
        for part in (span.line, *span.ticks):
            assert not crosses(part, route), f"{name}: the mark crosses the route"
            assert clear_of_route(part, route, 14.0 * SPAN_CLEAR_CAPS), (
                f"{name}: the mark comes nearer the route than the clearance"
            )


def test_the_mark_follows_the_shape_in_a_few_strokes_and_does_not_hold_its_gap():
    """Rules one, two and three together, which replace the held offset.

    The mark does not keep a constant distance from the path. It approximates
    the angle of the path and, at a bend, goes out and around the bendiest
    part of the route. A mark that smooths all of that away is too straight
    and mechanical: it should be a smooth curve that follows the shape and
    could be drawn by hand in a few strokes.

    So there are two failures to keep away from, not one. The mark has to have
    the road's turns in it, and it has to have only a few of them.
    """
    card = sheet_card()
    route = [(60.0 + i * 3.0, 120.0) for i in range(30)]
    route += [(150.0 + i * 2.1, 120.0 + i * 2.1) for i in range(1, 25)]
    route += [(202.0 + i * 3.0, 172.0) for i in range(1, 30)]
    span = Span(name="the corner", kind="climb", i0=0, i1=len(route) - 1)
    assert place_spans(
        [span], SpanSurroundings(card, route, flat_dark()), flat_measure, cap_px=14.0
    )
    gaps = [foot_on(p, route)[0] for p in span.line]
    # It stands off the route the whole way, and it does not hold one distance.
    assert min(gaps) >= 14.0 * SPAN_CLEAR_CAPS
    assert max(gaps) - min(gaps) > 0.25 * span.offset_px, (
        f"the mark holds its distance: {min(gaps):.1f} to {max(gaps):.1f}"
    )
    # It has the corner in it, and it has only a few turns in all.
    assert 1 <= corners(span.line) <= 6, f"{corners(span.line)} turns is not a few strokes"
    assert corners(span.line) >= corners(simplify(route, 3.0)) - 2


def test_the_mark_stops_short_of_a_tangle_rather_than_pushing_through_it():
    """Where the ends run into other road, the mark is cut back, not forced.

    On a tight bend the mark ends well before the end of the stretch when the
    end of the stretch is a junction. Cutting back is allowed; crossing is not.
    """
    card = sheet_card()
    route = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    # A lane across the far end of the stretch, on both sides of it.
    route += [(300.0, 150.0 + i * 4.0) for i in range(1, 12)]
    span = Span(name="the lane", kind="climb", i0=0, i1=59)
    assert place_spans(
        [span], SpanSurroundings(card, route, flat_dark()), flat_measure, cap_px=14.0
    )
    assert not crosses(span.line, route)
    assert max(x for x, _ in span.line) < 300.0, (
        "the mark ran through the lane at the end of the stretch"
    )


def test_a_span_with_nowhere_to_go_is_dropped_and_says_so(caplog):
    """The answer when the route rule cannot be met is no mark, not a bad one."""
    card = sheet_card()
    # Ground the route hatches from end to end, ten pixels between strands.
    # There is nowhere on it a mark can stand a cap height clear of a road,
    # and no direction to push one that reaches open paper.
    route: list[tuple[float, float]] = []
    for row in range(30):
        y = 10.0 + row * 10.0
        legs = [(20.0 + i * 4.0, y) for i in range(90)]
        route += legs if row % 2 == 0 else list(reversed(legs))
    span = Span(name="the tangle", kind="climb", i0=900, i1=989)
    with caplog.at_level(logging.INFO, logger="pyntpot.maps.lettering.spans"):
        placed = place_spans(
            [span], SpanSurroundings(card, route, flat_dark()), flat_measure, cap_px=14.0
        )
    assert placed == [], "a mark was drawn where none can clear the route"
    assert any("clears the route" in r.message for r in caplog.records)


def test_a_mark_prefers_clear_paper_to_lying_along_a_river():
    """Clear paper is preferred, and given up rather than cross the route.

    A mark would rather not sit tight against a river or a road, and it
    gives that up rather than cross the route. It is a cost weighed against
    how much mark each side yields, not a rule: with the water on one side of
    a straight lane and clear paper on the other, the mark takes the paper.
    """
    card = sheet_card()
    route = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    river = [[(60.0 + i * 4.0, 150.0 - 20.0) for i in range(60)]]
    north, south = [], []
    for lines, out in ((None, north), (river, south)):
        span = Span(name="the lane", kind="climb", i0=0, i1=59)
        assert place_spans(
            [span],
            SpanSurroundings(card, route, flat_dark(), lines=lines),
            flat_measure,
            cap_px=14.0,
        )
        out.append(sum(y for _, y in span.line) / len(span.line))
    assert south[0] > 150.0, "the mark stayed on the water"
    # And the river only tips a choice: it is not allowed to lose the mark.
    span = Span(name="the lane", kind="climb", i0=0, i1=59)
    both = [[(60.0 + i * 4.0, 150.0 + s) for i in range(60)] for s in (-20.0, 20.0)]
    assert place_spans(
        [span], SpanSurroundings(card, route, flat_dark(), lines=both), flat_measure, cap_px=14.0
    ), "water on both sides lost the mark"


def test_an_end_tick_stops_short_of_the_route_rather_than_touching_it():
    """A tick is part of the mark, so the route rule binds it too.

    The tick points at the road, because what it says is where on the road the
    span starts. On ground where the mark sits close, the leg that points at
    the road is shortened until its tip clears it.
    """
    card = sheet_card()
    route = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    span = Span(name="the lane", kind="climb", i0=0, i1=59)
    assert place_spans(
        [span], SpanSurroundings(card, route, flat_dark()), flat_measure, cap_px=14.0
    )
    assert len(span.ticks) == 2
    clear = 14.0 * SPAN_CLEAR_CAPS
    for tick in span.ticks:
        assert clear_of_route(tick, route, clear)
        assert length(tick) > 0.0


def test_a_span_mark_sits_at_the_hand_drawn_offset():
    """The offset is measured off hand-drawn marks, not chosen between extremes.

    2.6 cap heights reads as detached and 0.9 reads as drawn on the road.
    Hand-drawn marks run 10.7 to 14.5 display pixels from the route at a 14 px
    cap height, which is 0.8 to 1.0 cap heights, and the offset is 1.2.
    """
    assert SPAN_OFFSET_CAPS == 1.2
    assert 1.9 < SPAN_RUNG_CAPS < 2.4
    # And the clearance is not scaled off it: a mark drawn nearer the road
    # still keeps half a cap height from every strand of it.
    assert SPAN_CLEAR_CAPS == 0.5
