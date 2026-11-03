"""The rules that size and wrap a name: how long it is set, how it breaks, how wide its feature is.

Key types: `kind_measure`, a name's size as its kind's tracking sets it, with `KIND_TRACKING`
and `MeasureTracked`; `wrap_forms` and `block_size`, which break a long name over lines and
size the block it takes; `feature_px`, the painted width of a feature in display pixels;
`outboard`, the side of a span's line away from the route.

It places nothing and draws nothing, and it knows no hand: a caller supplies the measure.

Invariants: a settlement, river, road, marker or home name is never wrapped; a wrapped name
has at most `MAX_LINES` lines.
"""

import math
from collections.abc import Callable

from pyntpot.ink.polyline import Point
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.lettering.label import TIER_LANDMARK, TIER_SPAN, Measure, Span

#: The fewest lines a name must be allowed before it may wrap at all.
_FEWEST_LINES_TO_WRAP = 2

#: The fewest words a name needs before there is a place to break it.
_FEWEST_WORDS_TO_SPLIT = 2


#: `measure_tracked(text, size, tracking) -> (width, height)`, both in display
#: pixels, with `tracking` the extra letter spacing in em units. How the placer
#: asks how long a curved name is once the hand writes it with its kind's
#: tracking.
MeasureTracked = Callable[[str, float, float], tuple[float, float]]

#: Extra letter spacing a kind is set with, in em units. Water is set wide
#: because that is how a printed map has always said "this is a river" without
#: changing the size, and a road is set slightly wide for the same reason.
KIND_TRACKING = {"river": 0.24, "road": 0.10, "settlement": 0.05}


def kind_measure(measure_tracked: MeasureTracked, kind: str) -> Measure:
    """How wide and tall a name of one kind is as the hand writes it: with its kind's tracking.

    The hand writes every name with its kind's `KIND_TRACKING`, set flat or along a line,
    so a flat name's box is measured the same way; measured without it, a river's spaced
    letters run past the box the placer kept on the paper.
    """
    tracking = KIND_TRACKING.get(kind, 0.0)

    def measure(text: str, size: float) -> tuple[float, float]:
        """The name's width and height with the kind's tracking."""
        return measure_tracked(text, size, tracking)

    return measure


#: The kinds whose name is never broken over two lines, which is the shorter
#: list. A settlement never wraps: a place name is one thing a reader looks up
#: and breaking it reads as two places. A river, a road and a route marker are
#: set along their own line or are one word, where a second line has nowhere to
#: go. Everything else may: a span's name is a phrase the caller wrote, and
#: "the long climb out of Keswick" is 161 px of writing beside a 217 px
#: bracket, which a single line cannot sit beside without running off it. A
#: landmark may be a phrase too.
NO_WRAP_KINDS = ("settlement", "river", "road", "marker", "home")

#: The most lines a name is ever broken into: a third line on a map is a
#: paragraph, and a paragraph is not a label.
MAX_LINES: int = 2

#: The gap between two lines of one name, as a multiple of the type size.
WRAP_LEADING = 1.06

#: The shortest a wrapped line may be, in characters, and as a share of the
#: whole name; the longer of the two holds. Breaking "the steady middle hour"
#: after "the" is worse than not breaking it, and three characters of a
#: thirty-character phrase is that break exactly: without the share the card
#: draws "the" over "long climb out of Keswick", because a stub first line
#: makes the widest possible second line and the placer wants the block one
#: line tall wherever it can get it.
WRAP_MIN_CHARS = 3

WRAP_MIN_SHARE = 0.25


def wrap_forms(name: str, kind: str, tier: int = TIER_LANDMARK) -> list[list[str]]:
    """Every way this name may be written, one line first, then two.

    A break is only ever taken at a space, and only where both halves are worth
    writing, so "the long climb out of Keswick" may become "the long climb" /
    "out of Keswick" but never "the" / "long climb out of Keswick". Each split
    is offered to the placer and the placer decides; this only says which are
    allowed.

    The kind is a deny list rather than an allow list, because a span carries
    its own vocabulary as its kind ("climb", "steady", "fade") and an allow
    list would have to name all of them. The tier settles the collision in that
    vocabulary: `road` and `water` are span kinds as well as ground kinds, and
    a span named "the road along the Eden" may wrap where a road number never
    does.

    Args:
        name: The whole name.
        kind: The label's kind, which decides whether it may wrap at all.
        tier: Its tier. A span always may, whatever its kind says.

    Returns:
        The forms: the single line, then each two-line split, most balanced
        first.
    """
    whole = [name]
    if (kind in NO_WRAP_KINDS and tier != TIER_SPAN) or MAX_LINES < _FEWEST_LINES_TO_WRAP:
        return [whole]
    words = name.split()
    if len(words) < _FEWEST_WORDS_TO_SPLIT:
        return [whole]
    splits: list[tuple[float, list[str]]] = []
    for i in range(1, len(words)):
        head, tail = " ".join(words[:i]), " ".join(words[i:])
        floor = max(WRAP_MIN_CHARS, WRAP_MIN_SHARE * len(name))
        if len(head) < floor or len(tail) < floor:
            continue
        splits.append((abs(len(head) - len(tail)), [head, tail]))
    splits.sort(key=lambda kv: kv[0])
    return [whole] + [form for _bal, form in splits]


