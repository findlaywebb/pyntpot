"""Setting a name flat beside its anchor, broken over lines when that pays."""

from functools import partial

import pytest

from pyntpot.ink.polyline import Pt
from pyntpot.letters.hand import Hand
from pyntpot.letters.style import NibStyle
from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import (
    TIER_RIVER,
    TIER_SPAN,
    WRAP_LEADING,
    Box,
    Label,
    block_size,
)
from pyntpot.maps.lettering.placement import place
from pyntpot.maps.lettering.placement_costs import EDGE_PX, Backdrop, Terms
from pyntpot.maps.lettering.placement_flat import _place_flat
from pyntpot.maps.lettering.span_clear import seg_in_box
from pyntpot.maps.lettering_marks import box_size, label_marks

from support.basemaps import hung_card
from support.lettering import flat_dark, map_card, open_hand
from support.measure import flat_measure


def test_a_wrapped_name_is_written_on_the_lines_it_reserved():
    """The box is the block's, and the hand writes the block, not the name."""
    card = map_card()
    route = [(0.0, 295.0), (400.0, 295.0)]
    name = Label(
        name="the long climb out of Aviemore",
        kind="span",
        tier=TIER_SPAN,
        px=200.0,
        py=150.0,
        size=14.0,
    )
    name.lines = ["the long climb", "out of Aviemore"]
    wide, tall = block_size(name.lines, name.size, flat_measure)
    _place_flat(name, wide, tall, Terms(card, flat_dark(), [], [], [(route, 1.0)]), len(name.lines))
    assert name.box is not None
    assert name.text_lines == name.lines
    assert name.box[3] - name.box[1] == pytest.approx(tall)
    # The two baselines both sit inside the box the placer reserved.
    second = name.ty + name.size * WRAP_LEADING
    assert name.box[1] < name.ty < name.box[3]
    assert name.box[1] < second < name.box[3] + name.size


def test_a_leader_is_not_run_through_a_placed_label():
    """The cheapest unpenalised seat is east, but its leader would cut the label between."""
    card = map_card()
    mark = Label(name="Lake Road Chapel", kind="monument", tier=3, px=200.0, py=150.0, size=14.0)
    # A narrow placed label just east of the mark: a seat beyond it overlaps nothing,
    # but the line to that seat passes through it.
    wall = (205.0, 120.0, 213.0, 180.0)
    wide, tall = block_size([mark.name], mark.size, flat_measure)
    # West is taken, so the cheap seat left is the one beyond the wall.
    west = (0.0, 100.0, 196.0, 200.0)
    _place_flat(mark, wide, tall, Terms(card, flat_dark(), [wall, west], [], []))
    assert mark.leader is not None
    assert not seg_in_box(mark.leader[0], mark.leader[1], *wall)


def _set_flat(name: Label, card: Card, taken: list[Box]) -> tuple[list[Label], Hand]:
    """Place one name with a real hand's measures, as the map does, against the boxes taken."""
    hand = open_hand()
    got = place(
        [name],
        [],
        Backdrop(card, [(0.0, card.h - 5.0), (float(card.w), card.h - 5.0)], flat_dark()),
        taken,
        partial(box_size, hand),
        measure_tracked=partial(box_size, hand),
    )
    return got, hand


#: Where a river with no water to run along is anchored near an edge, and the paper already
#: taken beside it, so the cheap seat lies towards that edge.
EDGE_CASES = (
    ((110.0, 150.0), [(115.0, 0.0, 400.0, 300.0)]),
    ((290.0, 150.0), [(0.0, 0.0, 285.0, 300.0)]),
    ((200.0, 30.0), []),
    ((200.0, 270.0), []),
)


@pytest.mark.parametrize(("anchor", "taken"), EDGE_CASES, ids=["left", "right", "top", "bottom"])
def test_a_tracked_name_set_flat_near_the_edge_is_written_inside_the_paper(
    anchor: Pt, taken: list[Box]
) -> None:
    """Every glyph of a river name set flat, as wide as the hand tracks it, stays in its box."""
    card = map_card()
    river = Label(
        name="Afon Arddu", kind="river", px=anchor[0], py=anchor[1], tier=TIER_RIVER, size=18.0
    )
    got, hand = _set_flat(river, card, taken)
    assert got == [river]
    assert river.box is not None
    _assert_on_paper(river, hand, card)
    xs = [x for mark in label_marks(hand, river, NibStyle()) for x, _y in mark.pts]
    assert river.box[0] <= min(xs)
    assert max(xs) <= river.box[2]


def test_a_river_name_on_water_running_off_the_card_slides_along_it_onto_the_paper():
    """A river whose water leaves by the left edge is named on a reach wholly on the paper."""
    card = map_card()
    water = [(-120.0 + x * 4.0, 150.0) for x in range(70)]
    river = Label(name="Afon Arddu", kind="river", px=5.0, py=150.0, tier=TIER_RIVER, size=18.0)
    river.baseline = water
    got, hand = _set_flat(river, card, [])
    assert got == [river]
    assert river.window, "the river was not set along its own water"
    _assert_on_paper(river, hand, card)


def _assert_on_paper(name: Label, hand: Hand, card: Card) -> None:
    """Every point the hand writes for a placed name lies inside the card's torn margin."""
    marks = label_marks(hand, name, NibStyle())
    xs = [x for mark in marks for x, _y in mark.pts]
    ys = [y for mark in marks for _x, y in mark.pts]
    assert xs
    assert min(xs) > EDGE_PX
    assert max(xs) < card.w - EDGE_PX
    assert min(ys) > EDGE_PX
    assert max(ys) < card.h - EDGE_PX


def test_a_river_name_with_no_seat_on_the_paper_is_dropped():
    """A river name wider than the paper, with no water to run along, is not lettered at all."""
    card = hung_card(120, 90, 1.0, top=90.0)
    river = Label(
        name="Afon Nant Peris", kind="river", px=60.0, py=45.0, tier=TIER_RIVER, size=18.0
    )
    got, _hand = _set_flat(river, card, [])
    assert got == []
