"""What the map letters, where each name sits, and how wide it is.

One module owns the label layer, so the page and the standalone card put a
name in the same place: `charts.journal_map` and the map's lettering stage both
resolve their picks here and both call `place`. Nothing here draws. A caller takes the
placed `Label`s and the placed `Span`s and strokes them with whatever machinery
it has, vector on the page or a brush on a plate.

Three things are worth knowing before changing anything in here.

**The measure is the caller's, and it is required.** Every box on the sheet is
sized by the `measure` a caller passes to `place`, `place_spans` and
`home_labels`; there is no default. The map letters with the hand's own
`Hand.measure`, so the boxes the placer defends are the widths the letterforms
really take.

**A span is not a pin.** A climb has an extent, and the extent is thrown away
the moment it becomes a latitude and a longitude. `Span` carries the extent
through to a line drawn beside the route, offset by an iso-distance contour
rather than by a normal, because a normal offset self-intersects on exactly the
hairpins a climb is made of.

**The ground is drawn in the map's ink; the session is drawn in the route's
ink.** Settlements, rivers, roads, climbs and landmarks are the ground. Effort
spans and route markers are the session. Every other rule in here follows from
that one.
"""

from __future__ import annotations

import logging
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from pyntpot.ink.chains import joined
from pyntpot.ink.curves import offset_curve, spline
from pyntpot.ink.polyline import (
    cumulative_length,
    foot_on,
    length,
    meet,
    seg_gap,
    simplify,
)
from pyntpot.letters.setting import DEFAULT_LINE_PX

if TYPE_CHECKING:
    from pyntpot._port.paint import PaintStyle
    from pyntpot.ink.brush_style import BrushStyle
    from pyntpot.maps.basemap import Basemap, Line
    from pyntpot.maps.plates import Plates

log = logging.getLogger(__name__)

Anchor = Literal["start", "middle", "end"]
Pt = tuple[float, float]
Box = tuple[float, float, float, float]
#: The named lines a label may be set along, by kind: `roads` and `rivers`
#: (one entry a named line), `coast` and `crossings` (bare point lists), in
#: card metres. `named_lines` builds it from a basemap.
NamedLines = dict[str, list[Any]]

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

#: The type size a label takes when nothing sets one is `DEFAULT_LINE_PX`, in
#: display pixels, which the hand's setting module owns; it is the yardstick the
#: other kinds' sizes are set as shares of.

#: `measure(text, size) -> (width, height)`, both in display pixels.
Measure = Callable[[str, float], tuple[float, float]]

#: What a name laid across a road costs. Not a constraint: sometimes there is
#: nowhere else, and a name that vanished would be worse than one that crosses
#: a lane. It is priced against the leader, which costs `LEADER_COST_PX` a
#: pixel, so this buys about two hundred pixels of leader. That ratio is the
#: rule: a longer leader is a cheaper thing to spend than a road crossing, and "Braemar Castle" should step left rather than let
#: "Castle" sit on the tarmac.
ROAD_CROSS_COST = 90.0
#: What a pixel of leader costs, so the two are directly comparable.
LEADER_COST_PX = 0.4

#: How far a candidate may reach from its anchor before the leader is silly.
#: Four rungs, because with a road crossing priced at ninety the placer needs
#: somewhere further out to step to.
LEADER_RUNGS = (16.0, 30.0, 46.0, 64.0)

#: How many times the placer looks for two leaders that cross and swaps the
#: names over. The placer is greedy in tier order, so each name takes the
#: cheapest paper it can see and neither of two names knows the other's leader
#: exists; two of them reaching past each other is the result, and it joins
#: the wrong name to the wrong pin. Swapping
#: two crossing leaders always shortens them both, so the pass converges, and
#: three sweeps settle every arrangement a card of this size produces.
LEADER_UNCROSS_PASSES = 3

#: What clear space is worth. Absence of collision is not the same as being
#: legible: where several positions are all valid the one furthest from
#: everything already on the sheet is the one to take, and this is what a pixel
#: of that distance is worth against the rest of the cost.
SEPARATION_WEIGHT = 0.55
#: Past this, more room is not worth having. A name this far from its nearest
#: neighbour is as separated as a reader can tell.
SEPARATION_CAP_PX = 90.0

#: How near the track still costs a name something, in display pixels, and what
#: sitting on it costs. The reach was a flat nine pixels, which is under half a
#: line height: a twenty-pixel name could sit ten pixels off the track for
#: nothing, and "the long climb out of Keswick" did exactly that and read as
#: written through the route. A caller that knows the type size passes it in.
ROUTE_REACH_PX = 9.0
ROUTE_ON_COST = 260.0

#: What a span's own stretch of route counts for, against every other part of
#: the track. A quarter: enough to break a tie between two windows on the same
#: bracket, not enough to send the name away from the bracket altogether.
SPAN_OWN_ROUTE_FRAC = 0.25

#: What setting a name on the thing it names is worth, against setting it in
#: clear paper beside it. A river written along its water and a span written
#: along its bracket both say something a horizontal name cannot, so the curve
#: wins ties and wins near-ties; it does not win when the only window left puts
#: the name on top of two others.
ALONG_BONUS = 70.0

#: What a pixel of travel away from where a curved name started costs. Light,
#: because the freedom to slide along the whole feature is the point; not zero,
#: because with the separation reward and nothing pulling back, two names of one
#: river both run to opposite corners of the card and neither ends up where the
#: river is worth naming.
ANCHOR_PULL = 0.22

#: How far past the card's edge a mark may not go, in display pixels. The edge
#: is a constraint and never a penalty: a name in the torn margin is not a
#: cheaper answer than an awkward one on the paper, it is not an answer.
EDGE_PX = 14.0

#: Past this much turning across the run, text is not set along a line. The one
#: rule that separates elegant from unreadable.
MAX_TURN_DEG = 62.0
#: And past this much wander off the straight line between its ends.
MAX_BOW_FRAC = 0.09
#: And past this far from the horizontal. A name set down the sheet is read by
#: tilting the head, which is a worse fault than a name that does not follow
#: its own river, so a steep window is not used at all.
#:
#: Measured twice: once on the window's chord, and once on the steepest piece
#: of it, because a glyph is set on its own local tangent and not on the chord.
#: A window that runs level end to end and turns hard in the middle stands half
#: its letters on their side.
MAX_TILT_DEG = 52.0
#: What the steepest single piece of a window may do, which is a little more
#: than the chord, because one leaning letter in a curve is what a curve is.
MAX_LOCAL_TILT_DEG = 58.0
#: Under this many characters a curve is noise rather than a baseline. Three,
#: because "Eden" is a river name and the whole reason a river has a baseline is
#: that the water says which water it is.
MIN_CURVED_CHARS = 3

#: The kinds a steep window is never rejected for. A river
#: name follows its own water whatever the bearing, sideways or upwards
#: included, because the water is what says which water it is and a river name
#: sitting in clear paper beside its bend says nothing a reader can use. The
#: tilt test still applies to everything else, and a span's bracket still falls
#: back to flat text past `SPAN_ALONG_MAX_BEARING_DEG`.
TILT_EXEMPT_KINDS = ("river",)

#: The kinds whose name may sit on either side of the line it follows. A river
#: and a road are lines on the ground with paper on both sides of them, and
#: which side reads better is a question about what is underneath, not about
#: the feature: it is answered by the same cost as everything else.
TWO_SIDED_KINDS = ("river", "road")

#: What the ground terms a river's window is scored on are discounted by. A
#: river must follow its bend now, so the only thing these terms still decide
#: is *which* bend, and at full price they were deciding it wrongly: a river
#: crossing a pale wash or a thin lane is ordinary cartography and should not
#: be priced like a name laid across a road. Overlap with another label is not
#: discounted, because two names on top of each other is still two names on top
#: of each other.
RIVER_GROUND_FRAC = 0.35

#: How much water a name needs under it before it is written on the water, as a
#: multiple of its own type size. Two and a bit: the letters occupy about one
#: type size of band, so this leaves better than half a size of water either
#: side of them. Measured against the width the river is *typically* drawn at
#: rather than its widest point, because a name set on the water may be set
#: anywhere along it.
IN_WATER_CAPS = 2.2

#: What a bridge under a name written on the water costs, per share of the name
#: that sits on one. Priced with the route rather than with `ROAD_CROSS_COST`:
#: a name in clear paper clipping a lane is ordinary and cheap to allow, and a
#: river's name with a bridge drawn through its letters is neither.
IN_WATER_ROAD_COST = 320.0

#: How near its own feature a road or a river name set flat has to stay, in
#: display pixels beyond its own type size, and what a pixel past that costs.
#: A road name a reader cannot join to a road is not a road name: "Keswick
#: Road" sat far enough off its tarmac that the association was a guess.
OWN_FEATURE_SLACK_PX = 6.0
OWN_FEATURE_COST_PX = 3.0

#: What a span's own bracket may do, which is more than a river's water may.
#: A river is a fact about the ground and the reader meets its name without
#: having been following the water; a span's name and its bracket are one
#: gesture drawn together, and the eye arrives at the name already travelling
#: along the line, so it forgives a curve a river's name could not take.
SPAN_MAX_TURN_DEG = 115.0
SPAN_MAX_BOW_FRAC = 0.19

#: Where a leaderless name sits, in display pixels of clear space from the mark
#: it belongs to, and what a pixel of that gap costs. Far tighter than a
#: leadered label's, and for the reason the leader exists: with no line drawn
#: between them, the only thing joining a name to its mark is that they are
#: near each other, so the name has to stay near. A span, a settlement, a river
#: that could not be set along its water and a road all take these.
NEAR_RUNGS = (7.0, 12.0, 20.0, 30.0)
NEAR_GAP_COST_PX = 4.0

#: How far the middle of a span's name may sit from its own bracket before the
#: gap starts costing, as a multiple of the type size.
#:
#: A block set immediately beside the middle of a bracket has its middle about
#: one line height off it however tight the placement is, so a gap cost with no
#: slack in it is a magnet: it pulls the name onto the bracket and then onto
#: the road the bracket belongs to, whose own cost is at a quarter weight over
#: the span's own stretch. With the first line height and a half free, the
#: proximity cost says nothing at all about the placements that are already
#: near enough and everything about the ones that are not, and the route cost
#: still decides between the near ones.
SPAN_MARK_SLACK = 1.5

#: What a pixel of that gap costs a span, once the slack is used up. Heavier
#: than the leaderless cost every other kind pays, because a bracket is a mark
#: the renderer drew and a reader has nothing else to go on: a river name near
#: the wrong bend is still on the right river, and a span name near the wrong
#: bracket belongs to nothing at all.
SPAN_MARK_COST_PX = 14.0

#: What writing a name across its own bracket costs. The proximity cost above
#: pulls a name towards its mark and, on its own, pulls it right onto it: the
#: cheapest block of all is the one centred on the line, and the reader gets
#: the bracket struck through the middle of the words. Priced a little above a
#: road crossing, so a name beside its own line always beats a name over it.
SPAN_MARK_THROUGH_COST = 110.0

#: What sitting on the route's side of its own bracket costs a span's name.
#: The order the eye crosses should be route, line, name: the bracket is what
#: says which stretch of road the name is about, and a name in the gap between
#: the bracket and the road it belongs to has the mark reading as a rule drawn
#: under it rather than as a bracket beside the route. The anchors are outboard
#: already; without this the rungs walk the block straight back over them.
SPAN_INBOARD_COST = 150.0

#: The kinds whose name is never broken over two lines, which is the shorter
#: list. A settlement never wraps: a place name is one thing a reader looks up
#: and breaking it reads as two places. A river, a road and a route marker are
#: set along their own line or are one word, where a second line has nowhere to
#: go. Everything else may: a span's name is a phrase the review agent wrote,
#: and "the long climb out of Keswick" is 161 px of writing beside a 217 px
#: bracket, which is why every awkward placement on the card traced back to
#: there being no line breaking at all. A landmark may be a phrase too.
NO_WRAP_KINDS = ("settlement", "river", "road", "marker", "home")

#: The most lines a name is ever broken into. Two. A third line on a map is a
#: paragraph, and a paragraph is not a label.
MAX_LINES = 2

#: What a second line costs, so it is taken only when it buys a materially
#: better position rather than whenever it is marginally cheaper. Priced above
#: a rung of leader and below a road crossing: worth having to get off the
#: route, not worth having to save a few pixels of separation.
#:
#: Chosen by argument first and now measured against a card that exercises it.
#: On the Dovedale ride, "the long climb out of Keswick" costs 190.4 on
#: one line and 133.7 on its best two, so a break buys 56.7; "the A591 climb
#: past Ambleside" costs 107.1 against 105.5, so a break buys 1.6. Anything
#: from about 2 to about 56 separates those two cases, and 26 is the middle of
#: that window: the first wraps, the second does not, and neither is close to
#: the edge.
WRAP_COST = 26.0

#: The gap between two lines of one name, as a multiple of the type size.
WRAP_LEADING = 1.06

#: The shortest a wrapped line may be, in characters, and as a share of the
#: whole name. Breaking "the steady middle hour" after "the" is worse than not
#: breaking it, and three characters of a thirty-character phrase is that break
#: exactly: the card drew "the" over "long climb out of Keswick" until the
#: share was added, because a stub first line makes the widest possible second
#: line and the placer wanted the block one line tall wherever it could get it.
WRAP_MIN_CHARS = 3
WRAP_MIN_SHARE = 0.25


@dataclass
class Label:
    """One name on the sheet: what it is, where it points, and where it sits.

    `px`/`py` are the anchor, the thing the name is about, in card pixels.
    Everything else is filled in by `place`: the box the name occupies, the
    point its baseline starts from with the anchor that goes with it, and the
    two ends of its leader when it has one.
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
    #: The line a curved label is set along, in card pixels. Empty is horizontal.
    baseline: list[Pt] = field(default_factory=list)
    #: The run of that line the placer actually chose, once it has chosen it.
    #: Empty means it has not, and the hand picks its own window as it used to.
    window: list[Pt] = field(default_factory=list)
    #: True once the placer has decided this name is set flat. The distinction
    #: from "no window yet" matters: without it the hand went looking for its
    #: own window for every name the placer had already rejected one for, and
    #: the reader saw a curve the placer had never defended a box for. That was
    #: the whole of the curved-label fault, surviving one layer further down.
    flat: bool = False
    #: Which side of its own baseline a curved name sits on: +1 above the line
    #: in card pixels, -1 below it. A span sets this outboard of the route.
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
    #: The mark this name belongs to, in card pixels: a span's own bracket.
    #: With no leader drawn, the only thing joining a name to its mark is that
    #: the two are near each other, and "near" has to be measured against the
    #: whole mark and the whole block. Measured from the block's middle to the
    #: nearest point of the bracket, a name set off the end of a short bracket
    #: is charged for its own width and a compact two-line block beside the
    #: middle of it is not, which is what pulls a wrapped name in close.
    mark: list[Pt] = field(default_factory=list)
    #: The points the placer may hang this name off, in card pixels. Empty
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
        """The placed label in the shape the drawing code has always read."""
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
#: route it sits on. A span is not only a climb: any stretch of the activity
#: worth remarking on is one, which is what `steady`, `fade` and `best_effort`
#: are for.
SPAN_GROUND = ("climb", "drag", "descent", "road", "water")
SPAN_EFFORT = ("fast", "hard_set", "best_effort", "fade", "walk", "headwind", "steady", "other")

#: How many spans one card carries. Four made the sheet cluttered: with the
#: settlements, the rivers, the roads and the landmarks already on it, three
#: brackets is where the card still reads as a map rather than as a diagram.
#: Spans past the cap are dropped in the order the payload wrote them, so the
#: agent's own "best first" decides which survive.
SPAN_MAX = 3


@dataclass
class Span:
    """One stretch of the session the map annotates, with extent, not a pin.

    The payload states an extent in one of three vocabularies (`schema.Span`);
    by the time it is here it has been resolved to a pair of indices into the
    route, because that is the only vocabulary the drawing needs. `side`,
    `rank`, `line` and `label` are filled in by `place_spans`.
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
    #: The offset line in card pixels, and the two end ticks, likewise.
    line: list[Pt] = field(default_factory=list)
    ticks: list[list[Pt]] = field(default_factory=list)
    label: Label | None = None

    @property
    def ground(self) -> bool:
        """True when this span is a fact about the ground, not about the session."""
        return self.kind in SPAN_GROUND


