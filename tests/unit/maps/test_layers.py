"""The basemap assembled from cached payloads: feature selection, scale and real data.

The vector layers are built from small synthetic Overpass payloads written into a
temporary cache; the typed basemap is built from the Lynmouth fixture.
"""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.maps.cache import Cache
from pyntpot.maps.layers import (
    MAX_SCALE,
    BasemapInputs,
    _derived,
    _place_marks,
    basemap,
    build_basemap,
    scale_for,
)
from pyntpot.maps.projection import Projection
from pyntpot.maps.style import Style
from pyntpot.maps.style_groups import BasemapStyle, CardStyle, RibbonStyle
from pyntpot.maps.track import Track

from support.paths import FIXTURE_DIR, KEY

# A short east-west track inside the Lynmouth box.
LATS = [51.2250 + 2e-5 * i for i in range(60)]
LNGS = [-3.8400 + 0.00040 * i for i in range(60)]

#: A feature running alongside the track, 33 m off it for about a kilometre.
BESIDE = [(LATS[i] + 0.00030, LNGS[i]) for i in range(5, 32)]

#: The same shape, 660 m off: near enough to be on the sheet, far enough that
#: the session never met it.
AWAY = [(LATS[i] + 0.00600, LNGS[i]) for i in range(5, 32)]

#: The fixture box's own pinned layer figures.
FIXTURE_RIBBON_M = 553
FIXTURE_DISPLAY = (900, 728)


def _way(way_id: int, tags: dict[str, str], coords: list[tuple[float, float]]) -> dict[str, Any]:
    """One Overpass way with geometry."""
    return {
        "type": "way",
        "id": way_id,
        "tags": tags,
        "geometry": [{"lat": a, "lon": b} for a, b in coords],
    }


def _inputs(
    tmp_path: Path, elements: list[dict[str, Any]], places: list[dict[str, Any]] | None = None
) -> BasemapInputs:
    """The synthetic track with a synthetic Overpass payload written into a cache."""
    (tmp_path / "overpass-iTEST.json").write_text(json.dumps({"elements": elements}))
    track = Track(lat=tuple(LATS), lng=tuple(LNGS))
    return BasemapInputs("iTEST", track, Cache(tmp_path), places or [])


def _layers(inputs: BasemapInputs, options: BasemapStyle | None = None) -> dict[str, Any]:
    """The vector layers of one synthetic box under one set of basemap options."""
    data = basemap(inputs, options)
    assert data is not None
    return data


def _road_names(tmp_path: Path, roads: str) -> set[str]:
    """Names of the roads kept for one selection mode."""
    elements = [
        _way(
            1,
            {"highway": "primary", "name": "A road far away"},
            [(51.2290, -3.8400), (51.2290, -3.8200)],
        ),
        _way(2, {"highway": "residential", "name": "Lane beside the track"}, BESIDE),
        _way(3, {"highway": "residential", "name": "Lane a mile off"}, AWAY),
    ]
    return {
        road["n"]
        for road in _layers(_inputs(tmp_path, elements), BasemapStyle(roads=roads))["roads"]
    }


def test_major_roads_are_drawn_wherever_they_are(tmp_path: Path) -> None:
    """Trunk, primary and secondary are on the map whatever the session did."""
    assert "A road far away" in _road_names(tmp_path, "key")
    assert "A road far away" in _road_names(tmp_path, "major")


def test_a_minor_road_needs_the_track_to_have_met_it(tmp_path: Path) -> None:
    """A lane the track ran along is kept; the same lane a mile off is not."""
    kept = _road_names(tmp_path, "key")
    assert "Lane beside the track" in kept
    assert "Lane a mile off" not in kept


def test_major_only_drops_every_minor_road(tmp_path: Path) -> None:
    """The `major` mode is the plainest map: no minor road at any distance."""
    assert _road_names(tmp_path, "major") == {"A road far away"}


def test_all_keeps_the_lane_that_was_never_near(tmp_path: Path) -> None:
    """The `all` mode is the comparison, not the default: it keeps everything."""
    assert "Lane a mile off" in _road_names(tmp_path, "all")


