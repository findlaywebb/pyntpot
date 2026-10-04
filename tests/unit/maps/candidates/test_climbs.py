"""Climbs: sustained rises ranked as candidates, and the distances they are stated in."""

import pytest

from pyntpot.maps.candidates.candidate import Candidate
from pyntpot.maps.candidates.climbs import (
    bearing,
    compass,
    cumulative,
    haversine,
    rank_climbs,
)
from pyntpot.maps.projection import track_projection
from pyntpot.maps.track import Track


def _climbs(ele: list[float], lng: float = -3.840) -> list[Candidate]:
    """The climbs of a track running due north from the Lynmouth box, one sample per `ele`."""
    lat = [51.225 + 4e-4 * i for i in range(len(ele))]
    track = Track(lat=tuple(lat), lng=(lng,) * len(ele), ele=tuple(ele))
    _, pts = track_projection(lat, [lng] * len(ele))
    return rank_climbs(track, tuple(pts))


class TestMeasures:
    """The great-circle measures a climb is stated in."""

    def test_a_hundredth_of_a_degree_of_longitude_is_about_seven_hundred_metres(self) -> None:
        """Haversine at 51.2250 degrees north: 0.01 degrees east is 696.37 m."""
        assert haversine(51.2250, -3.8400, 51.2250, -3.8300) == pytest.approx(696.3734628, abs=1e-6)

    @pytest.mark.parametrize(
        ("lat2", "lng2", "expected"),
        [(51.2350, -3.8400, 0.0), (51.2250, -3.8300, 89.9961019)],
        ids=["north", "east"],
    )
    def test_the_initial_bearing_is_clockwise_from_north(
        self, lat2: float, lng2: float, expected: float
    ) -> None:
        """Due north is 0 degrees and due east is about 90."""
        assert bearing(51.2250, -3.8400, lat2, lng2) == pytest.approx(expected, abs=1e-6)

    @pytest.mark.parametrize(
        ("degrees", "word"),
        [
            (0.0, "north"),
            (22.4, "north"),
            (22.5, "north-east"),
            (180.0, "south"),
            (315.0, "north-west"),
            (359.9, "north"),
        ],
        ids=["0", "just-under-the-first-edge", "the-first-edge", "180", "315", "359.9"],
    )
    def test_a_bearing_is_one_of_eight_words(self, degrees: float, word: str) -> None:
        """Each point of the compass owns 45 degrees, centred on its heading."""
        assert compass(degrees) == word

    def test_cumulative_distance_starts_at_zero(self) -> None:
        """The metres travelled at each point start at zero and add the haversine of each leg."""
        assert cumulative([51.2250, 51.2260, 51.2270], [-3.8400] * 3) == pytest.approx(
            [0.0, 111.1949266, 222.3898533], abs=1e-6
        )


class TestRankClimbs:
    """The rises of a track, felt span, ranked by metres gained."""

    def test_a_climb_is_a_rise_that_never_gives_back(self) -> None:
        """Eighty metres up, with no fifteen-metre drop on the way, is one climb."""
        found = _climbs([100.0 + 4.0 * i for i in range(20)] + [180.0 - 4.0 * i for i in range(20)])
        assert len(found) == 1
        climb = found[0]
        assert (climb.kind, climb.name, climb.rank, climb.span) == ("climb", "", 1, (0, 20))
        assert climb.detail["gain_m"] == 80
        assert climb.detail["start_km"] < climb.detail["end_km"]

    def test_a_climb_says_where_it_starts_on_the_track_and_on_the_card(self) -> None:
        """`at_m` is the metres travelled to the foot and `where` the card point there."""
        found = _climbs([100.0 + 4.0 * i for i in range(20)] + [180.0 - 4.0 * i for i in range(20)])
        assert found[0].at_m == 0.0
        assert found[0].where == (0.0, 0.0)

    def test_a_climb_row_is_pinned(self) -> None:
        """The row the export writes for a plain 80 m climb, to the key."""
        found = _climbs([100.0 + 4.0 * i for i in range(20)] + [180.0 - 4.0 * i for i in range(20)])
        assert found[0].detail == {
            "start_km": 0.0,
            "end_km": 0.89,
            "gain_m": 80,
            "length_km": 0.89,
            "avg_grade_pct": 9.0,
            "steepest_500m_pct": 9.0,
            "steepest_500m_km": 0.18,
            "bottom_ele_m": 100,
            "top_ele_m": 180,
            "approach_trimmed_km": 0.0,
            "runout_trimmed_km": 0.0,
            "share_of_climbing_pct": 100,
            "position_pct": 0,
            "heading": "north",
            "bearing_deg": 0,
            "start_lat": 51.225,
            "start_lng": -3.84,
            "end_lat": 51.233,
            "end_lng": -3.84,
            "rank_by_gain": 1,
            "rank_by_steepness": 1,
            "of_climbs": 1,
        }

    def test_a_bumpy_flat_is_not_a_climb(self) -> None:
        """Noise is not terrain: nothing under the threshold is offered as a climb."""
        assert _climbs([100.0 + (i % 4) for i in range(40)]) == []

    def test_a_track_without_elevation_has_no_climbs(self) -> None:
        """No elevation, no climbs: nothing is invented from the track alone."""
        lat = [51.225 + 4e-4 * i for i in range(40)]
        _, pts = track_projection(lat, [-3.840] * 40)
        track = Track(lat=tuple(lat), lng=(-3.840,) * 40)
        assert rank_climbs(track, tuple(pts)) == []

    def test_a_flat_run_in_is_not_part_of_the_climb(self) -> None:
        """A climb starts where the pitch does, not where the valley floor last ticked up."""
        ele = [100.0 + 0.05 * i for i in range(20)] + [101.0 + 5.0 * i for i in range(30)]
        found = _climbs(ele)
        assert len(found) == 1
        detail = found[0].detail
        assert detail["approach_trimmed_km"] > 0.8, "the flat run-in was kept"
        assert detail["start_km"] > 0.8
        assert detail["bottom_ele_m"] == 101
        assert detail["avg_grade_pct"] > 10
        assert detail["start_lat"] > 51.225 + 4e-4 * 10, "the pin is still down on the valley floor"

    def test_climbs_come_in_the_order_ridden_and_are_ranked_by_metres_gained(self) -> None:
        """A short climb then a long one: ridden order is kept, rank one is the bigger gain."""
        ele = (
            [100.0 + 4.0 * i for i in range(20)]
            + [180.0 - 4.0 * i for i in range(20)]
            + [100.0 + 6.0 * i for i in range(20)]
            + [220.0 - 6.0 * i for i in range(20)]
        )
        first, second = _climbs(ele)
        assert (first.rank, first.span, first.detail["gain_m"]) == (2, (0, 20), 80)
        assert (second.rank, second.span, second.detail["gain_m"]) == (1, (40, 60), 120)
        assert first.at_m is not None and second.at_m is not None
        assert first.at_m < second.at_m
        assert second.where == pytest.approx((0.0, 1768.64), abs=1e-6)
        assert (second.detail["rank_by_steepness"], second.detail["of_climbs"]) == (1, 2)
