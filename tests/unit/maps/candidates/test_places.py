"""Places the route ran past, and climbs grounded in them, in roads and in features."""

import pytest

from pyntpot.maps.candidates.climbs import rank_climbs
from pyntpot.maps.candidates.landmarks import rank_landmarks
from pyntpot.maps.candidates.places import ground_climbs, place_view, rank_places
from pyntpot.maps.candidates.roads import named_roads
from pyntpot.maps.track import Track

from .conftest import Lynmouth


def _hill(track: Track) -> Track:
    """The fixture track with a synthetic profile: 60 m up, a long descent, then 130 m up."""
    n = len(track.lat)
    ele = tuple(
        100.0 + (i * 0.4 if i < 150 else 60 - (i - 150) * 0.2 if i < 250 else 10 + (i - 250) * 0.5)
        for i in range(n)
    )
    return Track(lat=track.lat, lng=track.lng, ele=ele)


class TestRankPlaces:
    """The settlements the route came near, in the order it passed them."""

    def test_the_fixture_route_passes_five_settlements_in_order(self, lynmouth: Lynmouth) -> None:
        """Lynmouth, Lynbridge, Lynton, Barbrook and West Lyn, each with its off-route metres."""
        placed = rank_places(lynmouth.payload, lynmouth.projection, lynmouth.track, lynmouth.line)
        assert [
            (c.rank, c.name, c.detail["kind"], c.detail["km"], c.detail["off_route_m"])
            for c in placed
        ] == [
            (1, "Lynmouth", "village", 0.08, 71),
            (2, "Lynbridge", "village", 0.46, 695),
            (3, "Lynton", "town", 0.58, 29),
            (4, "Barbrook", "village", 3.72, 382),
            (5, "West Lyn", "hamlet", 4.77, 319),
        ]

    def test_a_place_carries_where_it_was_passed_and_where_it_is(self, lynmouth: Lynmouth) -> None:
        """`span` is the nearest sample twice, `at_m` the metres there and `where` the card point."""
        lynmouth_village = rank_places(
            lynmouth.payload, lynmouth.projection, lynmouth.track, lynmouth.line
        )[0]
        assert lynmouth_village.kind == "place"
        assert lynmouth_village.span == (4, 4)
        assert lynmouth_village.at_m == pytest.approx(79.8817, abs=1e-4)
        assert lynmouth_village.where == pytest.approx((1599.8009, 1738.3520), abs=1e-4)
        assert lynmouth_village.detail["lat"] == 51.229864
        assert lynmouth_village.detail["lng"] == -3.8290651

    def test_a_node_that_is_not_a_settlement_or_is_unnamed_is_left_out(
        self, lynmouth: Lynmouth
    ) -> None:
        """Only a city, town, village, hamlet or suburb with a name can be a place."""
        payload = {
            "elements": [
                {
                    "type": "node",
                    "lat": 51.2299,
                    "lon": -3.829,
                    "tags": {"place": "farm", "name": "Hillsford"},
                },
                {"type": "node", "lat": 51.2299, "lon": -3.829, "tags": {"place": "village"}},
            ]
        }
        assert rank_places(payload, lynmouth.projection, lynmouth.track, lynmouth.line) == []

    def test_a_settlement_further_than_seven_hundred_metres_off_is_left_out(
        self, lynmouth: Lynmouth
    ) -> None:
        """The route never went near it, so it cannot be what a climb is out of."""
        payload = {
            "elements": [
                {
                    "type": "node",
                    "lat": 51.2400,
                    "lon": -3.8400,
                    "tags": {"place": "village", "name": "Countisbury"},
                }
            ]
        }
        assert rank_places(payload, lynmouth.projection, lynmouth.track, lynmouth.line) == []


def test_a_place_view_keeps_only_the_keys_asked_for() -> None:
    """The default view is name, kind, kilometre and off-route metres, without coordinates."""
    row = {
        "name": "Lynton",
        "kind": "town",
        "km": 0.58,
        "off_route_m": 29,
        "lat": 51.2,
        "lng": -3.8,
    }
    assert place_view(row) == {"name": "Lynton", "kind": "town", "km": 0.58, "off_route_m": 29}
    assert place_view(row, ("name",)) == {"name": "Lynton"}