def test_a_road_is_kept_whole_where_any_of_it_met_the_track(tmp_path: Path) -> None:
    """OSM cuts a street at every junction; the keep test is not cut with it."""
    elements = [
        _way(1, {"highway": "residential", "name": "Lane beside the track"}, BESIDE),
        # The next block of the same street, well away from the track.
        _way(2, {"highway": "residential", "name": "Lane beside the track"}, AWAY),
        _way(3, {"highway": "residential", "name": "A different lane"}, AWAY),
    ]
    data = _layers(_inputs(tmp_path, elements), BasemapStyle(roads="key"))
    kept = [r for r in data["roads"] if r["n"] == "Lane beside the track"]
    assert len(kept) == 2, "the street was kept in one block and dropped in the next"
    assert not [r for r in data["roads"] if r["n"] == "A different lane"]


def test_an_unnamed_way_is_still_decided_on_its_own(tmp_path: Path) -> None:
    """A service road with no number and no name belongs to no road."""
    elements = [_way(1, {"highway": "service"}, BESIDE), _way(2, {"highway": "service"}, AWAY)]
    assert len(_layers(_inputs(tmp_path, elements), BasemapStyle(roads="key"))["roads"]) == 1


def _river_names(tmp_path: Path, elements: list[dict[str, Any]]) -> set[str]:
    """The watercourses a box keeps."""
    return {
        r["n"] for r in _layers(_inputs(tmp_path, elements), BasemapStyle(rivers="all"))["rivers"]
    }


def test_a_buried_river_is_not_drawn(tmp_path: Path) -> None:
    """The Swale still flows; it flows in a Victorian sewer under a street."""
    elements = [
        _way(1, {"waterway": "river", "name": "Swale", "tunnel": "yes"}, BESIDE),
        _way(2, {"waterway": "river", "name": "Open water"}, AWAY),
    ]
    kept = _river_names(tmp_path, elements)
    assert "Swale" not in kept
    assert "Open water" in kept


def test_a_river_that_passes_under_one_culvert_stays_whole(tmp_path: Path) -> None:
    """A river tagged `tunnel=culvert` on one way in a long run is not a sewer."""
    long_open = [(LATS[i] + 0.00030, LNGS[i]) for i in range(5, 40)]
    short_covered = [(LATS[i] + 0.00030, LNGS[i]) for i in range(40, 42)]
    elements = [
        _way(1, {"waterway": "river", "name": "Wharfe"}, long_open),
        _way(2, {"waterway": "river", "name": "Wharfe", "tunnel": "culvert"}, short_covered),
    ]
    data = _layers(_inputs(tmp_path, elements), BasemapStyle(rivers="all"))
    assert len([r for r in data["rivers"] if r["n"] == "Wharfe"]) == 2


def test_rivers_are_always_drawn_and_a_stream_has_to_earn_it(tmp_path: Path) -> None:
    """A river is a feature of the ground; a stream is only a feature of the run."""
    elements = [
        _way(
            1, {"waterway": "river", "name": "The river"}, [(51.2290, -3.8400), (51.2290, -3.8200)]
        ),
        _way(2, {"waterway": "stream", "name": "Brook beside the track"}, BESIDE),
        _way(3, {"waterway": "stream", "name": "Brook a mile off"}, AWAY),
    ]
    inputs = _inputs(tmp_path, elements)
    kept = {
        river["n"]: river["c"] for river in _layers(inputs, BasemapStyle(rivers="key"))["rivers"]
    }
    assert kept["The river"] == "river"
    assert "Brook beside the track" in kept
    assert "Brook a mile off" not in kept
    only = _layers(inputs, BasemapStyle(rivers="rivers"))
    assert {river["n"] for river in only["rivers"]} == {"The river"}


