"""The focus-place fixtures each paint a card from their cache alone, with the names expected."""

import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest
from PIL import Image

from pyntpot.maps import (
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

from support import REPO_ROOT
from support.paths import (
    AMBLESIDE_KEY,
    FIXTURES,
    KESWICK_KEY,
    OXFORD_KEY,
    TROTTERNISH_KEY,
    Y_FENNI_KEY,
    YR_WYDDFA_KEY,
)

pytestmark = pytest.mark.golden

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


#: Each place's labels are the names its style (the default unless `theme` is given) places, pinned
#: from the first painting of the recorded fixture. The test compares the distinct names only: how
#: many times a long river is named, and in what order, can shift on a placement near-tie between
#: platforms (CI placed one "Cherwell" on Oxford where the recording machine placed two).
PLACES = (
    Place(
        "ambleside",
        AMBLESIDE_KEY,
        [
            "Ambleside",
            "Rydal",
            "Rydal Bridge",
            "Rydal Road",
            "A591",
            "Rothay",
            "Brathay",
            "Hope Church",
            "start",
        ],
    ),
    Place(
        "keswick",
        KESWICK_KEY,
        [
            "Keswick",
            "Portinscale",
            "Crosthwaite",
            "Greta",
            "Greta",
            "Derwent",
            "A5271",
            "Lake Road Chapel",
            "The Retro Zone",
            "Derwent Bridge",
            "start",
        ],
    ),
    Place(
        "trotternish",
        TROTTERNISH_KEY,
        ["Brogaig", "The Prison", "Quiraing South Pinnacle", "Fir Bhreugach", "start"],
    ),
    Place(
        "yr-wyddfa",
        YR_WYDDFA_KEY,
        [
            "Afon Arddu",
            "Afon Nant Peris",
            "A4086",
            "Garnedd Ugain",
            "Yr Wyddfa",
            "Crib Goch",
            "start",
            "finish",
        ],
        margin_m=3000.0,
        landcover_margin_m=3000.0,
    ),
    Place(
        "oxford",
        OXFORD_KEY,
        [
            "Cherwell",
            "Thames",
            "A4144",
            "A4158",
            "High Street",
            "Magdalen Tower",
            "The Bridge of Sighs",
            "start",
        ],
    ),
    Place(
        "y-fenni",
        Y_FENNI_KEY,
        [
            "Y Fenni",
            "Llan-ffwyst",
            "Afon Wysg",
            "Gavenny River",
            "A40",
            "Abergavenny Baptist Church",
            "Methodist Church",
            "Borough Theatre",
            "start",
        ],
        theme="examples/themes/y-fenni.toml",
    ),
)


@pytest.mark.parametrize("place", PLACES, ids=[p.directory for p in PLACES])
def test_a_focus_place_paints_from_its_cache_alone(place: Place, tmp_path: Path) -> None:
    """From a copy of the fixture, no request is made, the card paints and it letters the pinned names."""
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
    lettering = letter(plates, basemap, None, style)
    card = compose(plates, lettering, basemap, style)

    if place.margin_m != MARGIN_M:
        south, west, north, east = track.bounding_box(place.margin_m)
        (x0, y0), (x1, y1) = basemap.projection(south, west), basemap.projection(north, east)
        card_x0, card_y0, card_x1, card_y1 = basemap.card.box
        assert x0 <= card_x0 <= card_x1 <= x1
        assert y0 <= card_y0 <= card_y1 <= y1

    names = {label.name for label in lettering.labels}
    assert names == set(place.labels)
    if place.theme:
        assert "Y Fenni" in names
        assert "Abergavenny" not in names
    assert sorted(p.name for p in cache_dir.iterdir() if p.name != "plates") == before
    card.save(tmp_path / "map.png")
    with Image.open(tmp_path / "map.png") as saved:
        assert saved.mode == "RGB"
