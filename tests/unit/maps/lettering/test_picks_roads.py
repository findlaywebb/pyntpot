"""Which named roads a card numbers: by number first, by name only where there is none."""

import logging
from typing import Any

import pytest

from pyntpot.ink.polyline import length
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.basemap import Basemap, Road
from pyntpot.maps.lettering.picks_lines import NamedLines, named_lines
from pyntpot.maps.lettering.picks_roads import named_roads, pick_roads, road_min_px, road_ref

from support.basemaps import class_style, hung_card, label_basemap, tiny_basemap


def test_a_road_is_lettered_by_its_number_and_falls_back_to_its_name():
    """The rule: "A361" where OSM has a number, the name where it does not.

    A number places a climb for someone reading the card. A name like "Aviemore
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


def test_a_road_label_says_the_track_was_on_it():
    """A lettered road gives its reason in track words, with no sport word."""
    numbered = [[round(float(x), 1), 0.0] for x in range(0, 4000, 25)]
    lines = {"roads": [{"n": "Lyn Valley Road", "c": "major", "r": "A361", "d": numbered}]}
    card = hung_card(400, 300, 10.0, top=400.0)
    route = [(float(x), 45.0) for x in range(0, 400, 10)]
    got = pick_roads(label_basemap(), lines, card, route, budget=2)
    assert [(label.name, label.why) for label in got] == [("A361", "road the track was on")]


def _leg(x0: int, x1: int, northing: float) -> list[list[float]]:
    """A straight east-west run of road at `northing`, in card metres, a point every 25 m."""
    return [[round(float(x), 1), northing] for x in range(x0, x1 + 1, 25)]


def _road(
    name: str, ref: str, northing: float, cls: str = "major", x1: int = 3000
) -> dict[str, Any]:
    """One road entry as `named_lines` files it, running east from the card's west edge."""
    return {"n": name, "c": cls, "r": ref, "w": 0.0, "wn": 0.0, "d": _leg(0, x1, northing)}


def _lines(*roads: dict[str, Any], numbered: tuple[dict[str, Any], ...] = ()) -> NamedLines:
    """Named lines carrying `roads` under `roads` and `numbered` under `numbered`."""
    return {
        "roads": list(roads),
        "rivers": [],
        "coast": [],
        "crossings": [],
        "numbered": list(numbered),
    }


#: A tenth of a pixel a metre, the card's top edge 400 m north of the origin.
CARD = hung_card(400, 300, 10.0, top=400.0)

#: A track 45 px down the card, beside a road at northing 0 (40 px down).
ROUTE = [(float(x), 45.0) for x in range(0, 400, 10)]


