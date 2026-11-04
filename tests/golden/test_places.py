"""The focus-place fixtures each paint a card from their cache alone, with the names expected."""

import json
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

import pytest
from PIL import Image

from pyntpot.ink.polyline import meet
from pyntpot.maps import (
    Annotations,
    Basemap,
    Cache,
    FetchMargins,
    OpenTopoData,
    OverpassFeatures,
    Style,
    Track,
    compose,
    fetch,
    letter,
    paint,
)
from pyntpot.maps.cache import LANDCOVER_MARGIN_M, MARGIN_M
from pyntpot.maps.lettering.label import NO_LEADER, Label
from pyntpot.maps.lettering.placement_costs import RouteSegments, leader_route_crossings
from pyntpot.maps.lettering.placement_water import Water, on_water, water_from
from pyntpot.maps.rings import point_in_ring, signed_area

from support import REPO_ROOT
from support.paths import (
    AMBLESIDE_KEY,
    FIXTURES,
    OXFORD_KEY,
    SKYE_KEY,
    Y_FENNI_KEY,
    YR_WYDDFA_KEY,
)

pytestmark = pytest.mark.golden

#: The curated landmarks and journal notes of the showcase places, one table per fixture directory.
PLACES_TOML = REPO_ROOT / "examples" / "places.toml"

#: The share of a flat name's box a lake may graze at its padded edges.
LAKE_GRAZE = 0.05

#: The landmarks whose leader still crosses the route, per place. A leader across the track is
#: priced, not banned: each of these pins has the route or a road on every seat on its own
#: side, so its cheapest seat is over the track. Any other leader that crosses it fails.
#: Garnedd Ugain's pin is on the route where the spur to Yr Wyddfa leaves it, so every seat
#: west of it is across the spur. Shepherd's Ice Cream crossed a second strand of a retraced
#: leg, which is drawn as one stroke now, so its leader no longer crosses.
HEMMED_LEADERS = {
    "skye": {"Thursday: the Storr and a long Staffin lunch"},
    "y-fenni": {"Bean & Bread"},
    "yr-wyddfa": {"Garnedd Ugain"},
}

#: Villages either side of Kyle Akin that the Skye card paints as land: Kyleakin on Skye,
#: the rest on the mainland. Each is found by name among the payload's OSM place nodes.
SKYE_LAND = ("Kyle of Lochalsh", "Kyleakin", "Balmacara", "Plockton", "Dornie")

#: The loch whose OSM line, run down its water from Dornie to Kyle Akin, the card paints as sea.
SKYE_LOCH = "Loch Alsh"

#: How the providers name the caller; never sent, since no request is made.
CONTACT = "pyntpot-tests@example.invalid"


@dataclass(frozen=True)
class Place:
    """A focus-place fixture: its directory name, its cache key and the labels its card places."""

    directory: str
    key: str
    labels: list[str]
    #: A theme file under the repository root, or empty for the default style.
    theme: str = ""
    #: The fetch margins the fixture was recorded with, in metres.
    margin_m: float = MARGIN_M
    landcover_margin_m: float = LANDCOVER_MARGIN_M


#: Each place's labels are the names its style (the default unless `theme` is given) places, with
#: the curated landmarks and journal notes of `examples/places.toml`, pinned from the painting of
#: the recorded fixture at the style's own card width. The test compares the distinct names only:
#: how many times a long river is named, and in what order, can shift on a placement near-tie
#: between platforms (CI placed one "Cherwell" on Oxford where the recording machine placed two).
PLACES = (
    Place(
        "skye",
        SKYE_KEY,
        [
            "Monday: over the bridge, then Armadale",
            "Portree",
            "Sligachan",
            "Snizort",
            "The Cuillin",
            "Thursday: the Storr and a long Staffin lunch",
            "Tuesday: Dunvegan Castle and the Coral Beaches",
            "Wednesday: the Fairy Pools in the rain",
            "start",
            "finish",
        ],
        theme="examples/themes/skye.toml",
        margin_m=18000.0,
        landcover_margin_m=18000.0,
    ),
    Place(
        "ambleside",
        AMBLESIDE_KEY,
        [
            "A591",
            "Ambleside",
            "Brathay",
            "Bridge House",
            "Grasmere",
            "Loughrigg Fell",
            "Loughrigg Terrace",
            "Rothay",
            "Rydal",
            "Rydal Water",
            "start",
        ],
        theme="examples/themes/ambleside.toml",
    ),
    Place(
        "yr-wyddfa",
        YR_WYDDFA_KEY,
        [
            "A4086",
            "Afon Arddu",
            "Afon Nant Peris",
            "Crib Goch",
            "Garnedd Ugain",
            "Glaslyn",
            "Llyn Llydaw",
            "Yr Wyddfa",
            "start",
            "finish",
        ],
        theme="examples/themes/yr-wyddfa.toml",
        margin_m=3000.0,
        landcover_margin_m=3000.0,
    ),
    Place(
        "oxford",
        OXFORD_KEY,
        [
            "A4144",
            "A4158",
            "Cherwell",
            "Christ Church",
            "Magdalen Bridge",
            "Radcliffe Camera",
            "Thames",
            "The Bridge of Sighs",
            "start",
        ],
        theme="examples/themes/oxford.toml",
    ),
    Place(
        "y-fenni",
        Y_FENNI_KEY,
        [
            "A40",
            "Afon Wysg",
            "Angel Bakery",
            "Bean & Bread",
            "Castell y Fenni",
            "Gavenny River",
            "Rate of Rise",
            "Shepherd's Ice Cream",
            "Tŷ Melin",
            "Y Fenni",
            "start",
        ],
        theme="examples/themes/y-fenni.toml",
    ),
)


