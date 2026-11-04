"""`_ground`: the caller's named roads replace the picked ones, and stand alone without the ground."""

import dataclasses

import pytest

from pyntpot.maps.annotations import Annotations
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.lettering.picks_lines import NamedLines
from pyntpot.maps.lettering.pipeline import _ground
from pyntpot.maps.style import Style

from support.basemaps import class_style, tiny_basemap


def _leg(x0: int, x1: int, northing: float) -> list[list[float]]:
    """A straight east-west run of road at `northing`, in card metres, a point every 25 m."""
    return [[round(float(x), 1), northing] for x in range(x0, x1 + 1, 25)]


#: The A591 as Rydal Road, along the route at northing 0 (beside it on the card).
RYDAL = {"n": "Rydal Road", "c": "major", "r": "A591", "w": 0.0, "wn": 0.0, "d": _leg(0, 1350, 0.0)}

#: The A66 as Penrith Road, 800 m north of the route (about 80 px off it on the card).
PENRITH = {
    "n": "Penrith Road",
    "c": "major",
    "r": "A66",
    "w": 0.0,
    "wn": 0.0,
    "d": _leg(-500, 1800, 800.0),
}

#: The A82 as Glencoe Road, 300 m long: shorter on the card than its number needs.
GLENCOE = {
    "n": "Glencoe Road",
    "c": "major",
    "r": "A82",
    "w": 0.0,
    "wn": 0.0,
    "d": _leg(0, 300, -600.0),
}

#: What `_ground` gives for these lines when the caller names no road.
TODAYS_GROUND = ["A591", "start", "finish"]


def _lines() -> NamedLines:
    """Named lines carrying the A591, the A66 and the A82 as named roads."""
    return {
        "roads": [RYDAL, PENRITH, GLENCOE],
        "rivers": [],
        "coast": [],
        "crossings": [],
        "numbered": [],
    }


@pytest.fixture(scope="module")
def basemap() -> Basemap:
    """A 320 px card with nothing on it but the route, long enough to letter a road on."""
    return tiny_basemap(class_style(display_px=320, supersample=1))


def _strands(basemap: Basemap) -> list[tuple[float, float]]:
    """The basemap's route in display pixels."""
    return [basemap.card.xy(x, y) for x, y in basemap.layers.route]


def _no_ground(style: Style) -> Style:
    """The style with the ground left unlettered."""
    lettering = dataclasses.replace(style.lettering, label_ground=False)
    return style.model_copy(update={"lettering": lettering})


def _style() -> Style:
    """The style the basemap was built in."""
    return class_style(display_px=320, supersample=1)


class TestGround:
    """`_ground` letters the caller's named roads in place of the picked ones."""

    def test_without_named_roads_the_ground_is_todays(self, basemap: Basemap) -> None:
        """No annotations and empty annotations both give the ground with the picked A591."""
        strands = _strands(basemap)
        none = _ground(basemap, _lines(), strands, None, _style())
        empty = _ground(basemap, _lines(), strands, Annotations(), _style())
        assert [label.name for label in none] == TODAYS_GROUND
        assert [label.name for label in empty] == TODAYS_GROUND

    def test_named_roads_replace_the_picked_ones(self, basemap: Basemap) -> None:
        """Naming the A66, far from the route, letters it and drops the picked A591."""
        got = _ground(basemap, _lines(), _strands(basemap), Annotations(roads=("A66",)), _style())
        assert [label.name for label in got if label.kind == "road"] == ["A66"]

    def test_named_roads_are_all_there_is_when_the_style_letters_no_ground(
        self, basemap: Basemap
    ) -> None:
        """With the ground unlettered, the named roads alone come back, and nothing without them."""
        style = _no_ground(_style())
        strands = _strands(basemap)
        named = _ground(basemap, _lines(), strands, Annotations(roads=("A66",)), style)
        unnamed = _ground(basemap, _lines(), strands, Annotations(), style)
        assert [label.name for label in named] == ["A66"]
        assert unnamed == []

    def test_named_roads_too_short_bring_back_the_picked_ones(self, basemap: Basemap) -> None:
        """When every named road is too short to letter, the picked roads come back."""
        got = _ground(basemap, _lines(), _strands(basemap), Annotations(roads=("A82",)), _style())
        assert [label.name for label in got if label.kind == "road"] == ["A591"]

    def test_an_unmatched_named_road_raises(self, basemap: Basemap) -> None:
        """A named road that the lines do not carry raises, naming it."""
        with pytest.raises(ValueError, match="'A9'"):
            _ground(basemap, _lines(), _strands(basemap), Annotations(roads=("A9",)), _style())
