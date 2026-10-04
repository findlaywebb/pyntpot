"""Landmarks: the heuristic that picks what a map labels, and the ranking the export writes."""

from typing import Any

import pytest

from pyntpot.maps.candidates.landmarks import (
    landmark_rank,
    landmark_reach,
    pick_landmarks,
    rank_landmarks,
)
from pyntpot.maps.projection import track_projection

LATS = [51.2250 + 2e-5 * i for i in range(60)]
LNGS = [-3.8400 + 0.00040 * i for i in range(60)]


def _candidates() -> list[dict[str, Any]]:
    """A candidate list covering every class the heuristic sorts on."""
    return [
        {"n": "Dovedale", "cls": "sculpture", "d": 44.0, "x": 1.0, "y": 1.0},
        {"n": "Buxton Crescent", "cls": "sculpture", "d": 249.0, "x": 2.0, "y": 2.0},
        {"n": "Far sculpture", "cls": "sculpture", "d": 900.0, "x": 3.0, "y": 3.0},
        {"n": "Ben Macdui", "cls": "summit", "d": 120.0, "x": 4.0, "y": 4.0},
        {"n": "Ruined colliery", "cls": "ruin", "d": 20.0, "x": 5.0, "y": 5.0},
        {"n": "Bakewell", "cls": "place", "d": 5.0, "x": 6.0, "y": 6.0},
    ]


def _names(rows: list[dict[str, Any]]) -> list[str]:
    """The names of a list of candidate rows."""
    return [row["n"] for row in rows]


class TestPickLandmarks:
    """Which candidates the map labels."""

    def test_the_heuristic_keeps_what_a_runner_navigates_by_first(self) -> None:
        """Class decides the order, not distance: a hill outranks a nearer statue."""
        kept = pick_landmarks(_candidates(), radius_m=300.0, cap=8)
        assert _names(kept) == ["Ben Macdui", "Dovedale"]

    def test_a_sculpture_has_to_be_one_you_go_right_by(self) -> None:
        """A statue 249 m off the route is not a landmark, whatever the card's radius."""
        kept = pick_landmarks(_candidates(), radius_m=300.0, cap=8)
        assert "Buxton Crescent" not in _names(kept)

    def test_a_hill_is_kept_from_kilometres_away(self) -> None:
        """The reach is the thing's own: a summit is seen across the whole card."""
        far = [{"n": "Ben Macdui", "cls": "summit", "d": 2400.0, "x": 1.0, "y": 1.0}]
        assert _names(pick_landmarks(far, radius_m=300.0, cap=8)) == ["Ben Macdui"]

    def test_height_buys_reach(self) -> None:
        """An unusually tall building is notable from further off than a low one."""
        low = {"n": "Low block", "cls": "building", "d": 900.0, "x": 1.0, "y": 1.0}
        tall = {**low, "n": "The tower", "tags": {"height": "310 m"}}
        assert _names(pick_landmarks([low, tall], radius_m=300.0, cap=8)) == ["The tower"]

    def test_a_larger_radius_stretches_every_reach_together(self) -> None:
        """Ten times the radius keeps the statue 249 m off that 300 m left out."""
        kept = pick_landmarks(_candidates(), radius_m=3000.0, cap=8)
        assert "Buxton Crescent" in _names(kept)

    def test_a_village_is_never_a_landmark(self) -> None:
        """A place name is a label, not a landmark, however near the track it sat."""
        kept = pick_landmarks(_candidates(), radius_m=3000.0, cap=8)
        assert "Bakewell" not in _names(kept)
        assert "Ruined colliery" not in _names(kept)

    def test_the_cap_is_a_cap(self) -> None:
        """The heuristic keeps at most what it was asked for, most notable first."""
        kept = pick_landmarks(_candidates(), radius_m=3000.0, cap=2)
        assert _names(kept) == ["Ben Macdui", "Dovedale"]

    def test_all_keeps_every_named_thing_most_notable_first(self) -> None:
        """Mode `all` drops the class filter, so a village and a ruin are kept too."""
        kept = pick_landmarks(_candidates(), mode="all")
        assert _names(kept) == [
            "Ben Macdui",
            "Dovedale",
            "Buxton Crescent",
            "Far sculpture",
            "Bakewell",
            "Ruined colliery",
        ]

    def test_the_payload_replaces_the_heuristic(self) -> None:
        """A payload pick is drawn whether or not the rule would have chosen it."""
        kept = pick_landmarks(_candidates(), picks=("Bakewell", "Far sculpture"))
        assert set(_names(kept)) == {"Bakewell", "Far sculpture"}
        assert all(entry.get("picked") for entry in kept)

    def test_a_pick_the_box_does_not_hold_is_reported_not_dropped(self) -> None:
        """A name that is not there comes back marked, so the coach can see the miss."""
        kept = pick_landmarks(_candidates(), picks=("Dovedale", "Nowhere at all"))
        assert _names([e for e in kept if e.get("missing")]) == ["Nowhere at all"]


