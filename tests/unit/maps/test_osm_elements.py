"""`sort_element` names every element by the first tag the style's `name_tags` lists that it carries."""

from dataclasses import replace
from typing import Any

from pyntpot.maps.osm_elements import Harvest, Scope, sort_element
from pyntpot.maps.projection import Projection
from pyntpot.maps.style_groups import BasemapStyle
from pyntpot.maps.track_index import TrackIndex

#: Y Fenni, on the Wysg: the place and the river carry an English name and a Welsh one.
LAT, LNG = 51.8230, -3.0170
WELSH_FIRST = ("name:cy", "name")
BOTH = {"name": "Abergavenny", "name:cy": "Y Fenni"}
CLIP = (-5000.0, -5000.0, 5000.0, 5000.0)


def _scope(name_tags: tuple[str, ...]) -> Scope:
    """A scope over a short track, with every road and river kept and the given name tags."""
    proj = Projection(lat0=LAT, lat_ref=LAT, lng_ref=LNG)
    options = replace(BasemapStyle(), name_tags=name_tags, roads="all", rivers="all")
    derived = {
        "interaction_m": 60.0,
        "interaction_run_m": 100.0,
        "road_eps_m": 1.0,
        "river_eps_m": 1.0,
    }
    return Scope(proj, CLIP, TrackIndex([(0.0, 0.0), (100.0, 0.0)]), options, derived)


def _node(tags: dict[str, Any]) -> dict[str, Any]:
    """A place node at the origin carrying the tags."""
    return {"type": "node", "lat": LAT, "lon": LNG, "tags": {"place": "town", **tags}}


def _way(kind: str, value: str, tags: dict[str, Any]) -> dict[str, Any]:
    """A way of a few hundred metres, with its kind tag and the tags."""
    geometry = [{"lat": LAT + 0.0001, "lon": LNG + 0.0004 * i} for i in range(6)]
    return {"type": "way", "id": 1, "geometry": geometry, "tags": {kind: value, **tags}}


def _sorted(entry: dict[str, Any], name_tags: tuple[str, ...]) -> Harvest:
    """The harvest after sorting one element under the given name tags."""
    found = Harvest()
    sort_element(entry, _scope(name_tags), found)
    return found


def test_a_place_is_named_by_the_first_tag_the_style_lists() -> None:
    """A place with `name` and `name:cy` is Y Fenni under `("name:cy", "name")` and Abergavenny by default."""
    assert _sorted(_node(BOTH), WELSH_FIRST).candidates[0]["n"] == "Y Fenni"
    assert _sorted(_node(BOTH), BasemapStyle().name_tags).candidates[0]["n"] == "Abergavenny"


def test_an_element_without_the_preferred_tag_falls_back_to_name() -> None:
    """A place with only `name` keeps it under `("name:cy", "name")`, and one with neither stays unnamed."""
    assert _sorted(_node({"name": "Llanfoist"}), WELSH_FIRST).candidates[0]["n"] == "Llanfoist"
    assert _sorted(_node({}), WELSH_FIRST).candidates[0]["n"] == ""


def test_roads_and_rivers_are_named_by_the_same_rule() -> None:
    """A road and a river carrying a Welsh name are lettered with it, and by default with `name`."""
    river = _way("waterway", "river", {"name": "River Usk", "name:cy": "Afon Wysg"})
    road = _way("highway", "primary", {"name": "Merthyr Road", "name:cy": "Heol Merthyr"})
    assert _sorted(river, WELSH_FIRST).rivers[0]["n"] == "Afon Wysg"
    assert _sorted(river, ("name",)).rivers[0]["n"] == "River Usk"
    assert next(iter(_sorted(road, WELSH_FIRST).ways.values()))[0]["n"] == "Heol Merthyr"
    assert next(iter(_sorted(road, ("name",)).ways.values()))[0]["n"] == "Merthyr Road"


def test_minor_road_classes_without_service_drop_a_service_way() -> None:
    """With `roads = "all"`, a service way is kept by default and dropped once `service` is not listed."""
    service = _way("highway", "service", {"name": "Mill Lane"})
    track = _way("highway", "track", {"name": "Hill Track"})
    kept = _sorted(service, ("name",))
    assert list(kept.road_keep.values()) == [True]
    narrowed = replace(BasemapStyle(), roads="all", minor_road_classes=("track",))
    scope = _scope(("name",))
    scope = Scope(scope.proj, scope.clip, scope.index, narrowed, scope.derived)
    found = Harvest()
    sort_element(service, scope, found)
    sort_element(track, scope, found)
    assert found.road_keep == {("Mill Lane", "service"): False, ("Hill Track", "track"): True}
