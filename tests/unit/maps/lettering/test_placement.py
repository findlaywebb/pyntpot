"""Placing every name: the order, the leaders and the swaps that uncross them."""

import math
from functools import partial

from pyntpot.ink.polyline import meet
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.lettering.label import (
    TIER_LANDMARK,
    TIER_RIVER,
    TIER_ROAD,
    TIER_SETTLEMENT,
    TIER_SPAN,
    Label,
)
from pyntpot.maps.lettering.placement import _reseat, _uncross_leaders, place
from pyntpot.maps.lettering.placement_along import IN_WATER_ROAD_COST
from pyntpot.maps.lettering.placement_costs import Backdrop, _crossings, _on_road
from pyntpot.maps.lettering.placement_flat import LEADER_COST_PX, LEADER_RUNGS, ROAD_CROSS_COST
from pyntpot.maps.lettering.placement_lift import (
    MAX_TILT_DEG,
    TILT_EXEMPT_KINDS,
    _curved_boxes,
    _tilt,
)
from pyntpot.maps.lettering.placement_marks import _mark_through
from pyntpot.maps.lettering_marks import box_size

from support.basemaps import river_label, wide_card
from support.lettering import flat_dark, open_hand, sheet_card
from support.measure import flat_measure


def test_a_curved_label_reserves_the_room_it_actually_takes():
    """The fault every variant shared: a curved name defended the wrong box."""
    # A river used to claim the box its anchor fell in and then be set along a
    # window chosen afterwards, so nothing placed later avoided the pixels the
    # reader saw. The window is chosen in the placer now and contributes a run of
    # small boxes, and this asserts both: that the boxes follow the water, and
    # that a name placed afterwards is pushed off them.
    card = sheet_card()
    water = [(float(x), 150.0 + 18.0 * math.sin(x / 70.0)) for x in range(20, 380, 6)]
    river = Label(
        name="Heddon",
        kind="river",
        px=200.0,
        py=150.0,
        tier=TIER_RIVER,
        size=14.0,
        baseline=water,
    )
    later = Label(
        name="Monmouth Castle",
        kind="monument",
        px=200.0,
        py=150.0,
        tier=TIER_LANDMARK,
        size=14.0,
    )
    got = place(
        [river, later],
        [],
        Backdrop(card, [(0.0, 290.0), (400.0, 290.0)], flat_dark()),
        [],
        flat_measure,
    )
    assert river.window, "the river was not set along its own water"
    assert not river.flat
    # A box that follows the water, rather than one drawn round the anchor.
    assert river.box is not None
    assert river.box[2] - river.box[0] > 20.0
    # And the name that came after it is not sitting on top of it.
    assert later.box is not None
    x0, y0, x1, y1 = later.box
    for bx0, by0, bx1, by1 in [river.box]:
        assert not (min(x1, bx1) > max(x0, bx0) and min(y1, by1) > max(y0, by0)), (
            "the later name was placed on top of the curved one"
        )
    assert got == [river, later]


def test_a_road_crossing_costs_and_a_longer_leader_is_the_cheaper_answer():
    """The rule: shift the name and spend leader instead."""
    # Not a constraint. Sometimes there is nowhere else and a name that vanished
    # would be worse than one that crosses a lane, so it is priced, and priced
    # against the leader so the two are directly comparable. That ordering is the
    # rule: a crossing has to cost more than the placer could ever spend on
    # leader, or the cheap answer stays the one on the tarmac.
    assert max(LEADER_RUNGS) * LEADER_COST_PX < ROAD_CROSS_COST

    card = sheet_card()
    route = [(0.0, 290.0), (400.0, 290.0)]
    free = Label(name="Castle", kind="monument", px=200.0, py=150.0, size=14.0)
    place([free], [], Backdrop(card, route, flat_dark(), []), [], flat_measure)
    # A road laid straight down the middle of the box the placer just chose.
    assert free.box is not None
    x0, _y0, x1, _y1 = free.box
    road = [[((x0 + x1) / 2, 0.0), ((x0 + x1) / 2, 300.0)]]
    assert _crossings(free.box, road) > 0

    moved = Label(name="Castle", kind="monument", px=200.0, py=150.0, size=14.0)
    place([moved], [], Backdrop(card, route, flat_dark(), road), [], flat_measure)
    assert moved.box is not None
    assert _crossings(moved.box, road) == 0, "the road was not avoided"
    assert moved.box != free.box


