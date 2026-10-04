"""`Cache`: the key over box, margin and providers, the file names, and `ensure`'s order."""

from pathlib import Path

import pytest

from pyntpot._port import geo
from pyntpot.maps.cache import (
    ELEVATION_SAMPLES,
    LANDCOVER_MARGIN_M,
    MARGIN_M,
    Cache,
)
from pyntpot.maps.credit import Credit
from pyntpot.maps.providers.base import Elevation, ElevationGrid, Features
from pyntpot.maps.providers.opentopodata import OpenTopoData
from pyntpot.maps.providers.overpass import OverpassFeatures
from pyntpot.maps.track import BoundingBox, Track

from support.paths import FIXTURE_DIR, KEY
from support.providers import FixtureElevation, FixtureFeatures

#: The key the Lynmouth track gets with the fixture providers at the default margin.
LYNMOUTH_KEY = "f173b2f7a20bb9d4"


@pytest.fixture(scope="module")
def track() -> Track:
    """The Lynmouth fixture track, parsed once."""
    return Track.from_gpx(FIXTURE_DIR / "track.gpx")


class _MirrorFeatures(FixtureFeatures):
    """The fixture feature payloads under another provider's id."""

    id = "overpass-mirror"


class _OtherElevation(FixtureElevation):
    """The fixture elevation grid under another dataset's id."""

    id = "opentopodata-eudem25m"


class _Recorder:
    """One shared record of provider calls and the cache files present at each."""

    def __init__(self, cache: Cache, key: str) -> None:
        """Watch the three payload paths of one key."""
        self.paths = {
            "features": cache.features_path(key),
            "landcover": cache.landcover_path(key),
            "elevation": cache.elevation_path(key),
        }
        self.calls: list[str] = []
        self.present: dict[str, tuple[str, ...]] = {}

    def note(self, call: str) -> None:
        """Record a call and which payload files exist when it is made."""
        self.calls.append(call)
        self.present[call] = tuple(name for name, path in self.paths.items() if path.exists())


class _RecordingFeatures:
    """Fixture feature payloads that report each call to a shared recorder."""

    def __init__(self, recorder: _Recorder) -> None:
        """Wrap a fresh fixture provider."""
        self._inner = FixtureFeatures()
        self._recorder = recorder

    @property
    def id(self) -> str:
        """The wrapped provider's id."""
        return self._inner.id

    @property
    def credit(self) -> Credit:
        """The wrapped provider's credit."""
        return self._inner.credit

    def features(self, box: BoundingBox) -> str:
        """Record the call, then answer from the fixture."""
        self._recorder.note("features")
        return self._inner.features(box)

    def landcover(self, box: BoundingBox) -> str:
        """Record the call, then answer from the fixture."""
        self._recorder.note("landcover")
        return self._inner.landcover(box)


class _RecordingElevation:
    """The fixture elevation grid, reporting each call to a shared recorder."""

    def __init__(self, recorder: _Recorder) -> None:
        """Wrap a fresh fixture provider."""
        self._inner = FixtureElevation()
        self._recorder = recorder

    @property
    def id(self) -> str:
        """The wrapped provider's id."""
        return self._inner.id

    @property
    def credit(self) -> Credit:
        """The wrapped provider's credit."""
        return self._inner.credit

    def grid(self, box: BoundingBox, n: int) -> ElevationGrid:
        """Record the call, then answer from the fixture."""
        self._recorder.note("elevation")
        return self._inner.grid(box, n)


class TestKey:
    """The key derives from the box, the margin and both provider ids only."""

    def test_lynmouth_key_is_pinned(self, track: Track, tmp_path: Path) -> None:
        """The Lynmouth track with the fixture providers keys to the pinned literal."""
        cache = Cache(tmp_path)
        assert cache.key(track, FixtureFeatures(), FixtureElevation()) == LYNMOUTH_KEY

    def test_shipped_providers_key_to_the_fixture_files(self, track: Track, tmp_path: Path) -> None:
        """The shipped Overpass and OpenTopoData providers give the key the fixture files carry."""
        features = OverpassFeatures("walker@example.org")
        elevation = OpenTopoData("walker@example.org")
        assert Cache(tmp_path).key(track, features, elevation) == LYNMOUTH_KEY == KEY

    @pytest.mark.parametrize(
        ("features", "elevation", "margin_m"),
        [
            (FixtureFeatures, FixtureElevation, 2000.0),
            (_MirrorFeatures, FixtureElevation, MARGIN_M),
            (FixtureFeatures, _OtherElevation, MARGIN_M),
        ],
        ids=["margin", "features-id", "elevation-id"],
    )
    def test_any_input_change_changes_the_key(
        self,
        track: Track,
        tmp_path: Path,
        features: type[FixtureFeatures],
        elevation: type[FixtureElevation],
        margin_m: float,
    ) -> None:
        """Changing the margin or either provider id gives a different key."""
        changed = Cache(tmp_path).key(track, features(), elevation(), margin_m)
        assert changed != LYNMOUTH_KEY


