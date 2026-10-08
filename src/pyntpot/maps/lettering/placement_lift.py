"""How far a name is lifted off its line, how it tilts, and the boxes a curved name takes.

Key names: `lift_px`, `lift_baseline` and `lift_middle`, the lift of a name off its
line in pixels; `_offset_line`, a line moved sideways; `_curved_boxes`, the rectangles
that stand for the ribbon a curved name covers; `_tilt` and `_tilt_max`, how far a
line leans.

It does not choose a window of a line or a position for a name, and it draws nothing.

Invariants: the lift the placer reserves is the lift the pen writes with, so the boxes
defended are the pixels the reader sees.
"""

import itertools
import math

from pyntpot.ink.polyline import Pt, cumulative_length
from pyntpot.maps.lettering.label import Box, Label
from pyntpot.maps.lettering.placement_window import _on_line

#: The fewest points that make a segment.
_FEWEST_FOR_A_SEGMENT = 2

#: Below this a length is zero.
_ZERO_LENGTH = 1e-9

#: How far from the horizontal a window may run, in degrees, before a name is
#: not set along it. A name set down the map is read by tilting the head,
#: which is a worse fault than a name that does not follow its own feature, so
#: a steep window is not used for any kind outside `TILT_EXEMPT_KINDS`.
#:
#: Measured twice: once on the window's chord, and once on the steepest piece
#: of it, because a glyph is set on its own local tangent and not on the chord.
#: A window that runs level end to end and turns hard in the middle stands half
#: its letters on their side.
MAX_TILT_DEG = 52.0


#: What the steepest single piece of a window may do, which is a little more
#: than the chord, because one leaning letter in a curve is what a curve is.
MAX_LOCAL_TILT_DEG = 58.0


#: The kinds a steep window is never rejected for. A river
#: name follows its own water whatever the bearing, sideways or upwards
#: included, because the water is what says which water it is and a river name
#: sitting in clear paper beside its bend says nothing a reader can use. The
#: tilt test still applies to everything else, and a span's bracket still falls
#: back to flat text past `SPAN_ALONG_MAX_BEARING_DEG`.
TILT_EXEMPT_KINDS = ("river",)


def _reading(window: list[Pt]) -> list[Pt]:
    """The window turned so the name reads the more legible way along it.

    A run whose text would go right to left is written along the same line the
    other way. On a run with no horizontal component to speak of, which is what
    a river following its bend upwards is, there is no left to right to prefer,
    so the tie is broken downwards: a name read by tilting the head to the
    right is the convention, and it is the one a reader meets most often.

    This turns a window round; it never rejects one. That distinction is the
    whole of the river rule.
    """
    if len(window) < _FEWEST_FOR_A_SEGMENT:
        return window
    dx = window[-1][0] - window[0][0]
    dy = window[-1][1] - window[0][1]
    upright = abs(dx) <= abs(dy) * 0.18
    if (upright and dy < 0) or (not upright and dx < 0):
        return window[::-1]
    return window


#: How far off its own line a name sits before the width of the thing it names
#: is added, in type sizes, and how much of that width is added. A span's
#: bracket is a line the renderer drew and has no width of its own, so it takes
#: the larger clearance and nothing else.
LIFT_CAPS = 0.42


LIFT_SPAN_CAPS = 0.85


#: How much of the feature's own painted half-width the clearance stands off
#: before that gap is added. One: the name starts where the ink of the thing it
#: names stops, and `LIFT_CAPS` is the paper between them. Under one, the
#: clearance would start inside the water.
LIFT_FEATURE_FRAC = 1.0


#: Where the ink of one line of type sits about its own baseline, in type
#: sizes, above it and below it. From the face's own cap height (0.661 em) and
#: descender (0.312 em), rounded out to cover the tallest lowercase ascender.
#:
#: A clearance is a fact about the ink, and a baseline is not the ink: the
#: letters of a line of type do not straddle their baseline, they sit above it.
#: A lift applied to the baseline alone clears the feature on the side the
#: letters grow away from it and writes the whole ascent back across it on the
#: other side, putting most of the glyph pixels in the river. The side is
#: chosen by cost and neither side is wrong, so `lift_baseline` adds the
#: descent on one side and the ascent on the other.
INK_ASCENT_CAPS = 0.70


INK_DESCENT_CAPS = 0.32


