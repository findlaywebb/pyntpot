"""What a span's name pays for sitting near its own mark."""

import pytest

from pyntpot.maps.lettering.label import TIER_SPAN, Label
from pyntpot.maps.lettering.placement_marks import (
    SPAN_INBOARD_COST,
    SPAN_MARK_THROUGH_COST,
    _mark_gap,
    _mark_through,
)


def test_a_span_name_is_charged_for_every_corner_of_its_block():
    """A short bracket's name read as detached, and the cost could not see it."""
    # The gap a leaderless name pays for is the clear space between its anchor
    # and the near edge of its block, which says nothing at all about where the
    # rest of the block went. Off the end of a short bracket a long single line
    # clears the anchor by one rung and then runs on for its own width: near by
    # that measure, and belonging to nothing by eye. A span is measured over its
    # whole block against its whole bracket instead.
    bracket = [(100.0 + i * 8.0, 100.0) for i in range(11)]
    span = Label(
        name="the long climb out of Aviemore",
        kind="climb",
        tier=TIER_SPAN,
        size=14.0,
        px=140.0,
        py=80.0,
        mark=bracket,
    )
    beside = (108.0, 62.0, 194.0, 93.0)  # a two-line block over the middle
    off_end = (188.0, 72.0, 349.0, 88.0)  # one line, off the far end
    assert _mark_gap(off_end, span, 7.0) > _mark_gap(beside, span, 7.0)
    # And the rung the old measure would have reported is the same for both,
    # which is exactly why it could not tell them apart.
    assert _mark_gap(off_end, Label(name="x"), 7.0) == 7.0


def test_a_span_name_sits_outboard_of_its_bracket_and_never_across_it():
    """The order the eye crosses is route, line, name."""
    # The proximity pull that keeps a name beside its own bracket, left alone,
    # pulls it onto the bracket and then into the gap between the bracket and the
    # road it belongs to: the cheapest block of all is the one centred on the
    # line. Both are priced, so a name beside its own line beats a name over it
    # and a name outboard beats a name inboard.
    bracket = [(100.0 + i * 8.0, 100.0) for i in range(11)]
    # The anchor is outboard, which is what says which side outboard is.
    span = Label(
        name="the long climb",
        kind="climb",
        tier=TIER_SPAN,
        size=14.0,
        px=140.0,
        py=80.0,
        mark=bracket,
    )
    outboard = (110.0, 60.0, 190.0, 90.0)
    across = (110.0, 88.0, 190.0, 118.0)
    inboard = (110.0, 110.0, 190.0, 140.0)
    assert _mark_through(outboard, span) == 0.0
    assert _mark_through(across, span) >= SPAN_MARK_THROUGH_COST
    assert _mark_through(inboard, span) == pytest.approx(SPAN_INBOARD_COST)
    # Nothing that is not a span pays either: a river has its own rules.
    river = Label(name="Lyn", kind="river")
    assert _mark_through(across, river) == 0.0
