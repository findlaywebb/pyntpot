"""A span's line: the hand-drawn shape beside the route that a climb or effort is marked with.

Key names: `span_line`, the line drawn beside a stretch of route at an offset;
`shape_curve`, a stretch's raw path reduced to a few strokes; `doubling_px`, how far a
stretch doubles back on itself; `_resample`, a polyline at an even step.

It does not choose which side of the route the line sits on and does not place the name.

Invariants: the line is open, goes forward along its stretch, never crosses itself, and
a hairpin is taken over its mouth rather than cut across.
"""

import itertools
import math

from pyntpot.ink.curves import offset_curve, spline
from pyntpot.ink.polyline import Pt, foot_on, length, meet, simplify
from pyntpot.maps.lettering.span_clear import SPAN_CLEAR_CAPS, _clear_of, _nearest_on

#: The fewest points a stretch needs before it can be said to double back.
_FEWEST_TO_DOUBLE = 8

#: The fewest points that have a middle one.
_FEWEST_WITH_A_MIDDLE = 3

#: The fewest points that make a segment.
_FEWEST_FOR_A_SEGMENT = 2

#: Below this a distance in pixels is zero.
_ZERO_PX = 1e-6

#: Below this a length is zero.
_ZERO_LENGTH = 1e-9

#: How far off the route a span's first rung sits, in cap heights.
#:
#: Too far out, at 2.6 cap heights for the first rung, reads as detached; too
#: close, at 0.9, reads as drawn on the road. Hand-drawn marks measure about
#: 0.8 to 1.0 cap heights off the route, and the offset is set at 1.2. The rung
#: spacing, `SPAN_RUNG_CAPS` in `spans`, follows the same split: 2.4 at the
#: wide end against 1.9 at the near.
SPAN_OFFSET_CAPS = 1.2

#: How hard the stretch is simplified before the mark is drawn from it, as a
#: share of the offset, and how far apart the drawn line's own points sit.
#:
#: This one number is the whole argument about what a span mark is. Too fine
#: and the mark traces the road, as an iso-distance contour does: a span mark
#: needs no constant distance from the path. Too coarse and the mark throws the
#: shape away with the wiggles, as an envelope arc does: it follows the route
#: too little and looks too straight and mechanical.
#: What is wanted is between them: smoothed curves that follow the shape and
#: could be drawn by hand in a few strokes.
#:
#: A quarter of the offset keeps the significant turns of every panel of the
#: worksheet and drops the rest: two to five corners a stretch, which is what
#: a few pen strokes is. Swept over 0.15, 0.25, 0.33, 0.5 and 0.8 of the
#: offset and read against nine hand-drawn reference marks.
SHAPE_SIMPLIFY_FRAC = 0.25

SHAPE_STEP_FRAC = 0.25

#: How near the stretch has to come back to itself, in offsets, before it is
#: an out-and-back rather than a loop.
#:
#: Measured as the median distance from a point of the stretch to the nearest
#: part of it a quarter of its length away or more. Over the nine panels the
#: hairpin, which is one path walked twice, reads 0.1 offsets; the
#: loop on a wider run, whose strands are a hundred metres apart, reads 2.3; and
#: every ordinary stretch reads between 1.2 and 1.8. Half an offset is well
#: clear of everything but the hairpin, which is the one case drawn as a
#: bridge over rather than a line round.
DOUBLED_BACK_OFFSETS = 0.5


