"""The basemap's vector layers, read from the fetch cache as a typed value."""

import dataclasses
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from pyntpot.maps import Cache, Style, Track, VectorLayers, vector_layers

from support.paths import FIXTURE_DIR, KEY

#: The fixture box's own pinned figures in the default style.
FIXTURE_ROADS = 82
FIXTURE_RIVERS = 9
FIXTURE_COASTLINE = 4
FIXTURE_LANDMARKS = 34
FIXTURE_SPAN_M = 3052
FIXTURE_SCALE = 1.0
FIXTURE_RIVER_WIDTH_PX = 8.0

#: A landmark candidate the fixture box offers, named by its own payload.
PICKED = "Lyndale Bridge"

#: Supplied places on the track's first points, as a caller supplies them.
PLACES: tuple[dict[str, object], ...] = (
    {"name": "Watersmeet", "lat": 51.230678, "lng": -3.828447, "symbol": "house", "note": "tea"},
    {"name": "Countisbury", "lat": 51.230578, "lng": -3.828998, "kind": "settlement"},
)


@pytest.fixture(scope="module")
def track() -> Track:
    """The Lynmouth fixture track, parsed once."""
    return Track.from_gpx(FIXTURE_DIR / "track.gpx")


def _relief_style(mode: str) -> Style:
    """The default style drawing its relief in one hillshade mode."""
    style = Style.default()
    return style.model_copy(
        update={"basemap": dataclasses.replace(style.basemap, hillshade_mode=mode)}
    )


def _bands(layers: VectorLayers) -> bool:
    """Whether the relief is posterised bands, each a shadow or a light."""
    signs = {band.sign for band in layers.hillshade_bands}
    return bool(signs) and signs <= {-1, 1}


def _contours(layers: VectorLayers) -> bool:
    """Whether the relief is contours, each major or minor and at a level."""
    lines = layers.contours
    classes = {line.cls for line in lines}
    return bool(lines) and classes <= {"major", "minor"} and None not in {x.level_m for x in lines}


def _hachures(layers: VectorLayers) -> bool:
    """Whether the relief is hachure groups, each with a share of the relief opacity."""
    weights = [line.weight for line in layers.hachures]
    return bool(weights) and all(0.0 < weight <= 1.0 for weight in weights)


def _raster(layers: VectorLayers) -> bool:
    """Whether the relief is a greyscale image carried as a PNG data URI."""
    image = layers.hillshade_image
    return image is not None and image.href.startswith("data:image/png")


#: What each hillshade mode puts in the value.
RELIEF: dict[str, Callable[[VectorLayers], bool]] = {
    "bands": _bands,
    "contours": _contours,
    "hachures": _hachures,
    "raster": _raster,
}


def test_an_empty_cache_has_no_vector_layers(track: Track, tmp_path: Path) -> None:
    """A cache holding nothing under the key gives no vector layers."""
    assert vector_layers(track, Cache(tmp_path), KEY, Style.default()) is None


def test_the_fixture_box_carries_its_roads_rivers_and_coast(track: Track) -> None:
    """The fixture box gives its pinned roads, rivers, coast, landmarks and areas."""
    layers = vector_layers(track, Cache(FIXTURE_DIR), KEY, Style.default())
    assert layers is not None
    assert layers.key == KEY
    assert len(layers.sources) == 2
    assert (layers.span_m, layers.scale, layers.river_width_px) == (
        FIXTURE_SPAN_M,
        FIXTURE_SCALE,
        FIXTURE_RIVER_WIDTH_PX,
    )
    assert len(layers.roads) == FIXTURE_ROADS
    assert len(layers.rivers) == FIXTURE_RIVERS
    assert len(layers.coastline) == FIXTURE_COASTLINE
    assert len(layers.landmarks) == FIXTURE_LANDMARKS
    assert {road.cls for road in layers.roads} == {"major", "minor"}
    assert {river.cls for river in layers.rivers} == {"river"}
    areas = (layers.sea, layers.mapped_sea, layers.park, layers.wood, layers.lakes)
    assert all(area.path for area in areas)


