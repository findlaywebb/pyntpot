"""Resolving span requests onto the route and placing each span's line beside it.

Key names: `resolve_spans`, which turns the caller's span requests into `Span`s by
point index, distance or time; `place_spans`, which gives each its line, its ticks and
the side it is drawn on, within the pixels it may reach from the route.

It does not place the names (the placer does) and does not stroke anything.

Invariants: no more than `SPAN_MAX` spans are kept; a span with nowhere to go is
dropped and the drop is logged; a span's mark never crosses any piece of the route.
"""

import logging
import math
from dataclasses import dataclass
from typing import Any

from pyntpot.ink.polyline import Pt, foot_on, length
from pyntpot.maps.annotations import Annotations, SpanRequest
from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import Measure, Span
from pyntpot.maps.lettering.span_clear import (
    SPAN_ALONG_MAX_BEARING_DEG,
    SPAN_CLEAR_CAPS,
    _route_near,
)
from pyntpot.maps.lettering.span_ends import _span_label, _span_ticks
from pyntpot.maps.lettering.span_line import SPAN_OFFSET_CAPS, _resample, span_line
from pyntpot.maps.lettering.span_sides import _curved_side, _freer_side

log = logging.getLogger(__name__)

#: The fewest points that make a segment.
_FEWEST_FOR_A_SEGMENT = 2

#: How many spans one card carries. Four made the sheet cluttered: with the
#: settlements, the rivers, the roads and the landmarks already on it, three
#: brackets is where the card still reads as a map rather than as a diagram.
#: Spans past the cap are dropped in the order the annotations list them, so
#: the caller's own order decides which survive.
SPAN_MAX = 3


def resolve_spans(
    picks: Annotations | None, times: list[float], dist_m: list[float], cap: int = SPAN_MAX
) -> list[Span]:
    """The annotations' span requests, each resolved to a pair of route indices.

    A caller states an extent in one of three vocabularies, because it has one
    of them to hand and converting between them is the renderer's job. Indices
    go straight through; kilometres are read against the route's own cumulative
    distance; seconds are read against its clock, which only a track with times
    has, so a card composed from a bare track resolves the first two and logs
    that it cannot resolve the third. A request that does not land, or ends no
    later than it starts, is dropped and the drop is logged.

    Args:
        picks: The caller's annotations, whose `spans` are read, or None.
        times: Seconds at each route point, or empty when there is no clock.
        dist_m: Cumulative metres at each route point.
        cap: How many spans the card carries. The annotations' own order
            decides which survive.

    Returns:
        One `Span` per span request that lands inside the route, longest first.
    """
    wanted = list(getattr(picks, "spans", None) or [])
    if not wanted or len(dist_m) < _FEWEST_FOR_A_SEGMENT:
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


def _span_index(
    entry: SpanRequest, end: str, times: list[float], dist_m: list[float]
) -> int | None:
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


SPAN_RUNG_CAPS = 2.1


@dataclass(frozen=True)
class SpanSurroundings:
    """What the spans are placed among: the card, the route and the rest of the sheet.

    Attributes:
        card: The card, for its size in display pixels.
        route_px: The track in card pixels.
        dark: The painter's darkness grid, `{"w", "h", "v"}`.
        avoid: Places the mark would rather not be drawn through, each an
            `(x, y, weight, radius)` in card pixels. A cost and never a rule:
            see `_drawn_side`.
        lines: The watercourses, roads and lanes, in card pixels, which a mark
            would rather not be drawn along. A cost as well.
    """

    card: Card
    route_px: list[Pt]
    dark: dict[str, Any]
    avoid: list[tuple[float, float, float, float]] | None = None
    lines: list[list[Pt]] | None = None


def place_spans(
    spans: list[Span],
    around: SpanSurroundings,
    measure_fn: Measure,
    cap_px: float = 14.0,
    rails: int = 3,
    along_max_deg: float = SPAN_ALONG_MAX_BEARING_DEG,
) -> list[Span]:
    """Choose a side and a rung for every span, and draw its mark.

    The ground takes the side of the route with more free paper over its own
    extent; the session takes the other, so the two never interleave. Where the
    stretch bends, the outside of the bend takes that choice off the free side
    unless the free side is clearly freer: see `_curved_side`. Within a side
    the spans are taken longest first: the first takes the rung nearest the
    route, and a later span moves out one rung past every span on that side it
    overlaps.

    The name is set along the span's own line when the span runs across the
    sheet, on the far side of the line from the route so the order the eye
    crosses is route, line, name. When the span runs down the sheet it is not:
    the name goes horizontally into whatever clear paper the placer can find
    beside it, and with no leader either way, because a name a few pixels from
    its own bracket does not need a line drawn to it.

    Args:
        spans: The resolved spans, longest first. Placed in place.
        around: The card, the route, the darkness grid and the places and lines
            a mark would rather keep off.
        measure_fn: How wide a name is, so a span too short to carry its own
            name along it is known before the window search is tried.
        cap_px: The lettering's cap height, which sets the ladder's spacing.
        rails: How many rungs a side carries before a span is dropped.
        along_max_deg: The bearing threshold, in degrees off horizontal.

    Returns:
        The spans that were placed. A span past the last rung is left out, and
        so is one no arc of whose envelope clears the route.
    """
    route_px = around.route_px
    placed: list[Span] = []
    used: dict[int, list[tuple[int, int, int]]] = {1: [], -1: []}
    for span in spans:
        free, margin = _freer_side(span, route_px, around.dark, around.card, cap_px)
        base = free if span.ground else -free
        span.side = _curved_side(span, route_px, base, margin, cap_px)
        # The side is settled before the rung, because the rung is what nests
        # one span inside another on a side and a span that moves afterwards
        # would nest against a side it is no longer on. The mark that settles
        # it is drawn at the first rung's offset; a span that ends up further
        # out is drawn again there.
        first = cap_px * SPAN_OFFSET_CAPS
        span.side, drawn = _drawn_side(span, route_px, cap_px, first, around.avoid, around.lines)
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
                clear_px=cap_px * SPAN_CLEAR_CAPS,
            )
        )
        if not span.line:
            # No arc of the envelope could be drawn clear of the route. A span
            # dropped with a reason on the record beats one drawn across the
            # road the reader is looking at, which is the route rule.
            log.info("span %r is not drawn: no mark clears the route", span.name)
            continue
        span.ticks = _span_ticks(span, route_px, cap_px)
        span.label = _span_label(span, route_px, cap_px, measure_fn, along_max_deg)
        used[span.side].append((span.i0, span.i1, rank))
        placed.append(span)
    return placed


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
        side: span_line(route_px, span.i0, span.i1, side, offset_px, clear_px=clear)
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
    if not lines or len(line) < _FEWEST_FOR_A_SEGMENT:
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
    the route rule, which is a constraint, is enforced in `span_line`, and this
    is the preference that sits beside it.
    """
    if not avoid or len(line) < _FEWEST_FOR_A_SEGMENT:
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
