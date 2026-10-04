"""`fetch` builds the fixture's basemap from the cache; `paint` paints it once and reuses it."""

import shutil
from pathlib import Path
from typing import NamedTuple

import pytest

from pyntpot.maps import pipeline
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.cache import Cache
from pyntpot.maps.credit import Credit
from pyntpot.maps.pipeline import FetchError
from pyntpot.maps.plates import Plates
from pyntpot.maps.providers.base import ElevationGrid
from pyntpot.maps.style import Style
from pyntpot.maps.track import BoundingBox, Track

from support.paths import FIXTURE_DIR, KEY
from support.providers import OSM_CREDIT, SRTM_CREDIT, FixtureElevation, FixtureFeatures

#: The base hash of the regenerated golden `plates.json`.
GOLDEN_HASH = "340a7f6e260ee1e2-e5a5f1b4b3ca2177"

#: The first three points of the drawn route, taken once from the compose step.
FIRST_STRANDS = (
    (468.60535507679316, 229.12410015961044),
    (465.4753605571534, 229.95207657256395),
    (462.40319129045776, 231.02797742619708),
)


class Fetched(NamedTuple):
    """One fetch over a copy of the fixture, and the calls each provider saw."""

    cache: Cache
    basemap: Basemap
    feature_calls: tuple[str, ...]
    elevation_calls: tuple[str, ...]


class _VanishingElevation:
    """The fixture elevation grid, deleting the cached features before it answers."""

    def __init__(self, cache_dir: Path) -> None:
        """Wrap a fresh fixture provider over the cache directory it empties."""
        self._inner = FixtureElevation()
        self._cache_dir = cache_dir

    @property
    def id(self) -> str:
        """The wrapped provider's id."""
        return self._inner.id

    @property
    def credit(self) -> Credit:
        """The wrapped provider's credit."""
        return self._inner.credit

    def grid(self, box: BoundingBox, n: int) -> ElevationGrid:
        """Unlink every cached features payload, then answer from the fixture."""
        for path in self._cache_dir.glob("overpass-*.json"):
            path.unlink()
        return self._inner.grid(box, n)


@pytest.fixture(scope="module")
def track() -> Track:
    """The Lynmouth fixture track, parsed once."""
    return Track.from_gpx(FIXTURE_DIR / "track.gpx")


@pytest.fixture(scope="module")
def style() -> Style:
    """The packaged default style, read once."""
    return Style.default()


@pytest.fixture(scope="module")
def fetched(tmp_path_factory: pytest.TempPathFactory, track: Track, style: Style) -> Fetched:
    """The fixture fetched once over a copy of the fixture directory."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    cache = Cache(work)
    features, elevation = FixtureFeatures(), FixtureElevation()
    basemap = pipeline.fetch(track, cache, features, elevation, style)
    return Fetched(cache, basemap, tuple(features.calls), tuple(elevation.calls))


@pytest.fixture(scope="module")
def painted(fetched: Fetched, style: Style) -> Plates:
    """The fetched basemap painted once into the cache's plates directory for its key."""
    return pipeline.paint(fetched.basemap, style, fetched.cache.plates_dir(KEY))


class TestFetch:
    """`fetch` reads a filled cache without calling a provider."""

    def test_a_filled_cache_calls_no_provider(self, fetched: Fetched) -> None:
        """Over a copy of the fixture neither provider is called."""
        assert fetched.feature_calls == ()
        assert fetched.elevation_calls == ()

    def test_the_basemap_carries_the_pinned_roads(self, fetched: Fetched) -> None:
        """The fetched basemap holds the fixture box's pinned number of roads."""
        assert len(fetched.basemap.layers.roads) == 39

    def test_the_basemap_carries_both_credits(self, fetched: Fetched) -> None:
        """The basemap's credits are the feature and the elevation provider's, in that order."""
        assert fetched.basemap.credits == (OSM_CREDIT, SRTM_CREDIT)

    def test_the_basemap_carries_the_track_times(self, fetched: Fetched, track: Track) -> None:
        """The basemap's times are the track's, absent for the untimed fixture track."""
        assert fetched.basemap.track_time is None
        assert track.time is None

    def test_features_gone_after_the_fetch_raise(
        self, track: Track, style: Style, tmp_path: Path
    ) -> None:
        """Features unlinked before the basemap is built raise `FetchError` naming key and path."""
        cache = Cache(tmp_path)
        with pytest.raises(FetchError) as caught:
            pipeline.fetch(track, cache, FixtureFeatures(), _VanishingElevation(tmp_path), style)
        message = str(caught.value)
        assert KEY in message
        assert str(cache.features_path(KEY)) in message


@pytest.mark.golden
class TestPaint:
    """`paint` writes the three plates once, with the route on the card beside them."""

    def test_three_plates_are_written(self, painted: Plates) -> None:
        """The paper, wash and pen plates are written in the plates directory."""
        assert set(painted.paths) == {"paper", "wash", "pen"}
        assert all(path.is_file() for path in painted.paths.values())

    def test_the_hash_is_the_golden_hash(self, painted: Plates) -> None:
        """The painted plates carry the regenerated golden's base hash."""
        assert painted.hash == GOLDEN_HASH

    def test_route_and_strands_have_a_point_per_track_point(self, painted: Plates) -> None:
        """`route_px` and `strands` each hold the fixture track's 400 points."""
        assert len(painted.route_px) == 400
        assert len(painted.strands) == 400

    def test_the_strands_start_where_the_compose_step_drew(self, painted: Plates) -> None:
        """The first three strand points equal the compose step's, within a micro-pixel."""
        want = [pytest.approx(point, abs=1e-6) for point in FIRST_STRANDS]
        assert list(painted.strands[:3]) == want

    def test_a_second_paint_repaints_nothing(
        self, painted: Plates, fetched: Fetched, style: Style
    ) -> None:
        """Painting the same basemap again writes no file and returns the same plates."""
        files = sorted(painted.directory.iterdir())
        before = [path.stat().st_mtime_ns for path in files]
        again = pipeline.paint(fetched.basemap, style, painted.directory)
        assert sorted(painted.directory.iterdir()) == files
        assert [path.stat().st_mtime_ns for path in files] == before
        assert again == painted
