"""Keeping a span's mark clear of the route: the clear stretches and the bearing of a line.

Key names: `clear_of_route`, whether a line keeps its distance from every piece of the
route; `_clear_of` and `_longest_clear`, a line pushed off the route and the longest
stretch of it that stays clear; `span_bearing`, the angle a line makes across the page.

It does not shape a span's line, choose its side or draw its ticks and name, and it
never moves the route.

Invariants: a line that passes `clear_of_route` stays the stated clearance from every
piece of the route, and a stretch kept as clear is the longest one found.
"""

import itertools
import math

from pyntpot.ink.polyline import Pt, foot_on, length, seg_gap

#: The fewest points that have a middle one.
_FEWEST_WITH_A_MIDDLE = 3

#: The fewest points that make a segment.
_FEWEST_FOR_A_SEGMENT = 2

#: Below this a distance in pixels is zero.
_ZERO_PX = 1e-6

#: Below this a slab test treats a segment as parallel to the slab.
_PARALLEL_EPS = 1e-12


def _seg_in_box(a: Pt, b: Pt, x0: float, y0: float, x1: float, y1: float) -> bool:
    """Whether a segment touches an axis-aligned box, by the slab test."""
    if max(a[0], b[0]) < x0 or min(a[0], b[0]) > x1 or max(a[1], b[1]) < y0 or min(a[1], b[1]) > y1:
        return False
    if x0 <= a[0] <= x1 and y0 <= a[1] <= y1:
        return True
    dx, dy = b[0] - a[0], b[1] - a[1]
    lo, hi = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < _PARALLEL_EPS:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            lo = max(lo, t)
        else:
            hi = min(hi, t)
        if lo > hi:
            return False
    return True


#: How far from the horizontal a span may run and still have its name set along
#: it, in degrees of screen-space bearing.
#:
#: Three cases set the figure. The A66 drag and the long climb out of
#: Keswick both run across the sheet and read well with the name along them;
#: the A591 climb runs down the sheet from the viewer's point of view and does
#: not, because the letters end up stacked and the reader has to tilt their
#: head. Thirty-five degrees is where those three fall either side: it keeps
#: anything within about a sixth of a turn of horizontal and rejects the rest.
#: Set deliberately tighter than `MAX_TILT_DEG`, which is what a river may take,
#: because a river's own line is the reason the reader forgives its tilt and a
#: span's line is a bracket the renderer drew.
SPAN_ALONG_MAX_BEARING_DEG = 35.0


def span_bearing(line: list[Pt]) -> float:
    """A span line's screen-space bearing off the horizontal, 0 to 90 degrees.

    The chord, not the local tangent: what decides whether a name reads along a
    bracket is which way the bracket goes across the sheet, and a climb that
    wiggles about a westward chord still reads westward.
    """
    if len(line) < _FEWEST_FOR_A_SEGMENT:
        return 90.0
    a, b = line[0], line[-1]
    ang = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
    return min(ang, 180.0 - ang)


#: How near any strand of the route a mark may come, in cap heights.
#:
#: A hard constraint and not a cost: a span mark is never drawn over any other
#: piece of route. Any piece: the stretch the span covers, the strand it doubled back along, and
#: the part of the route that happens to pass through the same corner half an
#: hour later. Half a cap height is the width of the route stroke plus enough
#: white either side that the reader sees two lines rather than one join.
SPAN_CLEAR_CAPS = 0.5

#: How many rounds of measure-and-push the clearance repair runs, and how hard
#: the push is blurred along the line. What is blurred is the push and never
#: the line, for the reason `_blur` gives: a line pushed clear point by point
#: off a track sampled at pixel spacing is clear and drawn like a saw.
CLEAR_PASSES = 12

CLEAR_BLUR = 4

#: How far the repair may move one point of a mark in all, in clearances. Four,
#: which is about two offsets. Past that the mark is not being nudged off a
#: road, it is being thrown across the sheet, and the junction by the river
#: drew exactly that: a spike where the mark should have stopped short. A point
#: that cannot be freed inside the cap is left where it is, and what is left of
#: the mark is cut back to the run of it that is clear.
CLEAR_PUSH_CAP = 4.0


