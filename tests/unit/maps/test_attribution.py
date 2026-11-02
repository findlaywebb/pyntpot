"""The attribution text is the credits' short lines, and `compose` writes it at the bottom right."""

import dataclasses
import shutil
from typing import NamedTuple

import pytest
from PIL import Image, ImageChops

from pyntpot.maps import pipeline
from pyntpot.maps.attribution import (
    ATTRIBUTION_MIN_SIZE_PX,
    ATTRIBUTION_WIDE_FRACTION,
    attribution_size,
    attribution_text,
    draw_attribution,
    plate_scale,
)
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

#: Where the attribution may change pixels: the bottom 8 percent of rows and the columns right of
#: the share the widest line (`ATTRIBUTION_WIDE_FRACTION` of the card) and its padding leave.
BOTTOM_FRACTION = 0.08
RIGHT_FRACTION = 1 - ATTRIBUTION_WIDE_FRACTION - 0.05


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


class TestLabelsOff:
    """The labels switch letters the map; it does not gate the attribution."""

    def test_written_when_the_map_is_not_lettered(self) -> None:
        """A style that letters no names still writes the attribution it is asked for."""
        style = Style.default()
        style = style.model_copy(
            update={"lettering": dataclasses.replace(style.lettering, labels=False)}
        )
        image = Image.new("RGB", (600, 80), "white")
        draw_attribution(image, PINNED_TEXT, style)
        assert (
            ImageChops.difference(image, Image.new("RGB", (600, 80), "white")).getbbox() is not None
        )


def _ink_box(display_width: int, text: str, scale: int = 2) -> tuple[int, int, int, int]:
    """Draw `text` on a blank card of this display width at `scale`; return the ink's box."""
    blank = Image.new("RGB", (display_width * scale, 300 * scale), "white")
    image = blank.copy()
    draw_attribution(image, text, Style.default(), float(scale))
    box = ImageChops.difference(image, blank).getbbox()
    assert box is not None
    return box


class TestReadable:
    """The credit is sized in display pixels, so it is legible once the card is shrunk."""

    @pytest.mark.parametrize("width", [720, 1200], ids=["720", "1200"])
    def test_block_height_meets_the_floor(self, width: int) -> None:
        """The inked block is at least the floor tall in display pixels, 720 and 1200 wide."""
        _x0, y0, _x1, y1 = _ink_box(width, PINNED_TEXT)
        assert (y1 - y0) / 2 >= ATTRIBUTION_MIN_SIZE_PX

    @pytest.mark.parametrize(
        ("width", "want"),
        [(300, 12.0), (720, 13.0), (1200, 13.0 * 1200 / 720)],
        ids=["floor", "reference", "scaled"],
    )
    def test_size_follows_the_display_width(self, width: int, want: float) -> None:
        """The type size is 13 at 720, grows with the width and never drops under 12."""
        assert attribution_size(width) == pytest.approx(want)

    def test_long_credit_on_a_narrow_card_wraps_at_the_separator(self) -> None:
        """A credit wider than the share of a narrow card breaks into two lines, taller than one."""
        narrow = _ink_box(480, PINNED_TEXT)
        one = _ink_box(480, "© OpenStreetMap contributors")
        assert (narrow[3] - narrow[1]) > 1.5 * (one[3] - one[1])
        assert narrow[2] - narrow[0] <= 480 * 2 * ATTRIBUTION_WIDE_FRACTION

    def test_same_text_and_style_write_the_same_pixels(self) -> None:
        """Drawing twice gives byte-identical pixels."""
        a = Image.new("RGB", (1440, 600), "white")
        b = a.copy()
        draw_attribution(a, PINNED_TEXT, Style.default(), 2.0)
        draw_attribution(b, PINNED_TEXT, Style.default(), 2.0)
        assert a.tobytes() == b.tobytes()


@pytest.mark.golden
@pytest.mark.xdist_group("test_attribution")
class TestDrawn:
    """The attribution changes the bottom right of the card and nothing else."""

    def test_only_the_corner_changes(self, composed: Composed) -> None:
        """With attribution on, the differing pixels all lie in the bottom-right strip."""
        box = ImageChops.difference(composed.plain, composed.drawn).getbbox()
        width, height = composed.plain.size
        assert box is not None
        assert box[0] >= width * RIGHT_FRACTION
        assert box[1] >= height * (1 - BOTTOM_FRACTION)


class TestPlateScale:
    """The plate is supersampled only as far as the card needs."""

    def test_a_card_at_render_scale_two_or_more_adds_no_plate_scale(self) -> None:
        """At render scale 2 or 3 the plate is stroked at 1, so a supersampled card pays once."""
        assert [plate_scale(s) for s in (2.0, 3.0)] == [1, 1]

    def test_a_card_at_render_scale_one_strokes_the_plate_at_two(self) -> None:
        """A card composed at display size gets a plate stroked at 2 and shrunk, so it stays crisp."""
        assert plate_scale(1.0) == 2