def span_line(
    route_px: list[Pt],
    i0: int,
    i1: int,
    side: int,
    offset_px: float,
    clear_px: float | None = None,
) -> list[Pt]:
    """The span's own mark: the stretch's shape, smoothed, offset and inked.

    What a person does with a pen. They look at the stretch, see the three or
    four turns in it that matter, and draw one flowing line beside it that has
    those same turns in it. Not every wiggle, and not a bridge over the lot.

    1. **The shape.** The stretch is resampled, simplified at
       `SHAPE_SIMPLIFY_FRAC` of the offset so that only its significant turns
       are left, and a spline is run through those corners. What comes out is
       the road's shape drawn in a few strokes.
    2. **Offset, not held.** The shape is pushed off to the span's own side by
       about the offset. The distance to the track then varies, opening
       over a bend the smoothing cut and closing on a straight, which is the
       intent: the mark need not keep a consistent distance from the path, and
       should approximate its angle.
    3. **Out and around the bend.** On the outside of a bend the offset stands
       further out than the road does, and on the inside any loop the offset
       ties in a tight corner is cut out, so the mark bridges the corner
       rather than doubling back through itself.
    4. **A hairpin is bridged, a loop is gone round.** A stretch that walks one
       path out and back has no room for a line between its strands, so the
       mark is a short curve standing off the mouth, which is how it is
       drawn by hand. A stretch that comes back a field away is gone round the outside,
       and going round it encloses it.
    5. **Clear of every strand of route.** Whatever comes out is pushed off any
       piece of route it came near, cut back where pushing cannot do it, and
       given up when it cannot be drawn clear on this side.

    Args:
        route_px: The whole track in card pixels. The whole of it: the mark has
            to clear the parts of the route the span does not cover as well.
        i0: First route index of the span.
        i1: Last route index of the span.
        side: +1 for the left of travel, -1 for the right, signed the way
            `_side_at` signs it.
        offset_px: About how far off the route the mark sits, in card pixels.
            About: the offset is taken off the smoothed shape, so the gap to
            the track is whatever the smoothing left.
        clear_px: How near the route the mark may come. `SPAN_CLEAR_CAPS` of a
            cap height by default, worked back from the offset.

    Returns:
        The mark in card pixels, or an empty list when it cannot be drawn clear
        of the route. An empty list is an answer: the span is dropped, and said
        to be dropped, rather than drawn across the road.
    """
    raw = route_px[i0 : i1 + 1]
    if len(raw) < _FEWEST_FOR_A_SEGMENT or offset_px <= 0:
        return []
    if clear_px is None:
        clear_px = offset_px / SPAN_OFFSET_CAPS * SPAN_CLEAR_CAPS
    if doubling_px(raw) < offset_px * DOUBLED_BACK_OFFSETS:
        raw = _mouth_path(raw, offset_px)
    shape = shape_curve(raw, offset_px)
    if len(shape) < _FEWEST_FOR_A_SEGMENT:
        return []
    line = _uncross(
        _forward_only(_drop_folds(offset_curve(shape, side, offset_px), shape, offset_px), shape)
    )
    return _clear_of(line, route_px, clear_px)


def shape_curve(raw: list[Pt], offset_px: float) -> list[Pt]:
    """The stretch as a few strokes: its significant turns, splined together.

    Douglas-Peucker first, which is what picks the turns: it keeps the points a
    reader would say the road actually turns at and drops everything the
    smoothing is meant to lose. A spline is then run through those, so what
    comes back is a curve with those turns in it rather than a polygon, and the
    spline is broken at any turn sharp enough to be a corner, so a corner stays
    a corner. See `_corners_of`.
    """
    step = max(offset_px * SHAPE_STEP_FRAC, 1.0)
    even = _resample(raw, step)
    corners = simplify(even, offset_px * SHAPE_SIMPLIFY_FRAC)
    if len(corners) < _FEWEST_FOR_A_SEGMENT:
        return list(raw)
    return spline(corners, step, _corners_of(even, corners, offset_px))


#: How much a stretch has to turn inside one offset's worth of path before the
#: mark draws that turn as a corner rather than as a curve, in degrees.
#:
#: A loop with corners in it and a tight bend that reads as one smooth arc can
#: both turn about ninety degrees in all, so the total turn is not what tells
#: them apart. What does is how far the road takes to do it. Measured over the
#: nine panels at one offset either side: the loop's two corners read 98 and 80
#: degrees, and the sharpest turn on any panel drawn as a curve is the
#: S-bend's 66. Seventy-five sits between them.
SHAPE_CORNER_DEG = 75.0


def _corners_of(path: list[Pt], corners: list[Pt], offset_px: float) -> set[int]:
    """Which of the simplified points are corners rather than bends.

    Read on the path itself and not on the simplified line, because what makes
    a corner is that the road turns inside a short distance, and the simplified
    line has already thrown that distance away.
    """
    out: set[int] = set()
    for at, q in enumerate(corners):
        if at == 0 or at == len(corners) - 1:
            continue
        i = min(range(len(path)), key=lambda k: math.dist(path[k], q))
        if _turn_over(path, i, offset_px) >= SHAPE_CORNER_DEG:
            out.add(at)
    return out


