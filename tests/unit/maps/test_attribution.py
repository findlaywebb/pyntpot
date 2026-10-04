"""The attribution text is the credits' short lines, and `compose` writes it at the bottom right."""

import shutil
from typing import NamedTuple

import pytest
from PIL import Image, ImageChops

from pyntpot.maps import pipeline
from pyntpot.maps.attribution import attribution_text, draw_attribution
from pyntpot.maps.cache import Cache
from pyntpot.maps.credit import Credit
from pyntpot.maps.lettering.pipeline import letter
from pyntpot.maps.providers.opentopodata import OpenTopoData
from pyntpot.maps.providers.overpass import OverpassFeatures
from pyntpot.maps.style import Style
from pyntpot.maps.track import Track

from support.paths import FIXTURE_DIR, KEY
from support.providers import FixtureElevation, FixtureFeatures

PINNED_TEXT = "© OpenStreetMap contributors (openstreetmap.org/copyright) · elevation: NASA SRTM"

#: Where the attribution may change pixels: the bottom 5 percent of rows, right half of columns.
BOTTOM_FRACTION = 0.05
RIGHT_FRACTION = 0.5


class Composed(NamedTuple):
    """The fixture composed once without and once with the attribution."""

    plain: Image.Image
    drawn: Image.Image


@pytest.fixture(scope="module")
def composed(tmp_path_factory: pytest.TempPathFactory) -> Composed:
    """The fixture fetched, painted, lettered and composed both ways, once."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    style = Style.default()
    track = Track.from_gpx(work / "track.gpx")
    cache = Cache(work)
    basemap = pipeline.fetch(track, cache, FixtureFeatures(), FixtureElevation(), style)
    plates = pipeline.paint(basemap, style, cache.plates_dir(KEY))
    lettering = letter(plates, basemap, None, style)
    plain = pipeline.compose(plates, lettering, basemap, style, attribution=False)
    drawn = pipeline.compose(plates, lettering, basemap, style, attribution=True)
    return Composed(plain, drawn)


class TestText:
    """The line is the credits' short lines joined in the order given."""

    def test_shipped_credits(self) -> None:
        """The two shipped providers' credits give the pinned line, features first."""
        owed = (OverpassFeatures.credit, OpenTopoData.credit)
        assert attribution_text(owed) == PINNED_TEXT

    @pytest.mark.parametrize(
        ("shorts", "want"),
        [((), ""), (("a",), "a"), (("b", "a"), "b · a")],
        ids=["none", "one", "order-kept"],
    )
    def test_joined(self, shorts: tuple[str, ...], want: str) -> None:
        """The short lines are joined with a middle dot, in the order given."""
        owed = [Credit(text=s, url="https://example.org", short=s) for s in shorts]
        assert attribution_text(owed) == want


class TestEmpty:
    """An empty line draws nothing."""

    def test_empty_text_draws_nothing(self) -> None:
        """An empty line leaves a small image untouched."""
        image = Image.new("RGB", (64, 64), "white")
        draw_attribution(image, "", Style.default())
        assert ImageChops.difference(image, Image.new("RGB", (64, 64), "white")).getbbox() is None


@pytest.mark.golden
class TestDrawn:
    """The attribution changes the bottom right of the card and nothing else."""

    def test_only_the_corner_changes(self, composed: Composed) -> None:
        """With attribution on, the differing pixels all lie in the bottom-right strip."""
        box = ImageChops.difference(composed.plain, composed.drawn).getbbox()
        width, height = composed.plain.size
        assert box is not None
        assert box[0] >= width * RIGHT_FRACTION
        assert box[1] >= height * (1 - BOTTOM_FRACTION)