def test_no_layer_carries_an_administrative_border(tmp_path: Path) -> None:
    """Borders are not drawn at all: they are not ground the track covers."""
    elements = [
        _way(
            1,
            {"boundary": "administrative", "admin_level": "8", "name": "Parish"},
            [(51.2250, -3.8400), (51.2250, -3.8200)],
        )
    ]
    assert "Parish" not in json.dumps(_layers(_inputs(tmp_path, elements)))


def test_places_are_drawn_from_the_places_passed_in(tmp_path: Path) -> None:
    """Home is a place the caller passes in, not a marker at a track's start."""
    places = [{"name": "Home", "symbol": "house", "lat": 51.2255, "lng": -3.8350}]
    data = _layers(_inputs(tmp_path, [], places))
    assert [(p["n"], p["sym"]) for p in data["places"]] == [("Home", "house")]


def test_home_is_untouched_by_the_new_keys() -> None:
    """`Home` has a symbol, no kind and no always_label, and draws as it always did."""
    entries = [{"name": "Home", "symbol": "house", "lat": 51.2255, "lng": -3.835}]
    proj = Projection(lat0=51.225, lat_ref=51.225, lng_ref=-3.840)
    marks = _place_marks(entries, proj, (-9e9, -9e9, 9e9, 9e9))
    assert marks[0]["sym"] == "house"
    assert marks[0]["kind"] == "marker"
    assert marks[0]["always"] is False


def test_a_box_with_nothing_cached_has_no_layers(tmp_path: Path) -> None:
    """The renderer's signal to draw the bare track is a basemap of None."""
    track = Track(lat=tuple(LATS), lng=tuple(LNGS))
    assert basemap(BasemapInputs("iNONE", track, Cache(tmp_path), [])) is None


def test_generalisation_scales_with_the_box() -> None:
    """A ride's box is drawn coarser than a run's, rather than shrunk to fit."""
    assert scale_for(3000.0) == 1.0
    assert scale_for(12000.0) == pytest.approx(3.0)
    assert scale_for(100000.0) == MAX_SCALE
    run = _derived(BasemapStyle(), scale_for(3200.0))
    ride = _derived(BasemapStyle(), scale_for(13000.0))
    assert ride["road_eps_m"] > run["road_eps_m"]
    assert ride["landmark_radius_m"] > run["landmark_radius_m"]
    assert ride["landmark_cap"] >= run["landmark_cap"]
    assert ride["cell_m"] > run["cell_m"]
    assert ride["min_area_ha"] > run["min_area_ha"]


@pytest.fixture(scope="module")
def fixture_inputs(tmp_path_factory: pytest.TempPathFactory) -> BasemapInputs:
    """The Lynmouth fixture box, copied once so no test writes into the fixture."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    return BasemapInputs(KEY, Track.from_gpx(work / "track.gpx"), Cache(work), [])


def test_the_generalised_wood_is_smaller_and_simpler(fixture_inputs: BasemapInputs) -> None:
    """On the Lynmouth box the generalised layer loses rings and bytes."""
    raw = basemap(fixture_inputs, BasemapStyle(generalise=False))
    fine = basemap(fixture_inputs, BasemapStyle(generalise=True))
    assert raw is not None
    assert fine is not None
    assert fine["wood"]["n"] < raw["wood"]["n"]
    assert len(fine["wood"]["d"]) < len(raw["wood"]["d"])


def test_the_real_box_assembles_the_layers_the_painter_needs(
    fixture_inputs: BasemapInputs,
) -> None:
    """The Lynmouth box: land cover, roads by brush, and the fitted ribbon."""
    style = Style.default().model_copy(
        update={"card": CardStyle(), "ribbon": RibbonStyle(), "brush": BrushStyle()}
    )
    built = build_basemap(fixture_inputs, style)
    assert built is not None
    layers = built.layers
    assert layers.ribbon_m == FIXTURE_RIBBON_M
    assert built.card.display == FIXTURE_DISPLAY
    assert "wood" in layers.cover
    assert layers.cover_order[-1] == "wood"
    assert {r.band for r in layers.roads} <= {"major", "minor", "path"}
    assert layers.minor_roads is True
