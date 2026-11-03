"""Road and river strokes: a short piece with a loose end is a stub and is not drawn."""

from typing import Any

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.polyline import Pt
from pyntpot.maps.basemap_strokes import (
    STUB_FLOOR_PX,
    Frame,
    rivers_from_paths,
    roads_from_paths,
    stubs,
)
from pyntpot.maps.svg_path import path_d

#: Metres per display pixel of the test card.
MPP = 5.0
#: A piece this long is well under the stub floor, and well over any brush floor.
SHORT_M = STUB_FLOOR_PX * MPP / 2
FRAME = Frame(
    clip=(-2000.0, -2000.0, 2000.0, 2000.0),
    eps=1.0,
    geometry={"mpp_display": MPP, "wet_px": {"minor": 2.0, "medium": 4.0, "major": 6.0}},
    brush=BrushStyle(),
)
#: A long street, west to east along y = 0, and a second one along y = 2 * SHORT_M.
MAIN: list[Pt] = [(-1000.0, 0.0), (1000.0, 0.0)]
PARALLEL: list[Pt] = [(-1000.0, 2 * SHORT_M), (1000.0, 2 * SHORT_M)]
#: A short piece off the main street, ending on nothing.
SPUR: list[Pt] = [(0.0, 0.0), (0.0, SHORT_M)]
#: A short piece from the main street to the parallel one.
LINK: list[Pt] = [(300.0, 0.0), (300.0, 2 * SHORT_M)]


def _road(line: list[Pt], highway: str, name: str, cls: str = "minor") -> dict[str, Any]:
    """One road row as the vector map carries it."""
    return {"c": cls, "k": highway, "n": name, "r": "", "d": path_d(line)}


def _river(line: list[Pt], name: str, cls: str = "stream") -> dict[str, Any]:
    """One river row as the vector map carries it."""
    return {"c": cls, "n": name, "d": path_d(line)}


def _names(strokes) -> set[str]:
    """The names of the strokes drawn."""
    return {s.name for s in strokes}


class TestRoadStubs:
    """A short lane or path is drawn only where it joins two strokes."""

    def test_a_short_driveway_off_a_road_is_not_drawn(self) -> None:
        """A service way under the stub floor with one end on nothing is a hair off the road."""
        roads = roads_from_paths(
            [_road(MAIN, "residential", "Lake Road"), _road(SPUR, "service", "Driveway")],
            FRAME,
        )
        assert _names(roads) == {"Lake Road"}

    def test_a_short_link_between_two_roads_is_drawn(self) -> None:
        """A short lane with both ends on other roads is part of the network, not a stub."""
        rows = [
            _road(MAIN, "residential", "Lake Road"),
            _road(PARALLEL, "residential", "Compston Road"),
            _road(LINK, "residential", "Church Stile"),
        ]
        assert "Church Stile" in _names(roads_from_paths(rows, FRAME))

    def test_a_short_piece_of_a_major_road_is_drawn(self) -> None:
        """A major road is never cut for being short: a gap in it would show."""
        rows = [_road(SPUR, "primary", "Rydal Bridge", cls="major")]
        assert _names(roads_from_paths(rows, FRAME)) == {"Rydal Bridge"}

    def test_a_long_lane_with_a_loose_end_is_drawn(self) -> None:
        """A lane longer than the floor is a road however it ends."""
        lane = [(0.0, 0.0), (0.0, 3 * STUB_FLOOR_PX * MPP)]
        rows = [_road(MAIN, "residential", "Lake Road"), _road(lane, "track", "Loughrigg Terrace")]
        assert "Loughrigg Terrace" in _names(roads_from_paths(rows, FRAME))


class TestStreamStubs:
    """A short stream is drawn only where it runs from water to water."""

    def test_a_short_dash_of_stream_on_the_land_is_not_drawn(self) -> None:
        """A stream piece under the floor with one end on nothing is a dash that stops dead."""
        rivers = rivers_from_paths(
            [_river(MAIN, "River Rothay", cls="river"), _river(SPUR, "Rydal Beck")], [], FRAME
        )
        assert _names(rivers) == {"River Rothay"}

    def test_a_short_beck_from_a_river_to_a_lake_is_drawn(self) -> None:
        """A short stream ending on a lake shore at one end and a river at the other is kept."""
        lake = [(-200.0, SHORT_M), (200.0, SHORT_M), (200.0, 400.0), (-200.0, 400.0)]
        rivers = rivers_from_paths(
            [_river(MAIN, "River Rothay", cls="river"), _river(SPUR, "Rydal Beck")], [lake], FRAME
        )
        assert _names(rivers) == {"River Rothay", "Rydal Beck"}


def test_stubs_names_only_the_short_lines_with_a_loose_end() -> None:
    """Of a spur and a link, both short, only the spur is a stub; a long line never is."""
    lines = [MAIN, PARALLEL, SPUR, LINK]
    assert stubs(lines, [False, False, True, True], [], 1.0) == {2}