class TestReachAndRank:
    """How far off a thing is worth naming, and the order things are offered in."""

    @pytest.mark.parametrize(
        ("entry", "reach"),
        [
            ({"cls": "summit"}, 6000.0),
            ({"cls": "sculpture"}, 150.0),
            ({"class": "worship", "tags": {"height": "60"}}, 3600.0),
            ({"cls": "building", "tags": {"height": "310 m"}}, 8000.0),
            ({}, 150.0),
        ],
        ids=["summit", "sculpture", "tall-church", "capped", "unclassed"],
    )
    def test_reach_is_the_taller_of_the_class_and_the_height(
        self, entry: dict[str, Any], reach: float
    ) -> None:
        """A class sets a base reach, height at 60 m a metre can lift it, and 8 km caps it."""
        assert landmark_reach(entry) == reach

    def test_a_larger_scale_stretches_the_reach(self) -> None:
        """The scale multiplies the reach, so a card over more ground reaches further."""
        assert landmark_reach({"cls": "bridge"}, 2.0) == 500.0

    def test_the_rank_is_tier_then_comfort_and_a_missing_distance_is_last(self) -> None:
        """A tier one thing outranks tier two, and no distance ranks beyond any."""
        hill = landmark_rank({"cls": "summit", "d": 600.0})
        assert hill == (1, 0.1)
        assert landmark_rank({"cls": "monument", "d": 0.0}) == (2, 0.0)
        assert (
            landmark_rank({"cls": "monument"})[1] > landmark_rank({"cls": "monument", "d": 1e6})[1]
        )


class TestRankLandmarks:
    """The landmark rows the label step reads, as candidates."""

    @staticmethod
    def _entries() -> list[dict[str, Any]]:
        """Four things of the box, one unnamed and one with no position."""
        return [
            {"n": "Dovedale", "cls": "sculpture", "x": 100.0, "y": 80.0, "d": 44, "tags": {}},
            {"n": "Hollerday Hill", "cls": "summit", "x": 600.0, "y": 400.0, "d": 320, "tags": {}},
            {"n": "", "cls": "tower", "x": 10.0, "y": 10.0, "d": 3, "tags": {}},
            {"n": "Wind Hill", "cls": "summit", "x": None, "y": None, "d": 5, "tags": {}},
            {"n": "Lynton Toy Museum", "cls": "attraction", "x": 300.0, "y": 200.0, "d": 37},
        ]

    def test_candidates_come_most_notable_first_and_unplaced_things_are_left_out(self) -> None:
        """Tier one before tier two, the one sitting most comfortably inside its reach first; no name or position, no row."""
        proj, _ = track_projection(LATS, LNGS)
        ranked = rank_landmarks(self._entries(), proj)
        assert [(c.rank, c.name) for c in ranked] == [
            (1, "Hollerday Hill"),
            (2, "Lynton Toy Museum"),
            (3, "Dovedale"),
        ]

    def test_a_candidate_is_a_landmark_at_a_point_with_no_place_along_the_track(self) -> None:
        """`where` is the card point, and `at_m` and `span` are not stated for a landmark."""
        proj, _ = track_projection(LATS, LNGS)
        hill = rank_landmarks(self._entries(), proj)[0]
        assert (hill.kind, hill.where, hill.at_m, hill.span) == (
            "landmark",
            (600.0, 400.0),
            None,
            None,
        )

    def test_the_row_carries_position_both_ways_and_whether_it_is_notable(self) -> None:
        """A hill 320 m off is inside its 6 km reach; a statue 44 m off is inside 150 m."""
        proj, _ = track_projection(LATS, LNGS)
        by_name = {c.name: c.detail for c in rank_landmarks(self._entries(), proj)}
        hill = by_name["Hollerday Hill"]
        assert list(hill) == [
            "name",
            "class",
            "lat",
            "lng",
            "x",
            "y",
            "distance_m",
            "reach_m",
            "notable",
            "tags",
        ]
        assert (hill["class"], hill["distance_m"], hill["reach_m"], hill["notable"]) == (
            "summit",
            320,
            6000,
            True,
        )
        assert (hill["lat"], hill["lng"]) == pytest.approx((51.228619, -3.831394), abs=1e-6)

    def test_the_cap_keeps_the_most_notable(self) -> None:
        """Two of three kept are the first two of the ranking."""
        proj, _ = track_projection(LATS, LNGS)
        ranked = rank_landmarks(self._entries(), proj, cap=2)
        assert [c.name for c in ranked] == ["Hollerday Hill", "Lynton Toy Museum"]
