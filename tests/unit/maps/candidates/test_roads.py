"""Named roads from the raw payload, and the roads a stretch of track runs along."""

from typing import Any

import pytest

from pyntpot.maps.candidates.climbs import cumulative
from pyntpot.maps.candidates.roads import named_roads, rank_roads
from pyntpot.maps.projection import track_projection

from .conftest import Lynmouth

#: A short track due north from the Lynmouth box's south-west corner, one sample every 44 m.
LATS = [51.2250 + 4e-4 * i for i in range(40)]
LNGS = [-3.8400] * 40


def _way(tags: dict[str, str], coords: list[tuple[float, float]]) -> dict[str, Any]:
    """One Overpass way with its geometry."""
    return {
        "type": "way",
        "tags": tags,
        "geometry": [{"lat": lat, "lon": lng} for lat, lng in coords],
    }


def _alongside(first: int, last: int) -> list[tuple[float, float]]:
    """A line two metres east of the track between two samples."""
    return [(LATS[i], LNGS[i] + 3e-5) for i in range(first, last + 1)]


class TestNamedRoads:
    """Which ways of a payload are roads with something to call them."""

    def test_a_road_is_named_by_its_name_or_failing_that_its_number(self) -> None:
        """A way with a name keeps it, and one with only a `ref` is called by the number."""
        proj, _ = track_projection(LATS, LNGS)
        payload = {
            "elements": [
                _way(
                    {"highway": "primary", "name": "Lynmouth Hill", "ref": "A39"}, _alongside(0, 5)
                ),
                _way({"highway": "secondary", "ref": "B3234"}, _alongside(5, 10)),
            ]
        }
        roads = named_roads(payload, proj)
        assert [(r["name"], r["ref"], r["kind"]) for r in roads] == [
            ("Lynmouth Hill", "A39", "primary"),
            ("B3234", "B3234", "secondary"),
        ]

    @pytest.mark.parametrize(
        "way",
        [
            _way({"name": "Lee Abbey"}, _alongside(0, 5)),
            _way({"highway": "track"}, _alongside(0, 5)),
            _way({"highway": "footway", "name": "Hollerday Hill"}, _alongside(0, 0)),
        ],
        ids=["not-a-highway", "no-name-or-number", "one-point"],
    )
    def test_a_way_with_nothing_to_call_it_by_is_left_out(self, way: dict[str, Any]) -> None:
        """No highway tag, no name or number, or fewer than two points: not a named road."""
        proj, _ = track_projection(LATS, LNGS)
        assert named_roads({"elements": [way]}, proj) == []

    def test_the_fixture_holds_named_roads_projected_into_card_metres(
        self, lynmouth: Lynmouth
    ) -> None:
        """The cached payload yields 164 named roads, the A39 first, each point a pair."""
        roads = named_roads(lynmouth.payload, lynmouth.projection)
        assert len(roads) == 164
        assert (roads[0]["name"], roads[0]["kind"], len(roads[0]["pts"])) == ("A39", "primary", 5)


class TestRankRoads:
    """The ranking of the roads one stretch of track runs along."""

    def test_the_longest_run_is_first_and_each_names_its_stretch(self) -> None:
        """Two roads beside the track rank by metres run, and carry the span asked about."""
        proj, pts = track_projection(LATS, LNGS)
        payload = {
            "elements": [
                _way({"highway": "residential", "name": "Lydiate Lane"}, _alongside(0, 14)),
                _way({"highway": "primary", "name": "Station Hill"}, _alongside(14, 39)),
            ]
        }
        dist = cumulative(LATS, LNGS)
        ranked = rank_roads(named_roads(payload, proj), tuple(pts), dist, (0, 39))
        assert [(c.rank, c.name, c.detail["order"]) for c in ranked] == [
            (1, "Station Hill", 2),
            (2, "Lydiate Lane", 1),
        ]
        assert all(c.kind == "road" and c.span == (0, 39) for c in ranked)
        assert all(c.at_m is None and c.where is None for c in ranked)

    def test_a_road_run_for_less_than_a_hundred_metres_is_dropped(self) -> None:
        """A road the track only brushes is not worth a number."""
        proj, pts = track_projection(LATS, LNGS)
        payload = {"elements": [_way({"highway": "track", "name": "Tors Park"}, _alongside(0, 1))]}
        dist = cumulative(LATS, LNGS)
        assert rank_roads(named_roads(payload, proj), tuple(pts), dist, (0, 39)) == []

    def test_no_roads_is_no_candidates(self) -> None:
        """An empty road list ranks nothing."""
        _, pts = track_projection(LATS, LNGS)
        assert rank_roads([], tuple(pts), cumulative(LATS, LNGS), (0, 39)) == []

    def test_the_fixture_stretch_runs_along_five_named_roads(self, lynmouth: Lynmouth) -> None:
        """The whole fixture track runs along the A39 for 300 m, then four shorter roads."""
        roads = named_roads(lynmouth.payload, lynmouth.projection)
        dist = cumulative(lynmouth.track.lat, lynmouth.track.lng)
        ranked = rank_roads(roads, lynmouth.line, dist, (0, len(lynmouth.line) - 1))
        assert [(c.rank, c.name, c.detail["metres"], c.detail["order"]) for c in ranked] == [
            (1, "A39", 300, 9),
            (2, "Watersmeet Road", 180, 11),
            (3, "Barbrook Road", 120, 7),
            (4, "Tors Park", 120, 13),
            (5, "West Lyn Road", 120, 8),
        ]
