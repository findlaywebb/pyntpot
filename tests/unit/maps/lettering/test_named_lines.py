"""What `named_lines` files: road and river entries, numbered pieces, crossings and tolerance."""

import pytest

from pyntpot.maps.basemap import Basemap, River, Road
from pyntpot.maps.lettering.picks_lines import named_lines

from support.basemaps import flags_off_style, tiny_basemap


def _road(name: str, ref: str, line: tuple[tuple[float, float], ...]) -> Road:
    """A major trunk road along `line`, in card metres."""
    return Road(line=line, cls="major", band="major", highway="trunk", name=name, ref=ref)


def _basemap(*roads: Road, rivers: tuple[River, ...] = ()) -> Basemap:
    """A 320 px card, at 9.8 m a display pixel, carrying `roads` and `rivers`."""
    return tiny_basemap(flags_off_style(display_px=320, supersample=1), roads=roads, rivers=rivers)


class TestNamedLines:
    """What `named_lines` files for the roads and rivers a name can be set along."""

    def test_a_numbered_piece_is_filed_as_a_road_entry_with_no_name(self) -> None:
        """An unnamed numbered piece is a whole road entry, its name empty, under `numbered`."""
        a9 = _road("", "A9", ((-500.0, 800.0), (650.0, 800.0), (1800.0, 800.0)))
        assert named_lines(_basemap(a9), 2.0)["numbered"] == [
            {
                "n": "",
                "c": "major",
                "r": "A9",
                "w": 0.0,
                "wn": 0.0,
                "d": [[-500.0, 800.0], [1800.0, 800.0]],
            }
        ]

    def test_an_unnamed_road_with_no_number_is_only_a_crossing(self) -> None:
        """A road with neither name nor number is kept for the crossing cost and nowhere else."""
        lines = named_lines(_basemap(_road("", "", ((0.0, 0.0), (1360.0, 0.0)))), 2.0)
        assert lines["numbered"] == []
        assert lines["crossings"] == [[[0.0, 0.0], [1360.0, 0.0]]]

    def test_a_river_entry_carries_no_road_number(self) -> None:
        """A named river is filed with an empty `r`, whatever its class."""
        lyn = River(
            line=((0.0, 0.0), (1360.0, 0.0)),
            cls="major",
            name="East Lyn River",
            width_px=3.0,
            name_width_px=4.0,
        )
        lines = named_lines(_basemap(rivers=(lyn,)), 2.0)
        assert [(entry["n"], entry["r"]) for entry in lines["rivers"]] == [("East Lyn River", "")]

    @pytest.mark.parametrize(
        ("tol_px", "kink_m", "kept"),
        [(0.5, 3.0, 2), (0.0, 1.5, 3)],
        ids=["display-pixels-at-scale", "a-metre-floor"],
    )
    def test_the_tolerance_is_display_pixels_at_scale_and_at_least_a_metre(
        self, tol_px: float, kink_m: float, kept: int
    ) -> None:
        """Half a display pixel at 9.8 m a pixel drops a 3 m kink; no tolerance still drops under 1 m."""
        bent = _road("Rydal Road", "A591", ((0.0, 0.0), (680.0, kink_m), (1360.0, 0.0)))
        assert len(named_lines(_basemap(bent), tol_px)["roads"][0]["d"]) == kept