# --------------------------------------------------------------------------- picks


def journal_picks(picks: Any, basemap: Basemap, cap: int) -> list[dict[str, Any]]:
    """The payload's landmarks, each with a position, in the payload's order.

    A pick states its own latitude and longitude, which is what the label agent
    is asked for. A pick that is only a name is looked up in the candidates the
    box offered, so an older payload still labels its map.
    """
    wanted = list(getattr(picks, "landmarks", None) or [])
    if not wanted:
        return []
    by_name = {c["name"]: c for c in basemap.candidates}
    out: list[dict[str, Any]] = []
    for entry in wanted:
        if isinstance(entry, str):
            found = by_name.get(entry)
            if not found:
                continue
            out.append(
                {
                    "name": entry,
                    "kind": found.get("class", ""),
                    "why": "",
                    "x": found["x"],
                    "y": found["y"],
                }
            )
            continue
        name = getattr(entry, "name", "")
        lat, lng = getattr(entry, "lat", None), getattr(entry, "lng", None)
        item = {
            "name": name,
            "kind": getattr(entry, "kind", "") or "",
            "why": getattr(entry, "why", "") or "",
        }
        if lat is None or lng is None:
            found = by_name.get(name)
            if not found:
                continue
            item["x"], item["y"] = found["x"], found["y"]
        else:
            item["lat"], item["lng"] = float(lat), float(lng)
        out.append(item)
        if len(out) >= cap:
            break
    return out


def journal_heuristic(basemap: Basemap, cap: int) -> list[dict[str, Any]]:
    """The fallback when the payload named none: the nearest named things."""
    out = []
    for c in basemap.candidates:
        out.append(
            {
                "name": c["name"],
                "kind": c.get("class", ""),
                "why": f"nearest named feature, {c.get('distance_m')} m off the route",
                "x": c["x"],
                "y": c["y"],
            }
        )
        if len(out) >= cap:
            break
    return out


# --------------------------------------------------------------------------- placing


def place(
    labels: list[Label],
    spans: list[Span],
    card: Any,
    route_px: list[Pt],
    dark: dict[str, Any],
    taken: list[Box],
    measure_fn: Measure,
    roads: list[list[Pt]] | None = None,
) -> list[Label]:
    """Put every name somewhere, cheapest cost first, in tier order.

    Curved names are placed here too, which they were not: a river or a road or
    a span used to claim the box its anchor happened to fall in and then be set
    along a window chosen afterwards, at drawing time, by the hand. That is why
    "Derwent" sat over "Braemar Castle": the box the placer defended and the
    pixels the reader saw were in different places. The window is chosen here
    now, against everything already on the sheet, and the run of small boxes it
    really occupies goes back into the pile for the next name to avoid.

    It is also the one funnel every name on the sheet goes through, whichever
    pool found it, so it is where `dedupe_names` can see that the settlement
    "Elm" and the nearest-named-feature "Elm" are one village.

    Returns fewer labels than it was given where two of them named one place.

    Args:
        labels: The names to place, each with its anchor already in card pixels.
        spans: Spans to place first, so a span line is on the sheet before
            anything looks for room. Placed in place; their names join the
            queue and are placed with everything else.
        card: The card, for its width and height in display pixels.
        route_px: The track in card pixels.
        dark: The painter's darkness grid, `{"w", "h", "v"}`.
        taken: Boxes already spoken for, such as the home glyph's.
        measure_fn: How wide and tall a name is.
        roads: Named road centrelines in card pixels. A name laid across one is
            costed, never forbidden.

    Returns:
        The same labels, in tier order, each carrying its box, its text anchor
        and, when it is set along a line, the run of line it is set along.
    """
    boxes = list(taken)
    todo = list(labels)
    if spans:
        place_spans(
            spans,
            card,
            route_px,
            dark,
            measure_fn=measure_fn,
            avoid=_places_to_avoid(labels),
            lines=roads or [],
        )
        todo += [span.label for span in spans if span.label is not None]
    ordered = sorted(dedupe_names(todo, card), key=lambda lb: lb.tier)
    return _place(ordered, card, route_px, dark, boxes, measure_fn, roads or [])


#: How far a settlement's own ground reaches, in multiples of the size its
#: name is lettered at. A town is lettered larger than a village and takes up
#: more of the sheet, so one number covers both. Three: on a 900 px card that
#: is about 70 px round a town, which is the built-up part of the corner a
#: span mark is drawn round rather than through.
SETTLEMENT_GROUND_SIZES = 3.0


def _places_to_avoid(labels: list[Label]) -> list[tuple[float, float, float, float]]:
    """The settlements a span mark would rather not be drawn through.

    `(x, y, weight, radius)` in card pixels, weighted by how large the name is
    set, which is how the sheet already says how big the place is.
    """
    return [
        (lb.px, lb.py, lb.size / DEFAULT_LINE_PX, lb.size * SETTLEMENT_GROUND_SIZES)
        for lb in labels
        if lb.kind == "settlement"
    ]


def named_lines(basemap: Basemap, tol_px: float) -> NamedLines:
    """The lines a name can be set along, simplified, in the card's own metres.

    The named centrelines and the coastline, at a tolerance that is generous
    because a baseline is read at a glance and never measured.

    Args:
        basemap: The basemap, for its roads, watercourses and coastline.
        tol_px: Simplification tolerance in display pixels.

    Returns:
        `{"roads": [...], "rivers": [...], "coast": [...], "crossings": [...]}`:
        each road and river entry a name, a class, a road number where OSM has
        one, the painted widths and a polyline `d`; each coast and crossing
        entry a bare polyline.
    """
    layers = basemap.layers
    tol = max(tol_px * float(basemap.card.mpp_display), 1.0)

    def kept_lines(line: Line) -> list[list[list[float]]]:
        out = []
        for piece in [list(line)] if len(line) > 1 else []:
            kept = simplify(piece, tol)
            if len(kept) > 1:
                out.append([[x, y] for x, y in kept])
        return out

    named: dict[str, list[dict[str, Any]]] = {
        "roads": [
            {"n": r.name, "c": r.cls, "r": r.ref, "w": 0.0, "wn": 0.0, "line": r.line}
            for r in layers.roads
        ],
        "rivers": [
            {
                "n": r.name,
                "c": r.cls,
                "r": "",
                "w": r.width_px,
                "wn": r.name_width_px,
                "line": r.line,
            }
            for r in layers.rivers
        ],
    }
    geom: NamedLines = {"roads": [], "rivers": [], "coast": [], "crossings": []}
    for key in ("roads", "rivers"):
        for entry in named[key]:
            for line in kept_lines(entry["line"]):
                if entry["n"]:
                    # `w` is the width this watercourse was actually painted at,
                    # which is its own where one could be measured and the class
                    # floor where it could not. A name clears the ink it is set
                    # beside, so it has to be the ink that was laid down and not
                    # what the class would have laid down.
                    geom[key].append(
                        {
                            "n": entry["n"],
                            "c": entry["c"],
                            "r": entry["r"],
                            "w": entry["w"],
                            "wn": entry["wn"],
                            "d": line,
                        }
                    )
                else:
                    # An unnamed lane can carry no name of its own, so a label
                    # could be laid across one for nothing. It is kept, without
                    # a name, purely so the crossing cost can see it.
                    geom["crossings"].append(line)
    for coast in layers.coastline:
        geom["coast"].extend(kept_lines(coast))
    return geom


def road_lines(lines: NamedLines, card: Any) -> list[list[Pt]]:
    """Everything on the card a name should not be laid across, in card pixels.

    The named roads, the unnamed lanes, and the watercourses. All three are
    marks on the paper and a name written over any of them is harder to read;
    the named roads were the only ones charged, so a label could sit on an
    unnamed lane for nothing and "Swell" could sit on its own river. The
    lanes have no name and cannot carry one, so they are kept in `crossings`
    purely for this.
    """
    out: list[list[Pt]] = []
    geom = lines
    for key in ("roads", "rivers"):
        for entry in geom.get(key) or []:
            line = [card.xy(x, y) for x, y in entry.get("d") or []]
            if len(line) > 1:
                out.append(line)
    for raw in geom.get("crossings") or []:
        line = [card.xy(x, y) for x, y in raw]
        if len(line) > 1:
            out.append(line)
    return out


def _crossings(box: Box, roads: list[list[Pt]]) -> int:
    """How many roads a box sits on. One count a road, not one a segment."""
    if not roads:
        return 0
    x0, y0, x1, y1 = box
    hit = 0
    for line in roads:
        for a, b in zip(line, line[1:], strict=False):
            if _seg_in_box(a, b, x0, y0, x1, y1):
                hit += 1
                break
    return hit


def _on_road(box: Box, roads: list[list[Pt]]) -> float:
    """Whether a box sits on tarmac at all: 1.0 or 0.0.

    Deliberately not a count. A name that lands on a junction touches five ways
    and is one fault, not five, and counting them made a crossing the most
    expensive thing on the sheet by an order of magnitude.
    """
    return 1.0 if _crossings(box, roads) else 0.0


def _seg_in_box(a: Pt, b: Pt, x0: float, y0: float, x1: float, y1: float) -> bool:
    """Whether a segment touches an axis-aligned box, by the slab test."""
    if max(a[0], b[0]) < x0 or min(a[0], b[0]) > x1:
        return False
    if max(a[1], b[1]) < y0 or min(a[1], b[1]) > y1:
        return False
    if x0 <= a[0] <= x1 and y0 <= a[1] <= y1:
        return True
    dx, dy = b[0] - a[0], b[1] - a[1]
    lo, hi = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
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


def _overlap(box: Box, boxes: list[Box]) -> float:
    """Total area a box shares with what is already placed."""
    x0, y0, x1, y1 = box
    total = 0.0
    for bx0, by0, bx1, by1 in boxes:
        wide = min(x1, bx1) - max(x0, bx0)
        tall = min(y1, by1) - max(y0, by0)
        if wide > 0 and tall > 0:
            total += 6 + wide * tall * 0.5
    return total


def _separation(box: Box, boxes: list[Box]) -> float:
    """How far a box sits from the nearest thing already on the sheet.

    Capped, because past `SEPARATION_CAP_PX` more room is not something a
    reader can tell apart, and uncapped it would drag every name to the corner
    of the card furthest from the rest.
    """
    if not boxes:
        return SEPARATION_CAP_PX
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    best = SEPARATION_CAP_PX
    for bx0, by0, bx1, by1 in boxes:
        dx = max(bx0 - cx, 0.0, cx - bx1)
        dy = max(by0 - cy, 0.0, cy - by1)
        best = min(best, math.hypot(dx, dy))
    return best


def _darkness(box: Box, card: Any, dark: dict[str, Any]) -> float:
    """Mean darkness of the painter's own grid under a box."""
    gw, gh, grid = dark["w"], dark["h"], dark["v"]
    x0, y0, x1, y1 = box
    gx0 = max(int(x0 / card.w * gw), 0)
    gx1 = min(int(x1 / card.w * gw) + 1, gw)
    gy0 = max(int(y0 / card.h * gh), 0)
    gy1 = min(int(y1 / card.h * gh) + 1, gh)
    cells = [grid[r][c] for r in range(gy0, gy1) for c in range(gx0, gx1)]
    return sum(cells) / len(cells) if cells else 0.3


def _on_paper(box: Box, card: Any) -> bool:
    """Whether a box is wholly on the sheet rather than in the torn margin."""
    x0, y0, x1, y1 = box
    return EDGE_PX < x0 and x1 < card.w - EDGE_PX and EDGE_PX < y0 and y1 < card.h - EDGE_PX