def block_size(form: list[str], size: float, measure_fn: Measure) -> tuple[float, float]:
    """How wide and how tall a wrapped name is, as one block.

    The width is the widest line and the height is the lines plus their
    leading, so the box the placer reserves is the block the hand writes.
    """
    widths: list[float] = []
    heights: list[float] = []
    for line in form:
        w, h = measure_fn(line, size)
        widths.append(w)
        heights.append(h)
    tall = max(heights) + (len(form) - 1) * size * WRAP_LEADING
    return max(widths), tall


#: What each class of watercourse is painted at when the layers carry no width
#: for the class, in display pixels. The painter's own defaults, so such a map
#: letters its rivers where any other does.
WET_PX_DEFAULT = {"major": 8.4, "medium": 5.5, "minor": 2.2}

#: What a named road is painted at, in display pixels. The number sits over the
#: tarmac it names, so it clears the mark the same way a river name does.
ROAD_PX_DEFAULT = {"major": 5.0, "medium": 3.4}

#: What the painter's brush really lays down, as a multiple of the nominal
#: width the layers carry. A brush is not a rule: it bleeds, smooths and
#: drifts past its own nominal edge, and a clearance taken against the nominal
#: width stands a name off less water than it has to clear. Measured on the
#: painted plates, the major watercourse's ink reaches 1.30 times its nominal
#: half-width on one card and 1.42 on another. The painter records only the
#: nominal width, so this measured factor stands in for the width painted.
WET_SPREAD = 1.35


def feature_px(basemap: Basemap, kind: str, cls: str, own: float = 0.0) -> float:
    """How wide the painter's ink really is for one watercourse or road.

    The layers' `wet_px` is the brush's nominal width, not its footprint, so
    the spread the brush adds is put back on here.

    `own` is the width this particular watercourse was painted at, which is its
    own where one could be measured and the class floor where it could not; a
    river takes the wider of `own` and its class floor, because a river can be
    painted far wider than its class (the Calder at a quarter of a kilometre)
    and a name lifted by the class floor alone would be set in the water. A
    road takes its class width and ignores `own`.
    """
    if kind == "river":
        wet = basemap.layers.wet_px
        floor = float(wet.get(cls, WET_PX_DEFAULT.get(cls, 2.2)))
        return max(floor, float(own or 0.0)) * WET_SPREAD
    return float(ROAD_PX_DEFAULT.get(cls, 3.4)) * WET_SPREAD


def outboard(span: Span, route_px: list[Point]) -> float:
    """Which side of a span's own line is away from the route: +1 or -1.

    The line is the stretch's smoothed shape pushed off the route, bridged at a
    hairpin and pushed clear where it came near (`span_line`), not a contour
    held at one distance, so the answer cannot be taken from the offset's sign.
    It is read off the drawing instead: the line's normal at its middle point
    is compared with the way from the route's middle point to the line's, and
    the way the text lifts is the way that puts it further from the track.
    """
    if not span.line or not route_px:
        return 1.0
    mid = span.line[len(span.line) // 2]
    here = route_px[min(max((span.i0 + span.i1) // 2, 0), len(route_px) - 1)]
    i = min(max(len(span.line) // 2, 1), len(span.line) - 1)
    (ax, ay), (bx, by) = span.line[i - 1], span.line[i]
    run = math.hypot(bx - ax, by - ay) or 1.0
    up = ((by - ay) / run, -(bx - ax) / run)
    away = (mid[0] - here[0], mid[1] - here[1])
    return 1.0 if up[0] * away[0] + up[1] * away[1] >= 0 else -1.0