def clear_of_route(line: list[Pt], route_px: list[Pt], clear_px: float) -> bool:
    """Whether a drawn mark keeps `clear_px` from every strand of the route.

    Segment against segment, and exactly. Measured on the line and not on its
    points, because a mark drawn as four long strokes can step over a lane
    between two of its own vertices, which is exactly the fault the rule exists
    to stop; and exactly rather than by sampling, because a line sampled every
    pixel or two dips between its samples, and a mark that reads as clear by a
    tenth of a pixel and is not is worse than one that is honestly refused.

    Args:
        line: The mark, in card pixels.
        route_px: The whole track in card pixels.
        clear_px: How near the route the mark may come.

    Returns:
        True when the mark is clear of everything.
    """
    if len(line) < _FEWEST_FOR_A_SEGMENT or len(route_px) < _FEWEST_FOR_A_SEGMENT:
        return True
    near = _route_near(line, route_px, clear_px)
    if len(near) < _FEWEST_FOR_A_SEGMENT:
        return True
    for a, b in itertools.pairwise(line):
        for c, d in itertools.pairwise(near):
            if seg_gap(a, b, c, d) < clear_px:
                return False
    return True


def _route_near(line: list[Pt], route_px: list[Pt], clear_px: float) -> list[Pt]:
    """The run of route that could come near a mark, as one polyline.

    Every segment of route that touches the mark's own box grown by the
    clearance, with a break inserted between two pieces that were not
    neighbours on the route, so the gap between them is never measured as a
    piece of road.

    Segments and not points. A track sampled every few pixels has segments long
    enough to cross the box with both ends outside it, and a route kept by its
    points alone drops exactly those: the mark then measures itself against a
    road that is not there and reads as clear of one it lies on.
    """
    if len(line) < 1 or len(route_px) < _FEWEST_FOR_A_SEGMENT:
        return []
    pad = clear_px + 8.0
    x0 = min(x for x, _ in line) - pad
    x1 = max(x for x, _ in line) + pad
    y0 = min(y for _, y in line) - pad
    y1 = max(y for _, y in line) + pad
    out: list[Pt] = []
    last = -2
    for i, (a, b) in enumerate(itertools.pairwise(route_px)):
        if not _seg_in_box(a, b, x0, y0, x1, y1):
            continue
        if i > last and out:
            out.append(out[-1])  # a break: a zero-length step, not a road
        if i > last:
            out.append(a)
        out.append(b)
        last = i + 1
    return out


def _clear_of(line: list[Pt], route_px: list[Pt], clear_px: float) -> list[Pt]:
    """Push a mark off any strand of route it came near, or give it up.

    Rule seven is a constraint and not a cost, so this may move a line a long
    way and may not stop short of the answer. Each point inside the clearance
    is pushed straight out from the piece of route it is nearest, the push is
    blurred along the line so its neighbours come with it rather than a kink
    forming, and the whole thing is measured again.

    Args:
        line: The mark as it came off the envelope.
        route_px: The whole track in card pixels.
        clear_px: How near the route the mark may come.

    Returns:
        The mark, clear of the route, or an empty list when no amount of
        pushing got it clear.
    """
    if len(line) < _FEWEST_FOR_A_SEGMENT:
        return []
    out = list(line)
    walked = [0.0] * len(out)
    for _ in range(CLEAR_PASSES):
        if clear_of_route(out, route_px, clear_px):
            return out
        near = _route_near(out, route_px, clear_px * 6.0)
        if len(near) < _FEWEST_FOR_A_SEGMENT:
            return out
        feet = [foot_on(p, near) for p in out]
        want = _blur([max(0.0, clear_px * 1.3 - d) for d, _ in feet], CLEAR_BLUR)
        moved: list[Pt] = []
        for i, (p, (d, foot), push) in enumerate(zip(out, feet, want, strict=True)):
            if push <= 0.0:
                moved.append(p)
                continue
            ux, uy = (
                ((p[0] - foot[0]) / d, (p[1] - foot[1]) / d)
                if d > _ZERO_PX
                else _away_from(near, p)
            )
            step = min(push, CLEAR_PUSH_CAP * clear_px - walked[i])
            if step <= 0.0:
                moved.append(p)
                continue
            walked[i] += step
            moved.append((p[0] + step * ux, p[1] + step * uy))
        out = moved
    if clear_of_route(out, route_px, clear_px):
        return out
    return _longest_clear(out, route_px, clear_px)


