"""What the map letters: a name's `Label` and a climb's `Span`.

Key types: `Label`, one name with its anchor, kind, tier, size and the box or window the
placer gave it; `Span`, one effort or climb with the line drawn beside the route, its
end ticks and its name; `Anchor`, `Box` and `Measure`; the `TIER_*` order in which names
claim their boxes. The rules that size and wrap a name are in `maps.lettering.label_sizing`.

It places nothing and draws nothing, and it knows no hand: a caller supplies the
`Measure`, `measure(text, size) -> (width, height)` in display pixels.

Invariants: a lower tier claims its box first.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from pyntpot.ink.polyline import Pt
from pyntpot.letters.setting import DEFAULT_LINE_PX

Anchor = Literal["start", "middle", "end"]

Box = tuple[float, float, float, float]

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

#: The kinds whose name is dropped when no seat for it, along its line or flat,
#: is on the paper. The water and the tarmac still read without their name; a
#: place, a marker or a name the caller asked for keeps its fallback.
OFF_PAPER_DROPPED_KINDS = ("river", "road")

#: `measure(text, size) -> (width, height)`, both in display pixels.
Measure = Callable[[str, float], tuple[float, float]]


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


#: Every extent a span can be drawn for. The first group is the ground, the
#: second the track, and which group a kind is in decides which side of the
#: route it sits on. A span is not only a climb: any stretch of the track
#: worth remarking on is one, which is what `steady`, `fade` and `best_effort`
#: are for.
SPAN_GROUND = ("climb", "drag", "descent", "road", "water")

SPAN_EFFORT = ("fast", "hard_set", "best_effort", "fade", "walk", "headwind", "steady", "other")


@dataclass
class Span:
    """One stretch of the track the map annotates, with extent, not a pin.

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
        """True when this span is a fact about the ground, not about the track."""
        return self.kind in SPAN_GROUND
