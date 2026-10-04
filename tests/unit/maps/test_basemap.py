"""The typed basemap `journal_layers` assembles from the Lynmouth fixture, and its canonical text."""

import dataclasses
import math
import shutil

import pytest

from pyntpot._port import geo, paint
from pyntpot.maps.basemap import Basemap, ElevationPatch, Layers, River, Road
from pyntpot.maps.card import Card
from pyntpot.maps.credit import Credit
from pyntpot.maps.projection import Projection
from pyntpot.maps.style import Style

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
    built = geo.journal_layers(
        KEY,
        lat,
        lng,
        paint.PaintStyle(),
        cache_dir=work,
        places=[],
        basemap_style=Style.default().basemap,
    )
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


def synthetic_basemap() -> Basemap:
    """A small basemap whose every float sits away from a three-decimal boundary."""
    layers = Layers(
        route=((10.1234, 20.4321), (30.2341, 40.3412)),
        cover={"wood": (((0.1112, 0.2223), (5.3334, 0.4445), (5.5556, 6.6667)),)},
        cover_order=("wood",),
        lakes=(((1.1231, 1.2341), (2.3451, 1.4561), (2.5671, 3.6781)),),
        sea=(),
        coastline=(((-0.0001, 7.7771), (8.8881, 9.9991)),),
        roads=(
            Road(
                ((100.1234, 50.4321), (200.2341, 60.3412)), "major", "major", "primary", "A39", ""
            ),
        ),
        rivers=(
            River(
                ((3.1234, 4.2341), (5.3412, 6.4123)),
                "major",
                "East Lyn",
                4.1234,
                2.4321,
                (0.5123, 1.0012),
            ),
        ),
        elevation=ElevationPatch(
            n=2,
            x0=-1.1234,
            y0=-2.2341,
            x1=3.3412,
            y1=4.4123,
            values=(10.1234, 20.2341, 30.3412, 40.4123),
            low=10,
            high=40,
        ),
        ribbon_m=553,
        wet_px={"major": 9.5123, "minor": 2.4321},
        minor_roads=True,
        blotch_m=60.1234,
        dab_spacing_m=12.4321,
        gran_m=6.2341,
    )
    return Basemap(
        projection=Projection(lat0=51.2234, lat_ref=51.2234, lng_ref=-3.8321),
        card=Card(
            box=(-100.1234, -50.2341, 300.3412, 150.4123),
            display=(900, 728),
            render=(1800, 1456),
            mpp=0.2234,
            mpp_display=0.4468,
        ),
        layers=layers,
        bounds=(0.1234, 0.2341, 200.3412, 100.4123),
        span_m=200,
        ribbon_fitted_m=500,
        track=((10.1234, 20.4321), (30.2341, 40.3412)),
    )


def _nudged(value: object) -> object:
    """Return `value` with every float in it moved one ulp up."""
    if isinstance(value, float):
        return math.nextafter(value, math.inf)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        moved = {
            spec.name: _nudged(getattr(value, spec.name)) for spec in dataclasses.fields(value)
        }
        return dataclasses.replace(value, **moved)
    if isinstance(value, tuple):
        return tuple(_nudged(item) for item in value)
    if isinstance(value, dict):
        return {key: _nudged(item) for key, item in value.items()}
    return value


#: Basemap fields outside the hash input, each with a changed value.
OUTSIDE_THE_HASH: tuple[tuple[str, object], ...] = (
    ("places", ({"n": "Watersmeet", "x": 1.0, "y": 2.0},)),
    ("candidates", ({"name": "Countisbury", "class": "place"},)),
    ("sources", ("OpenStreetMap",)),
    ("credits", (Credit(text="OpenStreetMap contributors", url="https://osm.org", short="OSM"),)),
    ("track", ((11.0, 21.0), (31.0, 41.0), (51.0, 61.0))),
    ("track_time", (0.0, 5.0)),
)


class TestCanonical:
    """The hash input: fixed-precision text of the card frame and the layers only."""

    def test_a_last_bit_change_in_every_float_leaves_it(self) -> None:
        """Moving every float one ulp leaves the canonical text unchanged."""
        basemap = synthetic_basemap()
        nudged = _nudged(basemap)
        assert nudged != basemap
        assert isinstance(nudged, Basemap)
        assert nudged.canonical() == basemap.canonical()

    @pytest.mark.parametrize(
        ("field", "value"), OUTSIDE_THE_HASH, ids=[field for field, _ in OUTSIDE_THE_HASH]
    )
    def test_a_field_outside_the_hash_leaves_it(self, field: str, value: object) -> None:
        """Changing a basemap field outside the card frame and the layers leaves the text."""
        basemap = synthetic_basemap()
        changed = dataclasses.replace(basemap, **{field: value})
        assert changed.canonical() == basemap.canonical()

    def test_the_card_offset_leaves_it(self) -> None:
        """Changing the card's offset leaves the canonical text unchanged."""
        basemap = synthetic_basemap()
        card = dataclasses.replace(basemap.card, offset=(3.0, -4.0))
        assert dataclasses.replace(basemap, card=card).canonical() == basemap.canonical()

    def test_a_road_point_moved_a_centimetre_changes_it(self) -> None:
        """Moving one road point by 0.01 m changes the canonical text."""
        basemap = synthetic_basemap()
        road = basemap.layers.roads[0]
        (x, y), rest = road.line[0], road.line[1:]
        moved_road = dataclasses.replace(road, line=((x + 0.01, y), *rest))
        layers = dataclasses.replace(basemap.layers, roads=(moved_road,))
        assert dataclasses.replace(basemap, layers=layers).canonical() != basemap.canonical()

    def test_negative_zero_is_written_as_zero(self) -> None:
        """A float that rounds to negative zero is written as `0.000`."""
        text = synthetic_basemap().canonical()
        assert '"-0.000"' not in text
        assert '["0.000","7.777"]' in text