class TestGroundClimbs:
    """Climbs given the language a rider would use for them."""

    def test_a_climb_gains_its_grounds_beside_its_own_row(self, lynmouth: Lynmouth) -> None:
        """The first synthetic climb is out of Lynmouth, through two places, up to Barbrook."""
        track = _hill(lynmouth.track)
        climbs = rank_climbs(track, lynmouth.line)
        placed = rank_places(lynmouth.payload, lynmouth.projection, track, lynmouth.line)
        grounded = ground_climbs(climbs, placed, [], [], track, lynmouth.line)
        detail = grounded[0].detail
        assert detail["from"] == {
            "name": "Lynmouth",
            "kind": "village",
            "km": 0.08,
            "off_route_m": 71,
            "km_before_climb": -0.08,
        }
        assert [p["name"] for p in detail["through"]] == ["Lynbridge", "Lynton"]
        assert detail["to"]["name"] == "Barbrook"
        assert detail["to"]["km_after_top"] == 0.72
        assert [(n["name"], n["distance_m"], n["direction"]) for n in detail["near_start"]] == [
            ("Lynmouth", 100, "south-west"),
            ("Lynton", 579, "west"),
            ("Lynbridge", 949, "south-west"),
        ]
        assert detail["roads"] == []
        assert detail["features"] == []
        assert list(detail)[-7:] == [
            "from",
            "through",
            "to",
            "near_start",
            "near_top",
            "roads",
            "features",
        ]

    def test_grounding_returns_new_climbs_and_leaves_the_input_alone(
        self, lynmouth: Lynmouth
    ) -> None:
        """The climbs passed in keep their detail; the grounded ones are different objects."""
        track = _hill(lynmouth.track)
        climbs = rank_climbs(track, lynmouth.line)
        before = [dict(c.detail) for c in climbs]
        placed = rank_places(lynmouth.payload, lynmouth.projection, track, lynmouth.line)
        grounded = ground_climbs(climbs, placed, [], [], track, lynmouth.line)
        assert [dict(c.detail) for c in climbs] == before
        assert all("from" not in c.detail for c in climbs)
        assert all("from" in c.detail for c in grounded)
        assert [(g.rank, g.span, g.at_m) for g in grounded] == [
            (c.rank, c.span, c.at_m) for c in climbs
        ]

    def test_a_climb_names_the_roads_it_runs_on(self, lynmouth: Lynmouth) -> None:
        """The second synthetic climb runs along Watersmeet Road for 180 m; the first, no road."""
        track = _hill(lynmouth.track)
        roads = named_roads(lynmouth.payload, lynmouth.projection)
        grounded = ground_climbs(
            rank_climbs(track, lynmouth.line), [], [], roads, track, lynmouth.line
        )
        assert [c.detail["roads"] for c in grounded] == [
            [],
            [{"name": "Watersmeet Road", "metres": 180, "order": 4}],
        ]

    def test_a_climb_offers_the_named_features_beside_it_nearest_first(
        self, lynmouth: Lynmouth
    ) -> None:
        """Features within 600 m of the climb come nearest first; a place or a far one is left."""
        track = _hill(lynmouth.track)
        x, y = lynmouth.line[40]
        entries = [
            {"n": "Lynton and Exmoor Museum", "cls": "attraction", "x": x + 40.0, "y": y, "d": 40},
            {"n": "Saint Mary the Virgin", "cls": "worship", "x": x, "y": y + 30.0, "d": 30},
            {"n": "Lynton", "cls": "place", "x": x, "y": y + 5.0, "d": 5},
            {"n": "Hollerday Hill", "cls": "summit", "x": x + 5000.0, "y": y, "d": 5000},
        ]
        landmarks = rank_landmarks(entries, lynmouth.projection)
        grounded = ground_climbs(
            rank_climbs(track, lynmouth.line), [], landmarks, [], track, lynmouth.line
        )
        assert grounded[0].detail["features"] == [
            {"name": "Lynton and Exmoor Museum", "class": "attraction", "distance_m": 2},
            {"name": "Saint Mary the Virgin", "class": "worship", "distance_m": 30},
        ]

    def test_a_climb_with_nothing_to_ground_it_says_so_honestly(self, lynmouth: Lynmouth) -> None:
        """No places, roads or landmarks: `from` and `to` are `None` and the lists are empty."""
        track = _hill(lynmouth.track)
        grounded = ground_climbs(
            rank_climbs(track, lynmouth.line), [], [], [], track, lynmouth.line
        )
        detail = grounded[0].detail
        assert (detail["from"], detail["to"]) == (None, None)
        assert (detail["through"], detail["near_start"], detail["roads"], detail["features"]) == (
            [],
            [],
            [],
            [],
        )
