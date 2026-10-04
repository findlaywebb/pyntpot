"""Tests for the route basemap: projection, feature selection and layers.

Nothing here reaches the network. The layers are built from small synthetic
Overpass and SRTM payloads written into a temporary cache.
"""

from __future__ import annotations

import dataclasses
import json
import math
from typing import TYPE_CHECKING

import pytest

from pyntpot._port import geo
from pyntpot.ink.chains import join_strokes
from pyntpot.ink.polyline import clip_line
from pyntpot.maps.projection import track_projection
from pyntpot.maps.style_groups import BasemapStyle

from support.paths import FIXTURE_DIR, KEY

if TYPE_CHECKING:
    from pathlib import Path


# A short east-west track inside the Lynmouth box.
LATS = [51.2250 + 2e-5 * i for i in range(60)]


LNGS = [-3.8400 + 0.00040 * i for i in range(60)]


#: A feature running alongside the track, 33 m off it for about a kilometre.
BESIDE = [(LATS[i] + 0.00030, LNGS[i]) for i in range(5, 32)]


#: The same shape, 660 m off: near enough to be on the sheet, far enough that
#: the session never met it.
AWAY = [(LATS[i] + 0.00600, LNGS[i]) for i in range(5, 32)]


def _way(way_id: int, tags: dict[str, str], coords: list[tuple[float, float]]) -> dict:
    """One Overpass way with geometry."""
    return {
        "type": "way",
        "id": way_id,
        "tags": tags,
        "geometry": [{"lat": a, "lon": b} for a, b in coords],
    }


def _cache(tmp_path: Path, elements: list[dict]) -> Path:
    """Write a synthetic Overpass payload into a temporary cache directory."""
    path = tmp_path / "overpass-iTEST.json"
    path.write_text(json.dumps({"elements": elements}))
    return tmp_path


# --------------------------------------------------------------------------- projection


def test_projection_round_trips_through_its_inverse():
    """Inverting the projection gets the coordinate back."""
    proj, _ = track_projection(LATS, LNGS)
    x, y = proj(51.2270, -3.8200)
    lat, lng = proj.inverse(x, y)
    assert abs(lat - 51.2270) < 1e-9
    assert abs(lng - -3.8200) < 1e-9


def test_bounding_box_grows_by_the_margin():
    """The fetched box is the track's box plus the margin, in metres."""
    south, west, north, east = geo.bounding_box(LATS, LNGS, margin_m=1000.0)
    assert (min(LATS) - south) * 110540.0 == pytest.approx(1000.0, abs=1.0)
    assert (north - max(LATS)) * 110540.0 == pytest.approx(1000.0, abs=1.0)
    assert west < min(LNGS) and east > max(LNGS)


# --------------------------------------------------------------------------- roads


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
    data = geo.basemap(
        "iTEST",
        LATS,
        LNGS,
        BasemapStyle(roads=roads),
        cache_dir=_cache(tmp_path, elements),
        places=[],
    )
    return {road["n"] for road in data["roads"]}


def test_major_roads_are_drawn_wherever_they_are(tmp_path):
    """Trunk, primary and secondary are on the map whatever the session did."""
    assert "A road far away" in _road_names(tmp_path, "key")
    assert "A road far away" in _road_names(tmp_path, "major")


def test_a_minor_road_needs_the_track_to_have_met_it(tmp_path):
    """A lane the track ran along is kept; the same lane a mile off is not."""
    kept = _road_names(tmp_path, "key")
    assert "Lane beside the track" in kept
    assert "Lane a mile off" not in kept


def test_major_only_drops_every_minor_road(tmp_path):
    """The `major` mode is the plainest map: no minor road at any distance."""
    assert _road_names(tmp_path, "major") == {"A road far away"}


def test_all_keeps_the_lane_that_was_never_near(tmp_path):
    """`all` is the comparison, not the default: it keeps everything."""
    assert "Lane a mile off" in _road_names(tmp_path, "all")


