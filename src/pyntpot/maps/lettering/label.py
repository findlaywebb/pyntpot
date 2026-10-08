"""What the map letters: a name's `Label`, a climb's `Span`, and the rules that size a name.

Key types: `Label`, one name with its anchor, kind, tier, size and the box or window the
placer gave it; `Span`, one effort or climb with the line drawn beside the route, its
end ticks and its name; `Anchor`, `Box` and `Measure`; the `TIER_*` order in which names
claim their boxes; `wrap_forms` and `block_size`, which break a long name over lines and
size the block it takes; `feature_px`, the painted width of a feature in display pixels.

It places nothing and draws nothing, and it knows no hand: a caller supplies the
`Measure`, `measure(text, size) -> (width, height)` in display pixels.

Invariants: a lower tier claims its box first; a settlement, river, road, marker or
home name is never wrapped; a wrapped name has at most `MAX_LINES` lines.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from pyntpot.ink.polyline import Pt
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.basemap import Basemap

Anchor = Literal["start", "middle", "end"]

Box = tuple[float, float, float, float]

#: The fewest lines a name must be allowed before it may wrap at all.
_FEWEST_LINES_TO_WRAP = 2

#: The fewest words a name needs before there is a place to break it.
_FEWEST_WORDS_TO_SPLIT = 2

#: The order names claim their boxes in. A settlement cannot move, because it is
#: its place; a river can slide along its own water but not off it; a climb's
#: span line and a landmark's leader can both accommodate. So the ones that
#: cannot move go first. Lower places first.
TIER_PLACE = 10

TIER_SETTLEMENT = 20

TIER_RIVER = 30

TIER_ROAD = 40

TIER_SPAN = 50

TIER_LANDMARK = 60

TIER_MARKER = 70

#: The kinds whose name sits on its own mark, so a leader would only decorate.
NO_LEADER = ("settlement", "river", "road", "marker")

#: `measure(text, size) -> (width, height)`, both in display pixels.
Measure = Callable[[str, float], tuple[float, float]]

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


@dataclass
class Label:
    """One name on the map: what it is, where it points, and where it sits.

    `px`/`py` are the anchor, the thing the name is about, in display pixels.
    `place` fills in the rest (`home_labels` does for a house): the box the
    name occupies, the point its baseline starts from with the anchor that goes
    with it, and the two ends of its leader when it has one.
    """

    name: str
    kind: str = ""
    why: str = ""
    px: float = 0.0
    py: float = 0.0
    tier: int = TIER_LANDMARK
    #: The type size in display pixels, so a hierarchy can set one kind smaller
    #: than another without the placer having to know the hierarchy.
    size: float = DEFAULT_LINE_PX
    box: Box | None = None
    tx: float = 0.0
    ty: float = 0.0
    anchor: Anchor = "start"
    #: `((x0, y0), (x1, y1))` from the anchor to the text, or None for a label
    #: that sits on its own mark and needs no leader.
    leader: tuple[Pt, Pt] | None = None
    #: The name broken into the lines it is actually written on. Empty means
    #: one line, which is `name`. The placer fills this in when a second line
    #: bought a better position, and the boxes it claimed are the block's, so
    #: what is reserved and what is drawn are the same pixels.
    lines: list[str] = field(default_factory=list)
    #: The line a curved label is set along, in display pixels. Empty is horizontal.
    baseline: list[Pt] = field(default_factory=list)
    #: The run of that line the placer actually chose, once it has chosen it.
    #: Empty means it has not, and the hand picks its own window unless `flat`.
    window: list[Pt] = field(default_factory=list)
    #: True once the placer has decided this name is set flat. The distinction
    #: from "no window yet" matters: without it the hand would look for its own
    #: window for every name the placer had already rejected one for, and the
    #: reader would see a curve the placer had never defended a box for.
    flat: bool = False
    #: Which side of its own baseline a curved name sits on: +1 above the line
    #: in display pixels, -1 below it. A span sets this outboard of the route.
    lift: float = 1.0
    #: True when this name is written *on* its own feature rather than beside
    #: it. A river drawn at the quarter kilometre it occupies has room for its
    #: own name in the water, which is where a map puts it; a river drawn at the
    #: legibility floor has not, and its name stays in the paper beside it.
    in_water: bool = False
    #: How wide the thing this name is about was painted, in display pixels. A
    #: river's name has to clear its own water and a road number its own tarmac,
    #: and the width of the mark is not the width of the centreline the name is
    #: set along. Zero on anything that is not drawn as a ribbon.
    feature_px: float = 0.0
    #: A span's meaning, which is what its colour comes from. Empty on anything
    #: that is not a span.
    intent: str = ""
    #: The mark this name belongs to, in display pixels: a span's own bracket.
    #: With no leader drawn, the only thing joining a name to its mark is that
    #: the two are near each other, and "near" has to be measured against the
    #: whole mark and the whole block. Measured from the block's middle to the
    #: nearest point of the bracket, a name set off the end of a short bracket
    #: is charged for its own width and a compact two-line block beside the
    #: middle of it is not, which is what pulls a wrapped name in close.
    mark: list[Pt] = field(default_factory=list)
    #: The points the placer may hang this name off, in display pixels. Empty
    #: means the one anchor at `px`/`py`. A span offers several, spread along
    #: its own bracket, so a name blocked beside the middle of it slides along
    #: the line rather than away from it.
    anchors: list[Pt] = field(default_factory=list)
    #: The stretch of route a span's name belongs to, as indices. The route
    #: costs a name that sits on it, and a span's name is beside the route by
    #: construction, so its own stretch is exempt: what a span must not do is
    #: cross some *other* part of the track.
    span_range: tuple[int, int] | None = None

    @property
    def text_lines(self) -> list[str]:
        """The lines this name is written on: the wrap, or the whole name."""
        return self.lines or [self.name]

    @property
    def lx(self) -> float:
        """The leader's text end, x. The anchor itself when there is no leader."""
        return self.leader[1][0] if self.leader else self.px

    @property
    def ly(self) -> float:
        """The leader's text end, y."""
        return self.leader[1][1] if self.leader else self.py

    def as_dict(self) -> dict[str, Any]:
        """The placed label as a dict, the leader's text end as `lx`/`ly`."""
        return {
            "name": self.name,
            "kind": self.kind,
            "why": self.why,
            "px": self.px,
            "py": self.py,
            "tx": self.tx,
            "ty": self.ty,
            "anchor": self.anchor,
            "lx": self.lx,
            "ly": self.ly,
            "tier": self.tier,
            "size": self.size,
        }


