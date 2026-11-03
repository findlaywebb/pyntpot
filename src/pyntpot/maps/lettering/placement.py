"""Placing every name on the card: the order, the leaders, and the swaps that uncross them.

Key names: `place`, which places every label and every span request in tier order and
then swaps leaders that cross (`placement_leaders.uncross_leaders`); `_place`, one name's
cheapest seat; `_places_to_avoid`, the settlements a span keeps off.

It does not pick what is named (a caller hands in the labels), does not measure a name
(the caller's `measure` does) and draws nothing.

Invariants: labels come back in tier order each carrying its box and anchor, and its
window when it is set along a line; a name that repeats another's place is dropped, and
so is a river's repeat that finds no window on its water, rather than set flat, and a
river or road name with no seat on the paper; a flat box is as wide as the hand writes
the name, its kind's tracking included; two flat names whose leaders cross are swapped
over when the swap uncrosses them and makes the pair cheaper.
"""

from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.lettering.label import OFF_PAPER_DROPPED_KINDS, Box, Label, Measure, Span
from pyntpot.maps.lettering.label_sizing import MeasureTracked, kind_measure
from pyntpot.maps.lettering.placement_along import place_along
from pyntpot.maps.lettering.placement_costs import (
    Backdrop,
    Terms,
    box_on_paper,
    off_own,
    route_for,
)
from pyntpot.maps.lettering.placement_flat import best_flat
from pyntpot.maps.lettering.placement_leaders import uncross_leaders
from pyntpot.maps.lettering.placement_lift import TILT_EXEMPT_KINDS
from pyntpot.maps.lettering.placement_names import dedupe_names
from pyntpot.maps.lettering.spans import SpanSurroundings, place_spans

#: What setting a name on the thing it names is worth, against setting it in
#: clear paper beside it. A river written along its water and a span written
#: along its bracket both say something a horizontal name cannot, so the curve
#: wins ties and wins near-ties; it does not win when the only window left puts
#: the name on top of two others.
ALONG_BONUS = 70.0


#: Under this many characters a curve is noise rather than a baseline. Three,
#: because "Eden" is a river name and the whole reason a river has a baseline is
#: that the water says which water it is.
MIN_CURVED_CHARS = 3


def place(
    labels: list[Label],
    spans: list[Span],
    ground: Backdrop,
    taken: list[Box],
    measure_fn: Measure,
    *,
    measure_tracked: MeasureTracked,
) -> list[Label]:
    """Put every name in its cheapest seat, one at a time in tier order.

    Curved names are placed here too: a river, a road or a span has its window
    chosen here, against everything already on the map, and the run of small
    boxes it really occupies goes back into the pile for the next name to
    avoid, so the box the placer defends and the pixels the reader sees are in
    the same place.

    It is also the one funnel every name on the map goes through, whichever
    pool found it, so it is where `dedupe_names` can see that the settlement
    "Elm" and the landmark "Elm" are one village.

    A label that names a place another already names is dropped, and so is a
    river's repeat of a name already set along its water when no window on that
    water is left for it: a river's first name keeps its flat fallback, its
    repeat does not. A river or road name with no seat on the paper is dropped.

    Source: `label-placement` in docs/explanation/references.md.

    Args:
        labels: The names to place, each with its anchor already in display pixels.
        spans: Spans to place first, so a span line is on the map before
            anything looks for room. Placed in place; their names join the
            queue and are placed with everything else.
        ground: The card, the track in display pixels, the painter's
            dark grid and the named road centrelines. A name laid across a road
            is costed, never forbidden.
        taken: Boxes already spoken for, such as the home glyph's.
        measure_fn: How wide and tall a span's name is set flat, for the
            span's own seat beside its bracket.
        measure_tracked: How wide and tall a name is when the hand writes it
            with its kind's tracking: how long the window a curved name is cut
            to has to be, and how wide the box a flat name reserves.

    Returns:
        The labels that survive `dedupe_names`, the spans' names among them, in
        tier order, each carrying its box, its text anchor and, when it is set
        along a line, the run of line it is set along.
    """
    boxes = list(taken)
    todo = list(labels)
    if spans:
        around = SpanSurroundings(
            ground.card, ground.route_px, ground.dark, _places_to_avoid(labels), ground.roads
        )
        place_spans(spans, around, measure_fn)
        todo += [span.label for span in spans if span.label is not None]
    ordered = sorted(dedupe_names(todo, ground.card), key=lambda lb: lb.tier)
    return _place(ordered, ground, boxes, measure_tracked=measure_tracked)


