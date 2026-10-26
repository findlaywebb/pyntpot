"""The fetch margins: they reach the key, the requested boxes and `fetch`, and bad ones raise."""

import shutil
from pathlib import Path
from typing import override

import pytest

from pyntpot.maps import pipeline
from pyntpot.maps.cache import LANDCOVER_MARGIN_M, MARGIN_M, Cache, FetchMargins
from pyntpot.maps.cli import main
from pyntpot.maps.providers.base import ElevationGrid
from pyntpot.maps.providers.opentopodata import OpenTopoData
from pyntpot.maps.providers.overpass import OverpassFeatures
from pyntpot.maps.style import Style
from pyntpot.maps.track import BoundingBox, Track

from support.paths import FIXTURE_DIR, KEY
from support.providers import FixtureElevation, FixtureFeatures


class _BoxFeatures(FixtureFeatures):
    """The fixture feature payloads, keeping the box of each request."""

    def __init__(self) -> None:
        """Start with no boxes kept."""
        super().__init__()
        self.boxes: dict[str, BoundingBox] = {}

    @override
    def features(self, box: BoundingBox) -> str:
        """Keep the box, then answer from the fixture."""
        self.boxes["features"] = box
        return super().features(box)

    @override
    def landcover(self, box: BoundingBox) -> str:
        """Keep the box, then answer from the fixture."""
        self.boxes["landcover"] = box
        return super().landcover(box)


class _BoxElevation(FixtureElevation):
    """The fixture elevation grid, keeping the box of its request."""

    def __init__(self) -> None:
        """Start with no box kept."""
        super().__init__()
        self.box: BoundingBox | None = None

    @override
    def grid(self, box: BoundingBox, n: int) -> ElevationGrid:
        """Keep the box, then answer from the fixture."""
        self.box = box
        return super().grid(box, n)


@pytest.fixture(scope="module")
def track() -> Track:
    """The Lynmouth fixture track, parsed once."""
    return Track.from_gpx(FIXTURE_DIR / "track.gpx")


class TestKey:
    """The land cover margin joins the key only when it is not the default."""

    def test_default_margins_give_the_pinned_key(self, track: Track, tmp_path: Path) -> None:
        """Both margins at their defaults, spelled out, give the pinned Lynmouth key."""
        key = Cache(tmp_path, FetchMargins(MARGIN_M, LANDCOVER_MARGIN_M)).key(
            track, FixtureFeatures(), FixtureElevation()
        )
        assert key == KEY == "f173b2f7a20bb9d4"

    def test_a_wider_margin_changes_the_key(self, track: Track, tmp_path: Path) -> None:
        """A wider feature margin gives a different key."""
        key = Cache(tmp_path, FetchMargins(4000.0, 4000.0)).key(
            track, FixtureFeatures(), FixtureElevation()
        )
        assert key != KEY

    def test_the_landcover_margin_alone_changes_the_key(self, track: Track, tmp_path: Path) -> None:
        """Two keys that differ only in the land cover margin differ."""
        wide = Cache(tmp_path, FetchMargins(MARGIN_M, 3500.0)).key(
            track, FixtureFeatures(), FixtureElevation()
        )
        wider = Cache(tmp_path, FetchMargins(MARGIN_M, 4500.0)).key(
            track, FixtureFeatures(), FixtureElevation()
        )
        assert KEY not in {wide, wider}
        assert wide != wider


class TestValidation:
    """A margin outside 0 to 20 000 m, or a land cover margin under the feature margin, raises."""

    @pytest.mark.parametrize(
        ("margin_m", "landcover_margin_m", "bad"),
        [
            (-1.0, LANDCOVER_MARGIN_M, "-1.0"),
            (20_001.0, 30_000.0, "20001.0"),
            (MARGIN_M, 20_001.0, "20001.0"),
            (MARGIN_M, -5.0, "-5.0"),
            (3000.0, 2600.0, "2600.0"),
        ],
        ids=["negative", "margin-too-wide", "landcover-too-wide", "landcover-negative", "narrower"],
    )
    def test_bad_margins_raise_naming_the_value(
        self, margin_m: float, landcover_margin_m: float, bad: str
    ) -> None:
        """Making `FetchMargins` raises `ValueError` naming the offending value."""
        with pytest.raises(ValueError, match=bad):
            FetchMargins(margin_m, landcover_margin_m)

    def test_the_limits_themselves_are_allowed(self, track: Track, tmp_path: Path) -> None:
        """0 and 20 000 m are valid margins."""
        assert Cache(tmp_path, FetchMargins(0.0, 0.0)).key(
            track, FixtureFeatures(), FixtureElevation()
        )
        assert Cache(tmp_path, FetchMargins(20_000.0, 20_000.0)).key(
            track, FixtureFeatures(), FixtureElevation()
        )