def _turn_over(path: list[Pt], at: int, reach: float) -> float:
    """How far a path turns at one point, measured over `reach` either side."""
    back, run = at, 0.0
    while back > 0 and run < reach:
        run += math.dist(path[back], path[back - 1])
        back -= 1
    fwd, run = at, 0.0
    while fwd < len(path) - 1 and run < reach:
        run += math.dist(path[fwd], path[fwd + 1])
        fwd += 1
    a, b, c = path[back], path[at], path[fwd]
    if math.dist(a, b) < _ZERO_LENGTH or math.dist(b, c) < _ZERO_LENGTH:
        return 0.0
    t1 = math.atan2(b[1] - a[1], b[0] - a[0])
    t2 = math.atan2(c[1] - b[1], c[0] - b[0])
    return abs(math.degrees((t2 - t1 + math.pi) % (2 * math.pi) - math.pi))


#: How near the shape a point of the offset line may fall before it is thrown
#: away, as a share of the offset. Seven tenths: a mitre cut back to the limit
#: still stands off by more than that, and a fold does not.
FOLD_KEEP_FRAC = 0.7


def _drop_folds(line: list[Pt], shape: list[Pt], offset_px: float) -> list[Pt]:
    """Throw away the part of an offset line that folded back inside itself.

    Where the shape turns tighter than the offset, the inner offset runs
    backwards along itself: the points are still there, in order, but they
    describe a bow tie rather than a line, and a mark drawn from them zig-zags.
    Those points are the ones that end up nearer the shape than the offset they
    were pushed by, so they can be told apart from the good ones by measuring,
    and what is left is joined across the gap, which is the corner a person
    cuts anyway.
    """
    if len(line) < _FEWEST_WITH_A_MIDDLE or len(shape) < _FEWEST_FOR_A_SEGMENT:
        return list(line)
    keep = [p for p in line if foot_on(p, shape)[0] >= offset_px * FOLD_KEEP_FRAC]
    return keep if len(keep) >= _FEWEST_FOR_A_SEGMENT else list(line)


def _forward_only(line: list[Pt], shape: list[Pt]) -> list[Pt]:
    """Keep only the part of an offset line that goes forwards along the shape.

    A fold does not merely come too near the shape, it runs backwards along it,
    and what is left of one after the near points are dropped is a V or a
    staircase. Every point is asked which point of the shape it stands beside,
    and any that stands beside an earlier one than the point before it is
    dropped. What survives runs from one end of the stretch to the other and
    never doubles back on itself.
    """
    if len(line) < _FEWEST_WITH_A_MIDDLE or len(shape) < _FEWEST_FOR_A_SEGMENT:
        return list(line)
    out: list[Pt] = []
    seen = -1
    for p in line:
        at = _nearest_on(shape, p)
        if at < seen:
            continue
        out.append(p)
        seen = at
    return out if len(out) >= _FEWEST_FOR_A_SEGMENT else list(line)


def _uncross(line: list[Pt]) -> list[Pt]:
    """Cut the loop out of a line that crosses itself.

    The inside of a bend tighter than the offset ties the offset curve in a
    little knot. A person drawing the same stroke does not tie it; they cut
    the corner. Splicing the loop out at the crossing is that cut.
    """
    out: list[Pt] = list(line)
    for _ in range(8):
        hit = _first_loop(out)
        if hit is None:
            return out
        i, j, at = hit
        out = [*out[: i + 1], at, *out[j + 1 :]]
    return out


def _first_loop(line: list[Pt]) -> tuple[int, int, Pt] | None:
    """The first place a line crosses itself, and where the crossing is."""
    for i in range(len(line) - 1):
        for j in range(i + 2, len(line) - 1):
            at = meet(line[i], line[i + 1], line[j], line[j + 1])
            if at is not None:
                return i, j, at
    return None