def test_picked_landmarks_replace_the_chosen_ones(track: Track) -> None:
    """A landmark the style picks replaces every landmark the box would choose."""
    style = Style.default()
    picked = style.model_copy(
        update={"basemap": dataclasses.replace(style.basemap, pick_landmarks=(PICKED,))}
    )
    layers = vector_layers(track, Cache(FIXTURE_DIR), KEY, picked)
    assert layers is not None
    assert [landmark["n"] for landmark in layers.landmarks] == [PICKED]
    assert layers.landmarks[0]["picked"] is True


def test_an_origin_places_the_track_s_first_point(track: Track) -> None:
    """With no origin the track's south-west corner is 0, 0; an origin moves it rigidly."""
    cache = Cache(FIXTURE_DIR)
    style = Style.default()
    corner = vector_layers(track, cache, KEY, style)
    near = vector_layers(track, cache, KEY, style, origin=(500.0, 500.0))
    far = vector_layers(track, cache, KEY, style, origin=(600.0, 550.0))
    assert corner is not None
    assert near is not None
    assert far is not None
    assert corner.bounds[:2] == (0.0, 0.0)
    shifts = [b - a for a, b in zip(near.bounds, far.bounds, strict=True)]
    assert shifts == pytest.approx([100.0, 50.0, 100.0, 50.0], abs=0.11)


@pytest.mark.parametrize("mode", list(RELIEF), ids=list(RELIEF))
def test_the_relief_mode_chooses_the_relief(track: Track, mode: str) -> None:
    """Each hillshade mode carries its own relief entries in the value."""
    layers = vector_layers(track, Cache(FIXTURE_DIR), KEY, _relief_style(mode))
    assert layers is not None
    assert RELIEF[mode](layers)


def test_reading_writes_nothing(track: Track, tmp_path: Path) -> None:
    """Reading the vector layers leaves the cache directory exactly as it was."""
    root = tmp_path / "cache"
    shutil.copytree(FIXTURE_DIR, root)
    before = sorted((p.relative_to(root), p.stat().st_mtime_ns) for p in root.rglob("*"))
    assert vector_layers(track, Cache(root), KEY, Style.default()) is not None
    after = sorted((p.relative_to(root), p.stat().st_mtime_ns) for p in root.rglob("*"))
    assert after == before


def test_supplied_places_inside_the_box_are_carried(track: Track) -> None:
    """A supplied place inside the box is carried with `name` as `n` and `symbol` as `sym`."""
    layers = vector_layers(track, Cache(FIXTURE_DIR), KEY, Style.default(), PLACES)
    assert layers is not None
    marks = [
        (place["n"], place["sym"], place["kind"], place["always"], place["note"])
        for place in layers.places
    ]
    assert marks == [
        ("Watersmeet", "house", "marker", False, "tea"),
        ("Countisbury", "", "settlement", False, ""),
    ]
    assert all(isinstance(place["x"], float) for place in layers.places)


def test_landmark_and_place_entries_are_read_only(track: Track) -> None:
    """Changing a landmark or place entry, or a landmark's tags, raises `TypeError`."""
    layers = vector_layers(track, Cache(FIXTURE_DIR), KEY, Style.default(), PLACES)
    assert layers is not None
    entries: tuple[Any, ...] = (layers.places[0], layers.landmarks[0], layers.landmarks[0]["tags"])
    for entry in entries:
        with pytest.raises(TypeError):
            entry["n"] = "Lynton"


def test_an_elevation_only_cache_gives_relief_and_no_features(track: Track, tmp_path: Path) -> None:
    """With only the elevation payload cached the value is the relief, with no roads or rivers."""
    shutil.copy(Cache(FIXTURE_DIR).elevation_path(KEY), tmp_path)
    layers = vector_layers(track, Cache(tmp_path), KEY, Style.default())
    assert layers is not None
    assert len(layers.sources) == 1
    assert (layers.roads, layers.rivers, layers.coastline) == ((), (), ())
    assert layers.sea.path
