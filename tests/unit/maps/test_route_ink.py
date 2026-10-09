"""A fed route ink reaches the strands and the card, and repaints nothing."""

import shutil
from typing import NamedTuple

import numpy as np
import pytest
from PIL import Image

from pyntpot.maps import Basemap, Cache, Lettering, Plates, Style, Track, compose, fetch, paint

from support.paths import FIXTURE_DIR, KEY
from support.providers import FixtureElevation, FixtureFeatures

#: A blue, fed in place of the theme's red route colour.
FED_COLOUR = "#2050c2"

#: A width fed in place of the theme's route width, in display pixels.
FED_WIDTH_PX = 4.8

#: A thin and a wide fed width, in display pixels, both drawn in the fed colour.
THIN_WIDTH_PX = 2.0
WIDE_WIDTH_PX = 12.0

#: No labels, no spans and no label plate, so the route is the top mark on the card.
UNLETTERED = Lettering((), (), None)


class Painted(NamedTuple):
    """The fixture fetched and painted once, in the default style."""

    basemap: Basemap
    plates: Plates
    style: Style


@pytest.fixture(scope="module")
def painted(tmp_path_factory: pytest.TempPathFactory) -> Painted:
    """The fixture fetched and painted once over a copy of the fixture directory."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    style = Style.default()
    track = Track.from_gpx(work / "track.gpx")
    cache = Cache(work)
    basemap = fetch(track, cache, FixtureFeatures(), FixtureElevation(), style)
    plates = paint(basemap, style, cache.plates_dir(KEY))
    return Painted(basemap, plates, style)


def _middle_route_pixel(card: Image.Image, plates: Plates) -> tuple[int, int, int]:
    """The card's colour under the middle strand point, scaled to the card as `compose` scales it."""
    x, y = plates.strands[len(plates.strands) // 2]
    k = card.width / max(plates.card.display[0], 1)
    rgb = np.asarray(card.convert("RGB"))
    red, green, blue = (int(channel) for channel in rgb[round(y * k), round(x * k)])
    return red, green, blue


def _fed_coloured_pixels(card: Image.Image) -> int:
    """How many of the card's pixels are bluer than red by a clear margin, as the fed colour is."""
    rgb = np.asarray(card.convert("RGB")).astype(int)
    return int(np.count_nonzero(rgb[..., 2] - rgb[..., 0] > 64))


@pytest.mark.golden
class TestFedRouteInk:
    """The fed colour draws the card's route and the fed width spaces its strands."""

    def test_the_card_draws_the_route_in_the_fed_colour(self, painted: Painted) -> None:
        """The fed card's route is bluer than red where the default card's is redder than blue."""
        fed_style = painted.style.with_route_ink(colour=FED_COLOUR)
        default = compose(
            painted.plates, UNLETTERED, painted.basemap, painted.style, attribution=False
        )
        fed = compose(painted.plates, UNLETTERED, painted.basemap, fed_style, attribution=False)
        default_red, _, default_blue = _middle_route_pixel(default, painted.plates)
        fed_red, _, fed_blue = _middle_route_pixel(fed, painted.plates)
        assert default_red > default_blue
        assert fed_blue > fed_red

    def test_a_fed_width_respaces_the_strands_without_repainting(self, painted: Painted) -> None:
        """A fed width keeps the plates and their hash and moves only the doubled-back points."""
        before = {name: path.stat().st_mtime_ns for name, path in painted.plates.paths.items()}
        fed_style = painted.style.with_route_ink(width_px=FED_WIDTH_PX)
        fed = paint(painted.basemap, fed_style, painted.plates.directory)
        after = {name: path.stat().st_mtime_ns for name, path in fed.paths.items()}
        assert fed.hash == painted.plates.hash
        assert after == before
        assert fed.route_px == painted.plates.route_px
        assert len(fed.strands) == len(painted.plates.strands)
        moved = [
            i
            for i, (fed_point, default_point) in enumerate(
                zip(fed.strands, painted.plates.strands, strict=True)
            )
            if fed_point != default_point
        ]
        doubled = {
            i
            for i, (strand_point, route_point) in enumerate(
                zip(painted.plates.strands, painted.plates.route_px, strict=True)
            )
            if strand_point != route_point
        }
        assert moved
        assert set(moved) <= doubled

    def test_a_fed_width_draws_a_wider_line_for_a_non_pen_ink(self, painted: Painted) -> None:
        """For an ink that is not the pen, a wider fed width covers more of the card in its colour."""
        assert painted.style.route_ink().style != "pen"
        thin_style = painted.style.with_route_ink(colour=FED_COLOUR, width_px=THIN_WIDTH_PX)
        wide_style = painted.style.with_route_ink(colour=FED_COLOUR, width_px=WIDE_WIDTH_PX)
        thin = compose(painted.plates, UNLETTERED, painted.basemap, thin_style, attribution=False)
        wide = compose(painted.plates, UNLETTERED, painted.basemap, wide_style, attribution=False)
        thin_count = _fed_coloured_pixels(thin)
        assert thin_count > 0
        assert _fed_coloured_pixels(wide) > 2 * thin_count