class TestNamedRoads:
    """`named_roads` letters the roads the caller names, whatever their class and wherever they run."""

    def test_a_named_road_is_lettered_though_the_track_was_never_on_it(self) -> None:
        """A road 200 px off any track is lettered when named; `named_roads` takes no route."""
        lines = _lines(_road("Penrith Road", "A66", -2000.0))
        got = named_roads(label_basemap(), lines, CARD, ("A66",))
        assert [(label.name, label.kind, label.why) for label in got] == [
            ("A66", "road", "road the caller named")
        ]
        assert got[0].py == pytest.approx(240.0)

    def test_a_named_minor_road_is_lettered(self) -> None:
        """A named minor road is lettered by name, where the picker skips it for its class alone."""
        lines = _lines(_road("Old Lake Road", "", 0.0, cls="minor"))
        got = named_roads(label_basemap(), lines, CARD, ("Old Lake Road",))
        assert [label.name for label in got] == ["Old Lake Road"]
        assert length(got[0].baseline) > road_min_px(got[0].size)
        assert pick_roads(label_basemap(), lines, CARD, ROUTE) == []

    def test_a_road_is_matched_by_number_ignoring_case(self) -> None:
        """A number written in lower case matches the road's `ref`."""
        lines = _lines(_road("Rydal Road", "A591", 0.0))
        got = named_roads(label_basemap(), lines, CARD, ("a591",))
        assert [label.name for label in got] == ["A591"]

    def test_a_road_matched_by_its_name_is_lettered_by_its_number(self) -> None:
        """A road named by its street is lettered by the number it carries."""
        lines = _lines(_road("Rydal Road", "A591", 0.0))
        got = named_roads(label_basemap(), lines, CARD, ("rydal road",))
        assert [label.name for label in got] == ["A591"]

    def test_a_road_named_twice_is_lettered_once_at_its_first_place(self) -> None:
        """A road matched by number and again by street name is lettered once, where first named."""
        lines = _lines(_road("Rydal Road", "A591", 0.0), _road("Penrith Road", "A66", -1000.0))
        got = named_roads(label_basemap(), lines, CARD, ("A591", "A66", "Rydal Road"))
        assert [label.name for label in got] == ["A591", "A66"]

    def test_named_roads_come_in_the_callers_order(self) -> None:
        """The labels follow the order the caller listed the roads in, not the lines' order."""
        lines = _lines(_road("Rydal Road", "A591", 0.0), _road("Penrith Road", "A66", -1000.0))
        got = named_roads(label_basemap(), lines, CARD, ("A66", "A591"))
        assert [label.name for label in got] == ["A66", "A591"]

    def test_named_roads_are_not_held_to_the_budget(self) -> None:
        """Three named roads are all lettered, past the picker's budget of two."""
        lines = _lines(
            _road("Rydal Road", "A591", 0.0),
            _road("Penrith Road", "A66", -1000.0),
            _road("Glencoe Road", "A82", -2000.0),
        )
        got = named_roads(label_basemap(), lines, CARD, ("A591", "A66", "A82"))
        assert [label.name for label in got] == ["A591", "A66", "A82"]

    def test_a_named_road_too_short_for_its_number_is_skipped_and_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A named road shorter than its number needs is left out and logged at INFO, not raised."""
        caplog.set_level(logging.INFO, logger="pyntpot.maps.lettering.picks_roads")
        lines = _lines(_road("Rydal Road", "A591", 0.0, x1=500))
        got = named_roads(label_basemap(), lines, CARD, ("A591",))
        assert got == []
        assert "A591" in caplog.text

    def test_an_unmatched_name_raises_naming_it(self) -> None:
        """Names that match no drawn road raise, every one named in the listed order."""
        lines = _lines(_road("Rydal Road", "A591", 0.0))
        with pytest.raises(ValueError, match="'A9', 'B4521'"):
            named_roads(label_basemap(), lines, CARD, ("A591", "A9", "B4521"))

    def test_a_numbered_road_with_no_name_is_matched(self) -> None:
        """A road with a number and no name is filed under `numbered` and lettered by it."""
        basemap = _numbered_basemap()
        lines = named_lines(basemap, 2.0)
        assert [entry["r"] for entry in lines["numbered"]] == ["A9"]
        assert [entry["r"] for entry in lines["roads"]] == ["A591"]
        got = named_roads(basemap, lines, basemap.card, ("A9",))
        assert [label.name for label in got] == ["A9"]

    def test_the_numbered_lines_change_nothing_the_picker_reads(self) -> None:
        """The roads, rivers, coast and crossings are what they were before `numbered` existed."""
        lines = named_lines(_numbered_basemap(), 2.0)
        assert lines["roads"] == [
            {
                "n": "Rydal Road",
                "c": "major",
                "r": "A591",
                "w": 0.0,
                "wn": 0.0,
                "d": [[0.0, 0.0], [1360.0, 0.0]],
            }
        ]
        assert lines["rivers"] == []
        assert lines["coast"] == []
        assert lines["crossings"] == [[[-500.0, 800.0], [1800.0, 800.0]]]


def _numbered_basemap() -> Basemap:
    """A 320 px card carrying the A591 as Rydal Road and an A9 piece with no name."""
    rydal = Road(
        line=((0.0, 0.0), (680.0, 0.0), (1360.0, 0.0)),
        cls="major",
        band="major",
        highway="trunk",
        name="Rydal Road",
        ref="A591",
    )
    unnamed = Road(
        line=((-500.0, 800.0), (650.0, 800.0), (1800.0, 800.0)),
        cls="major",
        band="major",
        highway="trunk",
        name="",
        ref="A9",
    )
    return tiny_basemap(class_style(display_px=320, supersample=1), roads=(rydal, unnamed))
