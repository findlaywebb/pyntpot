"""The typed basemap `journal_layers` assembles from the Lynmouth fixture."""

import shutil

import pytest

from pyntpot._port import geo, paint
from pyntpot.maps.basemap import Basemap

from support.paths import FIXTURE_DIR, KEY

#: How many land-cover rings of each class the fixture box carries.
COVER_RINGS = {
    "built": 107,
    "meadow": 640,
    "farmland": 5,
    "heath": 77,
    "scrub": 76,
    "wetland": 2,
    "sand": 7,
    "rock": 155,
    "works": 1,
    "wood": 91,
}


@pytest.fixture(scope="module")
def basemap(tmp_path_factory: pytest.TempPathFactory) -> Basemap:
    """The fixture box's basemap, assembled once from a copy of the fixture."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    lat, lng = geo.read_gpx(work / "track.gpx")
    built = geo.journal_layers(KEY, lat, lng, paint.PaintStyle(), cache_dir=work, places=[])
    assert built is not None
    return built


def test_the_fixture_box_carries_the_pinned_counts(basemap: Basemap) -> None:
    """The fixture yields the pinned numbers of roads, watercourses and cover rings."""
    layers = basemap.layers
    assert len(layers.roads) == 39
    assert len(layers.rivers) == 4
    assert {cls: len(rings) for cls, rings in layers.cover.items()} == COVER_RINGS


def test_every_road_is_a_line(basemap: Basemap) -> None:
    """Every road stroke has at least two points."""
    assert all(len(road.line) >= 2 for road in basemap.layers.roads)


def test_the_track_keeps_every_point(basemap: Basemap) -> None:
    """The basemap's track holds all 400 fixture points, not the simplified route."""
    assert len(basemap.track) == 400
