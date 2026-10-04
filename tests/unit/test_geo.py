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
    proj, _ = geo.track_projection(LATS, LNGS)
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
        geo.GeoOptions(roads=roads),
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
        geo.GeoOptions(roads="key"),
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
        geo.GeoOptions(roads="key"),
        cache_dir=_cache(tmp_path, elements),
        places=[],
    )
    assert len(data["roads"]) == 1


# ------------------------------------------------------------ one road, one stroke


def test_the_pieces_of_one_road_are_chained_into_one_stroke():
    """A street cut at its junctions is one line again before it is painted."""
    pieces = [[(0.0, 0.0), (10.0, 0.0)], [(20.0, 0.0), (30.0, 0.0)], [(10.0, 0.0), (20.0, 0.0)]]
    chains = geo.join_strokes(pieces, tol=1.0)
    assert len(chains) == 1
    assert chains[0][0] == (0.0, 0.0) and chains[0][-1] == (30.0, 0.0)


def test_a_piece_taken_from_the_middle_grows_out_to_both_ends():
    """Whichever piece the chain starts from, it reaches both ends of the road."""
    pieces = [[(10.0, 0.0), (20.0, 0.0)], [(0.0, 0.0), (10.0, 0.0)], [(20.0, 0.0), (30.0, 0.0)]]
    chain = geo.join_strokes(pieces, tol=1.0)[0]
    assert {chain[0], chain[-1]} == {(0.0, 0.0), (30.0, 0.0)}


def test_a_piece_is_reversed_where_that_is_how_it_joins():
    """OSM way direction is not the direction a road is drawn in."""
    pieces = [[(0.0, 0.0), (10.0, 0.0)], [(20.0, 0.0), (10.0, 0.0)]]
    chain = geo.join_strokes(pieces, tol=1.0)[0]
    assert len(chain) == 3
    assert {chain[0], chain[-1]} == {(0.0, 0.0), (20.0, 0.0)}


def test_a_chain_is_left_open():
    """A road is a line, not a ring: closing one draws a street that is not there."""
    ends = [[(0.0, 0.0), (10.0, 0.0)], [(10.0, 0.0), (10.0, 10.0)]]
    chain = geo.join_strokes(ends, tol=1.0)[0]
    assert chain[0] != chain[-1]


def test_pieces_that_do_not_meet_stay_apart():
    """A gap wider than the tolerance is a gap, not a join to make up."""
    apart = [[(0.0, 0.0), (10.0, 0.0)], [(40.0, 0.0), (50.0, 0.0)]]
    assert len(geo.join_strokes(apart, tol=1.0)) == 2


# ------------------------------------------------- how wide a river really is


def _channel(x0: float, x1: float, half: float) -> list[tuple[float, float]]:
    """A straight water area running east to west, `half * 2` metres wide."""
    return [(x0, -half), (x1, -half), (x1, half), (x0, half)]


def test_a_river_is_measured_against_the_water_it_runs_in():
    """OSM maps a big river twice: a line for where, a polygon for how wide."""
    line = [[(0.0, 0.0), (2000.0, 0.0)]]
    got = geo.measured_width_m(line, [_channel(-100.0, 2100.0, 120.0)])
    assert got == pytest.approx(240.0, abs=2.0)