def test_a_road_is_kept_whole_where_any_of_it_met_the_track(tmp_path):
    """OSM cuts a street at every junction; the keep test is not cut with it.

    The block that crosses the route was kept and the next block along was not,
    so every side street came off the route as a stub and the sheet read as a
    comb of teeth rather than as a street pattern.
    """
    elements = [
        _way(1, {"highway": "residential", "name": "Lane beside the track"}, BESIDE),
        # The next block of the same street, well away from the track.
        _way(2, {"highway": "residential", "name": "Lane beside the track"}, AWAY),
        _way(3, {"highway": "residential", "name": "A different lane"}, AWAY),
    ]
    data = geo.basemap(
        "iTEST",
        LATS,
        LNGS,
        BasemapStyle(roads="key"),
        cache_dir=_cache(tmp_path, elements),
        places=[],
    )
    kept = [r for r in data["roads"] if r["n"] == "Lane beside the track"]
    assert len(kept) == 2, "the street was kept in one block and dropped in the next"
    assert not [r for r in data["roads"] if r["n"] == "A different lane"]


def test_an_unnamed_way_is_still_decided_on_its_own(tmp_path):
    """A service road with no number and no name belongs to no road."""
    elements = [
        _way(1, {"highway": "service"}, BESIDE),
        _way(2, {"highway": "service"}, AWAY),
    ]
    data = geo.basemap(
        "iTEST",
        LATS,
        LNGS,
        BasemapStyle(roads="key"),
        cache_dir=_cache(tmp_path, elements),
        places=[],
    )
    assert len(data["roads"]) == 1


# ------------------------------------------------------------ one road, one stroke


def test_the_pieces_of_one_road_are_chained_into_one_stroke():
    """A street cut at its junctions is one line again before it is painted."""
    pieces = [[(0.0, 0.0), (10.0, 0.0)], [(20.0, 0.0), (30.0, 0.0)], [(10.0, 0.0), (20.0, 0.0)]]
    chains = join_strokes(pieces, tol=1.0)
    assert len(chains) == 1
    assert chains[0][0] == (0.0, 0.0) and chains[0][-1] == (30.0, 0.0)


def test_a_piece_taken_from_the_middle_grows_out_to_both_ends():
    """Whichever piece the chain starts from, it reaches both ends of the road."""
    pieces = [[(10.0, 0.0), (20.0, 0.0)], [(0.0, 0.0), (10.0, 0.0)], [(20.0, 0.0), (30.0, 0.0)]]
    chain = join_strokes(pieces, tol=1.0)[0]
    assert {chain[0], chain[-1]} == {(0.0, 0.0), (30.0, 0.0)}


def test_a_piece_is_reversed_where_that_is_how_it_joins():
    """OSM way direction is not the direction a road is drawn in."""
    pieces = [[(0.0, 0.0), (10.0, 0.0)], [(20.0, 0.0), (10.0, 0.0)]]
    chain = join_strokes(pieces, tol=1.0)[0]
    assert len(chain) == 3
    assert {chain[0], chain[-1]} == {(0.0, 0.0), (20.0, 0.0)}


def test_a_chain_is_left_open():
    """A road is a line, not a ring: closing one draws a street that is not there."""
    ends = [[(0.0, 0.0), (10.0, 0.0)], [(10.0, 0.0), (10.0, 10.0)]]
    chain = join_strokes(ends, tol=1.0)[0]
    assert chain[0] != chain[-1]


def test_pieces_that_do_not_meet_stay_apart():
    """A gap wider than the tolerance is a gap, not a join to make up."""
    apart = [[(0.0, 0.0), (10.0, 0.0)], [(40.0, 0.0), (50.0, 0.0)]]
    assert len(join_strokes(apart, tol=1.0)) == 2


# ------------------------------------------------------- a river underground


def _river_names(tmp_path: Path, elements: list[dict]) -> set[str]:
    """The watercourses a box keeps."""
    data = geo.basemap(
        "iTEST",
        LATS,
        LNGS,
        BasemapStyle(rivers="all"),
        cache_dir=_cache(tmp_path, elements),
        places=[],
    )
    return {r["n"] for r in data["rivers"]}