class TestRequestedBoxes:
    """`ensure` asks the providers for boxes that follow the margins."""

    def test_defaults_ask_for_the_default_boxes(self, track: Track, tmp_path: Path) -> None:
        """With no margins given, the boxes are the track's box plus each default margin."""
        features, elevation = _BoxFeatures(), _BoxElevation()
        Cache(tmp_path).ensure(track, features, elevation)
        assert features.boxes["features"] == track.bounding_box(MARGIN_M)
        assert features.boxes["landcover"] == track.bounding_box(LANDCOVER_MARGIN_M)
        assert elevation.box == track.bounding_box(MARGIN_M)

    def test_wider_margins_ask_for_wider_boxes(self, track: Track, tmp_path: Path) -> None:
        """Given margins widen the requested boxes and name the payloads by the new key."""
        features, elevation = _BoxFeatures(), _BoxElevation()
        cache = Cache(tmp_path, FetchMargins(4000.0, 5000.0))
        key = cache.ensure(track, features, elevation)
        assert features.boxes["features"] == track.bounding_box(4000.0)
        assert features.boxes["landcover"] == track.bounding_box(5000.0)
        assert elevation.box == track.bounding_box(4000.0)
        assert key == cache.key(track, features, elevation)
        assert cache.features_path(key).is_file()


class TestFetch:
    """`fetch` passes the margins to the cache."""

    def test_fetch_requests_the_wider_box(self, track: Track, tmp_path: Path) -> None:
        """A `margin_m` given to `fetch` reaches the feature provider's request."""
        features = _BoxFeatures()
        pipeline.fetch(
            track,
            Cache(tmp_path, FetchMargins(3000.0, 3000.0)),
            features,
            FixtureElevation(),
            Style.default(),
        )
        assert features.boxes["features"] == track.bounding_box(3000.0)


class TestCli:
    """`--margin-m` reaches both the fetch and the key."""

    def test_margin_m_reaches_the_key(self, track: Track, tmp_path: Path) -> None:
        """A cache holding the payloads under the wide key answers `--margin-m 3000` offline."""
        providers = (OverpassFeatures("t"), OpenTopoData("t"))
        key = Cache(tmp_path, FetchMargins(3000.0, 3000.0)).key(track, *providers)
        for stem in ("overpass", "landcover", "elevation"):
            shutil.copy(FIXTURE_DIR / f"{stem}-{KEY}.json", tmp_path / f"{stem}-{key}.json")
        theme = Path(__file__).parents[3] / "src/pyntpot/maps/themes/default.toml"
        style = tmp_path / "small.toml"
        text = theme.read_text(encoding="utf-8")
        style.write_text(text.replace("display_px = 900", "display_px = 120"), encoding="utf-8")
        out = tmp_path / "out.png"
        argv = ["map", str(FIXTURE_DIR / "track.gpx"), "--cache", str(tmp_path), "--contact", "t"]
        argv += ["--margin-m", "3000", "--style", str(style), "--no-attribution", "-o", str(out)]
        assert main(argv) == 0
        assert (tmp_path / "plates" / key).is_dir()

    def test_a_negative_margin_exits_nonzero(self, tmp_path: Path) -> None:
        """A margin outside the allowed range raises `ValueError` rather than fetching."""
        argv = ["map", str(FIXTURE_DIR / "track.gpx"), "--cache", str(tmp_path), "--contact", "t"]
        argv += ["--margin-m", "-1", "-o", str(tmp_path / "o.png")]
        with pytest.raises(ValueError, match="-1"):
            main(argv)