def doubling_px(sub: list[Pt], apart: float = 0.25) -> float:
    """How near a stretch comes back to itself, in card pixels.

    For every point, the distance to the nearest part of the stretch at least
    `apart` of its length away in index; the median of those. An out-and-back
    on one path reads a pixel or two, a loop reads the width of the loop, and
    an ordinary stretch reads whatever its own wiggle is worth.
    """
    n = len(sub)
    if n < _FEWEST_TO_DOUBLE:
        return float("inf")
    step = max(n // 120, 1)
    gap = max(int(n * apart), 1)
    seen = []
    for i in range(0, n, step):
        far = [sub[j] for j in range(0, n, step) if abs(j - i) > gap]
        if far:
            seen.append(min(math.dist(sub[i], q) for q in far))
    if not seen:
        return float("inf")
    seen.sort()
    return seen[len(seen) // 2]


#: How near an end of an out-and-back another part of it has to come to count
#: as having reached that end, as a share of how wide the mouth is. Under a
#: third: the two ends are a mouth's width apart to begin with, so a generous
#: radius is satisfied by a path that has barely left the other end.
MOUTH_NEAR_FRAC = 0.3


def _mouth_path(raw: list[Pt], offset_px: float) -> list[Pt]:
    """The piece of an out-and-back that joins its two ends, and nothing else.

    A stretch that walks one path out and back has no room for a mark between
    its strands and no sense in one that goes all the way out to the turn and
    back: a short mark across the mouth is what is wanted. But a bow drawn over
    that mouth is a template and reads as too rounded without reason. The mark
    follows the ground instead: it runs beside the path that joins the two
    ends, with the corner that path has in it.

    So the mark is drawn from that piece, and by exactly the same rules as
    every other mark. What this returns is the shortest run of the stretch that
    reaches from one end to the other: the tail from the last time it came back
    alongside its start, or the head up to the first time it reached its
    finish, whichever is shorter. When there is no such run, the two ends
    themselves, which draws a straight mark across the mouth.
    """
    a, b = raw[0], raw[-1]
    near = math.dist(a, b) * MOUTH_NEAR_FRAC
    if near < _ZERO_PX:
        return [a, b]
    back = [i for i in range(1, len(raw)) if math.dist(raw[i], a) <= near]
    fwd = [i for i in range(len(raw) - 1) if math.dist(raw[i], b) <= near]
    runs = []
    if back and max(back) < len(raw) - 2:
        runs.append(raw[max(back) :])
    if fwd and min(fwd) > 1:
        runs.append(raw[: min(fwd) + 1])
    # Judged on how much of the mouth each run actually spans, not on how long
    # it is: the path here is walked slowly and sampled densely, and the piece
    # that crosses the mouth is seventy samples of twenty pixels.
    runs = [run for run in runs if math.dist(run[0], run[-1]) > math.dist(a, b) * 0.5]
    piece = min(runs, key=length) if runs else [a, b]
    if math.dist(piece[0], piece[-1]) >= offset_px * MOUTH_MIN_SPAN:
        return piece
    # An out-and-back that finishes where it started has no mouth to cross, so
    # there is no piece of it that crosses one. The mark then runs beside the
    # first of the stretch instead, which is still the ground and still where
    # the reader is being sent.
    out = [raw[0]]
    for q in raw[1:]:
        out.append(q)
        if math.dist(out[0], q) >= offset_px * MOUTH_MIN_SPAN:
            break
    return out if len(out) > 1 else [a, b]


#: How far across a mark over the mouth of an out-and-back has to reach before
#: it is a mark at all, in offsets. Two and a half: about two cap heights of
#: drawn line at the offset.
MOUTH_MIN_SPAN = 2.5


def _resample(line: list[Pt], step: float) -> list[Pt]:
    """A polyline at an even spacing, so an arc length is a straight lookup."""
    if len(line) < _FEWEST_FOR_A_SEGMENT or step <= 0:
        return list(line)
    out = [line[0]]
    carry = 0.0
    for a, b in itertools.pairwise(line):
        run = math.dist(a, b)
        if run < _ZERO_LENGTH:
            continue
        at = step - carry
        while at < run:
            t = at / run
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            at += step
        carry = (carry + run) % step
    out.append(line[-1])
    return out
