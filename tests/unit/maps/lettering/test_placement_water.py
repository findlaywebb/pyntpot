"""Keeping a name and its backing wash off the water: the lakes and the watercourses' strokes."""

import math

import pytest

from pyntpot.maps.lettering.label import TIER_LANDMARK, TIER_RIVER, Label
from pyntpot.maps.lettering.placement import place
from pyntpot.maps.lettering.placement_along import ink_band
from pyntpot.maps.lettering.placement_costs import Backdrop
from pyntpot.maps.lettering.placement_leaders import uncross_leaders
from pyntpot.maps.lettering.placement_water import (
    WASH_REACH_EM,
    Water,
    ink_on_water,
    on_water,
    water_cost,
)

from support.lettering import flat_dark, map_card
from support.measure import flat_measure

#: A square lake east of the middle of the small card, 100 by 100 display pixels.
LAKE = [(210.0, 100.0), (310.0, 100.0), (310.0, 200.0), (210.0, 200.0)]

#: An island in the middle of it.
ISLAND = [(240.0, 130.0), (280.0, 130.0), (280.0, 170.0), (240.0, 170.0)]

#: The route, along the bottom of the card where it decides nothing.
ROUTE = [(0.0, 295.0), (400.0, 295.0)]


class TestOnWater:
    """The share of a box, grown by its backing wash's reach, that lies on water."""

    def test_a_box_on_dry_paper_is_not_on_water(self) -> None:
        """A box well clear of the lake and of every stroke is priced nothing."""
        water = Water([LAKE], [([(20.0, 20.0), (20.0, 80.0)], 3.0)])
        assert on_water((60.0, 220.0, 120.0, 240.0), water, 14.0) == 0.0

    def test_a_box_in_the_middle_of_a_lake_is_wholly_on_water(self) -> None:
        """A box whose wash stays inside the lake is all water."""
        assert on_water((215.0, 105.0, 225.0, 115.0), Water([LAKE]), 2.0) == 1.0

    def test_an_island_is_dry(self) -> None:
        """A box on an island inside the lake, ring inside ring, is on dry land."""
        assert on_water((250.0, 145.0, 270.0, 155.0), Water([LAKE, ISLAND]), 2.0) == 0.0

    def test_a_watercourse_stroke_under_a_box_is_water(self) -> None:
        """A stream drawn through the middle of a box puts part of it on water."""
        stream = ([(100.0, 0.0), (100.0, 300.0)], 4.0)
        share = on_water((60.0, 140.0, 140.0, 160.0), Water([], [stream]), 2.0)
        assert 0.0 < share < 0.5

    def test_the_backing_wash_reaching_a_lake_counts(self) -> None:
        """A box just short of the lake still pays, because its wash lands on the water."""
        size = 14.0
        gap = size * WASH_REACH_EM / 2
        box = (150.0, 140.0, 210.0 - gap, 160.0)
        assert on_water(box, Water([LAKE]), size) > 0.0
        assert on_water(box, Water([LAKE]), 0.0) == 0.0


def _placed(name: Label, water: Water) -> Label:
    """One name placed alone on the small card against the given water."""
    place(
        [name],
        [],
        Backdrop(map_card(), ROUTE, flat_dark(), [], water),
        [],
        flat_measure,
        measure_tracked=lambda text, size, tracking: flat_measure(text, size),
    )
    return name


def test_a_landmark_beside_a_lake_is_seated_on_the_dry_side():
    """Llyn Llydaw's name, anchored on its shore, is lettered off the water with its wash."""
    lake = Label(name="Llyn Llydaw", kind="", px=205.0, py=150.0, tier=TIER_LANDMARK, size=14.0)
    _placed(lake, Water([LAKE]))
    assert lake.box is not None
    assert on_water(lake.box, Water([LAKE]), lake.size) == 0.0


#: A broad lake across the middle of the small card, with a dry shore along its south side.
BROAD_LAKE = [(60.0, 60.0), (340.0, 60.0), (340.0, 200.0), (60.0, 200.0)]


