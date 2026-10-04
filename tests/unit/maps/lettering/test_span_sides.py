"""Which side of the route a span's line is drawn on."""

import math

from pyntpot.maps.lettering import span_sides
from pyntpot.maps.lettering.label import Span
from pyntpot.maps.lettering.span_line import SPAN_OFFSET_CAPS, _resample, span_line
from pyntpot.maps.lettering.span_sides import (
    SPAN_CURVE_MIN_COHERENCE,
    SPAN_CURVE_MIN_TURN_DEG,
    SPAN_CURVE_WEIGHT,
    _convex_side,
    _curved_side,
    bend_strength,
    route_turn,
)

from support.lettering import arc


def test_the_outside_of_a_bend_is_the_side_the_mark_stands_off_the_chord():
    """The outside is defined on the drawn mark, and this pins which one it is.

    The module signs a side two ways that disagree: `_bracket` pushes off the
    chord's own normal, the contour filters a ring with `_side_at`, and on the
    same arc the two land on opposite flanks. So nothing about the outside is
    read off a normal. It is read off the two brackets, by how far each stands
    out of the bend, and the one that does is the convex one.
    """
    centre = (200.0, 150.0)
    for radius in (80.0, 110.0, 150.0):
        for turn in (45.0, -45.0):
            route = arc(turn, r=radius)
            span = Span(name="the bend", kind="climb", i0=0, i1=len(route) - 1)
            side, marks = _convex_side(span, route, 14.0)
            assert side in (1, -1)
            assert set(marks) == {1, -1}
            line = span_line(route, 0, len(route) - 1, side, 14.0 * SPAN_OFFSET_CAPS)
            far = sum(math.dist(p, centre) for p in line) / len(line)
            assert far > radius, (
                f"the {turn:+.0f} degree bend of radius {radius:.0f} put its "
                f"bracket inside, at {far:.0f}"
            )


def test_a_straight_or_an_s_bend_has_no_outside_and_the_bend_does_not_vote():
    """The two ways "the outside" names nothing, and both fall through.

    The rule is "the outside of the curve **where there is one**". A
    straight stretch has no outside because it has no curve, and an S-bend has
    no one outside because it has two: whichever side were chosen, half the
    stretch would be written on the inside of it. Both withhold the vote and
    leave the free-paper rule to decide, which is the fall-through.
    """
    straight = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    assert bend_strength(straight, 21.0) == 0.0
    # Turning, but not enough of it to be a bend.
    assert bend_strength(arc(SPAN_CURVE_MIN_TURN_DEG * 0.7), 21.0) == 0.0
    # And a bend is a strength, not a flag: gentle votes softly, hard votes 1.
    assert 0.0 < bend_strength(arc(55.0), 21.0) < 1.0
    assert bend_strength(arc(120.0), 21.0) == 1.0
    # An S: one arc one way, the same arc back. It turns plenty and nets zero.
    first = arc(100.0, r=140.0)
    dx, dy = first[-1][0] - first[-2][0], first[-1][1] - first[-2][1]
    back = arc(-100.0, r=140.0)
    ox, oy = back[0]
    ess = first + [(x - ox + first[-1][0] + dx, y - oy + first[-1][1] + dy) for x, y in back]
    net, gross = route_turn(_resample(ess, 21.0))
    assert gross > SPAN_CURVE_MIN_TURN_DEG * 2, "the S does turn"
    assert abs(net) / gross < SPAN_CURVE_MIN_COHERENCE
    assert bend_strength(ess, 21.0) == 0.0


def test_the_bend_is_a_weighted_term_and_a_clearer_side_still_wins():
    """The bend votes where there is one, not always: the vote can be outvoted.

    A bracket goes on the outside when the free-paper rule was close to a tie,
    and stays where the paper put it when the other side is properly clearer.
    The switch turns the whole term off and the free-paper answer comes back
    unchanged, which is what makes the A/B honest.
    """
    route = arc(-80.0, r=110.0)
    span = Span(name="the bend", kind="climb", i0=0, i1=len(route) - 1)
    outside = _convex_side(span, route, 14.0)[0]
    inside = -outside
    # A near tie: the bend turns the side round.
    assert _curved_side(span, route, inside, 0.01, 14.0) == outside
    # A margin past what the vote is worth: the free paper keeps it.
    assert _curved_side(span, route, inside, SPAN_CURVE_WEIGHT * 2, 14.0) == inside
    # Already on the outside: nothing to do either way.
    assert _curved_side(span, route, outside, 0.01, 14.0) == outside
    # And with the term off, the free-paper answer stands whatever the bend.
    span_sides.SPAN_CURVE_SIDE = False
    try:
        assert _curved_side(span, route, inside, 0.01, 14.0) == inside
    finally:
        span_sides.SPAN_CURVE_SIDE = True