#: How far a settlement's own ground reaches, in multiples of the size its
#: name is lettered at. A town is lettered larger than a village and takes up
#: more of the map, so one number covers both. Three: on a 900 px card that
#: is about 70 px round a town, which is the built-up part of the corner a
#: span mark is drawn round rather than through.
SETTLEMENT_GROUND_SIZES = 3.0


def _places_to_avoid(labels: list[Label]) -> list[tuple[float, float, float, float]]:
    """The settlements a span mark would rather not be drawn through.

    `(x, y, weight, radius)` in display pixels, weighted by how large the name is
    set, which is how the map already says how big the place is.
    """
    return [
        (lb.px, lb.py, lb.size / DEFAULT_LINE_PX, lb.size * SETTLEMENT_GROUND_SIZES)
        for lb in labels
        if lb.kind == "settlement"
    ]


def _place(
    labels: list[Label],
    ground: Backdrop,
    boxes: list[Box],
    *,
    measure_tracked: MeasureTracked,
) -> list[Label]:
    """Place each label, curved along its own line where it has one.

    The cost is what the reader would complain about: text over the route, text
    on top of another label, text on a dark wash, text laid across a road. The
    card's edge is not in that list because it is not a cost: a candidate on
    the paper beats every candidate off it outright.

    A river's repeat of a name already set along its water, with no window
    left on that water, is not placed at all, and nor is a river or road name
    with no seat on the paper: half a name in the torn margin is worse than none.
    """
    placed: list[Label] = []
    route_px, thin = ground.route_px, ground.thin
    # Where each name has already been set along its own line, so the major
    # river's second name lands somewhere else on the water rather than beside
    # its first.
    repeats: dict[str, list[float]] = {}
    for lb in labels:
        mine = route_for(lb, route_px, thin)
        terms = Terms(
            ground.card,
            ground.dark,
            boxes,
            off_own(ground.roads, lb),
            mine,
            ground.water,
            ground.segments,
        )
        # Flat or curved, the hand writes a name with its kind's tracking.
        measure_kind = kind_measure(measure_tracked, lb.kind)
        along = None
        if lb.baseline and len(lb.name) >= MIN_CURVED_CHARS:
            tw, th = measure_kind(lb.name, lb.size)
            along = place_along(lb, tw, th, terms, repeats.get(lb.name, []))
        if along is None and lb.kind == "river" and lb.name in repeats:
            # The second name of a river that has no water left is dropped: set
            # flat beside its first it would be a second, unrelated river.
            continue
        flat = best_flat(lb, terms, measure_kind)
        assert lb.box is not None
        on_paper = box_on_paper(lb.box, terms.card)
        if along is None and not on_paper and lb.kind in OFF_PAPER_DROPPED_KINDS:
            continue
        # Two real candidates, one scale. Setting a name on its own feature is
        # worth something in itself, and `ALONG_BONUS` is that something; past
        # it, a name jammed against three others on its river is worse than the
        # same name in clear paper beside it, and the placer should be able to
        # say so rather than always preferring the curve.
        #
        # A river is the exception: where its own water
        # offers any usable window at all the name goes on the water, whatever
        # the flat answer costs. So does any name whose flat answer is off the paper.
        if along is not None and (lb.kind in TILT_EXEMPT_KINDS or not on_paper):
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
    uncross_leaders(placed, ground)
    return placed