def test_a_land_callout_whose_cheapest_seat_is_on_a_lake_is_lettered_off_it():
    """A callout for a cave on a lake's shore, cheapest seated on the lake, is lettered on dry land."""

    def cave() -> Label:
        """Rydal Cave, a curated callout anchored on the dry shore just south of the lake."""
        return Label(name="Rydal Cave", kind="", px=200.0, py=205.0, tier=TIER_LANDMARK, size=14.0)

    unpriced = _placed(cave(), Water())
    assert unpriced.box is not None
    assert on_water(unpriced.box, Water([BROAD_LAKE]), 0.0) == 1.0, "the case needs a wet seat"
    priced = _placed(cave(), Water([BROAD_LAKE]))
    assert priced.box is not None
    assert on_water(priced.box, Water([BROAD_LAKE]), 0.0) == 0.0


def test_a_river_name_set_flat_keeps_off_its_own_stroke():
    """A river with no reach to write along is lettered beside its own water, not across it."""
    # A stream that zigzags down the card every 15 pixels: no reach of it is straight
    # enough to write along, so the name is set flat.
    stream = [(200.0 + (12.0 if i % 2 else -12.0), 30.0 + i * 15.0) for i in range(17)]
    water = Water([], [(stream, 3.0)])
    river = Label(name="Afon Arddu", kind="river", px=200.0, py=150.0, tier=TIER_RIVER, size=14.0)
    river.baseline = stream
    _placed(river, water)
    assert river.flat, "the bent stream offers no reach to write along"
    assert river.box is not None
    # The letters clear the stroke; the edge of the backing wash may graze it.
    assert on_water(river.box, water, 0.0) == 0.0
    assert on_water(river.box, water, river.size) < 0.1


def test_a_flat_river_name_slides_along_its_course_to_dry_paper():
    """A river whose anchor lies in a lake is lettered further along its own course, off the water."""
    stream = [(200.0 + (12.0 if i % 2 else -12.0), 30.0 + i * 15.0) for i in range(17)]
    mere = [(40.0, 80.0), (360.0, 80.0), (360.0, 220.0), (40.0, 220.0)]
    water = Water([mere], [(stream, 3.0)])
    river = Label(name="Afon Arddu", kind="river", px=200.0, py=150.0, tier=TIER_RIVER, size=14.0)
    river.baseline = stream
    _placed(river, water)
    assert river.flat
    assert river.box is not None
    assert on_water(river.box, water, 0.0) == 0.0
    assert on_water(river.box, water, river.size) < 0.1


def test_a_swap_that_would_put_a_name_on_a_lake_is_refused():
    """Two crossing leaders are not uncrossed by moving a wide name onto the water."""
    a = Label(name="Glaslyn", kind="", px=100.0, py=100.0, tier=TIER_LANDMARK, size=14.0)
    b = Label(name="Crib Goch", kind="", px=100.0, py=200.0, tier=TIER_LANDMARK, size=14.0)
    # Glaslyn's narrow block fits on the dry shore beside a mere; Crib Goch's wide one,
    # swapped onto the same seat, would reach the water.
    for label, (cx, cy), half in ((a, (330.0, 260.0), 20.0), (b, (330.0, 40.0), 60.0)):
        label.box = (cx - half, cy - 10.0, cx + half, cy + 10.0)
        label.flat = True
        label.leader = ((label.px, label.py), (cx, cy))
    mere = [(365.0, 230.0), (390.0, 230.0), (390.0, 290.0), (365.0, 290.0)]
    seats = (a.box, b.box)
    uncross_leaders([a, b], Backdrop(map_card(), ROUTE, flat_dark(), [], Water([mere])))
    assert (a.box, b.box) == seats


#: A rounder mere, a stream that zigzags down the card and a beck across its top, with the
#: square lake and its island: water enough to cut every kind of box against.
MERE = [(60.0 + 40.0 * math.cos(k / 9.0), 230.0 + 25.0 * math.sin(k / 9.0)) for k in range(57)]
STREAM = [(200.0 + (12.0 if i % 2 else -12.0), 30.0 + i * 15.0) for i in range(17)]
BECK = [(20.0 + i * 7.0, 60.0 + 9.0 * math.sin(i / 3.0)) for i in range(50)]