def test_a_river_follows_its_bend_even_when_the_bend_runs_down_the_sheet():
    """The rule that overrules the tilt test for rivers only."""
    # A river name says which water it is by sitting on that water. A steep
    # window used to be refused outright, which put the Heddon and the lower Lyn
    # in clear paper beside their own bends; a name read sideways is better than
    # one that could be about anything.
    card = sheet_card()
    water = [(200.0 + 12.0 * math.sin(y / 60.0), float(y)) for y in range(20, 280, 5)]
    river = Label(
        name="Heddon",
        kind="river",
        px=200.0,
        py=150.0,
        tier=TIER_RIVER,
        size=14.0,
        baseline=water,
    )
    place(
        [river], [], Backdrop(card, [(0.0, 295.0), (400.0, 295.0)], flat_dark()), [], flat_measure
    )
    assert river.window, "a vertical river was not set along its own water"
    assert not river.flat
    assert _tilt(river.window) > MAX_TILT_DEG, "this window is a steep one"
    assert "river" in TILT_EXEMPT_KINDS


def test_the_tilt_test_still_holds_for_everything_that_is_not_a_river():
    """A road is not exempt: the rule that was overruled was about water."""
    card = sheet_card()
    tarmac = [(200.0 + 12.0 * math.sin(y / 60.0), float(y)) for y in range(20, 280, 5)]
    road = Label(
        name="A361", kind="road", px=200.0, py=150.0, tier=TIER_ROAD, size=14.0, baseline=tarmac
    )
    place([road], [], Backdrop(card, [(0.0, 295.0), (400.0, 295.0)], flat_dark()), [], flat_measure)
    assert road.flat, "a steep road window was accepted"


def test_a_span_name_lands_beside_the_bracket_it_belongs_to():
    """End to end, on a bracket short enough for the fault to bite."""
    # The whole point of the two costs above is what the placer does with them.
    # A name whose block is a good deal wider than its own bracket still has to
    # end up beside the bracket, on the outboard side, without the line through
    # the words.
    card = sheet_card()
    route = [(100.0 + i * 6.0, 200.0) for i in range(16)]
    bracket = [(100.0 + i * 6.0, 170.0) for i in range(16)]
    span = Label(
        name="the long climb out of Aviemore",
        kind="climb",
        tier=TIER_SPAN,
        size=14.0,
        px=145.0,
        py=150.0,
        mark=bracket,
        span_range=(0, 15),
        anchors=[(115.0, 150.0), (145.0, 150.0), (175.0, 150.0)],
    )
    place(
        [span],
        [],
        Backdrop(card, route, {"w": 2, "h": 2, "v": [[0.0, 0.0], [0.0, 0.0]]}),
        [],
        flat_measure,
    )
    assert span.box is not None
    x0, y0, x1, y1 = span.box
    near = min(min(math.dist(((x0 + x1) / 2, y), q) for q in bracket) for y in (y0, y1))
    assert near < 3.0 * span.size, f"the name landed {near:.0f} px off its bracket"
    assert (y0 + y1) / 2 < 170.0, "the name sat between the bracket and the road"
    assert _mark_through(span.box, span) == 0.0


def test_a_rivers_two_names_are_kept_apart_along_the_water_not_across_the_sheet():
    """A river doubles back, so a straight line between two names is not the gap."""
    # The guard used to measure the distance across the paper, which on a
    # meandering river is a fraction of the water between the two, and on the Lyn
    # it rejected every window the second name had left.
    card = sheet_card()
    # A hairpin: two long reaches whose ends are near each other on the map.
    down = [(60.0 + x * 0.6, 60.0 + x * 0.02) for x in range(0, 300, 4)]
    back = [(240.0 - x * 0.6, 74.0 + x * 0.02) for x in range(0, 300, 4)]
    water = down + back
    river = Label(
        name="Lyn", kind="river", px=150.0, py=70.0, tier=TIER_RIVER, size=13.0, baseline=water
    )
    second = Label(
        name="Lyn", kind="river", px=150.0, py=90.0, tier=TIER_RIVER, size=13.0, baseline=water
    )
    place(
        [river, second],
        [],
        Backdrop(card, [(0.0, 295.0), (400.0, 295.0)], flat_dark()),
        [],
        flat_measure,
    )
    assert river.window and second.window, "the second name lost its water"
    # Far apart along the water, and that is what the guard measures.
    assert math.dist((river.tx, river.ty), (second.tx, second.ty)) > 20.0