class TestPaths:
    """Payload and plate paths sit under the explicit directory."""

    def test_payload_names_match_the_painter(self, tmp_path: Path) -> None:
        """The three payload paths use the painter's file names for the key."""
        cache = Cache(tmp_path)
        assert cache.features_path("k") == geo.overpass_path("k", tmp_path)
        assert cache.landcover_path("k") == geo.landcover_path("k", tmp_path)
        assert cache.elevation_path("k") == geo.elevation_path("k", tmp_path)

    def test_plates_dir_is_under_the_directory(self, tmp_path: Path) -> None:
        """The plates directory for a key is `plates/<key>` and is not created."""
        plates = Cache(tmp_path).plates_dir("k")
        assert plates == tmp_path / "plates" / "k"
        assert not plates.exists()

    @pytest.mark.parametrize(
        ("ours", "theirs"),
        [
            (MARGIN_M, geo.MARGIN_M),
            (LANDCOVER_MARGIN_M, geo.LANDCOVER_MARGIN_M),
            (ELEVATION_SAMPLES, geo.ELEV_N),
        ],
        ids=["margin", "landcover-margin", "elevation-samples"],
    )
    def test_constants_equal_the_painter(self, ours: float, theirs: float) -> None:
        """The copied fetch constants equal the painter's."""
        assert ours == theirs


class TestEnsure:
    """`ensure` fetches only what is missing, in a fixed order, writing as it goes."""

    def test_fills_an_empty_directory(self, track: Track, tmp_path: Path) -> None:
        """Into an empty directory each provider is called once and the files equal the fixture's."""
        cache = Cache(tmp_path / "cache")
        features, elevation = FixtureFeatures(), FixtureElevation()
        key = cache.ensure(track, features, elevation)
        assert key == LYNMOUTH_KEY
        assert features.calls == ["features", "landcover"]
        assert elevation.calls == ["grid"]
        written = {
            cache.features_path(key): FIXTURE_DIR / f"overpass-{KEY}.json",
            cache.landcover_path(key): FIXTURE_DIR / f"landcover-{KEY}.json",
            cache.elevation_path(key): FIXTURE_DIR / f"elevation-{KEY}.json",
        }
        for ours, fixture in written.items():
            # The committed fixture files end in a newline the painter never writes.
            expected = fixture.read_bytes().removesuffix(b"\n")
            assert ours.read_bytes().removesuffix(b"\n") == expected, ours.name
        assert sorted(p.name for p in cache.directory.iterdir()) == sorted(p.name for p in written)

    def test_second_ensure_calls_nothing(self, track: Track, tmp_path: Path) -> None:
        """A second `ensure` over a filled directory calls no provider."""
        cache = Cache(tmp_path)
        first = cache.ensure(track, FixtureFeatures(), FixtureElevation())
        features, elevation = FixtureFeatures(), FixtureElevation()
        assert cache.ensure(track, features, elevation) == first
        assert features.calls == []
        assert elevation.calls == []

    def test_order_and_writes_before_the_next_call(self, track: Track, tmp_path: Path) -> None:
        """Features, land cover, elevation in turn, each written before the next call."""
        cache = Cache(tmp_path)
        recorder = _Recorder(cache, LYNMOUTH_KEY)
        features: Features = _RecordingFeatures(recorder)
        elevation: Elevation = _RecordingElevation(recorder)
        assert cache.ensure(track, features, elevation) == LYNMOUTH_KEY
        assert recorder.calls == ["features", "landcover", "elevation"]
        assert recorder.present == {
            "features": (),
            "landcover": ("features",),
            "elevation": ("features", "landcover"),
        }