def test_a_buried_river_is_not_drawn(tmp_path):
    """The Swale still flows; it flows in a Victorian sewer under a street."""
    elements = [
        _way(1, {"waterway": "river", "name": "Swale", "tunnel": "yes"}, BESIDE),
        _way(2, {"waterway": "river", "name": "Open water"}, AWAY),
    ]
    kept = _river_names(tmp_path, elements)
    assert "Swale" not in kept
    assert "Open water" in kept


def test_a_river_that_passes_under_one_culvert_stays_whole(tmp_path):
    """The Wharfe is `tunnel=culvert` on one way of thirteen and is not a sewer.

    The test is per watercourse and by length, so a short covered stretch does
    not take the river with it, and it does not leave a gap in it either.
    """
    long_open = [(LATS[i] + 0.00030, LNGS[i]) for i in range(5, 40)]
    short_covered = [(LATS[i] + 0.00030, LNGS[i]) for i in range(40, 42)]
    elements = [
        _way(1, {"waterway": "river", "name": "Wharfe"}, long_open),
        _way(2, {"waterway": "river", "name": "Wharfe", "tunnel": "culvert"}, short_covered),
    ]
    data = geo.basemap(
        "iTEST",
        LATS,
        LNGS,
        BasemapStyle(rivers="all"),
        cache_dir=_cache(tmp_path, elements),
        places=[],
    )
    assert len([r for r in data["rivers"] if r["n"] == "Wharfe"]) == 2


# --------------------------------------------------------------------------- rivers


def test_rivers_are_always_drawn_and_a_stream_has_to_earn_it(tmp_path):
    """A river is a feature of the ground; a stream is only a feature of the run."""
    elements = [
        _way(
            1, {"waterway": "river", "name": "The river"}, [(51.2290, -3.8400), (51.2290, -3.8200)]
        ),
        _way(2, {"waterway": "stream", "name": "Brook beside the track"}, BESIDE),
        _way(3, {"waterway": "stream", "name": "Brook a mile off"}, AWAY),
    ]
    cache = _cache(tmp_path, elements)
    data = geo.basemap("iTEST", LATS, LNGS, BasemapStyle(rivers="key"), cache_dir=cache, places=[])
    kept = {river["n"]: river["c"] for river in data["rivers"]}
    assert kept["The river"] == "river"
    assert "Brook beside the track" in kept
    assert "Brook a mile off" not in kept

    only = geo.basemap(
        "iTEST", LATS, LNGS, BasemapStyle(rivers="rivers"), cache_dir=cache, places=[]
    )
    assert {river["n"] for river in only["rivers"]} == {"The river"}


def test_no_layer_carries_an_administrative_border(tmp_path):
    """Borders are not drawn at all: they are not ground the track covers."""
    elements = [
        _way(
            1,
            {"boundary": "administrative", "admin_level": "8", "name": "Parish"},
            [(51.2250, -3.8400), (51.2250, -3.8200)],
        )
    ]
    data = geo.basemap("iTEST", LATS, LNGS, cache_dir=_cache(tmp_path, elements), places=[])
    assert "Parish" not in json.dumps(data)


# --------------------------------------------------------------------------- landmarks


def test_the_query_asks_for_the_things_a_runner_would_pick():
    """Buildings, bridges and zoos are in the box's own question to OSM."""
    query = geo.OVERPASS_QUERY.format(
        box="0,0,1,1",
        roads="primary",
        tourism="|".join(geo.TOURISM_LANDMARKS),
        manmade="|".join(geo.MANMADE_LANDMARKS),
        buildings="|".join(geo.BUILDING_LANDMARKS),
        amenities="|".join(geo.AMENITY_LANDMARKS),
        leisure="|".join(geo.LEISURE_LANDMARKS),
    )
    assert "zoo" in query
    assert '"bridge"' in query
    assert "cathedral" in query
    assert "place_of_worship" in query


# --------------------------------------------------------------------------- places