def lift_px(lb: Label) -> float:
    """How far the ink of a curved name keeps off its own feature, in display px.

    A river's centreline is not its water: the Eden is painted eight or nine
    display pixels wide, and half a type size off its middle is in the river.
    For a river or a road the clearance is the painted half-width of the
    feature itself plus `LIFT_CAPS` of the type size as paper, so a wide river
    pushes its name further out than a thin one does and the whole thing
    scales with the card. Any other kind keeps `LIFT_SPAN_CAPS` of its type
    size.

    This is the clearance the *letters* keep. `lift_baseline` is what the pen
    and the placer's boxes are offset by, which is this plus whatever part of
    the letterform would otherwise be written back over the feature.

    A name written on its own water keeps no clearance at all: the water is
    what it is written on.
    """
    if lb.in_water:
        return 0.0
    if lb.kind in ("river", "road"):
        return lb.size * LIFT_CAPS + lb.feature_px * 0.5 * LIFT_FEATURE_FRAC
    return lb.size * LIFT_SPAN_CAPS


def lift_baseline(lb: Label, side: float) -> float:
    """The signed offset the baseline of a name set along a line takes.

    Args:
        lb: The label, for its clearance and its type size.
        side: Which side of the line the name sits on, positive or negative.

    Returns:
        The signed distance to offset the feature's own line by to get the
        line the pen writes on, in display pixels.
    """
    if lb.in_water:
        # Centred on the water rather than lifted off it, so `lift_middle`
        # comes out at zero and the band of ink straddles the centreline.
        return -lb.size * (INK_ASCENT_CAPS - INK_DESCENT_CAPS) / 2
    lift = lift_px(lb)
    if side >= 0:
        return lift + lb.size * INK_DESCENT_CAPS
    return -(lift + lb.size * INK_ASCENT_CAPS)


def lift_middle(lb: Label, side: float) -> float:
    """Where the middle of that name's ink band sits, off the feature's line.

    The placer reserves boxes and the pen writes glyphs, and the two have to be
    the same pixels or the placer defends paper the reader never sees used. The
    boxes are centred here; the glyphs sit on `lift_baseline`, an ascent above
    it and a descent below.
    """
    return lift_baseline(lb, side) + lb.size * (INK_ASCENT_CAPS - INK_DESCENT_CAPS) / 2


def _offset_line(line: list[Pt], lift: float) -> list[Pt]:
    """A polyline pushed off itself by `lift`, on the normal at each point.

    Signed: positive is the upper side in display pixels, where y runs down. This
    is the line a curved name is really written on, so it is what both the
    boxes and the pen use.
    """
    if len(line) < _FEWEST_FOR_A_SEGMENT or abs(lift) < _ZERO_LENGTH:
        return list(line)
    out: list[Pt] = []
    for i, (x, y) in enumerate(line):
        a = line[max(i - 1, 0)]
        b = line[min(i + 1, len(line) - 1)]
        run = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        nx, ny = (b[1] - a[1]) / run, -(b[0] - a[0]) / run
        out.append((x + nx * lift, y + ny * lift))
    return out


def _curved_boxes(window: list[Pt], lb: Label, th: float, side: float | None = None) -> list[Box]:
    """One small box every few characters of a name set along a line.

    A curved name's real extent is a ribbon, and the placer works in rectangles,
    so the ribbon is cut into a handful of them, and the placer reserves those.

    Args:
        window: The run of line the name is set on.
        lb: The label, for its size and its kind.
        th: The line height.
        side: Which side of the line to lift to; the label's own when not given.

    Returns:
        The boxes, in order along the window.
    """
    walk = _offset_line(window, lift_middle(lb, lb.lift if side is None else side))
    cum = cumulative_length(walk)
    total = cum[-1] or 1.0
    step = max(th * 0.9, 6.0)
    out: list[Box] = []
    at = 0.0
    while at < total:
        (cx, cy), _theta = _on_line(walk, cum, min(at + step / 2, total))
        half = step / 2 + 1.0
        out.append((cx - half, cy - th / 2, cx + half, cy + th / 2))
        at += step
    return out


def _tilt(line: list[Pt]) -> float:
    """How far a run leaves the horizontal, in degrees, ignoring its direction.

    A name set down the map is read by tilting the head, which is a worse
    fault than a name that does not follow its own feature, so a steep window
    is not used for any kind outside `TILT_EXEMPT_KINDS`.
    """
    a, b = line[0], line[-1]
    ang = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
    return min(ang, 180.0 - ang)


def _tilt_max(line: list[Pt]) -> float:
    """The steepest single piece of a run, which is what one glyph sits on."""
    worst = 0.0
    for a, b in itertools.pairwise(line):
        if math.dist(a, b) < _ZERO_LENGTH:
            continue
        ang = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
        worst = max(worst, min(ang, 180.0 - ang))
    return worst
