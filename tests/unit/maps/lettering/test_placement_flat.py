"""Setting a name flat beside its anchor, broken over lines when that pays."""

import pytest

from pyntpot.maps.lettering.label import TIER_SPAN, WRAP_LEADING, Label, block_size
from pyntpot.maps.lettering.placement_costs import Terms
from pyntpot.maps.lettering.placement_flat import _place_flat
from pyntpot.maps.lettering.span_clear import seg_in_box

from support.lettering import flat_dark, map_card
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
