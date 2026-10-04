"""A span's own line: its shape, offset and hairpin handling."""

import math

from pyntpot.ink.polyline import length
from pyntpot.maps.lettering.span_line import span_line

from support.lettering import corners, crosses


def test_a_span_that_doubles_back_is_still_one_open_gesture():
    """The iso-contour cannot self-intersect, but it can enclose.

    An out-and-back on the same lane comes back as one closed ring round both
    strands, and read by side alone every point of it qualifies: that is how
    the Aviemore bracket came to be drawn as a ring round its own climb. The
    contour is read along the route now, from the span's start to its end, with
    the caps trimmed and the run broken wherever it jumps to the other strand,
    so what comes back is one open flank whatever the route did.
    """
    out = [(100.0 + i * 4.0, 150.0) for i in range(30)]
    back = [(x, y + 1.0) for x, y in reversed(out)]
    doubled = out + back
    line = span_line(doubled, 0, len(doubled) - 1, 1, 14.0)
    assert line, "a doubled-back span drew nothing at all"
    # Not a ring: it does not come back to where it started.
    assert math.dist(line[0], line[-1]) > 0.33 * length(line)
    # And it stands off the stretch it belongs to rather than wrapping it.
    assert min(min(math.dist(p, q) for q in doubled) for p in line) > 8.0


def test_a_doubled_back_stretch_is_enclosed_rather_than_cut_across():
    """Rule four, which withdrew the rule before it.

    A mark round a stretch that comes back on itself encloses both strands.
    That used to be forbidden and the straight fallback was what enforced it,
    by drawing a rule across the middle of the loop, and that line crossed the
    route on both sides of the span. The mark goes round the outside of both
    strands now.
    """
    out = [(80.0 + i * 4.0, 150.0) for i in range(40)]
    back = [(x, y + 26.0) for x, y in reversed(out)]
    route = out + back
    line = span_line(route, 0, len(route) - 1, 1, 20.0)
    assert length(line) > 2.0 * 20.0, "the doubled-back stretch drew no mark"
    assert not crosses(line, route), "the mark cuts across the loop"
    # Corners, because the loop's own turns are corners: a route that turns
    # right round in a few pixels is not drawn as an arc. So the mark is a few
    # long strokes rather than a hundred short ones.
    assert corners(line) <= 4
    # Round the outside of both strands: the mark reaches past the turn at the
    # east end, and past both strands north and south.
    assert max(x for x, _ in line) > max(x for x, _ in route)
    assert min(y for _, y in line) < 150.0
    assert max(y for _, y in line) > 176.0


def test_a_hairpin_takes_the_short_way_over_its_own_mouth():
    """Rule three's limit: the short mark over the open end wins.

    Both strands of an out-and-back are the same piece of ground, so the two
    ways round the envelope are a short mark over the open end and a long one
    all the way out to the turn and back. The short one is taken.
    """
    out = [(60.0 + i * 4.0, 150.0) for i in range(50)]
    back = [(x, y + 6.0) for x, y in reversed(out)]
    route = out + back
    line = span_line(route, 0, len(route) - 1, 1, 20.0)
    assert line, "the hairpin drew no mark"
    assert not crosses(line, route)
    # Over the mouth, which is the west end where the two ends of the span are,
    # and nothing like the length of the stretch itself.
    assert length(line) < 0.4 * length(route)
    assert sum(x for x, _ in line) / len(line) < 100.0