def _place(
    labels: list[Label],
    card: Any,
    route_px: list[Pt],
    dark: dict[str, Any],
    boxes: list[Box],
    measure_fn: Measure,
    roads: list[list[Pt]],
) -> list[Label]:
    """Place each label, curved along its own line where it has one.

    The cost is what the reader would complain about: text over the route, text
    on top of another label, text on a dark wash, text laid across a road. The
    card's edge is not in that list because it is not a cost: a candidate on
    the paper beats every candidate off it outright.
    """
    placed: list[Label] = []
    thin = route_px[::3] or route_px
    # Where each name has already been set along its own line, so the major
    # river's second name lands somewhere else on the water rather than beside
    # its first.
    repeats: dict[str, list[float]] = {}
    for lb in labels:
        tw, th = measure_fn(lb.name, lb.size)
        mine = _route_for(lb, route_px, thin)
        crossings = _off_own(roads, lb)
        along = None
        if lb.baseline and len(lb.name) >= MIN_CURVED_CHARS:
            along = _place_along(
                lb, tw, th, card, dark, boxes, crossings, mine, repeats.get(lb.name, [])
            )
        flat = _best_flat(lb, card, mine, dark, boxes, crossings, measure_fn)
        # Two real candidates, one scale. Setting a name on its own feature is
        # worth something in itself, and `ALONG_BONUS` is that something; past
        # it, a name jammed against three others on its river is worse than the
        # same name in clear paper beside it, and the placer should be able to
        # say so rather than always preferring the curve.
        #
        # A river is the exception: where its own water
        # offers any usable window at all the name goes on the water, whatever
        # the flat answer costs.
        if along is not None and lb.kind in TILT_EXEMPT_KINDS:
            flat = float("inf")
        if along is not None and along[0] - ALONG_BONUS < flat:
            cells, window = along[1], along[2]
            lb.window = window
            lb.lift = along[4]
            lb.flat = False
            # A name on a curve is one line by construction.
            lb.lines = []
            xs = [v for box in cells for v in (box[0], box[2])]
            ys = [v for box in cells for v in (box[1], box[3])]
            lb.box = (min(xs), min(ys), max(xs), max(ys))
            lb.tx, lb.ty = window[len(window) // 2]
            lb.anchor = "middle"
            lb.leader = None
            boxes.extend(cells)
            repeats.setdefault(lb.name, []).append(along[3])
        else:
            boxes.append(lb.box)
        placed.append(lb)
    _uncross_leaders(placed, card, route_px, thin, dark, roads)
    return placed


def _leader_px(lb: Label) -> float:
    """How long one label's leader is, in card pixels."""
    return math.dist(lb.leader[0], lb.leader[1]) if lb.leader else 0.0


def _centre(box: Box) -> Pt:
    """The middle of a box."""
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def _seat(lb: Label) -> tuple[Any, ...]:
    """Everything `_reseat` overwrites, so a refused swap can be put back."""
    return (lb.box, lb.tx, lb.ty, lb.anchor, lb.leader)


def _unseat(lb: Label, state: tuple[Any, ...]) -> None:
    """Put a label back where it was before a swap was tried."""
    lb.box, lb.tx, lb.ty, lb.anchor, lb.leader = state


def _reseat(lb: Label, cx: float, cy: float) -> None:
    """Move a placed flat block so its middle sits at `(cx, cy)`.

    The block keeps its own width, its own wrap and its own size: only where it
    sits changes, and everything the placer derived from that (the text anchor,
    the first baseline, the leader's text end) is rebuilt from the new middle
    exactly as `_place_flat` derived it from the old one.
    """
    x0, y0, x1, y1 = lb.box
    tw, th = x1 - x0, y1 - y0
    ax, ay = lb.leader[0]
    ox = 0 if abs(cx - ax) <= tw / 2 else (1 if cx > ax else -1)
    lb.box = (cx - tw / 2, cy - th / 2, cx + tw / 2, cy + th / 2)
    lb.tx = (cx + (tw / 2 if ox < 0 else -tw / 2)) if ox else cx
    lb.ty = cy + 6 - (len(lb.text_lines) - 1) * lb.size * WRAP_LEADING / 2
    lb.anchor = "middle" if not ox else ("end" if ox < 0 else "start")
    lb.leader = ((ax, ay), (cx - ox * tw / 2 if ox else cx, cy))


def _seat_cost(
    lb: Label,
    card: Any,
    route_px: list[Pt],
    thin: list[Pt],
    dark: dict[str, Any],
    roads: list[list[Pt]],
    others: list[Box],
) -> float:
    """What one flat block's position costs, leader length aside.

    The same ground terms `_place_flat` scored the candidate on, so a swap that
    would drop a name onto the route, into a wood or across a road is refused
    by the numbers that would have refused it at placement time. The leader is
    left out because a swap is a trade between two of them and is priced over
    the pair.
    """
    box = lb.box
    cost = 0.0 if _on_paper(box, card) else 400.0
    cost += _near_route(box, _route_for(lb, route_px, thin), max(ROUTE_REACH_PX, lb.size))
    cost += _overlap(box, others)
    cost += _darkness(box, card, dark) * 150
    cost += _on_road(box, roads) * ROAD_CROSS_COST
    cost += _off_own_feature(box, lb)
    return cost


def _pair_cost(
    a: Label,
    b: Label,
    card: Any,
    route_px: list[Pt],
    thin: list[Pt],
    dark: dict[str, Any],
    roads: list[list[Pt]],
    others: list[Box],
) -> float:
    """What two names cost where they currently sit, leaders included.

    `b` is costed against `a`'s box as well as the rest of the sheet, so the
    overlap the two would make with each other is charged once rather than
    twice or not at all.
    """
    return (
        _seat_cost(a, card, route_px, thin, dark, roads, others)
        + _seat_cost(b, card, route_px, thin, dark, roads, others + [a.box])
        + (_leader_px(a) + _leader_px(b)) * LEADER_COST_PX
    )


def _swap_seats(
    a: Label,
    b: Label,
    placed: list[Label],
    card: Any,
    route_px: list[Pt],
    thin: list[Pt],
    dark: dict[str, Any],
    roads: list[list[Pt]],
) -> bool:
    """Put each of two names where the other was, and keep it if it reads better.

    Returns True when the swap was kept.
    """
    others = [lb.box for lb in placed if lb is not a and lb is not b and lb.box is not None]
    was = (_seat(a), _seat(b))
    before = _pair_cost(a, b, card, route_px, thin, dark, roads, others)
    here, there = _centre(a.box), _centre(b.box)
    _reseat(a, *there)
    _reseat(b, *here)
    crossed = meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is not None
    after = _pair_cost(a, b, card, route_px, thin, dark, roads, others)
    if not crossed and after < before:
        return True
    _unseat(a, was[0])
    _unseat(b, was[1])
    return False


def _uncross_leaders(
    placed: list[Label],
    card: Any,
    route_px: list[Pt],
    thin: list[Pt],
    dark: dict[str, Any],
    roads: list[list[Pt]],
) -> None:
    """Swap two names over where their leaders cross.

    The placer is greedy in tier order: each name takes the cheapest paper it
    can see, and neither of two names knows that the other has a leader at all.
    Two of them reaching past each other is what comes of that, and a reader
    meeting a crossing follows the wrong line to the wrong pin. Swapping the
    two names over is the fix rather than moving either of them away, because
    the paper each is sitting on was already the cheapest either could find and
    exchanging them strictly shortens both leaders.

    A swap is offered, not imposed. It is kept only when the pair no longer
    crosses *and* the two names together cost less than they did, on the same
    ground terms the placer priced them with, so a name is never swapped onto
    the route or into a wood to straighten a line.
    """
    seats = [lb for lb in placed if lb.flat and lb.leader is not None and lb.box is not None]
    for _ in range(LEADER_UNCROSS_PASSES):
        swapped = False
        for i, a in enumerate(seats):
            for b in seats[i + 1 :]:
                if meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is None:
                    continue
                swapped |= _swap_seats(a, b, placed, card, route_px, thin, dark, roads)
        if not swapped:
            return


#: How near a crossing line has to run to a name's own feature, and how much of
#: it has to, before it is taken to *be* that feature. The lines come from the
#: same simplified geometry the baseline was chained from, so they coincide
#: exactly; the tolerance is for the arithmetic, not for the map.
OWN_LINE_PX = 2.0
OWN_LINE_FRAC = 0.9


def _is_own_feature(line: list[Pt], baseline: list[Pt]) -> bool:
    """Whether one crossing line is a piece of the feature a name belongs to."""
    if len(line) < 2 or len(baseline) < 2:
        return False
    near = 0
    for p in line:
        if foot_on(p, baseline)[0] <= OWN_LINE_PX:
            near += 1
    return near >= OWN_LINE_FRAC * len(line)


def _off_own(roads: list[list[Pt]], lb: Label) -> list[list[Pt]]:
    """The lines a name is charged for crossing, its own feature removed.

    `road_lines` is everything a name should not be laid across, and it holds
    the watercourses as well as the tarmac. For a name set along its own
    feature that includes the feature itself, so every candidate window scored
    as "on a road" and the term cancelled out: a river's name could not be
    moved off a bridge because it was already on a road wherever it went.

    **A name is not charged for crossing the thing it names.** Everything else
    still counts, which is what leaves a bridge as the one road under a river's
    name that means anything.
    """
    if not lb.baseline:
        return roads
    return [line for line in roads if not _is_own_feature(line, lb.baseline)]


def _route_for(lb: Label, route_px: list[Pt], thin: list[Pt]) -> list[tuple[list[Pt], float]]:
    """The route this label keeps off, and how much each part of it counts.

    A span's bracket is drawn beside its own extent, so its name is near that
    stretch by design, and charging the full price there would rule out the one
    position the span is meant to take. It is not free either: given two windows
    on the same bracket, the one that does not have the track running through
    the middle of the word is the better one, and at a quarter weight the placer
    can say so without the answer being decided by it.
    """
    if lb.span_range is None:
        return [(thin, 1.0)]
    i0, i1 = lb.span_range
    own = [p for j, p in enumerate(thin) if i0 <= j * 3 <= i1]
    rest = [p for j, p in enumerate(thin) if not (i0 <= j * 3 <= i1)]
    out = [(rest, 1.0)] if rest else []
    if own:
        out.append((own, SPAN_OWN_ROUTE_FRAC))
    return out or [(thin, 1.0)]


def wrap_forms(name: str, kind: str, tier: int = TIER_LANDMARK) -> list[list[str]]:
    """Every way this name may be written, one line first, then two.

    A break is only ever taken at a space, and only where both halves are worth
    writing, so "the long climb out of Keswick" may become "the long climb" /
    "out of Keswick" but never "the" / "long climb out of Keswick". Each split
    is offered to the placer and the placer decides; this only says which are
    allowed.

    The kind is a deny list rather than an allow list, because a span carries
    its own vocabulary as its kind ("climb", "steady", "fade") and an allow
    list would have had to name all of them, which is how the first version of
    this missed every span on the card. The tier settles the collision in that
    vocabulary: `road` and `water` are span kinds as well as ground kinds, and
    a span named "the road along the Eden" may wrap where a road number never
    does.

    Args:
        name: The whole name.
        kind: The label's kind, which decides whether it may wrap at all.
        tier: Its tier. A span always may, whatever its kind says.

    Returns:
        The forms, cheapest-intent first: the single line, then each two-line
        split, most balanced first.
    """
    whole = [name]
    if (kind in NO_WRAP_KINDS and tier != TIER_SPAN) or MAX_LINES < 2:
        return [whole]
    words = name.split()
    if len(words) < 2:
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
    widths, heights = [], []
    for line in form:
        w, h = measure_fn(line, size)
        widths.append(w)
        heights.append(h)
    tall = max(heights) + (len(form) - 1) * size * WRAP_LEADING
    return max(widths), tall


def _best_flat(
    lb: Label,
    card: Any,
    thin: list[tuple[list[Pt], float]],
    dark: dict[str, Any],
    boxes: list[Box],
    roads: list[list[Pt]],
    measure_fn: Measure,
) -> float:
    """The cheapest horizontal answer over every way the name may be broken.

    A second line is charged `WRAP_COST`, so it is taken when it buys a
    materially better position and not when it merely ties. The label is left
    holding whichever form won, with the block's own box.
    """
    best: tuple[float, list[str], Any] | None = None
    for form in wrap_forms(lb.name, lb.kind, lb.tier):
        tw, th = block_size(form, lb.size, measure_fn)
        cost = _place_flat(lb, tw, th, card, thin, dark, boxes, roads, len(form))
        cost += WRAP_COST * (len(form) - 1)
        state = (lb.box, lb.tx, lb.ty, lb.anchor, lb.leader)
        if best is None or cost < best[0]:
            best = (cost, form, state)
    cost, form, state = best
    lb.lines = form if len(form) > 1 else []
    lb.box, lb.tx, lb.ty, lb.anchor, lb.leader = state
    lb.window = []
    lb.flat = True
    return cost


def _mark_gap(box: Box, lb: Label, fallback: float) -> float:
    """How far a block sits from the mark it names, for the leaderless cost.

    A rung is the clear space between the anchor and the near edge of the
    block, which is the right measure for a name beside a point and the wrong
    one beside a line. Off the end of a short bracket a wide block clears the
    anchor by one rung and then runs on for its own width, and nothing in the
    cost notices, so a name can read as belonging to nothing.

    A span is measured over the whole block instead: its middle and its four
    corners, each against the nearest point of its own bracket, each allowed
    the slack, and the five averaged. The middle alone is not enough, because
    a long single line centred on a short bracket has its middle on the mark
    and both its ends in open country; charging the corners is what makes a
    compact two-line block beside the line the cheap answer and a banner across
    it the dear one.
    """
    if lb.tier != TIER_SPAN or not lb.mark:
        return fallback
    x0, y0, x1, y1 = box
    slack = lb.size * SPAN_MARK_SLACK
    at = [((x0 + x1) / 2, (y0 + y1) / 2), (x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    gaps = [
        max((foot_on(p, lb.mark)[0] if len(lb.mark) > 1 else math.dist(p, lb.mark[0])) - slack, 0.0)
        for p in at
    ]
    return sum(gaps) / len(gaps)


def _mark_through(box: Box, lb: Label) -> float:
    """What a block across, or inboard of, its own bracket costs.

    Two faults with one measure, because both are about where the block sits
    relative to the line rather than how far off it is: the bracket struck
    through the words, and the block sitting in the gap between the bracket and
    the road it brackets.
    """
    if lb.tier != TIER_SPAN or not lb.mark:
        return 0.0
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    hw, hh = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
    cost = 0.0
    for px, py in lb.mark:
        if abs(px - cx) <= hw and abs(py - cy) <= hh:
            cost += SPAN_MARK_THROUGH_COST
            break
    mid = lb.mark[len(lb.mark) // 2]
    out = (lb.px - mid[0], lb.py - mid[1])
    run = math.hypot(*out)
    if run < 1e-6:
        return cost
    _d, foot = foot_on((cx, cy), lb.mark)
    side = ((cx - foot[0]) * out[0] + (cy - foot[1]) * out[1]) / run
    if side < 0.0:
        cost += SPAN_INBOARD_COST
    return cost


def _place_flat(
    lb: Label,
    tw: float,
    th: float,
    card: Any,
    thin: list[tuple[list[Pt], float]],
    dark: dict[str, Any],
    boxes: list[Box],
    roads: list[list[Pt]],
    nlines: int = 1,
) -> float:
    """One horizontal name beside its anchor, on the cheapest rung that fits.

    Fills the label in and returns what that answer cost, so the caller can
    hold it against setting the same name along its own line.
    """
    offs = [(1, 0), (-1, 0), (1, -1), (-1, -1), (1, 1), (-1, 1), (0, -1), (0, 1)]
    near_mark = lb.tier == TIER_SPAN or lb.kind in NO_LEADER
    rungs = NEAR_RUNGS if near_mark else LEADER_RUNGS
    per_px = NEAR_GAP_COST_PX if near_mark else LEADER_COST_PX
    best = None
    on_paper = None
    for ax, ay in lb.anchors or [(lb.px, lb.py)]:
        for ox, oy in offs:
            for dist in rungs:
                cx = ax + ox * (dist + tw / 2 if ox else 0)
                cy = ay + oy * (dist + th / 2 if oy else 0)
                if not ox:
                    cx = ax
                x0, y0 = cx - tw / 2, cy - th / 2
                box = (x0, y0, x0 + tw, y0 + th)
                cost = 0.0
                inside = _on_paper(box, card)
                if not inside:
                    cost += 400
                cost += _near_route(box, thin, max(ROUTE_REACH_PX, lb.size))
                cost += _overlap(box, boxes)
                cost += _darkness(box, card, dark) * 150
                cost += _on_road(box, roads) * ROAD_CROSS_COST
                cost += _off_own_feature(box, lb)
                gap_px = SPAN_MARK_COST_PX if lb.tier == TIER_SPAN else per_px
                cost += _mark_gap(box, lb, dist) * gap_px
                cost += _mark_through(box, lb)
                cost -= _separation(box, boxes) * SEPARATION_WEIGHT
                here = (cost, cx, cy, x0, y0, ox, ax, ay)
                if best is None or cost < best[0]:
                    best = here
                if inside and (on_paper is None or cost < on_paper[0]):
                    on_paper = here
    cost, cx, cy, x0, y0, ox, ax, ay = on_paper or best
    lb.window = []
    lb.flat = True
    lb.box = (x0, y0, x0 + tw, y0 + th)
    lb.tx = (cx + (tw / 2 if ox < 0 else -tw / 2)) if ox else cx
    # The first baseline, not the block's middle: a two-line name is written
    # downwards from here and the block has to stay centred on the box.
    lb.ty = cy + 6 - (nlines - 1) * lb.size * WRAP_LEADING / 2
    lb.anchor = "middle" if not ox else ("end" if ox < 0 else "start")
    lb.leader = ((ax, ay), (cx - ox * tw / 2 if ox else cx, cy))
    return cost


def _off_own_feature(box: Box, lb: Label) -> float:
    """What sitting away from the thing it names costs a road or a river name.

    A name set flat beside a line still belongs to that line, and with no
    leader drawn the only thing joining them is that they are near each other.
    "Keswick Road" was far enough off its own tarmac that a reader had to
    guess which road it meant. The anchor is one point on a long feature, so
    the distance is measured to the whole centreline rather than to the anchor.
    """
    if not lb.baseline or lb.kind not in NO_LEADER:
        return 0.0
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    hw, hh = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
    near = (
        min(
            (max(abs(px - cx) - hw, 0.0) ** 2 + max(abs(py - cy) - hh, 0.0) ** 2)
            for px, py in lb.baseline
        )
        ** 0.5
    )
    return max(near - lb.size - OWN_FEATURE_SLACK_PX, 0.0) * OWN_FEATURE_COST_PX


def _near_route(
    box: Box, thin: list[tuple[list[Pt], float]], reach: float = ROUTE_REACH_PX
) -> float:
    """What sitting on or beside the route costs one box.

    Takes the route in weighted parts, because a span's own stretch counts for
    less than the rest of the track does.

    `reach` is how near counts as near, and it is the label's own type size
    rather than a flat nine pixels, which was under half a line height and let
    a twenty-pixel name sit ten pixels off the track for nothing. The cost
    falls off linearly to zero at `reach`, so widening it does not put a step
    in the middle of the placer's cost surface.

    Args:
        box: The box being scored.
        thin: The route in weighted parts.
        reach: How far from the track still costs, in display pixels.

    Returns:
        The cost, worst part of the route wins.
    """
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    hw, hh = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
    reach = max(reach, 1.0)
    worst = 0.0
    for pts, weight in thin:
        if not pts:
            continue
        near = (
            min(
                (max(abs(px - cx) - hw, 0.0) ** 2 + max(abs(py - cy) - hh, 0.0) ** 2)
                for px, py in pts
            )
            ** 0.5
        )
        # The discount a span gets over its own stretch is for sitting *beside*
        # the track, which is where its bracket put it. It is not a licence to
        # write across it: a zero here means a point of the route is inside the
        # block, so the letters have the road through them, and that costs what
        # it costs anybody else. Without this the proximity pull that keeps a
        # short bracket's name beside its bracket bought the last few pixels by
        # crossing the road.
        if near <= 0.0:
            weight = 1.0
        if near < reach:
            worst = max(worst, ROUTE_ON_COST * (1.0 - near / reach) * weight)
    return worst


def _place_along(
    lb: Label,
    tw: float,
    th: float,
    card: Any,
    dark: dict[str, Any],
    boxes: list[Box],
    roads: list[list[Pt]],
    thin: list[tuple[list[Pt], float]],
    apart_from: list[float] | None = None,
) -> tuple[float, list[Box], list[Pt], float, float] | None:
    """The run of its own line a curved name is set on, and the boxes it takes.

    Every window of the right length along the whole feature is a candidate,
    not just the one nearest the anchor. A river label may go anywhere along
    its water and that freedom is the point: it is what lets the Derwent move
    upstream and out of the Braemar names rather than sit on top of them.

    Args:
        lb: The label, carrying the whole feature as its `baseline`.
        tw: How wide the name is.
        th: How tall it is.
        card: The card, for its size.
        dark: The painter's darkness grid.
        boxes: What is already on the sheet.
        roads: Named road centrelines, for the crossing cost.
        thin: The route, thinned, in weighted parts, for the route cost.
        apart_from: How far along this same line each window this name already
            took started, in pixels of run. This is what stops the major
            river's two names converging on the same reach of water. Measured
            along the water rather than across the sheet: a river doubles back,
            and two points half a kilometre apart on the water can be a
            hundred pixels apart on the paper, which is what left the second
            "Eden" with no window at all.

    Returns:
        `(cost, boxes, window, at, side)`: what the chosen window costs on the
        same scale the flat answer is scored on, the boxes the text would
        occupy, the run of line it would sit on, how far along the line it
        starts, and which side of it the name lifts to. None when no window on
        this line is usable.
    """
    want = tw * 1.02
    span = lb.tier == TIER_SPAN
    turn_max = SPAN_MAX_TURN_DEG if span else MAX_TURN_DEG
    bow_max = SPAN_MAX_BOW_FRAC if span else MAX_BOW_FRAC
    line = _resample(lb.baseline, max(want / 24.0, 2.0))
    if length(line) < want:
        return None
    apart = max(length(line) * RIVER_REPEAT_FRAC, want)
    cum = cumulative_length(line)
    # A span's bracket is a contour and a contour can loop, so which side of it
    # is "away from the route" is not one answer for the whole line: it was
    # read once at the bracket's middle and applied everywhere, which is how
    # "the long climb out of Keswick" came to be written on the inside of its
    # own bracket with the track running through the word. Both sides are
    # candidates now and the route cost decides, which is what it is for.
    # The same for a river and a road. A name set along its own water has two
    # sides to sit on and the better one is chosen rather than assumed; the cost already knows what is under each, so both
    # are offered and it decides. Nothing here can reject a window for its
    # side: if the preferred side is blocked the other one is taken, and the
    # name still follows the bend.
    sides = (
        (lb.lift, -lb.lift) if lb.tier == TIER_SPAN or lb.kind in TWO_SIDED_KINDS else (lb.lift,)
    )
    best: tuple[float, list[Pt], list[Box], float, float, float] | None = None
    step = max(len(line) // 60, 1)
    for i in range(0, len(line), step):
        window = _window(line, i, want)
        if window is None:
            break
        turn = _turning(window)
        if turn > turn_max:
            continue
        chord = math.dist(window[0], window[-1]) or 1.0
        if _bow(window) / chord > bow_max:
            continue
        tilt = _tilt(window)
        # A river follows its own bend whatever the bearing. Everything else
        # still has a steep window refused outright: a name read by tilting the
        # head is a worse fault than a name that does not follow its feature,
        # and a span's bracket is a line the renderer drew rather than a fact
        # about the ground, so it earns less patience than water does.
        if lb.kind not in TILT_EXEMPT_KINDS and (
            tilt > MAX_TILT_DEG or _tilt_max(window) > MAX_LOCAL_TILT_DEG
        ):
            continue
        here = cum[i]
        if any(abs(here - other) < apart for other in apart_from or []):
            continue
        for side in sides:
            cells = _curved_boxes(window, lb, th, side)
            if not all(_on_paper(box, card) for box in cells):
                continue
            # Two scores, because two different questions are being asked.
            #
            # `ground` is what this position costs a reader, per box, on the
            # same terms the flat placement is scored on: what it sits on, how
            # near the route and the roads it is, how much room it has. That
            # one is what decides whether the name is set along the line at all.
            #
            # The shape terms are added only to choose between windows on the
            # same line. They must not go into the comparison with the flat
            # answer: a river that bends is not thereby better off in clear
            # paper, and pricing its own curvature against a horizontal
            # alternative meant nothing was ever set along anything.
            n = len(cells)
            # A river's window is no longer choosing whether to follow the
            # water, only which reach of it, so the terms that describe the
            # ground under the name are discounted: crossing a pale wash or a
            # thin lane is ordinary cartography. Overlap with another label is
            # not discounted.
            soft = RIVER_GROUND_FRAC if lb.kind in TILT_EXEMPT_KINDS else 1.0
            ground = sum(_overlap(box, boxes) for box in cells) / n
            # A name written on the water is not charged for the water being
            # dark: that is the ground it was sent to sit on, and charging it
            # would send the name off down the river to its palest reach.
            dark_frac = 0.0 if lb.in_water else soft
            ground += sum(_darkness(box, card, dark) for box in cells) / n * 150 * dark_frac
            # A curved name has to keep off the route as much as a flat one
            # does. It did not, because the route cost only ever existed on the
            # flat path, and the result was a span name written straight across
            # the track it belongs to.
            ground += sum(_near_route(box, thin, max(ROUTE_REACH_PX, lb.size)) for box in cells) / n
            # The share of the name that lies on tarmac, so a long name
            # clipping one lane at its tail is not scored as if the whole of it
            # were on a road.
            # A name on the water pays a route's price for a road under it. A
            # discount is right for a name in paper clipping a lane; a bridge
            # drawn through the letters of a river's name is not ordinary
            # cartography, and a name across a bridge is worse when there is a
            # clear reach of water just beside it.
            road_cost = IN_WATER_ROAD_COST if lb.in_water else ROAD_CROSS_COST * soft
            ground += (sum(_on_road(box, roads) for box in cells) / n) * road_cost
            mid = window[len(window) // 2]
            ground += math.dist(mid, (lb.px, lb.py)) * ANCHOR_PULL
            ground -= min(_separation(box, boxes) for box in cells) * SEPARATION_WEIGHT
            tilt_term = 0.0 if lb.kind in TILT_EXEMPT_KINDS else tilt * 0.8
            pick = ground + turn * 1.5 + tilt_term + (_bow(window) / chord) * 400.0
            if best is None or pick < best[0]:
                best = (pick, window, cells, ground, here, side)
    if best is None:
        return None
    _pick, window, cells, cost, at, side = best
    read = _reading(window)
    # Turning the window round turns its normal round with it, so the side the
    # name lifts to has to turn as well or the boxes the placer defended and
    # the pixels the hand writes are on opposite sides of the line.
    if read is not window:
        side = -side
    return cost, cells, read, at, side


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
    if len(window) < 2:
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
#: names stops, and `LIFT_CAPS` is the paper between them. It was 0.62, which
#: put the start of the clearance a third of the way inside the water.
LIFT_FEATURE_FRAC = 1.0

#: Where the ink of one line of type sits about its own baseline, in type
#: sizes, above it and below it. From the face's own cap height (0.661 em) and
#: descender (0.312 em), rounded out to cover the tallest lowercase ascender.
#:
#: A clearance is a fact about the ink, and a baseline is not the ink. The lift
#: used to be applied to the baseline, and the letters of a line of type do not
#: straddle their baseline: they sit above it. Lifting to the side the letters
#: grow away from the feature therefore cleared it, and lifting to the other
#: side wrote the whole ascent back across the thing the name was there to
#: clear. A label that takes that second side has most of its glyph pixels in
#: the river, while one that takes the first looks tuned. The side is chosen by
#: cost and neither side is wrong, so the geometry has to hold on both.
INK_ASCENT_CAPS = 0.70
INK_DESCENT_CAPS = 0.32


def lift_px(lb: Label) -> float:
    """How far the ink of a curved name keeps off its own feature, in display px.

    A river's centreline is not its water: the Eden is painted eight or nine
    display pixels wide and the name was lifted by half a type size off the
    middle of it, which put the letters in the river. The clearance is the
    painted half-width of the feature itself plus `LIFT_CAPS` of the type size
    as paper, so a wide river pushes its name further out than a thin one does
    and the whole thing scales with the card.

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

    Signed: positive is the upper side in card pixels, where y runs down. This
    is the line a curved name is really written on, so it is what both the
    boxes and the pen use.
    """
    if len(line) < 2 or abs(lift) < 1e-9:
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
    so the ribbon is cut into a handful of them. This is the whole of the fix
    for the collision the three variants shared: a curved label used to reserve
    nothing at all after itself.

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

    A name set down the sheet is read by tilting the head, which is a worse
    fault than a name that does not follow its own river, so a steep window is
    not used at all.
    """
    a, b = line[0], line[-1]
    ang = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
    return min(ang, 180.0 - ang)


def _tilt_max(line: list[Pt]) -> float:
    """The steepest single piece of a run, which is what one glyph sits on."""
    worst = 0.0
    for a, b in zip(line, line[1:], strict=False):
        if math.dist(a, b) < 1e-9:
            continue
        ang = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
        worst = max(worst, min(ang, 180.0 - ang))
    return worst


# --------------------------------------------------------------------------- spans


def resolve_spans(
    picks: Any, times: list[float], dist_m: list[float], cap: int = SPAN_MAX
) -> list[Span]:
    """The payload's spans, each resolved to a pair of indices into the route.

    A caller states an extent in one of three vocabularies, because it has one
    of them to hand and converting between them is the renderer's job. Indices
    go straight through; kilometres are read against the route's own cumulative
    distance; seconds are read against its clock, which only a caller holding a
    snapshot has, so a card composed from a bare track resolves the first two
    and says so about the third.

    Args:
        picks: The payload's `map` block, or None.
        times: Seconds at each route point, or empty when there is no clock.
        dist_m: Cumulative metres at each route point.
        cap: How many spans the card carries. The payload's own order decides
            which survive, because the agent is asked for its best first.

    Returns:
        One `Span` per payload entry that lands inside the route, longest first.
    """
    wanted = list(getattr(picks, "spans", None) or [])
    if not wanted or len(dist_m) < 2:
        return []
    out: list[Span] = []
    for entry in wanted:
        i0 = _span_index(entry, "from", times, dist_m)
        i1 = _span_index(entry, "to", times, dist_m)
        if i0 is None or i1 is None or i1 <= i0:
            log.info("span %r does not land on the route", getattr(entry, "name", ""))
            continue
        out.append(
            Span(
                name=getattr(entry, "name", ""),
                kind=getattr(entry, "kind", "climb") or "climb",
                why=getattr(entry, "why", "") or "",
                intent=getattr(entry, "intent", "note") or "note",
                i0=i0,
                i1=i1,
            )
        )
    if len(out) > cap:
        log.info("card carries %d spans; %d were asked for", cap, len(out))
        out = out[:cap]
    out.sort(key=lambda s: s.i0 - s.i1)
    return out


def _span_index(entry: Any, end: str, times: list[float], dist_m: list[float]) -> int | None:
    """One end of a span as an index into the route, from whichever pair it has."""
    last = len(dist_m) - 1
    idx = getattr(entry, f"{end}_i", None)
    if idx is not None:
        return max(0, min(int(idx), last))
    km = getattr(entry, f"{end}_km", None)
    if km is not None:
        return _nearest(dist_m, float(km) * 1000.0)
    secs = getattr(entry, f"{end}_s", None)
    if secs is None:
        return None
    if len(times) != len(dist_m):
        log.info("a span given in seconds needs a clock this caller has not got")
        return None
    return _nearest(times, float(secs))


def _nearest(values: list[float], target: float) -> int:
    """The index of the route point nearest a value on a monotone stream."""
    return min(range(len(values)), key=lambda i: abs(values[i] - target))


#: How far off the route a span's line sits, in cap heights, and how far apart
#: two rungs of the ladder are.
#:
#: Too far out, at 2.6 cap heights for the first rung, reads as detached; too
#: close, at 0.9, reads as drawn on the road. Hand-drawn marks measure about
#: 0.8 to 1.0 cap heights off the route, and the offset is set at 1.2. The rung
#: spacing follows the same split: 2.4 at the wide end against 1.9 at the near.
SPAN_OFFSET_CAPS = 1.2
SPAN_RUNG_CAPS = 2.1

#: How long a span's end tick is, in cap heights. It runs from the end of the
#: mark towards the end of the stretch on the road, taking the direction of
#: the segment rather than standing exactly perpendicular to the local route.
#: A tick square to the route reads as wrong.
SPAN_TICK_CAPS = 0.85

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


def place_spans(
    spans: list[Span],
    card: Any,
    route_px: list[Pt],
    dark: dict[str, Any],
    measure_fn: Measure,
    cap_px: float = 14.0,
    rails: int = 3,
    along_max_deg: float = SPAN_ALONG_MAX_BEARING_DEG,
    avoid: list[tuple[float, float, float, float]] | None = None,
    lines: list[list[Pt]] | None = None,
) -> list[Span]:
    """Choose a side and a rung for every span, and draw its mark.

    The ground takes the side of the route with more free paper over its own
    extent; the session takes the other, so the two never interleave. Where the
    stretch bends, the outside of the bend takes that choice off the free side
    unless the free side is clearly freer: see `_curved_side`. Within a side
    the longest span is the outer rail and shorter ones nest inside it, and
    only an overlapping span moves out a rung.

    The name is set along the span's own line when the span runs across the
    sheet, on the far side of the line from the route so the order the eye
    crosses is route, line, name. When the span runs down the sheet it is not:
    the name goes horizontally into whatever clear paper the placer can find
    beside it, and with no leader either way, because a name a few pixels from
    its own bracket does not need a line drawn to it.

    Args:
        spans: The resolved spans, longest first. Placed in place.
        card: The card, for its size in display pixels.
        route_px: The track in card pixels.
        dark: The painter's darkness grid.
        measure_fn: How wide a name is, so a span too short to carry its own
            name along it is known before the window search is tried.
        cap_px: The lettering's cap height, which sets the ladder's spacing.
        rails: How many rungs a side carries before a span is dropped.
        along_max_deg: The bearing threshold, in degrees off horizontal.
        avoid: Places the mark would rather not be drawn through, each an
            `(x, y, weight, radius)` in card pixels. A cost and never a rule:
            see `_drawn_side`.
        lines: The watercourses, roads and lanes, in card pixels, which a mark
            would rather not be drawn along. A cost as well.

    Returns:
        The spans that were placed. A span past the last rung is left out, and
        so is one no arc of whose envelope clears the route.
    """
    placed: list[Span] = []
    used: dict[int, list[tuple[int, int, int]]] = {1: [], -1: []}
    for span in spans:
        free, margin = _freer_side(span, route_px, dark, card, cap_px)
        base = free if span.ground else -free
        span.side = _curved_side(span, route_px, base, margin, cap_px, card)
        # The side is settled before the rung, because the rung is what nests
        # one span inside another on a side and a span that moves afterwards
        # would nest against a side it is no longer on. The mark that settles
        # it is drawn at the first rung's offset; a span that ends up further
        # out is drawn again there.
        first = cap_px * SPAN_OFFSET_CAPS
        span.side, drawn = _drawn_side(span, route_px, card, cap_px, first, avoid, lines)
        rank = _rung(used, span, span.side, rails)
        if rank is None and span.side != base:
            # Curvature is a preference, not a licence to lose the span. If the
            # outside of the bend is already full and the inside is not, the
            # span goes back inside rather than off the sheet.
            log.info(
                "span %r takes the inside of the bend: the outside is past the last rail", span.name
            )
            span.side, rank = base, _rung(used, span, base, rails)
        if rank is None:
            log.info("span %r is past the third rail and is not drawn", span.name)
            continue
        span.rank = rank
        span.offset_px = first + rank * cap_px * SPAN_RUNG_CAPS
        span.line = (
            drawn
            if rank == 0
            else span_line(
                route_px,
                span.i0,
                span.i1,
                span.side,
                span.offset_px,
                card,
                clear_px=cap_px * SPAN_CLEAR_CAPS,
            )
        )
        if not span.line:
            # No arc of the envelope could be drawn clear of the route. A span
            # dropped with a reason on the record beats one drawn across the
            # road the reader is looking at, which is rule seven.
            log.info("span %r is not drawn: no mark clears the route", span.name)
            continue
        span.ticks = _span_ticks(span, route_px, cap_px)
        span.label = _span_label(span, route_px, cap_px, measure_fn, along_max_deg)
        used[span.side].append((span.i0, span.i1, rank))
        placed.append(span)
    return placed


def span_bearing(line: list[Pt]) -> float:
    """A span line's screen-space bearing off the horizontal, 0 to 90 degrees.

    The chord, not the local tangent: what decides whether a name reads along a
    bracket is which way the bracket goes across the sheet, and a climb that
    wiggles about a westward chord still reads westward.
    """
    if len(line) < 2:
        return 90.0
    a, b = line[0], line[-1]
    ang = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
    return min(ang, 180.0 - ang)


#: How much better the other side's mark has to be before a span is moved off
#: the side the paper and the bend chose for it, as a ratio of what each mark
#: is worth. A quarter better: the two earlier rules are about where a mark
#: reads best and this one is about whether there is a mark to read at all, so
#: it wins a rout and loses a close thing.
SPAN_SIDE_SWAP_MARGIN = 1.25

#: What a mark drawn through something the sheet has already given to a place
#: costs, as a share of its own length per unit of weight. A mark is drawn
#: round a town rather than through it where it can be. That is leeway, so a
#: cost: a mark with a
#: town's worth of weight over a third of its length pays about its own length
#: again, which loses to any decent mark on the other side and beats a stub.
SPAN_FEATURE_COST = 1.5


def _drawn_side(
    span: Span,
    route_px: list[Pt],
    card: Any,
    cap_px: float,
    offset_px: float,
    avoid: list[tuple[float, float, float, float]] | None,
    lines: list[list[Pt]] | None = None,
) -> tuple[int, list[Pt]]:
    """The side the mark is actually drawn on, and the mark.

    The side arrives already chosen, by free paper and then by the bend. Both
    of those are about where a mark reads best, and neither has yet looked at
    what the mark on that side turns out to be. Two things can only be known
    once it is drawn: whether the route left room for it at all, since a mark
    that meets a junction stops short of it, and whether it runs through a
    place the sheet has already named or lies tight along a river. So both
    sides are drawn and scored on how much of a mark came back, less what it
    cost to cross a settlement and what it cost to lie on another strong line,
    and the chosen side keeps the span unless the other is clearly better.

    Args:
        span: The span, for its extent, side and offset.
        route_px: The whole track in card pixels.
        card: The card, for its size.
        cap_px: The lettering's cap height.
        offset_px: The level the two marks are drawn at, which is the first
            rung's: the side is settled before the rung is.
        avoid: `(x, y, weight, radius)` places, in card pixels, or None.
        lines: The other strong line on the sheet - the watercourses, the
            roads and the lanes - in card pixels, which a mark would rather
            not be drawn along. A preference and nothing more: where the
            route runs down the far bank of a river there is nowhere else
            for the mark, and it may sit tight against the water.

    Returns:
        `(side, line)`, the line empty when neither side drew a mark.
    """
    clear = cap_px * SPAN_CLEAR_CAPS
    drawn = {
        side: span_line(route_px, span.i0, span.i1, side, offset_px, card, clear_px=clear)
        for side in (span.side, -span.side)
    }
    worth = {
        side: (length(line) - _feature_cost(line, avoid) - _on_line_cost(line, lines, cap_px))
        for side, line in drawn.items()
    }
    other = -span.side
    if drawn[other] and worth[other] > max(worth[span.side], 0.0) * SPAN_SIDE_SWAP_MARGIN:
        log.info(
            "span %r is drawn on the other side: %.0f px of mark there against %.0f px here",
            span.name,
            worth[other],
            worth[span.side],
        )
        return other, drawn[other]
    return span.side, drawn[span.side]


#: How near another strong line on the sheet counts as lying along it, in cap
#: heights, and what that costs as a share of the mark's own length.
#:
#: A mark prefers clear paper and would
#: rather not sit tight against a river or a road. It is a softer preference
#: than the leeway round a settlement and much softer than the route rule: a
#: mark lying on water for its whole length pays half its length, which loses
#: to a side that yields a full mark and beats a side that yields a stub.
SPAN_LINE_REACH_CAPS = 0.7
SPAN_LINE_COST = 0.5


def _on_line_cost(line: list[Pt], lines: list[list[Pt]] | None, cap_px: float) -> float:
    """What a mark pays for lying along a river, a road or a lane, in pixels.

    Charged on how much of the mark sits within `SPAN_LINE_REACH_CAPS` of one
    of them, so a mark that crosses a river pays almost nothing and a mark
    drawn down the middle of one pays a share of its whole length.
    """
    if not lines or len(line) < 2:
        return 0.0
    run = length(line)
    if run <= 0.0:
        return 0.0
    reach = cap_px * SPAN_LINE_REACH_CAPS
    pts = _resample(line, max(run / 60.0, 1.0))
    near = [_route_near(line, other, reach) for other in lines]
    near = [other for other in near if len(other) > 1]
    if not near:
        return 0.0
    on = sum(1 for q in pts if min(foot_on(q, other)[0] for other in near) < reach)
    return (on / len(pts)) * run * SPAN_LINE_COST


def _feature_cost(line: list[Pt], avoid: list[tuple[float, float, float, float]] | None) -> float:
    """What a mark pays for the map content it is drawn over, in pixels.

    Charged on how much of the line lies inside a place's own radius, times
    what the place is worth, times its own length. Nothing is forbidden here:
    rule seven, which is a constraint, is enforced in `span_line`, and this is
    the preference that sits beside it.
    """
    if not avoid or len(line) < 2:
        return 0.0
    run = length(line)
    if run <= 0.0:
        return 0.0
    pts = _resample(line, max(run / 60.0, 1.0))
    cost = 0.0
    for x, y, weight, radius in avoid:
        if radius <= 0.0:
            continue
        inside = sum(1 for p in pts if math.dist(p, (x, y)) < radius)
        cost += weight * (inside / len(pts)) * run * SPAN_FEATURE_COST
    return cost


def _rung(
    used: dict[int, list[tuple[int, int, int]]], span: Span, side: int, rails: int
) -> int | None:
    """Which rung of one side this span nests on, or None when the side is full."""
    rank = 0
    for i0, i1, taken in used[side]:
        if span.i0 < i1 and span.i1 > i0:
            rank = max(rank, taken + 1)
    return None if rank >= rails else rank


#: Whether the outside of a bend gets a say in which side of the route a span's
#: bracket is drawn on. There is a geometric
#: argument for it: **a bracket is an offset line, and an offset line
#: contracts on the inside of a bend and expands on the outside.** The inside
#: is where the contour crowds, kinks and closes on itself, which is the
#: failure that has produced a ring round the Keswick climb and a doubled-back
#: stub; the outside gives more arc length for the same stretch, so a name
#: fits along it more often and the mark stays an open gesture.
#:
#: On by default and named here so it can be turned off or reweighted without
#: a code change. Off, `place_spans` chooses exactly as it did before.
SPAN_CURVE_SIDE = True

#: How much net turning a stretch has to do before it has an outside at all,
#: and where the vote reaches full strength, both in degrees over the whole
#: extent. Below the first, the stretch is straight enough that "the outside"
#: names nothing and the free-paper choice stands unopposed; between the two
#: the vote ramps, so a gentle bend is a gentle preference.
#:
#: Thirty-five degrees is a little over a third of a right angle over the whole
#: stretch, which is about where a road stops reading as a road that goes
#: somewhere and starts reading as a bend. It is also where the sweep settles:
#: over the four cached rides, 25 degrees moves 33 stretches for 24 better and
#: 8 worse, 35 moves 32 for 24 and 7, and 45 and 60 both drop a win to save
#: nothing. The A591 climb on the Dovedale card turns 11 degrees over its
#: whole extent and gets no vote: a span on a straight stretch staying where
#: the free paper put it is the threshold working, not the term failing.
SPAN_CURVE_MIN_TURN_DEG = 35.0
SPAN_CURVE_FULL_TURN_DEG = 75.0

#: How single-minded the bend has to be. `net / gross`: one long curve is near
#: 1, an S-bend that turns as far back as it turned out is near 0. A stretch
#: below this has no outside either, because half of it would be written on the
#: inside whichever side were chosen, so the vote is withheld and the free-paper
#: choice stands. Not a small number: the ambiguous case is the one where
#: forcing a side does harm, and a stretch that is two thirds one way is where
#: the eye starts calling it a bend.
SPAN_CURVE_MIN_COHERENCE = 0.62

#: What the vote is worth, in the units the free-paper choice is scored in,
#: which is mean darkness from 0 (clear paper) to 1 (solid ink). The vote can
#: only turn the side round when the darkness margin between the two sides is
#: under `SPAN_CURVE_WEIGHT` times the vote's strength. So this number is
#: exactly the answer to "how near a tie does the free-paper choice have to be
#: before the bend gets to decide it".
#:
#: Picked by measuring the margins, not by taste. Over the same 187 stretches,
#: the margin the free-paper rule wins by has a median of 0.042 and a ninetieth
#: percentile of 0.122. At 0.08 a fully committed bend overrules about four
#: margins in five and loses to the darkest fifth, which is the side that is
#: off the paper, under a wash or already carrying names; a half-strength bend,
#: which is a stretch turning about 50 degrees, overrules only about half.
#: That is the shape wanted: the outside of the curve **where there is one**,
#: and not otherwise.
SPAN_CURVE_WEIGHT = 0.08

#: At what scale the bend is read, as a multiple of the cap height. The single
#: most important number here, and the one the outside-of-the-bend rule
#: lives or dies on.
#:
#: The route in card pixels is sampled about a pixel apart, and per-vertex turn
#: at that spacing is mostly the sampling, so the stretch is resampled before
#: it is measured. **The right spacing is the offset the bracket will be drawn
#: at**, 1.7 cap heights, because contraction is what an offset line does at
#: its own offset: a bend the offset can see is a bend that squeezes it. Read
#: coarser, the measure answers a different question and stops predicting
#: anything. Over 187 stretches from the four cached rides, the share of the
#: decisive cases the outside gets right is 89% read at 1.5 caps, 79% at 2,
#: 60% at 3 and 46% at 4, which is a coin toss. 1.5 is under the offset and is
#: where the sweep peaks; the trend either side of it is the argument.
SPAN_CURVE_SCALE_CAPS = 1.5


def route_turn(line: list[Pt]) -> tuple[float, float]:
    """How far a polyline turns, net and gross, in degrees.

    Signed the way a turn is signed in card pixels, where y runs down:
    positive turning is towards the normal `(-dy, dx)`. Only the ratio of the
    two numbers is used to decide anything, because which drawn side the bend's
    outside corresponds to is settled by measuring the marks, in `_convex_side`.

    Args:
        line: The polyline, in card pixels, already sampled at the scale the
            bend is to be read at.

    Returns:
        `(net, gross)`: the signed sum of the turn at every interior vertex,
        and the sum of its absolute value. Their ratio says how single-minded
        the turning is; `(0.0, 0.0)` for a line with no interior vertex.
    """
    net = gross = 0.0
    for a, b, c in zip(line, line[1:], line[2:], strict=False):
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        if math.hypot(ux, uy) < 1e-9 or math.hypot(vx, vy) < 1e-9:
            continue
        turn = math.degrees(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy))
        net += turn
        gross += abs(turn)
    return net, gross


def bend_strength(sub: list[Pt], scale_px: float) -> float:
    """How much of an outside a stretch has, from 0 to 1.

    Zero when the stretch is too straight for "the outside" to name anything,
    and zero when it turns both ways about equally, which is the same statement
    made twice: there is no one outside, so nothing is voted for and the
    free-paper rule keeps the choice. Otherwise the strength ramps from 0 to 1
    between `SPAN_CURVE_MIN_TURN_DEG` and `SPAN_CURVE_FULL_TURN_DEG` of net
    turning, so a gentle bend is a gentle preference.

    Unsigned on purpose. Which side the outside actually is, is settled by
    `_convex_side` on the drawn marks rather than from a normal, because this
    module signs a side two different ways: `_bracket` pushes off the chord's
    own normal and takes its chord from the widest pair of points rather than
    from the direction of travel, while the contour filters a ring with
    `_side_at`. The two do not agree, so nothing here relies on either.

    Args:
        sub: The stretch of route the span covers, in card pixels.
        scale_px: The spacing the stretch is read at, which should be about the
            offset the bracket will be drawn at.

    Returns:
        `0.0` to `1.0`.
    """
    if len(sub) < 3 or scale_px <= 0.0:
        return 0.0
    net, gross = route_turn(_resample(sub, scale_px))
    if gross <= 1e-9 or abs(net) < SPAN_CURVE_MIN_TURN_DEG:
        return 0.0
    if abs(net) / gross < SPAN_CURVE_MIN_COHERENCE:
        return 0.0
    span_deg = SPAN_CURVE_FULL_TURN_DEG - SPAN_CURVE_MIN_TURN_DEG
    ramp = (abs(net) - SPAN_CURVE_MIN_TURN_DEG) / span_deg if span_deg > 0 else 1.0
    return min(max(ramp, 0.0), 1.0)


def _outward(sub: list[Pt]) -> tuple[Pt, Pt]:
    """The middle of a stretch's chord, and the unit vector out of its bend.

    The chord is the widest pair of points and not the two ends, for the reason
    `_bracket` uses the same pair: an out-and-back finishes where it started,
    and the middle of *that* chord says nothing about anything. The stretch's
    own middle of mass sits on the convex side of that chord, because that is
    what bending is, so the direction from the one to the other points out of
    the bend.

    Args:
        sub: The stretch of route, in card pixels.

    Returns:
        `(middle, outward)`: the chord's middle, and a unit vector, or a zero
        vector when the stretch is straight enough to have no bulge at all.
    """
    far = max(sub, key=lambda q: math.dist(sub[0], q))
    near = max(sub, key=lambda q: math.dist(far, q))
    middle = ((far[0] + near[0]) / 2.0, (far[1] + near[1]) / 2.0)
    cx = sum(p[0] for p in sub) / len(sub) - middle[0]
    cy = sum(p[1] for p in sub) / len(sub) - middle[1]
    run = math.hypot(cx, cy)
    return middle, ((cx / run, cy / run) if run > 1e-9 else (0.0, 0.0))


#: When a mark fails as a mark. Two things only: nothing was drawn, or what was
#: drawn comes nearer the route than the clearance it was given. Neither is a
#: matter of taste. What used to be here as well - that a mark must not close
#: on itself, and that it must hold the offset the ladder reserved to within a
#: quarter - is withdrawn: a mark may be drawn round a doubled-back stretch,
#: which encloses it, and its distance from the route is allowed to vary.


def _mark_broken(line: list[Pt], route_px: list[Pt], clear_px: float) -> bool:
    """Whether a drawn mark failed as a mark rather than merely read worse."""
    if len(line) < 2:
        return True
    return not clear_of_route(line, route_px, clear_px)


def _convex_side(
    span: Span, route_px: list[Pt], cap_px: float, card: Any
) -> tuple[int, dict[int, list[Pt]]]:
    """Which side draws the bracket on the outside of the bend, by measurement.

    The mark is drawn both ways and the two are compared, rather than a side
    being worked out from a normal. Two reasons. The convention is not settled
    in this module, as `bend_strength` says; and the answer wanted is about the
    mark, not about the route, so measuring the mark is the direct question.

    Each drawn line is measured by how far it stands *out of the bend*: the
    mean of its displacement from the chord's middle, projected onto the
    outward direction. Distance alone would not do, because the straight
    fallback is pushed out past the widest point of the stretch and stands a
    long way from the chord's middle on either flank; the projection is signed,
    so a mark pushed the wrong way scores negative rather than large.

    Args:
        span: The span, for its extent.
        route_px: The track in card pixels.
        cap_px: The lettering's cap height, which sets the probe offset.
        card: The card, for its size.

    Returns:
        `(side, marks)`: `+1` or `-1`, or `0` when there is nothing to compare,
        and the line each side drew, so the caller can look at them without
        drawing them again.
    """
    sub = route_px[span.i0 : span.i1 + 1]
    marks = {
        side: span_line(route_px, span.i0, span.i1, side, cap_px * SPAN_OFFSET_CAPS, card)
        for side in (1, -1)
    }
    if len(sub) < 3:
        return 0, marks
    (mx, my), (ox, oy) = _outward(sub)
    if ox == 0.0 and oy == 0.0:
        return 0, marks
    reach = {
        side: sum((p[0] - mx) * ox + (p[1] - my) * oy for p in line) / len(line)
        for side, line in marks.items()
        if line
    }
    if len(reach) < 2:
        return next(iter(reach), 0), marks
    return (1 if reach[1] > reach[-1] else -1), marks


def _curved_side(
    span: Span, route_px: list[Pt], base: int, margin: float, cap_px: float, card: Any
) -> int:
    """The side the bracket goes on once the bend has had its say.

    A weighted term and never an override. The free-paper choice arrives with
    the margin it won by, in mean darkness; the bend arrives with a strength
    from 0 to 1; and the bend only turns the answer round when the outside is
    not already where the paper put it **and** `SPAN_CURVE_WEIGHT` times its
    strength beats that margin. So the outside wins a near-tie, and a side that
    is off the paper, under a wash or already carrying names keeps the span.

    One thing outranks the bend outright, and it is not a preference: **the
    bend may not break the mark.** Both marks are drawn to find the outside, so
    what the outside would actually look like is already in hand, and where the
    outside comes back as a ring or as the straight fallback standing well off
    the offset while the free-paper side came back as a proper contour, the
    move is refused. Measured over the four cached rides this refusal is what
    turns the term from roughly even into clearly worth having.

    Args:
        span: The span, for its extent.
        route_px: The track in card pixels.
        base: The side the free-paper rule chose, +1 or -1.
        margin: How far apart the two sides' mean darkness was.
        cap_px: The lettering's cap height, which sets the reading scale.
        card: The card, for its size.

    Returns:
        `base`, or `-base` when the bend overrules it.
    """
    if not SPAN_CURVE_SIDE:
        return base
    strength = bend_strength(route_px[span.i0 : span.i1 + 1], cap_px * SPAN_CURVE_SCALE_CAPS)
    if strength <= 0.0:
        return base
    outside, marks = _convex_side(span, route_px, cap_px, card)
    if outside == 0 or outside == base:
        return base
    if SPAN_CURVE_WEIGHT * strength <= margin:
        log.info(
            "span %r keeps the inside of its bend: darkness margin %.3f beats the bend's %.3f",
            span.name,
            margin,
            SPAN_CURVE_WEIGHT * strength,
        )
        return base
    clear = cap_px * SPAN_CLEAR_CAPS
    if _mark_broken(marks[outside], route_px, clear) and not _mark_broken(
        marks[base], route_px, clear
    ):
        log.info(
            "span %r keeps the inside of its bend: the outside draws no usable mark", span.name
        )
        return base
    log.info(
        "span %r moves to the outside of its bend (strength %.2f, darkness margin %.3f)",
        span.name,
        strength,
        margin,
    )
    return outside


def _freer_side(
    span: Span, route_px: list[Pt], dark: dict[str, Any], card: Any, cap_px: float
) -> tuple[int, float]:
    """Which side of its own extent has the more free paper, and by how much.

    Returns:
        `(side, margin)`: +1 for left and -1 for right, and the difference in
        mean darkness between the two sides, from 0 to 1. The margin is what
        the bend's vote is weighed against.
    """
    gw, gh, grid = dark["w"], dark["h"], dark["v"]
    score = {1: [], -1: []}
    step = max((span.i1 - span.i0) // 12, 1)
    for i in range(span.i0, span.i1, step):
        (ax, ay), (bx, by) = route_px[i], route_px[min(i + step, len(route_px) - 1)]
        run = math.hypot(bx - ax, by - ay)
        if run < 1e-6:
            continue
        nx, ny = -(by - ay) / run, (bx - ax) / run
        for side in (1, -1):
            x = ax + nx * side * cap_px * 3.0
            y = ay + ny * side * cap_px * 3.0
            if not (0 <= x < card.w and 0 <= y < card.h):
                score[side].append(1.0)
                continue
            c = min(int(x / card.w * gw), gw - 1)
            r = min(int(y / card.h * gh), gh - 1)
            score[side].append(grid[r][c])
    left = sum(score[1]) / len(score[1]) if score[1] else 0.5
    right = sum(score[-1]) / len(score[-1]) if score[-1] else 0.5
    return (1 if left <= right else -1), abs(left - right)


#: How near any strand of the route a mark may come, in cap heights.
#:
#: A hard constraint and not a cost: a span mark is never drawn over any other
#: piece of route. Any piece: the stretch the span covers, the strand it doubled back along, and
#: the part of the route that happens to pass through the same corner half an
#: hour later. Half a cap height is the width of the route stroke plus enough
#: white either side that the reader sees two lines rather than one join.
SPAN_CLEAR_CAPS = 0.5

#: How hard the stretch is simplified before the mark is drawn from it, as a
#: share of the offset, and how far apart the drawn line's own points sit.
#:
#: This one number is the whole argument about what a span mark is. Too fine
#: and the mark traces the road, which is what the iso-distance contour did: a
#: span mark needs no constant distance from the path. Too coarse and the
#: mark throws the shape away with the wiggles, which is what the envelope arc
#: did: it follows the route too little and looks too straight and mechanical.
#: What is wanted is between them: smoothed curves that follow the shape and
#: could be drawn by hand in a few strokes.
#:
#: A third of the offset keeps the significant turns of every panel of the
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


def span_line(
    route_px: list[Pt],
    i0: int,
    i1: int,
    side: int,
    offset_px: float,
    card: Any,
    cells: float | None = None,
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
       about the offset. The distance to the real track then varies, opening
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
       dropped when neither side can be drawn clear.

    Args:
        route_px: The whole track in card pixels. The whole of it: the mark has
            to clear the parts of the route the span does not cover as well.
        i0: First route index of the span.
        i1: Last route index of the span.
        side: +1 for the left of travel, -1 for the right, signed the way
            `_side_at` signs it.
        offset_px: About how far off the route the mark sits, in card pixels.
            About: the offset is taken off the smoothed shape, so the gap to
            the real track is whatever the smoothing left.
        card: The card. Unused by the construction and kept because every
            caller has one and the signature is stable.
        cells: Unused. Kept for the same reason.
        clear_px: How near the route the mark may come. `SPAN_CLEAR_CAPS` of a
            cap height by default, worked back from the offset.

    Returns:
        The mark in card pixels, or an empty list when it cannot be drawn clear
        of the route. An empty list is an answer: the span is dropped, and said
        to be dropped, rather than drawn across the road.
    """
    raw = route_px[i0 : i1 + 1]
    if len(raw) < 2 or offset_px <= 0:
        return []
    if clear_px is None:
        clear_px = offset_px / SPAN_OFFSET_CAPS * SPAN_CLEAR_CAPS
    if doubling_px(raw) < offset_px * DOUBLED_BACK_OFFSETS:
        raw = _mouth_path(raw, offset_px)
    shape = shape_curve(raw, offset_px)
    if len(shape) < 2:
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
    if len(corners) < 2:
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
    if math.dist(a, b) < 1e-9 or math.dist(b, c) < 1e-9:
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
    if len(line) < 3 or len(shape) < 2:
        return list(line)
    keep = [p for p in line if foot_on(p, shape)[0] >= offset_px * FOLD_KEEP_FRAC]
    return keep if len(keep) >= 2 else list(line)


def _forward_only(line: list[Pt], shape: list[Pt]) -> list[Pt]:
    """Keep only the part of an offset line that goes forwards along the shape.

    A fold does not merely come too near the shape, it runs backwards along it,
    and what is left of one after the near points are dropped is a V or a
    staircase. Every point is asked which point of the shape it stands beside,
    and any that stands beside an earlier one than the point before it is
    dropped. What survives runs from one end of the stretch to the other and
    never doubles back on itself.
    """
    if len(line) < 3 or len(shape) < 2:
        return list(line)
    out: list[Pt] = []
    seen = -1
    for p in line:
        at = _nearest_on(shape, p)
        if at < seen:
            continue
        out.append(p)
        seen = at
    return out if len(out) >= 2 else list(line)


def _uncross(line: list[Pt]) -> list[Pt]:
    """Cut the loop out of a line that crosses itself.

    The inside of a bend tighter than the offset ties the offset curve in a
    little knot. A person drawing the same stroke does not tie it; they cut
    the corner. Splicing the loop out at the crossing is that cut.
    """
    out = list(line)
    for _ in range(8):
        hit = _first_loop(out)
        if hit is None:
            return out
        i, j, at = hit
        out = out[: i + 1] + [at] + out[j + 1 :]
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
    if n < 8:
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
    if near < 1e-6:
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
    if len(line) < 2 or len(route_px) < 2:
        return True
    near = _route_near(line, route_px, clear_px)
    if len(near) < 2:
        return True
    for a, b in zip(line, line[1:], strict=False):
        for c, d in zip(near, near[1:], strict=False):
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
    if len(line) < 1 or len(route_px) < 2:
        return []
    pad = clear_px + 8.0
    x0 = min(x for x, _ in line) - pad
    x1 = max(x for x, _ in line) + pad
    y0 = min(y for _, y in line) - pad
    y1 = max(y for _, y in line) + pad
    out: list[Pt] = []
    last = -2
    for i, (a, b) in enumerate(zip(route_px, route_px[1:], strict=False)):
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
    if len(line) < 2:
        return []
    out = list(line)
    walked = [0.0] * len(out)
    for _ in range(CLEAR_PASSES):
        if clear_of_route(out, route_px, clear_px):
            return out
        near = _route_near(out, route_px, clear_px * 6.0)
        if len(near) < 2:
            return out
        feet = [foot_on(p, near) for p in out]
        want = _blur([max(0.0, clear_px * 1.3 - d) for d, _ in feet], CLEAR_BLUR)
        moved: list[Pt] = []
        for i, (p, (d, foot), push) in enumerate(zip(out, feet, want, strict=True)):
            if push <= 0.0:
                moved.append(p)
                continue
            ux, uy = (
                ((p[0] - foot[0]) / d, (p[1] - foot[1]) / d) if d > 1e-6 else _away_from(near, p)
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
    if len(line) < 3:
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
    while hi - lo >= 3:
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
        if len(out) < 3:
            break
        nxt = [out[0]]
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


def _side_of(sub: list[Pt], p: Pt) -> int:
    """Which side of the sub-route a point falls on: +1 left of travel, -1 right."""
    best, at = math.inf, 0
    for i, (x, y) in enumerate(sub):
        gap = (x - p[0]) ** 2 + (y - p[1]) ** 2
        if gap < best:
            best, at = gap, i
    a = sub[max(at - 1, 0)]
    b = sub[min(at + 1, len(sub) - 1)]
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    return 1 if cross < 0 else -1


def _span_ticks(span: Span, route_px: list[Pt], cap_px: float) -> list[list[Pt]]:
    """A tick from each end of the mark, pointing at the end of the stretch.

    The end marks run from the end of the line towards the end of the segment,
    not perpendicular to the local route. So the direction is the
    vector from where the mark stops to where the span stops on the road, and
    nothing else: not the route's own bearing at that index, which is a
    property of two GPS samples rather than of anything the reader can see, and
    not the mark's own bearing, which the smoothing chose.

    It is one stroke off the end of the line rather than a cross-mark on it,
    which is what "from the end of the line" says. A tick is part of the mark,
    so rule seven binds it too: it is shortened until its tip clears the road
    it points at, and left off when even a short one would touch it.
    """
    if len(span.line) < 2:
        return []
    out = []
    length = cap_px * SPAN_TICK_CAPS
    clear = cap_px * SPAN_CLEAR_CAPS
    for end, at in ((span.line[0], span.i0), (span.line[-1], span.i1)):
        target = route_px[at]
        run = math.dist(end, target)
        if run < 1e-6:
            continue
        ux, uy = (target[0] - end[0]) / run, (target[1] - end[1]) / run
        reach = min(length, max(run - clear, 0.0))
        while reach > length * 0.25:
            tick = [end, (end[0] + ux * reach, end[1] + uy * reach)]
            if clear_of_route(tick, route_px, clear):
                out.append(tick)
                break
            reach -= length * 0.1
    return out


def _span_label(
    span: Span,
    route_px: list[Pt],
    cap_px: float,
    measure_fn: Measure,
    along_max_deg: float = SPAN_ALONG_MAX_BEARING_DEG,
) -> Label:
    """The span's own name: along the line where that reads, beside it where not.

    A span whose line is too short to carry its own name falls back to the same
    horizontal treatment as a steep one, because the alternative is a name that
    runs off both ends of the bracket it belongs to.
    """
    mid = span.line[len(span.line) // 2] if span.line else (0.0, 0.0)
    size = cap_px * (1.0 if span.ground else 0.85)
    lift = _outboard(span, route_px)
    width, _h = measure_fn(span.name, size)
    along = (
        bool(span.line)
        and span_bearing(span.line) <= along_max_deg
        and length(span.line) >= width * 1.02
    )
    anchors: list[Pt] = []
    if not along and span.line:
        # Anchored on the outboard side of the line, so the placer looks for
        # its clear paper on the far side from the route rather than in the gap
        # between the route and the bracket. Offered at points along the whole
        # bracket rather than at its middle alone: the middle of a short
        # bracket in a busy corner may have another name sitting over it, and a
        # name pushed out of the way from there ends up further from the line
        # than one that simply slid along it.
        nx, ny = _span_normal(span.line)
        push = lift * cap_px * 0.9
        anchors = [_beside(span.line, f, (nx * push, ny * push)) for f in SPAN_ANCHOR_FRACS]
        mid = anchors[len(anchors) // 2]
    return Label(
        name=span.name,
        kind=span.kind,
        why=span.why,
        px=mid[0],
        py=mid[1],
        tier=TIER_SPAN,
        size=size,
        box=None,
        tx=mid[0],
        ty=mid[1],
        anchor="middle",
        intent=span.intent,
        lift=lift,
        span_range=(span.i0, span.i1),
        mark=list(span.line),
        anchors=anchors,
        baseline=list(span.line) if along else [],
    )


#: Where along its own bracket a span's name may be anchored, as fractions of
#: the bracket's run. The middle is one of them and is still what the label
#: carries as its anchor; the others let a name slide along the line it belongs
#: to instead of being pushed off it.
SPAN_ANCHOR_FRACS = (0.15, 0.325, 0.5, 0.675, 0.85)


def _beside(line: list[Pt], frac: float, push: Pt) -> Pt:
    """A point a fraction along a line, shifted by one offset.

    The shift is the same vector at every fraction, taken from the line's
    middle, and not a local normal. A bracket beside a stretch that doubles
    back turns right round inside its own length, so a local normal at one end
    of it points where a local normal at the other end came from: anchors built
    that way put a name on the far side of the road from its own mark.
    """
    run = length(line)
    want, walked = run * frac, 0.0
    at = len(line) - 1
    for i in range(len(line) - 1):
        step = math.dist(line[i], line[i + 1])
        if walked + step >= want:
            at = i
            break
        walked += step
    p = line[at]
    return (p[0] + push[0], p[1] + push[1])


def _span_normal(line: list[Pt]) -> Pt:
    """The unit normal to a span line at its middle, pointing to +1 lift."""
    i = len(line) // 2
    a, b = line[max(i - 1, 0)], line[min(i + 1, len(line) - 1)]
    run = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return ((b[1] - a[1]) / run, -(b[0] - a[0]) / run)


# --------------------------------------------------------------------------- settlements

#: What a settlement is worth before the route is taken into account.
SETTLEMENT_RANK = {"city": 4.0, "town": 3.0, "village": 2.0, "suburb": 1.5, "hamlet": 1.0}
#: The qualifiers a pair of settlements is split by. Upper and Lower Swell
#: are one place to the person riding through them, and are called by their
#: stem.
QUALIFIERS = (
    "Upper",
    "Lower",
    "Great",
    "Little",
    "Nether",
    "Over",
    "North",
    "South",
    "East",
    "West",
    "New",
    "Old",
)
#: How near two members of a pair have to be to be the same place, in metres.
MERGE_M = 1500.0
#: Past this a settlement is not part of this ride.
SETTLEMENT_MAX_OFF_M = 1500.0
#: Under this a settlement is not worth a name: a run through empty country gets
#: one label or none rather than three hamlets.
SETTLEMENT_FLOOR = 3.0
#: How far apart two settlement names have to be on the sheet, in display pixels
#: of a 900 px card, so two villages a kilometre apart never both letter. Scaled
#: with the card, because the constraint is the sheet and not the ground.
SETTLEMENT_SEPARATION_PX = 120.0
#: How near an end of the route a settlement has to be to have been where the
#: session set off from or finished, as a fraction of the route's own length.
#: Stated against the ride rather than in metres because on a loop through empty
#: country the one settlement for miles is nearest to both ends and has earned
#: nothing by it.
SETTLEMENT_ENDPOINT_FRAC = 0.05


def _stem(name: str) -> str:
    """A settlement name without its leading qualifier."""
    return re.sub(rf"^({'|'.join(QUALIFIERS)})\s+", "", str(name)).strip()


def settlements(basemap: Basemap) -> list[dict[str, Any]]:
    """Every settlement the painted box holds, merged into places.

    The candidates already carry them: `journal_layers` asks for every named
    thing, so a place node is in the basemap whether or not it is a landmark.
    Nothing here is fetched and nothing is repainted.
    """
    found: list[dict[str, Any]] = []
    for c in basemap.candidates:
        if c.get("class") != "place":
            continue
        kind = str((c.get("tags") or {}).get("place", ""))
        if kind not in SETTLEMENT_RANK:
            continue
        found.append(
            {
                "name": c["name"],
                "kind": kind,
                "x": c["x"],
                "y": c["y"],
                "off_route_m": float(c.get("distance_m") or 0.0),
            }
        )
    groups: list[dict[str, Any]] = []
    for entry in sorted(found, key=lambda e: e["off_route_m"]):
        stem = _stem(entry["name"])
        for group in groups:
            if group["stem"] != stem:
                continue
            if math.dist((group["x"], group["y"]), (entry["x"], entry["y"])) > MERGE_M:
                continue
            # Positioned on the member nearest the route, which is the one the
            # route actually runs through.
            group["kind"] = max(group["kind"], entry["kind"], key=lambda k: SETTLEMENT_RANK[k])
            break
        else:
            groups.append({**entry, "name": stem, "stem": stem})
    return groups


def settlement_budget(display_px: float) -> int:
    """How many settlements a card this wide carries.

    The constraint is card area, not ground area: a bigger box means more
    settlements competing for the same slots, not more slots.
    """
    return max(2, min(round(3 * display_px / 900.0), 5))


def pick_settlements(
    basemap: Basemap,
    card: Any,
    route_px: list[Pt],
    always: list[str] | None = None,
    wanted: list[str] | None = None,
    budget: int | None = None,
) -> list[Label]:
    """Which settlements the sheet names, by rank and by route relationship.

    Never by raw distance order: a distance sort exhausts itself inside one
    town's wall plaques, which is the fault the "a place name is not a landmark"
    rule was written to stop. Settlements draw from their own pool and their own
    budget and never compete with the landmarks for a slot.

    Args:
        basemap: The basemap, for its candidates.
        card: The card, for the projection and its size.
        route_px: The track in card pixels.
        always: Names the user's own file says to letter whenever the box
            holds them, which do not spend a slot.
        wanted: Names this session's payload asked for, likewise.
        budget: How many to letter; from the card's width when not given.

    Returns:
        One `Label` a settlement, highest score first, anchored in card pixels.
    """
    always_set = {str(n).casefold() for n in (always or [])}
    wanted_set = {str(n).casefold() for n in (wanted or [])}
    budget = budget if budget is not None else settlement_budget(card.w)
    ends = [route_px[0], route_px[-1]] if route_px else []
    reach = length(route_px) * SETTLEMENT_ENDPOINT_FRAC
    found = settlements(basemap)
    scored: list[tuple[float, bool, dict[str, Any], Pt]] = []
    for entry in found:
        if entry["off_route_m"] > SETTLEMENT_MAX_OFF_M:
            continue
        at = card.xy(entry["x"], entry["y"])
        forced = entry["name"].casefold() in always_set or entry["name"].casefold() in wanted_set
        endpoint = bool(ends) and _nearest_to_ends(entry, found, card, ends, reach)
        score = (
            1.6 * SETTLEMENT_RANK[entry["kind"]]
            + 2.0 * max(0.0, 1.0 - entry["off_route_m"] / 800.0)
            + (1.5 if endpoint else 0.0)
            + (100.0 if forced else 0.0)
        )
        scored.append((score, forced, entry, at))
    scored.sort(key=lambda s: -s[0])
    out: list[Label] = []
    spent = 0
    for score, forced, entry, (x, y) in scored:
        if not (0 < x < card.w and 0 < y < card.h):
            continue
        if not forced and (score < SETTLEMENT_FLOOR or spent >= budget):
            continue
        apart = SETTLEMENT_SEPARATION_PX * card.w / 900.0
        if any(math.dist((x, y), (lb.px, lb.py)) < apart for lb in out):
            continue
        town = entry["kind"] in ("city", "town")
        out.append(
            Label(
                name=entry["name"],
                kind="settlement",
                why=f"{entry['kind']}, {entry['off_route_m']:.0f} m off the route",
                px=x,
                py=y,
                tier=TIER_SETTLEMENT,
                size=DEFAULT_LINE_PX * (1.15 if town else 0.85),
            )
        )
        if not forced:
            spent += 1
    return out


def _nearest_to_ends(
    entry: dict[str, Any], found: list[dict[str, Any]], card: Any, ends: list[Pt], reach: float
) -> bool:
    """True when this is the settlement the route set off from or finished in.

    Nearest is not enough on its own: on a loop through empty country the only
    settlement for miles is nearest to both ends and has earned nothing.
    """
    here = card.xy(entry["x"], entry["y"])
    for end in ends:
        mine = math.dist(here, end)
        if mine > reach:
            continue
        if all(math.dist(card.xy(o["x"], o["y"]), end) >= mine for o in found):
            return True
    return False


# --------------------------------------------------------------------------- rivers

#: How many watercourses a sheet names. The major one always, and the best
#: medium only when it is worth having beside it. Never a brook.
RIVER_MAX = 2
RIVER_REL_FLOOR = 0.2

#: How many times the major watercourse carries its own name. Two, and only the
#: major one: a river crossing the whole sheet is read in pieces, and a reader
#: who meets it at the bottom of the card should not have to trace it to the top
#: to find out what it is. This is ordinary cartographic practice for a long
#: feature. Every other watercourse gets
#: one, because a tributary that runs a third of the card twice-named is
#: repetition rather than help.
MAJOR_RIVER_LABELS = 2
#: How much water a river has to have on the sheet before it is lettered twice,
#: as a share of the card's longer side. The reason for the second name is that
#: a river crossing the whole sheet is read in pieces; a river clipping a corner
#: is read in one, and the second name has nowhere to go but away from its own
#: water. With a single major watercourse on the sheet and only 295 px of
#: water on a 900 px sheet, it would take both allowances and write the second
#: one in open paper past the end of the river. The allowance is earned by the
#: run, not by the rank.
MAJOR_RIVER_TWICE_FRAC = 0.55
#: And how far apart two names of the same river have to be before the second
#: is worth setting, as a share of the run of water inside the card. Under this
#: the two would read as one repeated name rather than as the same river met
#: twice.
RIVER_REPEAT_FRAC = 0.35


# ------------------------------------------------------------- one name, once

#: Which repeat family each kind of name is counted in. Families never see each
#: other, because the answer is different in each: the major watercourse is
#: deliberately lettered twice, a road number once, and a place exactly once
#: however many pools found it. A guard that were one number for the whole
#: sheet would either letter the Eden once or letter Elm twice.
NAME_FAMILY = {"river": "water", "road": "road"}
#: What everything that is a point on the ground counts in. A settlement, a
#: user's own place and a landmark all name somewhere a reader goes, and
#: they come from three different pools that have never known about each other:
#: "Elm" can arrive as a settlement and again as the nearest named feature,
#: and "Bakewell" can do the same.
NAME_FAMILY_DEFAULT = "place"

#: How many times one name may be lettered inside its own family.
NAME_ALLOWANCE = {"water": MAJOR_RIVER_LABELS}
NAME_ALLOWANCE_DEFAULT = 1

#: How near two names have to be on the ground before they can be one place, in
#: metres. Stated in metres and not in pixels because "basically the same
#: place" is a fact about the ground rather than about the sheet: High Cup Nick
#: and High Cup Nick Cairn are five metres apart and are one headland, which
#: is a pixel on that card and would be a fifth of a pixel on a ride's, and
#: neither number says anything a rule can be built on.
NEAR_DUPLICATE_M = 150.0

#: And how many words the longer name may add to the shorter one before they
#: stop being two names for one thing. Two. The string relationship alone is
#: not enough and neither is the distance: Braemar and Braemar War Memorial
#: stand in the same word relationship as High Cup Nick and its chimney and are
#: a town and a monument in it, and they are told apart by being 485 m apart
#: rather than five. Both tests have to pass.
NEAR_DUPLICATE_EXTRA_WORDS = 2


def _words(name: str) -> list[str]:
    """A name as comparable words: case folded, unpunctuated, unqualified."""
    plain = re.sub(r"[^\w\s]", " ", _stem(str(name)))
    return plain.casefold().split()


def _one_place(a: str, b: str) -> bool:
    """Whether one name is the other with a few words added at either end.

    Whole words only. "High Cup Nick Cairn" is "High Cup Nick" and a thing on
    it; "High Cup Nicks" is not, and a character-wise prefix test cannot say so.
    """
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return False
    short, whole = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    extra = len(whole) - len(short)
    if extra > NEAR_DUPLICATE_EXTRA_WORDS:
        return False
    return whole[: len(short)] == short or whole[extra:] == short


def dedupe_names(labels: list[Label], card: Any) -> list[Label]:
    """One name a place, and one name for a place, in the caller's own order.

    Two rules, and they are the same rule at two distances.

    A name repeated exactly is lettered once inside its family, wherever the
    two anchors are: a settlement named at both ends of the sheet is still one
    settlement. The major watercourse is the deliberate exception and carries
    its allowance in `NAME_ALLOWANCE`, which is why the guard is per family and
    not global.

    A name that contains another, within `NEAR_DUPLICATE_M` of it, is two names
    for one place and the sheet keeps one. Which one is not a judgement about
    fame: the tiers already rank what a name *is*, so the lower tier wins, and
    between two of the same tier the shorter and more general name does. That
    gives the village over the nearest-feature repeat of it, and the headland
    over the chimney standing on it.

    A span is never deduped. Its name is prose an agent wrote about a stretch
    of the session rather than a name for somewhere, and two stretches may
    fairly be called the same thing.

    Args:
        labels: The names, in the order the caller wants them back.
        card: The card, for the pixels-per-metre its distances are read in.

    Returns:
        The labels that survive, in the order they were given.
    """
    scale = max(float(getattr(card, "scale", 0.0)), 1e-9)
    order = sorted(labels, key=lambda lb: (lb.tier, len(str(lb.name))))
    kept: list[Label] = []
    used: dict[tuple[str, str], int] = {}
    for lb in order:
        if lb.tier == TIER_SPAN:
            kept.append(lb)
            continue
        family = NAME_FAMILY.get(lb.kind, NAME_FAMILY_DEFAULT)
        key = (family, " ".join(_words(lb.name)))
        allowance = NAME_ALLOWANCE.get(family, NAME_ALLOWANCE_DEFAULT)
        if used.get(key, 0) >= allowance:
            log.info("dropped a repeat of %r: %s carries %d already", lb.name, family, allowance)
            continue
        near = any(
            other.tier != TIER_SPAN
            and NAME_FAMILY.get(other.kind, NAME_FAMILY_DEFAULT) == family
            and " ".join(_words(other.name)) != key[1]
            and _one_place(other.name, lb.name)
            and math.dist((lb.px, lb.py), (other.px, other.py)) / scale <= NEAR_DUPLICATE_M
            for other in kept
        )
        if near:
            log.info("dropped %r: the sheet already names that place", lb.name)
            continue
        used[key] = used.get(key, 0) + 1
        kept.append(lb)
    keep = {id(lb) for lb in kept}
    return [lb for lb in labels if id(lb) in keep]


def pick_rivers(
    basemap: Basemap,
    lines: NamedLines,
    card: Any,
    route_px: list[Pt],
    budget: int = RIVER_MAX,
) -> list[Label]:
    """Which watercourses the sheet names, by run inside the card and proximity.

    The painting classes answer "how wide is the brush" and are computed from
    run length alone, which cannot separate two tributaries of the same length.
    What separates them on a ride is the route: the one it crossed is the one
    worth naming.

    Args:
        basemap: The basemap, for the width each class was painted at.
        lines: The named lines, for the watercourses.
        card: The card, for the projection and its size.
        route_px: The track in card pixels.
        budget: How many to letter.

    Returns:
        One `Label` a river, best first, anchored on its own water and carrying
        the water as its baseline.
    """
    geom = lines.get("rivers") or []
    thin = route_px[::3] or route_px
    typical: dict[str, float] = {}
    scored: list[tuple[float, str, list[Pt]]] = []
    widths: dict[str, float] = {}
    for entry in geom:
        name = str(entry.get("n") or "")
        if not name or entry.get("c") == "minor":
            continue
        line = [card.xy(x, y) for x, y in entry.get("d") or []]
        if len(line) < 2:
            continue
        run_m = length(line) / max(card.scale, 1e-9)
        near_m = min(min(math.dist(p, q) for q in thin) for p in line[::2]) / max(card.scale, 1e-9)
        score = run_m / 1000.0 * min(max(1.0 - near_m / 500.0, 0.2), 1.0)
        widths[name] = max(
            widths.get(name, 0.0),
            feature_px(basemap, "river", str(entry.get("c")), float(entry.get("w") or 0.0)),
        )
        # The width the river is typically drawn at, which is what decides
        # whether its own name fits in it.
        typical[name] = max(
            typical.get(name, 0.0),
            feature_px(basemap, "river", str(entry.get("c")), float(entry.get("wn") or 0.0)),
        )
        scored.append((score, name, line))
    # One river arrives as a dozen ways, and taking the longest of them threw
    # most of the water away: a name may go anywhere along its own watercourse,
    # and that freedom is only real if the whole watercourse is one line. The
    # pieces are chained end to end first, exactly as a road's are.
    pieces: dict[str, list[list[Pt]]] = {}
    totals: dict[str, float] = {}
    for score, name, line in scored:
        pieces.setdefault(name, []).append(line)
        totals[name] = totals.get(name, 0.0) + score
    merged: dict[str, tuple[float, list[Pt]]] = {
        name: (totals[name], max(joined(parts), key=length)) for name, parts in pieces.items()
    }
    order = sorted(merged.items(), key=lambda kv: -kv[1][0])
    out: list[Label] = []
    for rank, (name, (score, line)) in enumerate(order[:budget]):
        if out and score < RIVER_REL_FLOOR * order[0][1][0]:
            break
        # The major river is the first, and it is the only one lettered twice.
        # The two are anchored at the third and at the two-thirds point of the
        # water so the placer starts them in different halves; each is then free
        # to move anywhere along the whole line from there, and the repeat guard
        # in `place` keeps them from converging on the same window.
        run = length(line)
        twice = run >= MAJOR_RIVER_TWICE_FRAC * max(card.w, card.h)
        times = MAJOR_RIVER_LABELS if rank == 0 and twice else 1
        for n in range(times):
            at = (n + 1) / (times + 1)
            anchor = _on_line(line, cumulative_length(line), run * at)[0]
            size = DEFAULT_LINE_PX * 0.9
            out.append(
                Label(
                    name=river_name(name),
                    kind="river",
                    why=name,
                    px=anchor[0],
                    py=anchor[1],
                    tier=TIER_RIVER,
                    size=size,
                    baseline=line,
                    in_water=typical.get(name, 0.0) >= size * IN_WATER_CAPS,
                    feature_px=widths.get(name, 0.0),
                )
            )
    return out


def river_name(name: str) -> str:
    """ "River Eden" as "Eden": the water it is written on says the rest."""
    return re.sub(r"^River\s+", "", str(name)).strip() or str(name)


# --------------------------------------------------------------------------- the ground


def home_places(basemap: Basemap, card: Any) -> list[Label]:
    """The user's own places, as labels, for the ones with no glyph of their own.

    An entry with a symbol is drawn by the caller as it always was, glyph and
    name together, and is not returned here. An entry marked
    `kind: settlement` has no glyph and is lettered like any other settlement,
    which is what "Swell, a village" wants and what a house
    marker would say wrongly.
    """
    out: list[Label] = []
    for place in basemap.places:
        if place.get("kind") != "settlement":
            continue
        x, y = card.xy(place["x"], place["y"])
        if not (0 < x < card.w and 0 < y < card.h):
            continue
        out.append(
            Label(
                name=place.get("n", ""),
                kind="settlement",
                why=place.get("note", ""),
                px=x,
                py=y,
                tier=TIER_PLACE,
                size=DEFAULT_LINE_PX * 1.15,
            )
        )
    return out


def ground_labels(
    basemap: Basemap,
    lines: NamedLines,
    card: Any,
    route_px: list[Pt],
    picks: Any | None = None,
) -> list[Label]:
    """The names the ground is entitled to, whatever the payload asked for.

    Settlements and watercourses are already in the data and have simply never
    been lettered: the settlements sit in the basemap's candidates and the
    watercourses in its named lines. Choosing them is a rule, not a judgement,
    so it runs by default and the payload only ever adds to it.

    Three tiers own the answer, in this order: the rule, the user's own file
    for a standing exception, and `map.places` in the payload for this session.

    Args:
        basemap: The basemap, for its places and candidates.
        lines: The named lines, for the watercourses.
        card: The card, for the projection and its size.
        route_px: The track in card pixels.
        picks: The payload's `map` block, whose `places` name this session's
            exceptions. That hook has existed and done nothing since it was
            written; this is what reads it.

    Returns:
        The user's places, then the settlements, then the rivers, in the
        order they claim their boxes.
    """
    mine = home_places(basemap, card)
    always = [p.get("n", "") for p in basemap.places if p.get("always")] + [lb.name for lb in mine]
    wanted = list(getattr(picks, "places", None) or [])
    # The user writes "Swell" and OSM has Upper and Lower; the entry
    # carries its own position and it is authoritative, so a group within about
    # a merge's distance of it is the same place and is not lettered twice.
    near = MERGE_M * card.scale
    settled = [
        lb
        for lb in pick_settlements(basemap, card, route_px, always=always, wanted=wanted)
        if all(
            lb.name.casefold() != own.name.casefold()
            and math.dist((lb.px, lb.py), (own.px, own.py)) > near
            for own in mine
        )
    ]
    return mine + settled + pick_rivers(basemap, lines, card, route_px)


# --------------------------------------------------------------------------- roads

#: How long a named road has to run inside the card before its number is worth
#: setting along it, as a multiple of the type size the number is written at.
#: Stated against the type because the question is whether the road is longer
#: than its own name: a road number is five characters and about two and a half
#: type sizes wide, so this is a run about two and a half times the name, which
#: is enough for the number to read as a name along the tarmac rather than as a
#: tag on the end of it.
#:
#: It was a flat 110 display pixels, which is over three times the widest road
#: number and was that only because the card it was tuned on happened to carry
#: a 235 px run of one road, while a card whose longest run of that same
#: road is 92 px carried no number at all.
ROAD_MIN_CAPS = 6.4


def road_min_px(size: float) -> float:
    """The shortest run of road a number may be set along, in display pixels."""
    return size * ROAD_MIN_CAPS


ROAD_MAX = 2


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
#: half-width on one card and 1.42 on another. The
#: durable answer is for the painter to record the width it actually painted;
#: until it does, this is that measurement.
WET_SPREAD = 1.35


def feature_px(basemap: Basemap, kind: str, cls: str, own: float = 0.0) -> float:
    """How wide the painter's ink really is for one watercourse or road.

    The layers' `wet_px` is the brush's nominal width, not its footprint, so
    the spread the brush adds is put back on here.

    `own` is the width this particular watercourse was painted at, which is its
    own where one could be measured and the class floor where it could not. The
    class alone was enough while every river of a class was drawn at one width;
    the Calder is drawn at a quarter of a kilometre now, and a name lifted by
    the major class floor would be set in the water.
    """
    if kind == "river":
        wet = basemap.layers.wet_px
        floor = float(wet.get(cls, WET_PX_DEFAULT.get(cls, 2.2)))
        return max(floor, float(own or 0.0)) * WET_SPREAD
    return float(ROAD_PX_DEFAULT.get(cls, 3.4)) * WET_SPREAD


def pick_roads(
    basemap: Basemap,
    lines: NamedLines,
    card: Any,
    route_px: list[Pt],
    budget: int = ROAD_MAX,
) -> list[Label]:
    """Which named roads the sheet numbers, set along their own tarmac.

    A road number is the quietest thing on the map and one of the most useful:
    it is how a rider works out where a climb actually was. A road is lettered
    by its number where OSM has one, and by its name only where it has none:
    "A591" places a climb, "Keswick Road" eats a corner and says nothing at
    26 m a pixel. Only the roads the ride was on, and only where there is
    enough of one inside the card to write on.

    **A numbered road is one road, whatever OSM calls each mile of it.** The
    pieces used to be chained by their street name, and a street name changes
    at every parish: the A82 crosses a card as Glencoe, then
    Ballachulish, then New Road, then Kinlochleven Road, none of them a third of
    the shortest run a name can be set on, so that card carried no number at
    all while the same code numbered another card twice. Where a
    road has a number the number is what its pieces are gathered by, and the
    name is only the fallback for a lane that has none.

    Args:
        basemap: The basemap, for the width each class was painted at.
        lines: The named lines, for the roads.
        card: The card, for the projection and its size.
        route_px: The track in card pixels.
        budget: How many to letter.

    Returns:
        One `Label` a road, best first, carrying the tarmac as its baseline.
    """
    geom = lines.get("roads") or []
    thin = route_px[::4] or route_px
    pieces: dict[str, list[list[Pt]]] = {}
    widths: dict[str, float] = {}
    for entry in geom:
        name = str(entry.get("n") or "")
        if not name or entry.get("c") not in ("major", "medium"):
            continue
        line = [card.xy(x, y) for x, y in entry.get("d") or []]
        if len(line) > 1:
            key = road_ref(entry.get("r")) or name
            pieces.setdefault(key, []).append(line)
            widths[key] = max(
                widths.get(key, 0.0), feature_px(basemap, "road", str(entry.get("c")))
            )
    size = DEFAULT_LINE_PX * 0.7
    shortest = road_min_px(size)
    best: dict[str, tuple[float, list[Pt]]] = {}
    for key, parts in pieces.items():
        line = max(joined(parts), key=length)
        if length(line) < shortest:
            continue
        near = min(min(math.dist(p, q) for q in thin) for p in line[::2])
        if near > 40.0:  # a road the session was never on is not this map's
            continue
        best[key] = (length(line) - near, line)
    out: list[Label] = []
    for key, (_score, line) in sorted(best.items(), key=lambda kv: -kv[1][0])[:budget]:
        mid = line[len(line) // 2]
        out.append(
            Label(
                name=key,
                kind="road",
                why="road the session was on",
                px=mid[0],
                py=mid[1],
                tier=TIER_ROAD,
                size=size,
                baseline=line,
                feature_px=widths.get(key, 0.0),
            )
        )
    return out


def road_ref(raw: Any) -> str:
    """The road number to letter, out of whatever OSM put in `ref`.

    OSM joins concurrent numbers with a semicolon ("A5;A470") and sometimes
    pads them. A card has room for one number, so the first is taken: it is the
    one the signs lead with.

    Not every `ref` on a highway is a road number. Walking and cycling routes
    put their own code there and this box carries "NCN", "LDP" and "PW" from
    the Pennine Way and its neighbours. A road number always carries a
    digit and a route code here does not, so a ref with no digit in it is not
    treated as one.

    Args:
        raw: The `ref` tag, or None.

    Returns:
        The number to write, or "" when the road has none.
    """
    text = str(raw or "").strip().split(";")[0].strip()
    return text if any(ch.isdigit() for ch in text) else ""


def route_markers(route_px: list[Pt], size: float = DEFAULT_LINE_PX * 0.65) -> list[Label]:
    """Where the session set off and where it finished, in the route's own ink.

    The ground is drawn in the map's ink and the session in the route's, and
    these two are the session: they are facts about the ride, not about the
    place. A loop puts them on top of each other, so it gets one mark.
    """
    if len(route_px) < 2:
        return []
    start, end = route_px[0], route_px[-1]
    if math.dist(start, end) < 30.0:
        return [
            Label(
                name="start",
                kind="marker",
                why="where the session began",
                px=start[0],
                py=start[1],
                tier=TIER_MARKER,
                size=size,
            )
        ]
    return [
        Label(
            name="start",
            kind="marker",
            why="where the session began",
            px=start[0],
            py=start[1],
            tier=TIER_MARKER,
            size=size,
        ),
        Label(
            name="finish",
            kind="marker",
            why="where the session ended",
            px=end[0],
            py=end[1],
            tier=TIER_MARKER,
            size=size,
        ),
    ]


# --------------------------------------------------------------------------- geometry


def _outboard(span: Span, route_px: list[Pt]) -> float:
    """Which side of a span's own line is away from the route: +1 or -1.

    The line is an iso-distance contour, so it can sit either side of the run
    in card pixels and the answer cannot be taken from the offset's sign. It is
    read off the drawing instead: the way the text lifts is the way that puts
    it further from the track.
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


def _resample(line: list[Pt], step: float) -> list[Pt]:
    """A polyline at an even spacing, so an arc length is a straight lookup."""
    if len(line) < 2 or step <= 0:
        return list(line)
    out = [line[0]]
    carry = 0.0
    for a, b in zip(line, line[1:], strict=False):
        run = math.dist(a, b)
        if run < 1e-9:
            continue
        at = step - carry
        while at < run:
            t = at / run
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            at += step
        carry = (carry + run) % step
    out.append(line[-1])
    return out


def _window(line: list[Pt], start: int, want: float) -> list[Pt] | None:
    """The run of a line from one point that is `want` long, or None."""
    out = [line[start]]
    run = 0.0
    for i in range(start + 1, len(line)):
        run += math.dist(line[i - 1], line[i])
        out.append(line[i])
        if run >= want:
            return out
    return None


def _turning(pts: list[Pt]) -> float:
    """Total turning along a polyline, in degrees.

    The test that decides whether text can be set along something. Curvature at
    a point says nothing: what makes a run unreadable is how far round it goes
    from one end to the other.
    """
    total = 0.0
    for a, b, c in zip(pts, pts[1:], pts[2:], strict=False):
        u = math.atan2(b[1] - a[1], b[0] - a[0])
        v = math.atan2(c[1] - b[1], c[0] - b[0])
        total += abs((v - u + math.pi) % math.tau - math.pi)
    return math.degrees(total)


def _bow(pts: list[Pt]) -> float:
    """How far a run wanders off the straight line between its own ends."""
    (ax, ay), (bx, by) = pts[0], pts[-1]
    run = math.hypot(bx - ax, by - ay) or 1.0
    return max(abs((bx - ax) * (ay - y) - (ax - x) * (by - ay)) / run for x, y in pts)


def _on_line(line: list[Pt], cum: list[float], at: float) -> tuple[Pt, float]:
    """The point at an arc length along a line, and the tangent's angle there."""
    at = min(max(at, 0.0), cum[-1])
    i = min(_bisect(cum, at), len(line) - 2)
    run = max(cum[i + 1] - cum[i], 1e-9)
    t = (at - cum[i]) / run
    (ax, ay), (bx, by) = line[i], line[i + 1]
    return ((ax + (bx - ax) * t, ay + (by - ay) * t), math.atan2(by - ay, bx - ax))


def _bisect(cum: list[float], at: float) -> int:
    """The segment an arc length falls in."""
    lo, hi = 0, len(cum) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if cum[mid] <= at:
            lo = mid
        else:
            hi = mid
    return lo


# --------------------------------------------------------------------------- home

#: How far below its house a user's own place has its name written.
HOME_NAME_DROP = 25.0


def home_labels(
    basemap: Basemap, card: Any, pstyle: PaintStyle, measure_fn: Measure
) -> tuple[list[Label], list[Box]]:
    """The user's marked places, already placed, and the room they need.

    A house is not placed by the placer: it is where it is, and its name goes
    under it. So it comes back placed, with the box it occupies, and the box
    goes into the placer's `taken` list so nothing else is written across it.

    Args:
        basemap: The basemap, for its places.
        card: The card, for the projection and its size.
        pstyle: The paint style, for the type size and whether to draw at all.
        measure_fn: How wide a name is.

    Returns:
        The labels, and the boxes they have already claimed.
    """
    if not pstyle.home_glyph:
        return [], []
    size = pstyle.label_size_px * 0.85
    out: list[Label] = []
    boxes: list[Box] = []
    for place in basemap.places:
        if place.get("sym") != "house":
            continue
        x, y = card.xy(place["x"], place["y"])
        name = str(place.get("n") or "home")
        wide = max(measure_fn(name, size)[0], 26.0)
        out.append(
            Label(
                name=name,
                kind="home",
                why="the rider's own place",
                px=x,
                py=y,
                tier=TIER_PLACE,
                size=size,
                box=(x - wide / 2, y - 10, x + wide / 2, y + 28),
                tx=x,
                ty=y + HOME_NAME_DROP,
                anchor="middle",
            )
        )
        boxes.append(out[-1].box)
    return out, boxes


# --------------------------------------------------------------------------- the plate


def plate_key(placed: list[Label], spans: list[Span], pstyle: Any, base: str = "") -> str:
    """A hash over what is lettered and how, so a stale plate is never drawn.

    The base plates' own hash goes in as well: a repaint moves the paper the
    ink is gated on and the darkness the wash is judged against, so a label
    plate drawn against the old sheet is stale even when every name is the same.
    """
    from pyntpot._port import paint

    # The window, the lift, the intent and the wrap are drawn and are not in
    # `as_dict`,
    # which is the shape the page's tooltips have always read. A plate keyed
    # without them would survive a change to the very thing it drew.
    rows = [{"base": base}]
    for lb in placed:
        rows.append(
            {
                **lb.as_dict(),
                "intent": lb.intent,
                "lift": lb.lift,
                "flat": lb.flat,
                "lines": list(lb.lines),
                "window": [(round(x, 1), round(y, 1)) for x, y in lb.window],
            }
        )
    rows += [
        {
            "span": s.name,
            "kind": s.kind,
            "i0": s.i0,
            "i1": s.i1,
            "side": s.side,
            "rank": s.rank,
            "intent": s.intent,
            "line": [(round(x, 1), round(y, 1)) for x, y in s.line],
        }
        for s in spans
    ]
    return paint.labels_hash(rows, pstyle)


def draw_plate(
    plates: Plates,
    placed: list[Label],
    spans: list[Span],
    route_px: list[Pt],
    pstyle: Any,
    brush: BrushStyle,
    route: str | None = None,
) -> Any:
    """Stroke the placed names into an RGBA plate beside the other plates.

    The lettering is raster because the ink is: `stamp` deposits into a numpy
    accumulator gated on the paper's own height, and there is no path out of
    that to vector. So the label layer is a fourth plate, and the page and the
    card both draw the same pixels instead of each approximating them.

    It is cached on a hash of the names, their places and the label half of the
    paint style, because the picks live in the analysis payload and the plate
    hash cannot see them. A plate whose key does not match is not drawn at all
    rather than lettering yesterday's names over today's map.

    Args:
        plates: The painted plates, beside which the label plate is written.
        placed: The placed labels.
        spans: The placed spans.
        route_px: The track in card pixels.
        pstyle: The paint style.
        brush: The brush style the lettering's brushes and ink pads are made with.
        route: `centreline` or `outline`; the style's when not given.

    Returns:
        The path to the plate, or None when there is nothing to draw or no
        engine to draw it with.
    """
    import json

    if not placed and not spans:
        return None
    try:
        from pyntpot._port import paint
    except ImportError:  # no numpy or no Pillow: the caller letters in vector
        return None
    from pyntpot.letters.hand import Hand
    from pyntpot.letters.style import FaceStyle, HandStyle
    from pyntpot.maps import lettering_marks

    try:
        hand = Hand(
            FaceStyle(label_route=pstyle.label_route, label_face=pstyle.label_face),
            HandStyle(label_seed=pstyle.label_seed),
            route,
        )
    except (ImportError, OSError) as exc:  # no fonttools, or no face on disk
        log.info("no face to letter with: %s", exc)
        return None
    root = plates.directory
    stem = f"labels-{hand.route}"
    path, side = root / f"{stem}.webp", root / f"{stem}.json"
    key = plate_key(placed, spans, pstyle, plates.hash)
    if path.exists() and side.exists():
        try:
            if json.loads(side.read_text()).get("key") == key:
                return path
        except (OSError, ValueError):  # a half-written key is not a crash
            pass
    marks = lettering_marks.marks(hand, placed, spans)
    if not marks:
        return None
    written = paint.label_plate(plates.manifest.to_dict(), marks, pstyle, brush, path)
    if written is not None:
        side.write_text(json.dumps({"key": key, "face": hand.font.name, "route": hand.route}))
    return written