def curated(directory: str) -> Annotations | None:
    """The landmarks and journal notes `examples/places.toml` holds for a place, else `None`."""
    with PLACES_TOML.open("rb") as handle:
        entry = tomllib.load(handle).get(directory)
    if entry is None:
        return None
    return Annotations.model_validate(
        {"landmarks": entry.get("callouts", []), "notes": entry.get("notes", [])}
    )


@pytest.mark.parametrize("place", PLACES, ids=[p.directory for p in PLACES])
def test_a_focus_place_paints_from_its_cache_alone(place: Place, tmp_path: Path) -> None:
    """From a copy of the fixture, no request is made, the card paints and letters the pinned names clear."""
    cache_dir = tmp_path / "cache"
    shutil.copytree(FIXTURES / place.directory, cache_dir)
    features = OverpassFeatures(CONTACT, ("http://127.0.0.1:9/api/interpreter",), budget=0)
    elevation = OpenTopoData(CONTACT, "http://127.0.0.1:9", budget=0)
    track = Track.from_gpx(cache_dir / "track.gpx")
    cache = Cache(cache_dir, FetchMargins(place.margin_m, place.landcover_margin_m))
    style = Style.from_toml(REPO_ROOT / place.theme) if place.theme else Style.default()
    assert cache.key(track, features, elevation) == place.key
    before = sorted(p.name for p in cache_dir.iterdir())

    basemap = fetch(track, cache, features, elevation, style)
    plates = paint(basemap, style, cache.plates_dir(place.key))
    lettering = letter(plates, basemap, curated(place.directory), style)
    card = compose(plates, lettering, basemap, style)

    if place.margin_m != MARGIN_M:
        south, west, north, east = track.bounding_box(place.margin_m)
        (x0, y0), (x1, y1) = basemap.projection(south, west), basemap.projection(north, east)
        card_x0, card_y0, card_x1, card_y1 = basemap.card.box
        assert x0 <= card_x0 <= card_x1 <= x1
        assert y0 <= card_y0 <= card_y1 <= y1

    names = {label.name for label in lettering.labels}
    assert names == set(place.labels)
    _assert_clear(list(lettering.labels), water_from(basemap))
    crossing = {
        lb.name
        for lb in lettering.labels
        if lb.leader is not None
        and lb.kind not in NO_LEADER
        and leader_route_crossings(*lb.leader, RouteSegments.of(list(plates.strands)))
    }
    assert crossing == HEMMED_LEADERS.get(place.directory, set()), "a leader crosses the route"
    if place.directory == "skye":
        _assert_skye_sea(basemap, cache_dir / f"overpass-{place.key}.json")
    if place.directory == "y-fenni":
        assert {"Y Fenni", "Tŷ Melin", "Castell y Fenni"} <= names
        assert "Abergavenny" not in names
    assert sorted(p.name for p in cache_dir.iterdir() if p.name != "plates") == before
    card.save(tmp_path / "map.png")
    with Image.open(tmp_path / "map.png") as saved:
        assert saved.mode == "RGB"


def _assert_skye_sea(basemap: Basemap, payload: Path) -> None:
    """Both shores of Kyle Akin are land on the Skye card and the water between them is sea.

    The mainland's coast crosses the card's east edge; cut short of it, its land was sea.
    The places are read from the fixture's own OSM payload by name, so no coordinate is
    written here: the villages' place nodes, the vertices of Loch Alsh's line, and the
    point halfway between Kyleakin and Kyle of Lochalsh, in the narrows.
    """
    elements = json.loads(payload.read_text())["elements"]
    villages = {
        e["tags"]["name"]: (e["lat"], e["lon"])
        for e in elements
        if e["type"] == "node" and (e.get("tags") or {}).get("name") in SKYE_LAND
    }
    loch = next(
        e["geometry"]
        for e in elements
        if e["type"] == "way" and (e.get("tags") or {}).get("name") == SKYE_LOCH
    )
    sea = [list(ring) for ring in basemap.layers.sea]

    def is_sea(lat: float, lng: float) -> bool:
        """Whether the sea rings, filled by the nonzero rule, cover a place."""
        x, y = basemap.projection(lat, lng)
        winding = sum(
            1 if signed_area(ring) > 0 else -1 for ring in sea if point_in_ring(x, y, ring)
        )
        return winding != 0

    assert set(villages) == set(SKYE_LAND)
    for name, (lat, lng) in villages.items():
        assert not is_sea(lat, lng), f"{name} is painted as sea"
    for k, vertex in enumerate(loch):
        assert is_sea(vertex["lat"], vertex["lon"]), f"{SKYE_LOCH} vertex {k} is painted as land"
    (lat_a, lng_a), (lat_b, lng_b) = villages["Kyleakin"], villages["Kyle of Lochalsh"]
    assert is_sea((lat_a + lat_b) / 2, (lng_a + lng_b) / 2), "Kyle Akin is painted as land"


def _assert_clear(labels: list[Label], water: Water) -> None:
    """No two leaders on the card cross, and no flat name off the water sits on a lake."""
    leaders = [lb.leader for lb in labels if lb.leader is not None and lb.kind not in NO_LEADER]
    for i, (a0, a1) in enumerate(leaders):
        for b0, b1 in leaders[i + 1 :]:
            assert meet(a0, a1, b0, b1) is None, "two leaders cross"
    lakes = Water(water.lakes)
    for lb in labels:
        if lb.flat and not lb.in_water and lb.box is not None:
            # A box is half an em wider than its ink, so a lake may graze a corner of it
            # (Sligachan's, on Skye) without touching a letter.
            assert on_water(lb.box, lakes, 0.0) < LAKE_GRAZE, f"{lb.name} is lettered on a lake"