#: How much of a mark has to survive being cut back for what is left to be the
#: mark, as a share of what was drawn. A mark that runs into a junction stops
#: short of it rather than pushing through it, which is how a hand-drawn mark
#: on a tight bend behaves: it ends well before the end of the stretch. Under a
#: third left, there is no mark and the span is dropped instead.
CLEAR_KEEP_FRAC = 0.34


def _longest_clear(line: list[Pt], route_px: list[Pt], clear_px: float) -> list[Pt]:
    """The longest run of a mark that is clear of the route, or nothing.

    The end of a mark is where a tangle is usually met: the stretch finishes at
    a junction, and the envelope's cap wraps round it into whatever else passes
    through. Pushing cannot help there, because every direction out of a
    junction is into a road. Stopping short can, and it is how a hand-drawn
    mark on a tight bend ends.
    """
    if len(line) < _FEWEST_WITH_A_MIDDLE:
        return []
    near = _route_near(line, route_px, clear_px)
    ok = [foot_on(p, near)[0] >= clear_px * 1.05 for p in line] if near else [True] * len(line)
    best: tuple[int, int] = (0, 0)
    at = None
    for i, good in enumerate([*ok, False]):
        if good and at is None:
            at = i
        elif not good and at is not None:
            if i - at > best[1] - best[0]:
                best = (at, i)
            at = None
    lo, hi = best
    want = length(line) * CLEAR_KEEP_FRAC
    while hi - lo >= _FEWEST_WITH_A_MIDDLE:
        cut = line[lo:hi]
        if length(cut) < want:
            break
        if clear_of_route(cut, route_px, clear_px):
            return cut
        lo, hi = lo + 1, hi - 1
    return []


def _away_from(poly: list[Pt], p: Pt) -> Pt:
    """A unit vector square to a polyline, for a point sitting exactly on it."""
    at = _nearest_on(poly, p)
    a = poly[max(at - 1, 0)]
    b = poly[min(at + 1, len(poly) - 1)]
    run = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return (-(b[1] - a[1]) / run, (b[0] - a[0]) / run)


def _blur(series: list[float], passes: int) -> list[float]:
    """A 1-2-1 blur along a series, with its ends held.

    What is blurred is the correction, never the line. A per-point correction
    read straight off a track sampled at pixel spacing is noisy, and a noisy
    correction trades a smooth bow for a rough line: the bracket has to stay
    one gesture. Blurring the correction keeps the low-frequency part, which
    is the bow, and drops the high-frequency part, which is the sampling.
    """
    out = list(series)
    for _ in range(max(passes, 0)):
        if len(out) < _FEWEST_WITH_A_MIDDLE:
            break
        nxt: list[float] = [out[0]]
        nxt += [(out[i - 1] + 2.0 * out[i] + out[i + 1]) / 4.0 for i in range(1, len(out) - 1)]
        nxt.append(out[-1])
        out = nxt
    return out


def _nearest_on(sub: list[Pt], p: Pt) -> int:
    """The index of the route point a mark's own point stands beside."""
    return min(range(len(sub)), key=lambda i: (sub[i][0] - p[0]) ** 2 + (sub[i][1] - p[1]) ** 2)


def _side_at(sub: list[Pt], at: int, p: Pt) -> int:
    """Which side of the route a point falls on, at a known index.

    +1 is the left of travel in card pixels, where y runs down the sheet. This
    is now the module's only convention: everything that signs a side signs it
    this way. `_bracket` signed it the other way round, so anything reasoning
    about a side from a normal was wrong on half the marks on the card.
    """
    a = sub[max(at - 1, 0)]
    b = sub[min(at + 1, len(sub) - 1)]
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    return 1 if cross < 0 else -1
