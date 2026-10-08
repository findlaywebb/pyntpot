"""What a name costs where it sits: crossings, overlap, darkness, the route and its own feature.

Key names: `_crossings`, `_on_road`, `_overlap`, `_separation`, `_darkness`, `_on_paper`
and `_near_route`, which price one box against the roads, the other names, the painted
plates and the route; `_off_own` and `_off_own_feature`, which leave a name's own line
out of the roads it keeps off; `_is_own_feature`.

It does not choose a position and does not move a box; a caller adds these prices up.

Invariants: a price is never negative; no price here asks whether the box is on the
paper, which `_on_paper` answers for the caller.
"""

import itertools
import math
from dataclasses import dataclass, field
from typing import Any

from pyntpot.ink.polyline import Pt, foot_on
from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import NO_LEADER, Box, Label
from pyntpot.maps.lettering.span_clear import _seg_in_box

#: The fewest points that make a segment.
_FEWEST_FOR_A_SEGMENT = 2

#: Every how-manyth route point the placer prices the route at.
_ROUTE_THINNING = 3

#: Past this, more room is not worth having. A name this far from its nearest
#: neighbour is as separated as a reader can tell.
SEPARATION_CAP_PX = 90.0


#: How near the track still costs a name something, at the least, in display
#: pixels, and what sitting on it costs. Nine pixels is under half a line
#: height: alone it would let a twenty-pixel name sit ten pixels off the track
#: for nothing and read as written through the route, so the placer passes the
#: larger of this and the name's type size.
ROUTE_REACH_PX = 9.0


ROUTE_ON_COST = 260.0


#: How far inside the card's edge a name's box has to stay, in display pixels.
#: The edge is a constraint and never a penalty: a name in the torn margin is
#: not a cheaper answer than an awkward one on the paper, it is not an answer.
EDGE_PX = 14.0


#: How near its own feature a road or a river name set flat has to stay, in
#: display pixels beyond its own type size, and what a pixel past that costs.
#: A road name a reader cannot join to a road is not a road name: "Keswick
#: Road" sat far enough off its tarmac that the association was a guess.
OWN_FEATURE_SLACK_PX = 6.0


OWN_FEATURE_COST_PX = 3.0


@dataclass(frozen=True)
class Backdrop:
    """What every name on the card is priced against: the map, the route and the roads.

    Attributes:
        card: The card, for its size in display pixels.
        route_px: The track in display pixels.
        dark: The painter's dark grid, `{"w", "h", "v"}`.
        roads: Named road centrelines in display pixels. A name laid across one is
            costed, never forbidden.
    """

    card: Card
    route_px: list[Pt]
    dark: dict[str, Any]
    roads: list[list[Pt]] = field(default_factory=list)

    @property
    def thin(self) -> list[Pt]:
        """The route, thinned, which is what a name is priced against."""
        return self.route_px[::_ROUTE_THINNING] or self.route_px


@dataclass(frozen=True)
class Terms:
    """What one name is priced against where it is tried: the card and the map so far.

    Attributes:
        card: The card, for its size in display pixels.
        dark: The painter's dark grid, `{"w", "h", "v"}`.
        boxes: What is already on the map.
        roads: The lines the name is charged for crossing, its own feature
            already removed.
        route: The route in weighted parts, for the route cost.
    """

    card: Card
    dark: dict[str, Any]
    boxes: list[Box]
    roads: list[list[Pt]]
    route: list[tuple[list[Pt], float]]


def _crossings(box: Box, roads: list[list[Pt]]) -> int:
    """How many roads a box sits on. One count a road, not one a segment."""
    if not roads:
        return 0
    x0, y0, x1, y1 = box
    hit = 0
    for line in roads:
        for a, b in itertools.pairwise(line):
            if _seg_in_box(a, b, x0, y0, x1, y1):
                hit += 1
                break
    return hit


def _on_road(box: Box, roads: list[list[Pt]]) -> float:
    """Whether a box sits on tarmac at all: 1.0 or 0.0.

    Deliberately not a count. A name that lands on a junction touches five ways
    and is one fault, not five, and counting them made a crossing the most
    expensive thing on the map by an order of magnitude.
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
    """How far a box sits from the nearest thing already on the map.

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


def _darkness(box: Box, card: Card, dark: dict[str, Any]) -> float:
    """Mean darkness of the painter's own grid under a box."""
    gw, gh, grid = dark["w"], dark["h"], dark["v"]
    x0, y0, x1, y1 = box
    gx0 = max(int(x0 / card.w * gw), 0)
    gx1 = min(int(x1 / card.w * gw) + 1, gw)
    gy0 = max(int(y0 / card.h * gh), 0)
    gy1 = min(int(y1 / card.h * gh) + 1, gh)
    cells = [grid[r][c] for r in range(gy0, gy1) for c in range(gx0, gx1)]
    return float(sum(cells) / len(cells)) if cells else 0.3


def _on_paper(box: Box, card: Card) -> bool:
    """Whether a box is wholly inside the torn margin, on the paper."""
    x0, y0, x1, y1 = box
    return x0 > EDGE_PX and x1 < card.w - EDGE_PX and y0 > EDGE_PX and y1 < card.h - EDGE_PX


#: How near a crossing line has to run to a name's own feature, and how much of
#: it has to, before it is taken to *be* that feature. The lines come from the
#: same simplified geometry the baseline was chained from, so they coincide
#: exactly; the tolerance is for the arithmetic, not for the map.
OWN_LINE_PX = 2.0


OWN_LINE_FRAC = 0.9


def _is_own_feature(line: list[Pt], baseline: list[Pt]) -> bool:
    """Whether one crossing line is a piece of the feature a name belongs to."""
    if len(line) < _FEWEST_FOR_A_SEGMENT or len(baseline) < _FEWEST_FOR_A_SEGMENT:
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
    feature that includes the feature itself, so without this every candidate
    window would score as "on a road" and the term would cancel out: a river's
    name could not be moved off a bridge because it would be on a road
    wherever it went.

    **A name is not charged for crossing the thing it names.** Everything else
    still counts, which is what leaves a bridge as the one road under a river's
    name that means anything.
    """
    if not lb.baseline:
        return roads
    return [line for line in roads if not _is_own_feature(line, lb.baseline)]


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
    near = float(
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

    `reach` is how near counts as near; the placer passes the larger of the
    label's own type size and `ROUTE_REACH_PX`. The cost falls off linearly to
    zero at `reach`, so widening it puts no step in the middle of the costs the
    placer compares.

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
        near = float(
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
        counts = 1.0 if near <= 0.0 else weight
        if near < reach:
            worst = max(worst, ROUTE_ON_COST * (1.0 - near / reach) * counts)
    return worst
