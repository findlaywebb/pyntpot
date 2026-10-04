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
from typing import TYPE_CHECKING, Any

from pyntpot.ink.chains import joined
from pyntpot.ink.polyline import (
    cumulative_length,
    foot_on,
    length,
    meet,
    simplify,
)
from pyntpot.ink.sheet import Canvas
from pyntpot.letters import nib
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.letters.style import NibGroups

if TYPE_CHECKING:
    from pyntpot.maps.basemap import Basemap, Line
    from pyntpot.maps.lettering.label import Box, Label, Measure, Span
    from pyntpot.maps.plates import Plates
    from pyntpot.maps.style import Style

log = logging.getLogger(__name__)

Pt = tuple[float, float]
#: The named lines a label may be set along, by kind: `roads` and `rivers`
#: (one entry a named line), `coast` and `crossings` (bare point lists), in
#: card metres. `named_lines` builds it from a basemap.
NamedLines = dict[str, list[Any]]


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
    from pyntpot.maps.lettering.spans import SpanSurroundings, place_spans

    boxes = list(taken)
    todo = list(labels)
    if spans:
        around = SpanSurroundings(card, route_px, dark, _places_to_avoid(labels), roads or [])
        place_spans(spans, around, measure_fn)
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
    from pyntpot.maps.lettering.span_clear import _seg_in_box

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
    from pyntpot.maps.lettering.label import WRAP_LEADING

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
    from pyntpot.maps.lettering.label import block_size, wrap_forms

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
    from pyntpot.maps.lettering.label import TIER_SPAN

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
    from pyntpot.maps.lettering.label import TIER_SPAN

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
    from pyntpot.maps.lettering.label import NO_LEADER, TIER_SPAN, WRAP_LEADING

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
    from pyntpot.maps.lettering.label import NO_LEADER

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
    from pyntpot.maps.lettering.label import TIER_SPAN
    from pyntpot.maps.lettering.span_line import _resample

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


#: When a mark fails as a mark. Two things only: nothing was drawn, or what was
#: drawn comes nearer the route than the clearance it was given. Neither is a
#: matter of taste. What used to be here as well - that a mark must not close
#: on itself, and that it must hold the offset the ladder reserved to within a
#: quarter - is withdrawn: a mark may be drawn round a doubled-back stretch,
#: which encloses it, and its distance from the route is allowed to vary.


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
    from pyntpot.maps.lettering.label import TIER_SETTLEMENT, Label

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
    from pyntpot.maps.lettering.label import TIER_SPAN

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
    from pyntpot.maps.lettering.label import TIER_RIVER, Label, feature_px

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
    from pyntpot.maps.lettering.label import TIER_PLACE, Label

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
    from pyntpot.maps.lettering.label import TIER_ROAD, Label, feature_px

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
    from pyntpot.maps.lettering.label import TIER_MARKER, Label

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
    basemap: Basemap, card: Any, style: Style, measure_fn: Measure
) -> tuple[list[Label], list[Box]]:
    """The user's marked places, already placed, and the room they need.

    A house is not placed by the placer: it is where it is, and its name goes
    under it. So it comes back placed, with the box it occupies, and the box
    goes into the placer's `taken` list so nothing else is written across it.

    Args:
        basemap: The basemap, for its places.
        card: The card, for the projection and its size.
        style: The style, for the type size and whether to draw at all.
        measure_fn: How wide a name is.

    Returns:
        The labels, and the boxes they have already claimed.
    """
    from pyntpot.maps.lettering.label import TIER_PLACE, Label

    if not style.lettering.home_glyph:
        return [], []
    size = style.nib.label_size_px * 0.85
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


def draw_plate(
    plates: Plates,
    placed: list[Label],
    spans: list[Span],
    route_px: list[Pt],
    style: Style,
    route: str | None = None,
) -> Any:
    """Stroke the placed names into an RGBA plate beside the other plates.

    The lettering is raster because the ink is: `stamp` deposits into a numpy
    accumulator gated on the paper's own height, and there is no path out of
    that to vector. So the label layer is a fourth plate, and the page and the
    card both draw the same pixels instead of each approximating them.

    It is cached on `Cache.lettering_key`: the marks to be stroked, the base
    plates' hash and the style's lettering digest, so a moved name, pin, leader
    or span line, a repaint of the base plates or another hand all change it. A
    plate whose key does not match is not drawn at all rather than lettering
    yesterday's names over today's map.

    Args:
        plates: The painted plates, beside which the label plate is written.
        placed: The placed labels.
        spans: The placed spans.
        route_px: The track in card pixels.
        style: The style the card is lettered in; its brush style makes the
            lettering's brushes and ink pads.
        route: `centreline` or `outline`; the style's when not given.

    Returns:
        The path to the plate, or None when there is nothing to draw or no
        engine to draw it with.
    """
    import json

    if not placed and not spans:
        return None
    from pyntpot.letters.hand import Hand
    from pyntpot.maps import lettering_marks
    from pyntpot.maps.cache import Cache
    from pyntpot.maps.plates import dark_array

    try:
        hand = Hand(style.face, style.hand, route)
    except (ImportError, OSError) as exc:  # no fonttools, or no face on disk
        log.info("no face to letter with: %s", exc)
        return None
    root = plates.directory
    stem = f"labels-{hand.route}"
    path, side = root / f"{stem}.webp", root / f"{stem}.json"
    marks = lettering_marks.marks(hand, placed, spans)
    if not marks:
        return None
    key = Cache.lettering_key(marks, plates.hash, style)
    if path.exists() and side.exists():
        try:
            if json.loads(side.read_text()).get("key") == key:
                return path
        except (OSError, ValueError):  # a half-written key is not a crash
            pass
    card = plates.card
    rw, rh = card.render
    surface = nib.NibSurface(
        Canvas(*card.box, rw, rh),
        card.render_scale,
        dark_array(plates.manifest.dark, rh, rw),
        plates.manifest.gran_px,
    )
    written = nib.plate(
        marks, surface, NibGroups(style.nib, style.face, style.hand, style.brush, style.paper), path
    )
    if written is not None:
        side.write_text(json.dumps({"key": key, "face": hand.font.name, "route": hand.route}))
    return written