def test_a_river_is_re_centred_in_its_own_channel():
    """OSM's line says where a river goes, not that it runs down the middle.

    The Wharfe's own line hugs the north bank for half its run, and a stroke
    a quarter of a kilometre wide centred on it overshoots one bank and falls short of the other.
    """
    off_centre = [(0.0, 60.0), (2000.0, 60.0)]
    pts, widths = geo.channel(off_centre, [_channel(-100.0, 2100.0, 120.0)])
    middle = pts[len(pts) // 2]
    assert middle[1] == pytest.approx(0.0, abs=2.0)
    assert widths[len(widths) // 2] == pytest.approx(240.0, abs=2.0)


def test_the_width_comes_from_both_banks():
    """Twice the nearest bank understates a river its line does not halve."""
    off_centre = [[(0.0, 60.0), (2000.0, 60.0)]]
    got = geo.measured_width_m(off_centre, [_channel(-100.0, 2100.0, 120.0)])
    assert got == pytest.approx(240.0, abs=2.0)


def test_the_correction_is_eased_rather_than_stepped():
    """A river slides into the middle of its channel; it does not jump."""
    line = [(0.0, 0.0), (3000.0, 0.0)]
    # A channel that steps sideways halfway along, so the middle moves with it.
    ring = [
        (-100.0, -120.0),
        (1500.0, -120.0),
        (1500.0, -20.0),
        (3100.0, -20.0),
        (3100.0, 220.0),
        (1500.0, 220.0),
        (1500.0, 120.0),
        (-100.0, 120.0),
    ]
    pts, _widths = geo.channel(line, [ring])
    steps = [abs(b[1] - a[1]) for a, b in zip(pts, pts[1:], strict=False)]
    assert max(steps) < 40.0, "the line steps sideways instead of easing"


def test_a_tributarys_mouth_is_not_its_width():
    """The Swale meets the Wharfe inside the Wharfe's own polygon.

    A river is as wide as the water it runs along, not as the water it runs
    into, so a short overlap buys no measurement at all.
    """
    mouth = [[(0.0, -400.0), (0.0, -20.0)]]
    assert geo.measured_width_m(mouth, [_channel(-500.0, 500.0, 120.0)]) is None


def test_a_watercourse_outside_every_area_is_not_measured():
    """A culvert has no banks to measure, and says so rather than guessing."""
    assert (
        geo.measured_width_m([[(0.0, 900.0), (2000.0, 900.0)]], [_channel(-100.0, 2100.0, 120.0)])
        is None
    )


def test_thin_water_is_exaggerated_up_to_the_floor():
    """A brook two metres across is not drawn two metres across."""
    assert geo.painted_width_px(4.69, 2.0, 7.533) == 4.69
    assert geo.painted_width_px(4.69, 0.0, 7.533) == 4.69


def test_wide_water_is_drawn_at_its_own_width():
    """The Wharfe is a quarter of a kilometre wide and is drawn as one."""
    assert geo.painted_width_px(10.83, 221.0, 7.533) == pytest.approx(29.34, abs=0.1)


def test_a_measured_river_is_never_exaggerated_further():
    """The floor is a floor, not a multiplier: nothing is added on top of it."""
    wide = geo.painted_width_px(10.83, 221.0, 7.533)
    assert wide == pytest.approx(221.0 / 7.533, abs=0.01)


def test_the_widest_water_is_the_main_river_not_the_longest():
    """A 4.8 km culvert does not outrank the Wharfe clipping a corner."""
    pieces = {
        "Wharfe": [[(0.0, 0.0), (2000.0, 0.0)]],
        "Swale": [[(500.0, 900.0), (500.0, 6000.0)]],
    }
    major, widths = geo.major_rivers(pieces, [_channel(-100.0, 2100.0, 120.0)], 0.65)
    assert major == {"Wharfe"}
    assert "Swale" not in widths


def test_the_longest_run_still_wins_where_nothing_is_mapped_as_an_area():
    """Away from a big river no watercourse has a polygon, and the old rule holds."""
    pieces = {
        "Tay": [[(0.0, 0.0), (6000.0, 0.0)]],
        "Teviot": [[(0.0, 500.0), (900.0, 500.0)]],
    }
    major, widths = geo.major_rivers(pieces, [], 0.65)
    assert major == {"Tay"}
    assert widths == {}


# ------------------------------------------------------- a river underground


def _river_names(tmp_path: Path, elements: list[dict]) -> set[str]:
    """The watercourses a box keeps."""
    data = geo.basemap(
        "iTEST",
        LATS,
        LNGS,
        geo.GeoOptions(rivers="all"),
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
        geo.GeoOptions(rivers="all"),
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
    data = geo.basemap(
        "iTEST", LATS, LNGS, geo.GeoOptions(rivers="key"), cache_dir=cache, places=[]
    )
    kept = {river["n"]: river["c"] for river in data["rivers"]}
    assert kept["The river"] == "river"
    assert "Brook beside the track" in kept
    assert "Brook a mile off" not in kept

    only = geo.basemap(
        "iTEST", LATS, LNGS, geo.GeoOptions(rivers="rivers"), cache_dir=cache, places=[]
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


def _candidates() -> list[dict]:
    """A candidate list covering every class the heuristic sorts on."""
    return [
        {"n": "Dovedale", "cls": "sculpture", "d": 44.0, "x": 1.0, "y": 1.0},
        {"n": "Buxton Crescent", "cls": "sculpture", "d": 249.0, "x": 2.0, "y": 2.0},
        {"n": "Far sculpture", "cls": "sculpture", "d": 900.0, "x": 3.0, "y": 3.0},
        {"n": "Ben Macdui", "cls": "summit", "d": 120.0, "x": 4.0, "y": 4.0},
        {"n": "Ruined colliery", "cls": "ruin", "d": 20.0, "x": 5.0, "y": 5.0},
        {"n": "Bakewell", "cls": "place", "d": 5.0, "x": 6.0, "y": 6.0},
    ]


def test_the_heuristic_keeps_what_a_runner_navigates_by_first():
    """Class decides the order, not distance: a hill outranks a nearer statue."""
    kept = geo.pick_landmarks(_candidates(), radius_m=300.0, cap=8)
    assert [entry["n"] for entry in kept] == ["Ben Macdui", "Dovedale"]


def test_a_sculpture_has_to_be_one_you_go_right_by():
    """A statue 249 m off the route is not a landmark, whatever the card's radius."""
    kept = geo.pick_landmarks(_candidates(), radius_m=300.0, cap=8)
    assert "Buxton Crescent" not in {entry["n"] for entry in kept}


def test_a_hill_is_kept_from_kilometres_away():
    """The reach is the thing's own: a summit is seen across the whole card."""
    kept = geo.pick_landmarks(
        [{"n": "Ben Macdui", "cls": "summit", "d": 2400.0, "x": 1.0, "y": 1.0}],
        radius_m=300.0,
        cap=8,
    )
    assert [entry["n"] for entry in kept] == ["Ben Macdui"]


def test_height_buys_reach():
    """An unusually tall building is notable from further off than a low one."""
    low = {"n": "Low block", "cls": "building", "d": 900.0, "x": 1.0, "y": 1.0}
    tall = {
        "n": "The tower",
        "cls": "building",
        "d": 900.0,
        "x": 2.0,
        "y": 2.0,
        "tags": {"height": "310 m"},
    }
    kept = geo.pick_landmarks([low, tall], radius_m=300.0, cap=8)
    assert [entry["n"] for entry in kept] == ["The tower"]


def test_height_is_read_from_levels_and_from_feet():
    """`building:levels` and an imperial height are both a statement of height."""
    assert geo.height_m({"height": "310 m"}) == 310.0
    assert geo.height_m({"building:levels": "10"}) == 32.0
    assert round(geo.height_m({"height": "100 ft"})) == 30
    assert geo.height_m({}) == 0.0
    assert geo.height_m({"height": "about"}) == 0.0


def test_a_zoo_a_church_and_a_bridge_are_landmarks():
    """The classes the old query could not even ask OSM for."""
    assert geo.classify({"tourism": "zoo"}) == "attraction"
    assert geo.classify({"amenity": "place_of_worship"}) == "worship"
    assert geo.classify({"building": "cathedral"}) == "worship"
    assert geo.classify({"bridge": "yes", "highway": "footway"}) == "bridge"
    assert geo.classify({"building": "stadium"}) == "building"
    assert geo.classify({"man_made": "tower", "height": "50"}) == "tower"
    assert geo.classify({"amenity": "cafe"}) == "other"


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


def test_a_village_is_never_a_landmark():
    """A place name is a label, not a landmark, however near the track it sat."""
    kept = geo.pick_landmarks(_candidates(), radius_m=3000.0, cap=8)
    assert "Bakewell" not in {entry["n"] for entry in kept}
    assert "Ruined colliery" not in {entry["n"] for entry in kept}


def test_the_cap_is_a_cap():
    """The heuristic keeps at most what it was asked for, most notable first."""
    kept = geo.pick_landmarks(_candidates(), radius_m=3000.0, cap=2)
    assert [entry["n"] for entry in kept] == ["Ben Macdui", "Dovedale"]


def test_the_payload_replaces_the_heuristic():
    """A payload pick is drawn whether or not the rule would have chosen it."""
    kept = geo.pick_landmarks(_candidates(), picks=("Bakewell", "Far sculpture"))
    assert {entry["n"] for entry in kept} == {"Bakewell", "Far sculpture"}
    assert all(entry.get("picked") for entry in kept)


def test_a_pick_the_box_does_not_hold_is_reported_not_dropped():
    """A name that is not there comes back marked, so the coach can see the miss."""
    kept = geo.pick_landmarks(_candidates(), picks=("Dovedale", "Nowhere at all"))
    missing = [entry for entry in kept if entry.get("missing")]
    assert [entry["n"] for entry in missing] == ["Nowhere at all"]


# --------------------------------------------------------------------------- places


def test_places_are_drawn_from_the_places_passed_in(tmp_path):
    """Home is a place the caller passes in, not a marker at a track's start."""
    places = [{"name": "Home", "symbol": "house", "lat": 51.2255, "lng": -3.8350}]
    data = geo.basemap("iTEST", LATS, LNGS, cache_dir=_cache(tmp_path, []), places=places)
    assert [(p["n"], p["sym"]) for p in data["places"]] == [("Home", "house")]


# --------------------------------------------------------------------------- geometry


def test_rings_are_wound_so_overlapping_fills_never_stack():
    """Two overlapping woods fill once: outer rings share a winding direction."""
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    overlap = [(5.0, 5.0), (15.0, 5.0), (15.0, 15.0), (5.0, 15.0)]
    assert geo.signed_area(geo.orient(square, True)) > 0
    assert geo.signed_area(geo.orient(list(reversed(overlap)), True)) > 0
    assert geo.signed_area(geo.orient(square, False)) < 0


def test_a_relation_split_across_ways_is_joined_into_one_ring():
    """The Ilkley Moor is one boundary cut into pieces; the pieces are chained."""
    rings = geo.join_ways(
        [
            [(0.0, 0.0), (10.0, 0.0)],
            [(10.0, 0.0), (10.0, 10.0)],
            [(10.0, 10.0), (0.0, 10.0), (0.0, 0.0)],
        ]
    )
    assert len(rings) == 1
    assert abs(geo.signed_area(rings[0])) == pytest.approx(200.0)


def test_a_polygon_bigger_than_the_sheet_is_clipped_not_dropped():
    """A wood that covers everything is cut to the box, which is what shades it."""
    huge = [(-5000.0, -5000.0), (5000.0, -5000.0), (5000.0, 5000.0), (-5000.0, 5000.0)]
    cut = geo.clip_ring(huge, (0.0, 0.0, 100.0, 50.0))
    assert abs(geo.signed_area(cut)) == pytest.approx(10000.0)


def test_the_sea_is_traced_where_the_grid_is_below_the_waterline():
    """Cells at or below zero become water; ground above it does not."""
    grid = [[-5.0 if col < 4 else 40.0 for col in range(10)] for _ in range(10)]
    lats = [51.20 + 2e-3 * i for i in range(10)]
    lons = [-3.87 + 2e-3 * i for i in range(10)]
    proj, _ = geo.track_projection([51.21, 51.22], [-3.86, -3.85])
    water, islands = geo.sea_rings(grid, lats, lons, proj)
    assert water and not islands
    assert geo.rings_path(water).startswith("M")


def test_dry_ground_has_no_sea():
    """A grid entirely above the waterline traces nothing."""
    grid = [[100.0] * 6 for _ in range(6)]
    lats = [51.225 + 2e-3 * i for i in range(6)]
    lons = [-3.840 + 2e-3 * i for i in range(6)]
    proj, _ = geo.track_projection(
        [
            51.225,
            51.235,
        ],
        [-3.840, -3.830],
    )
    assert geo.sea_rings(grid, lats, lons, proj) == ([], [])


# --------------------------------------------------------------------------- fallback


def test_generalisation_scales_with_the_box():
    """A ride's box is drawn coarser than a run's, rather than shrunk to fit."""
    assert geo.scale_for(3000.0) == 1.0
    assert geo.scale_for(12000.0) == pytest.approx(3.0)
    assert geo.scale_for(100000.0) == geo.MAX_SCALE
    run = geo._derived(geo.GeoOptions(), geo.scale_for(3200.0))
    ride = geo._derived(geo.GeoOptions(), geo.scale_for(13000.0))
    assert ride["road_eps_m"] > run["road_eps_m"]
    assert ride["landmark_radius_m"] > run["landmark_radius_m"]
    assert ride["landmark_cap"] >= run["landmark_cap"]


def test_hachures_leave_the_track_alone():
    """No stroke starts inside the buffer the track keeps clear."""
    grid = [[float(col * 30) for col in range(20)] for _ in range(20)]
    lats = [51.225 + 4e-4 * i for i in range(20)]
    lons = [-3.840 + 0.0006 * i for i in range(20)]
    proj, pts = geo.track_projection(LATS, LNGS)
    field = geo.Field(grid, lats, lons, proj)
    index = geo.TrackIndex(pts)
    clip = (
        min(x for x, _ in pts) - 200,
        min(y for _, y in pts) - 200,
        max(x for x, _ in pts) + 200,
        max(y for _, y in pts) + 200,
    )
    strokes = geo.hachures(field, clip, index, spacing_m=60.0, buffer_m=50.0)
    assert strokes
    for group in strokes:
        for chunk in group["d"].split("M")[1:]:
            x, y = (float(v) for v in chunk.split("l")[0].split(","))
            assert index.distance(x, y, cap_m=200.0) > 50.0


def test_the_png_encoder_writes_a_real_png():
    """The hillshade raster is a PNG, header and all, with no image library."""
    uri, width, height = geo.hillshade_png(
        [[float(r * c) for c in range(8)] for r in range(8)], 30.0, 30.0, upsample=1
    )
    assert uri.startswith("data:image/png;base64,")
    assert width == height == 8
    import base64

    assert base64.b64decode(uri.split(",", 1)[1])[:8] == b"\x89PNG\r\n\x1a\n"


def test_shade_bands_come_back_darkest_and_lightest_apart():
    """Bands are signed, so the page can paint shadow in ink and light in paper."""
    grid = [
        [200.0 - ((row - 6) ** 2 + (col - 6) ** 2) * 2.0 for col in range(12)] for row in range(12)
    ]
    lats = [51.225 + 4e-4 * i for i in range(12)]
    lons = [-3.840 + 0.0006 * i for i in range(12)]
    proj, _ = geo.track_projection(LATS, LNGS)
    bands = geo.shade_bands(grid, lats, lons, proj, 40.0, 40.0, levels=4)
    assert bands
    assert {band["s"] for band in bands} <= {-1, 1}
    assert all(band["d"].startswith("M") for band in bands)


def test_a_stroke_path_is_written_as_deltas():
    """Hachures ship as relative steps, which is what keeps the layer small."""
    d = geo.stroke_d([(100.0, 200.0), (110.0, 205.0), (118.0, 212.0)])
    assert d == "M100,200l10,5l8,7"


def test_marching_squares_finds_the_level_it_was_asked_for():
    """A ramp crossed at one level gives one line, not a field of fragments."""
    grid = [[float(col * 10) for col in range(10)] for _ in range(10)]
    lines = geo.marching_squares(grid, 45.0)
    assert len(lines) == 1
    assert all(abs(col - 4.5) < 1e-6 for col, _ in lines[0])


def test_the_track_index_measures_what_it_should():
    """A point on the track is at zero; one a field away is not."""
    proj, pts = geo.track_projection(LATS, LNGS)
    index = geo.TrackIndex(pts)
    assert index.distance(*pts[10]) == pytest.approx(0.0, abs=0.5)
    assert index.distance(pts[10][0], pts[10][1] + 500.0, cap_m=900.0) > 400.0


def test_interaction_needs_a_run_not_a_moment():
    """Passing within 60 m for one step is not an interaction; running alongside is."""
    proj, pts = geo.track_projection(LATS, LNGS)
    index = geo.TrackIndex(pts)
    alongside = [(x, y + 30.0) for x, y in pts[5:40]]
    glancing = [(pts[10][0], pts[10][1] + 40.0), (pts[10][0] + 10.0, pts[10][1] + 900.0)]
    assert index.interacts(alongside, 60.0, 100.0)
    assert not index.interacts(glancing, 60.0, 100.0)


def test_a_crossing_counts_even_though_it_is_brief():
    """A lane the track crossed is part of the session however short the contact."""
    proj, pts = geo.track_projection(LATS, LNGS)
    index = geo.TrackIndex(pts)
    x, y = pts[20]
    crossing = [(x, y - 400.0), (x, y + 400.0)]
    assert index.interacts(crossing, 60.0, 100.0)


def test_wave_strokes_only_appear_over_water():
    """The hand-drawn sea is drawn where the grid says there is sea, and nowhere else."""
    proj, _ = geo.track_projection(LATS, LNGS)
    dry = [[50.0] * 8 for _ in range(8)]
    lats = [51.225 + 1e-3 * i for i in range(8)]
    lons = [-3.840 + 1e-3 * i for i in range(8)]
    field = geo.Field(dry, lats, lons, proj)
    box = (0.0, 0.0, 400.0, 400.0)
    assert geo.wave_strokes(field, box) == ""
    wet = geo.Field([[-3.0] * 8 for _ in range(8)], lats, lons, proj)
    assert geo.wave_strokes(wet, box, spacing_m=100.0).count("M") >= 4


def test_the_sun_never_lights_a_flat_plain():
    """Flat ground carries no shade, so a flat sheet stays empty paper."""
    flat = [[100.0] * 6 for _ in range(6)]
    signal = geo._shade(flat, 30.0, 30.0, 315.0, 42.0, 1.4)
    assert all(abs(value) < 1e-6 for row in signal for value in row)


def test_distance_is_capped_so_a_far_feature_costs_nothing():
    """The index stops looking once a feature is clearly not near the track."""
    proj, pts = geo.track_projection(LATS, LNGS)
    index = geo.TrackIndex(pts)
    assert index.distance(pts[0][0], pts[0][1] + 100000.0, cap_m=250.0) == 250.0


def test_clip_line_splits_a_road_that_leaves_and_returns():
    """A road that leaves the sheet comes back as two pieces, not one long jump."""
    line = [(0.0, 0.0), (50.0, 0.0), (500.0, 0.0), (50.0, 50.0), (10.0, 50.0)]
    pieces = geo.clip_line(line, (0.0, 0.0, 100.0, 100.0))
    assert len(pieces) == 2
    assert math.dist(pieces[0][0], (0.0, 0.0)) < 1e-9


# --------------------------------------------------------------------------- generalise


def _square(x0: float, y0: float, side: float) -> list[tuple[float, float]]:
    """One axis-aligned square ring in metres."""
    return [(x0, y0), (x0 + side, y0), (x0 + side, y0 + side), (x0, y0 + side)]


CLIP = (0.0, 0.0, 1200.0, 1200.0)


def test_a_mask_is_the_union_of_its_rings():
    """Two overlapping woods rasterise to one shape, not to two stacked ones."""
    mask = geo.rasterise([_square(100, 100, 400), _square(300, 300, 400)], [], CLIP, 50.0)
    filled = sum(sum(row) for row in mask)
    assert filled > (400 / 50) ** 2
    assert filled < 2 * (400 / 50) ** 2


def test_a_hole_is_cut_out_of_the_mask():
    """A ring passed as a hole erases what it covers."""
    solid = geo.rasterise([_square(100, 100, 600)], [], CLIP, 50.0)
    holed = geo.rasterise([_square(100, 100, 600)], [_square(250, 250, 200)], CLIP, 50.0)
    assert sum(sum(r) for r in holed) < sum(sum(r) for r in solid)


def test_declutter_drops_a_speck_and_fills_a_pinhole():
    """A wood too small to matter goes, and so does a clearing too small to matter."""
    mask = geo.rasterise(
        [_square(100, 100, 500), _square(1000, 1000, 80)], [_square(300, 300, 80)], CLIP, 50.0
    )
    assert len(geo._components(mask, 1)) == 2
    inner = [
        b
        for b in geo._components(mask, 0)
        if all(0 < r < len(mask) - 1 and 0 < c < len(mask[0]) - 1 for r, c in b)
    ]
    assert inner, "the fixture is meant to carry a pinhole"
    cleaned = geo.declutter(mask, min_cells=8)
    assert len(geo._components(cleaned, 1)) == 1
    assert not [
        b
        for b in geo._components(cleaned, 0)
        if all(0 < r < len(cleaned) - 1 and 0 < c < len(cleaned[0]) - 1 for r, c in b)
    ]


def test_the_close_joins_two_woods_a_field_apart():
    """Closing is what turns a scatter of inclosures into one forest."""
    apart = geo.rasterise([_square(100, 100, 300), _square(460, 100, 300)], [], CLIP, 50.0)
    assert len(geo._components(apart, 1)) == 2
    closed = geo._spread(geo._spread(apart, 2, grow=True), 2, grow=False)
    assert len(geo._components(closed, 1)) == 1


def test_generalise_returns_few_big_smooth_shapes():
    """The whole point: many intricate rings in, a handful of smooth ones out."""
    rings = [_square(100 + 60 * i, 100 + 40 * i, 220) for i in range(8)]
    rings += [_square(1100, 20, 30)]
    out = geo.generalise(rings, [], CLIP, cell=50.0, morph_cells=2, min_area_ha=4.0, passes=3)
    assert 1 <= len(out) <= 2
    assert all(len(ring) > 6 for ring in out)


def test_generalise_of_nothing_is_nothing():
    """An empty layer stays empty rather than becoming a full-sheet blob."""
    assert geo.generalise([], [], CLIP, cell=50.0) == []


def test_the_generalised_wood_is_smaller_and_simpler():
    """On the Lynmouth box the generalised layer loses rings and bytes."""
    lat, lng = geo.read_gpx(FIXTURE_DIR / "track.gpx")
    options = {"cache_dir": FIXTURE_DIR, "places": []}
    raw = geo.basemap(KEY, lat, lng, geo.GeoOptions(generalise=False), **options)
    fine = geo.basemap(KEY, lat, lng, geo.GeoOptions(generalise=True), **options)
    assert fine["wood"]["n"] < raw["wood"]["n"]
    assert len(fine["wood"]["d"]) < len(raw["wood"]["d"])


def test_the_generalisation_scales_with_the_box():
    """A ride's grid is coarser and its minimum blob larger than a run's."""
    run = geo._derived(geo.GeoOptions(), geo.scale_for(3200.0))
    ride = geo._derived(geo.GeoOptions(), geo.scale_for(13000.0))
    assert ride["cell_m"] > run["cell_m"]
    assert ride["min_area_ha"] > run["min_area_ha"]


def test_resolved_geo_options_have_the_type_of_the_default_in_every_field():
    """A JSON round trip keeps tuples as tuples in every option."""
    resolved = json.loads(json.dumps(dataclasses.asdict(geo.GeoOptions())))
    rebuilt = geo.GeoOptions.from_resolved(resolved)
    default = geo.GeoOptions()
    for field in dataclasses.fields(geo.GeoOptions):
        got = getattr(rebuilt, field.name)
        want = getattr(default, field.name)
        assert type(got) is type(want), field.name
    assert rebuilt == default


def test_resolved_geo_options_refuse_an_unknown_field():
    """An option the dataclass does not have is named, not silently dropped."""
    with pytest.raises(ValueError, match="nonsense"):
        geo.GeoOptions.from_resolved({"nonsense": 1})