def test_a_name_on_the_water_is_moved_off_a_bridge():
    """A bridge drawn through the letters is not ordinary cartography."""
    assert IN_WATER_ROAD_COST > ROAD_CROSS_COST
    hand = open_hand()
    name = river_label(40.0)
    bridge = [(450.0, 300.0), (450.0, 500.0)]
    dark = {"w": 2, "h": 2, "v": [[0.6, 0.6], [0.6, 0.6]]}
    place(
        [name],
        [],
        Backdrop(wide_card(), [(0.0, 0.0)], dark, [name.baseline, bridge]),
        [],
        partial(box_size, hand),
    )
    cells = _curved_boxes(name.window, name, name.size)
    assert cells
    assert sum(_on_road(c, [bridge]) for c in cells) == 0


def _leadered(name, x, y):
    """One landmark waiting to be placed."""
    return Label(
        name=name,
        kind="monument",
        why="",
        px=float(x),
        py=float(y),
        tier=TIER_LANDMARK,
        size=DEFAULT_LINE_PX,
    )


def _dark():
    return {"w": 2, "h": 2, "v": [[0.1, 0.1], [0.1, 0.1]]}


def _seat(label, cx, cy, width):
    """Sit one placed name's block on a point, as the placer would have."""
    label.box = (cx - width / 2, cy - 10, cx + width / 2, cy + 10)
    label.flat = True
    label.leader = ((label.px, label.py), (cx, cy))
    _reseat(label, cx, cy)


def test_two_leaders_that_cross_are_swapped_over():
    """The placer is greedy, so two names can reach past each other."""
    # A reader meeting a crossing follows the wrong line to the wrong pin, and
    # swapping the two names over is what shortens both leaders at once.
    a, b = _leadered("Alpha", 100.0, 100.0), _leadered("Beta", 100.0, 200.0)
    # Seated deliberately the wrong way round: each name is off past the other.
    _seat(a, 300.0, 200.0, 60.0)
    _seat(b, 300.0, 100.0, 60.0)
    assert meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is not None
    _uncross_leaders([a, b], Backdrop(sheet_card(), [(0.0, 10.0), (400.0, 10.0)], _dark(), []))
    assert meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is None
    assert a.leader[1][1] < b.leader[1][1], "each name is still past the other"


def test_a_swap_that_reads_worse_is_refused():
    """The swap is offered, not imposed: a name is never pushed off the map."""
    # A wide name and a narrow one can cross, and the wide one does not fit where
    # the narrow one is sitting. A shorter pair of leaders is not worth a name in
    # the torn margin.
    a, b = _leadered("Alpha", 100.0, 100.0), _leadered("Beta", 340.0, 100.0)
    _seat(a, 365.0, 200.0, 40.0)
    _seat(b, 110.0, 200.0, 160.0)
    assert meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is not None
    seats = (a.box, b.box)
    _uncross_leaders([a, b], Backdrop(sheet_card(), [(0.0, 10.0), (400.0, 10.0)], _dark(), []))
    assert (a.box, b.box) == seats, "a name was swapped off the paper"


def test_a_name_on_its_own_mark_is_never_swapped():
    """A settlement is its place: it has no leader and cannot be moved."""
    a = _leadered("Alpha", 150.0, 150.0)
    a.box, a.flat, a.leader = (270.0, 140.0, 330.0, 160.0), True, ((150.0, 150.0), (300.0, 150.0))
    town = Label(
        name="Elm",
        kind="settlement",
        px=250.0,
        py=150.0,
        tier=TIER_SETTLEMENT,
        size=DEFAULT_LINE_PX,
    )
    town.box, town.flat, town.leader = (70.0, 140.0, 130.0, 160.0), True, None
    seat = town.box
    _uncross_leaders([a, town], Backdrop(sheet_card(), [(0.0, 10.0), (400.0, 10.0)], _dark(), []))
    assert town.box == seat
