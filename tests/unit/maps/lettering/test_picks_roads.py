"""Which named roads a card numbers: by number first, by name only where there is none."""

import pytest

from pyntpot.ink.polyline import length
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.lettering.picks_roads import pick_roads, road_min_px, road_ref

from support.basemaps import hung_card, label_basemap


def test_a_road_is_lettered_by_its_number_and_falls_back_to_its_name():
    """The rule: "A361" where OSM has a number, the name where it does not.

    A number places a climb for a rider reading the card. A name like "Aviemore
    Road" is longer, eats a corner and says nothing at 26 m a pixel.
    """
    numbered = [[round(float(x), 1), 0.0] for x in range(0, 4000, 25)]
    unnumbered = [[round(float(x), 1), -200.0] for x in range(0, 4000, 25)]
    lines = {
        "roads": [
            {"n": "Lyn Valley Road", "c": "major", "r": "A361", "d": numbered},
            {"n": "Aviemore Road", "c": "major", "r": "", "d": unnumbered},
        ]
    }

    # A tenth of a pixel a metre, the card's top edge 400 m north of the origin.
    card = hung_card(400, 300, 10.0, top=400.0)
    route = [(float(x), 45.0) for x in range(0, 400, 10)]
    got = pick_roads(label_basemap(), lines, card, route, budget=2)
    names = {label.name for label in got}
    assert "A361" in names, "the numbered road is lettered by its number"
    assert "Lyn Valley Road" not in names
    assert "Aviemore Road" in names, "an unnumbered road keeps its name"


def test_a_concurrent_road_number_is_written_once():
    """OSM joins two numbers on one carriageway; the card has room for one."""
    assert road_ref("A5;A470") == "A5"
    assert road_ref(" B4231 ") == "B4231"
    assert road_ref(None) == ""
    # A walking route's code is not a road number, and this box carries three.
    assert road_ref("EXE") == ""
    assert road_ref("CFG") == ""


def test_a_road_number_needs_a_run_of_road_measured_against_its_own_type():
    """How much road is enough is a question about the name, not about a card.

    It was a flat 110 display pixels, which is over three times the widest road
    number, and it was that only because the card it was tuned on carried a
    235 px run of the A3052.
    """
    assert road_min_px(28.0) == pytest.approx(2 * road_min_px(14.0))
    assert road_min_px(DEFAULT_LINE_PX * 0.7) < 110.0


def test_a_numbered_road_is_gathered_by_its_number_not_by_its_street_name():
    """A street name changes at every parish and the road does not.

    The A3052 crosses a card as Hollow Lane, Coastguard Road and New Road,
    none of them long enough to letter, so the card carried no road number at
    all while the same code could number another card twice.
    """

    def leg(x0, x1, y):
        return [[round(float(x), 1), float(y)] for x in range(x0, x1 + 1, 25)]

    lines = {
        "roads": [
            {"n": "Hollow Lane", "c": "major", "r": "A3052", "d": leg(0, 500, 0)},
            {"n": "Coastguard Road", "c": "major", "r": "A3052", "d": leg(500, 1000, 0)},
            {"n": "New Road", "c": "major", "r": "A3052", "d": leg(1000, 1500, 0)},
        ]
    }

    card = hung_card(400, 300, 10.0, top=400.0)

    route = [(float(x), 41.0) for x in range(0, 150, 5)]
    got = pick_roads(label_basemap(), lines, card, route, budget=2)
    assert [label.name for label in got] == ["A3052"]
    # No one leg is long enough on its own; the number is what gathers them.
    assert length(got[0].baseline) > road_min_px(got[0].size)