#: Every extent a span can be drawn for. The first group is the ground, the
#: second the session, and which group a kind is in decides which side of the
#: route it sits on. A span is not only a climb: any stretch of the track
#: worth remarking on is one, which is what `steady`, `fade` and `best_effort`
#: are for.
SPAN_GROUND = ("climb", "drag", "descent", "road", "water")

SPAN_EFFORT = ("fast", "hard_set", "best_effort", "fade", "walk", "headwind", "steady", "other")


@dataclass
class Span:
    """One stretch of the session the map annotates, with extent, not a pin.

    A span request states an extent in one of three vocabularies
    (`maps.annotations.SpanRequest`); by the time it is here it has been
    resolved to a pair of indices into the route, because that is the only
    vocabulary the drawing needs. `side`, `rank`, `offset_px`, `line`, `ticks`
    and `label` are filled in by `place_spans`.
    """

    name: str
    kind: str = "climb"
    why: str = ""
    #: One of the intents `maps.lettering_marks.SPAN_INTENT_INK` names, which is what decides
    #: the colour it is drawn in.
    intent: str = "note"
    i0: int = 0
    i1: int = 0
    #: +1 is left of the direction of travel, -1 is right, 0 is not yet chosen.
    side: int = 0
    #: The rung of the offset ladder, so overlapping spans nest rather than
    #: stack on each other.
    rank: int = 0
    offset_px: float = 0.0
    #: The offset line in display pixels, and the two end ticks, likewise.
    line: list[Pt] = field(default_factory=list)
    ticks: list[list[Pt]] = field(default_factory=list)
    label: Label | None = None

    @property
    def ground(self) -> bool:
        """True when this span is a fact about the ground, not about the session."""
        return self.kind in SPAN_GROUND


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


def _outboard(span: Span, route_px: list[Pt]) -> float:
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