#: Each box, its share of water with the wash at 14 px type, without it, and its water cost:
#: pinned from the point-by-point implementation the array one replaced.
PINNED_SHARES = (
    ((60.0, 220.0, 120.0, 240.0), 0.5454545454545454, 0.625, 421.8181818181818),
    ((215.0, 105.0, 225.0, 115.0), 0.6790123456790124, 1.0, 485.9259259259259),
    ((250.0, 145.0, 270.0, 155.0), 0.16666666666666666, 0.0, 80.0),
    ((150.0, 140.0, 205.0, 160.0), 0.225, 0.15555555555555556, 268.0),
    ((207.0, 123.0, 295.0, 143.0), 0.7155172413793104, 0.6884057971014492, 503.448275862069),
    ((30.0, 50.0, 140.0, 72.0), 0.11029411764705882, 0.19704433497536947, 212.94117647058823),
    ((180.0, 40.0, 260.0, 62.0), 0.2037037037037037, 0.2585034013605442, 257.77777777777777),
    ((40.0, 215.0, 130.0, 245.0), 0.4630541871921182, 0.6296296296296297, 382.2660098522167),
    ((300.0, 190.0, 380.0, 212.0), 0.1111111111111111, 0.061224489795918366, 121.9047619047619),
    ((100.0, 100.0, 180.0, 122.0), 0.021604938271604937, 0.0, 10.37037037037037),
)


@pytest.mark.parametrize(
    ("box", "washed", "bare", "cost"), PINNED_SHARES, ids=[f"box{i}" for i in range(10)]
)
def test_the_water_share_is_the_one_pinned(
    box: tuple[float, float, float, float], washed: float, bare: float, cost: float
) -> None:
    """Every share and cost is exactly what the point-by-point pricing gave."""
    water = Water([LAKE, ISLAND, MERE], [(STREAM, 3.0), (BECK, 2.5)])
    assert on_water(box, water, 14.0) == washed
    assert on_water(box, water, 0.0) == bare
    assert water_cost(box, water, 14.0) == cost


class TestInkOnWater:
    """The share of the points over a name's ink that lie on water."""

    def test_points_under_a_stroke_are_on_water(self) -> None:
        """Half the points on a stream's stroke, half on the paper beside it."""
        water = Water([], [([(100.0, 0.0), (100.0, 300.0)], 4.0)])
        points = [(99.0, 150.0), (102.0, 160.0), (120.0, 150.0), (140.0, 160.0)]
        assert ink_on_water(points, water) == 0.5

    def test_points_on_an_island_are_dry(self) -> None:
        """A point in the lake is on water; one on its island is not."""
        water = Water([LAKE, ISLAND])
        assert ink_on_water([(220.0, 110.0), (260.0, 150.0)], water) == 0.5

    def test_no_points_and_no_water_price_nothing(self) -> None:
        """An empty band, or a card with no water, is dry."""
        assert ink_on_water([], Water([LAKE])) == 0.0
        assert ink_on_water([(220.0, 110.0)], Water()) == 0.0


def test_a_river_name_set_along_its_water_keeps_its_letters_off_a_second_channel():
    """The Cherwell runs in two channels: its name is set beside one, clear of the other."""
    channel = [(float(x), 150.0) for x in range(20, 381, 10)]
    # The second channel runs beside the first, close enough that a name lifted off the
    # first to that side is written across it.
    other = [(float(x), 128.0) for x in range(20, 381, 10)]
    water = Water([], [(channel, 3.0), (other, 3.0)])
    river = Label(name="Cherwell", kind="river", px=200.0, py=150.0, tier=TIER_RIVER, size=14.0)
    river.baseline = channel
    river.feature_px = 6.0
    _placed(river, water)
    assert not river.flat, "the straight channel was not written along"
    assert ink_on_water(ink_band(river, river.window, river.lift), water) == 0.0