def test_places_are_drawn_from_the_places_passed_in(tmp_path):
    """Home is a place the caller passes in, not a marker at a track's start."""
    places = [{"name": "Home", "symbol": "house", "lat": 51.2255, "lng": -3.8350}]
    data = geo.basemap("iTEST", LATS, LNGS, cache_dir=_cache(tmp_path, []), places=places)
    assert [(p["n"], p["sym"]) for p in data["places"]] == [("Home", "house")]


# --------------------------------------------------------------------------- fallback


def test_generalisation_scales_with_the_box():
    """A ride's box is drawn coarser than a run's, rather than shrunk to fit."""
    assert geo.scale_for(3000.0) == 1.0
    assert geo.scale_for(12000.0) == pytest.approx(3.0)
    assert geo.scale_for(100000.0) == geo.MAX_SCALE
    run = geo._derived(BasemapStyle(), geo.scale_for(3200.0))
    ride = geo._derived(BasemapStyle(), geo.scale_for(13000.0))
    assert ride["road_eps_m"] > run["road_eps_m"]
    assert ride["landmark_radius_m"] > run["landmark_radius_m"]
    assert ride["landmark_cap"] >= run["landmark_cap"]


def test_clip_line_splits_a_road_that_leaves_and_returns():
    """A road that leaves the sheet comes back as two pieces, not one long jump."""
    line = [(0.0, 0.0), (50.0, 0.0), (500.0, 0.0), (50.0, 50.0), (10.0, 50.0)]
    pieces = clip_line(line, (0.0, 0.0, 100.0, 100.0))
    assert len(pieces) == 2
    assert math.dist(pieces[0][0], (0.0, 0.0)) < 1e-9


# --------------------------------------------------------------------------- generalise


def test_the_generalised_wood_is_smaller_and_simpler():
    """On the Lynmouth box the generalised layer loses rings and bytes."""
    lat, lng = geo.read_gpx(FIXTURE_DIR / "track.gpx")
    options = {"cache_dir": FIXTURE_DIR, "places": []}
    raw = geo.basemap(KEY, lat, lng, BasemapStyle(generalise=False), **options)
    fine = geo.basemap(KEY, lat, lng, BasemapStyle(generalise=True), **options)
    assert fine["wood"]["n"] < raw["wood"]["n"]
    assert len(fine["wood"]["d"]) < len(raw["wood"]["d"])


def test_the_generalisation_scales_with_the_box():
    """A ride's grid is coarser and its minimum blob larger than a run's."""
    run = geo._derived(BasemapStyle(), geo.scale_for(3200.0))
    ride = geo._derived(BasemapStyle(), geo.scale_for(13000.0))
    assert ride["cell_m"] > run["cell_m"]
    assert ride["min_area_ha"] > run["min_area_ha"]


def test_the_candidate_basemap_is_the_old_candidate_options():
    """The candidate export's basemap equals the options it drew with before the style groups."""
    assert dataclasses.asdict(geo.candidate_basemap()) == {
        "hillshade_mode": "off",
        "hillshade_levels": 5,
        "hillshade_opacity": 0.5,
        "hachure_spacing_m": 75.0,
        "hachure_min_slope": 0.035,
        "hachure_max_length_m": 90.0,
        "sea_style": "fill",
        "contour_interval": 50.0,
        "roads": "key",
        "rivers": "key",
        "interaction_m": 60.0,
        "interaction_run_m": 100.0,
        "landmarks": "all",
        "landmark_max": 80,
        "landmark_radius_m": 300.0,
        "pick_landmarks": (),
        "pick_roads": (),
        "pick_places": (),
        "generalise": False,
        "cell_m": 60.0,
        "morph_cells": 2,
        "min_area_ha": 4.0,
        "smooth_passes": 3,
        "blob_jitter_m": 22.0,
        "inset_cells": 2,
        "tree_spacing_m": 450.0,
        "all_variants": False,
    }
    assert geo.CANDIDATE_CLIP_MARGIN_M == 2600.0
