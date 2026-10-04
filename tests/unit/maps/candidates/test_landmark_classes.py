"""What a set of OSM tags means as a landmark: its class, its height and its reach."""

import pytest

from pyntpot.maps.candidates.landmark_classes import (
    LANDMARK_CLASSES,
    LANDMARK_REACH_M,
    OFFERED_CLASSES,
    classify,
    height_m,
)


class TestClassify:
    """The class one tag set belongs to."""

    @pytest.mark.parametrize(
        ("tags", "cls"),
        [
            ({"tourism": "zoo"}, "attraction"),
            ({"amenity": "place_of_worship"}, "worship"),
            ({"building": "cathedral"}, "worship"),
            ({"bridge": "yes", "highway": "footway"}, "bridge"),
            ({"building": "stadium"}, "building"),
            ({"man_made": "tower", "height": "50"}, "tower"),
            ({"amenity": "cafe"}, "other"),
            ({"tourism": "artwork"}, "sculpture"),
            ({"artwork_type": "statue"}, "sculpture"),
            ({"natural": "peak"}, "summit"),
            ({"tourism": "viewpoint"}, "viewpoint"),
            ({"man_made": "lighthouse"}, "monument"),
            ({"historic": "wayside_cross"}, "monument"),
            ({"tourism": "gallery"}, "sight"),
            ({"building": "hospital"}, "block"),
            ({"historic": "ruins"}, "ruin"),
            ({"place": "village"}, "place"),
            ({}, "other"),
        ],
        ids=[
            "zoo",
            "place-of-worship",
            "cathedral",
            "bridge",
            "stadium",
            "tower",
            "cafe",
            "artwork",
            "artwork-type",
            "peak",
            "viewpoint",
            "lighthouse",
            "wayside-cross",
            "gallery",
            "hospital",
            "ruins",
            "village",
            "no-tags",
        ],
    )
    def test_a_tag_set_takes_the_class_its_tags_earn(self, tags: dict[str, str], cls: str) -> None:
        """Each class is reached through the tag that earns it, and nothing else is `other`."""
        assert classify(tags) == cls

    def test_the_first_matching_class_wins(self) -> None:
        """A church that is also a tower is a tower, and a viewpoint that is an artwork is art."""
        assert classify({"building": "tower", "amenity": "place_of_worship"}) == "tower"
        assert classify({"tourism": "artwork", "natural": "peak"}) == "sculpture"

    def test_a_plaque_is_not_a_monument(self) -> None:
        """A blue plaque carries the name of the wall it is on, so it names nothing.

        It is classed apart and stays readable; any other memorial is a monument.
        """
        assert classify({"historic": "memorial", "memorial": "plaque"}) == "plaque"
        assert classify({"historic": "memorial", "memorial": "blue_plaque"}) == "plaque"
        assert classify({"historic": "memorial", "memorial": "war_memorial"}) == "monument"
        assert classify({"historic": "memorial"}) == "monument"
        assert LANDMARK_CLASSES["plaque"] is False

    def test_every_class_it_returns_has_a_reach(self) -> None:
        """`classify` only ever answers with a key of the reach table."""
        answers = {
            classify(t) for t in ({"tourism": "zoo"}, {"place": "town"}, {}, {"natural": "peak"})
        }
        assert answers <= set(LANDMARK_REACH_M)


def test_a_place_a_plaque_and_an_unknown_are_never_offered() -> None:
    """The offered classes are the reach table less the three drawn or dropped by other rules."""
    assert OFFERED_CLASSES.isdisjoint({"place", "plaque", "other"})
    assert {"summit", "worship", "bridge"} <= OFFERED_CLASSES


class TestHeight:
    """How tall OSM says a thing is."""

    @pytest.mark.parametrize(
        ("tags", "metres"),
        [
            ({"height": "310 m"}, 310.0),
            ({"building:levels": "10"}, 32.0),
            ({"height": "100 ft"}, 30.48),
            ({}, 0.0),
            ({"height": "about"}, 0.0),
            ({"height": "."}, 0.0),
            ({"building:levels": "many"}, 0.0),
            ({"height": "about", "building:levels": "5"}, 16.0),
        ],
        ids=[
            "metres",
            "levels",
            "feet",
            "nothing",
            "words",
            "a-bare-dot",
            "words-levels",
            "fallback",
        ],
    )
    def test_height_is_read_from_metres_feet_and_levels(
        self, tags: dict[str, str], metres: float
    ) -> None:
        """A stated height wins, `building:levels` is the fallback, and nonsense is zero."""
        assert height_m(tags) == pytest.approx(metres)
