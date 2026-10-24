"""The focus-place fixtures each paint a card from their cache alone, with the names expected."""

import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest
from PIL import Image

from pyntpot.maps import (
    Cache,
    OpenTopoData,
    OverpassFeatures,
    Style,
    Track,
    compose,
    fetch,
    letter,
    paint,
)

from support import REPO_ROOT
from support.paths import (
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


#: Each place's labels are the names its style (the default unless `theme` is given) places, in placement order, pinned from
#: the first painting of the recorded fixture.
PLACES = (
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
            "Llanberis",
            "Nant Peris",
            "Afon Arddu",
            "Afon Nant Peris",
            "A4086",
            "Garnedd Ugain",
            "Yr Wyddfa",
            "Crib Goch",
            "start",
            "finish",
        ],
    ),
    Place(
        "oxford",
        OXFORD_KEY,
        [
            "Cherwell",
            "Cherwell",
            "Holywell Mill Stream",
            "A4158",
            "B480",
            "Tom Tower",
            "Christ Church",
            "Magdalen Tower",
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
            "Afon Wysg",
            "Gavenny River",
            "A40",
            "B4246",
            "United Reformed Church",
            "Methodist Church",
            "Borough Theatre",
            "start",
        ],
        theme="examples/themes/y-fenni.toml",
    ),
)


@pytest.mark.parametrize("place", PLACES, ids=[p.directory for p in PLACES])
def test_a_focus_place_paints_from_its_cache_alone(place: Place, tmp_path: Path) -> None:
    """From a copy of the fixture, no request is made, the card paints and its labels are the pinned names."""
    cache_dir = tmp_path / "cache"
    shutil.copytree(FIXTURES / place.directory, cache_dir)
    features = OverpassFeatures(CONTACT, ("http://127.0.0.1:9/api/interpreter",), budget=0)
    elevation = OpenTopoData(CONTACT, "http://127.0.0.1:9", budget=0)
    track = Track.from_gpx(cache_dir / "track.gpx")
    cache = Cache(cache_dir)
    style = Style.from_toml(REPO_ROOT / place.theme) if place.theme else Style.default()
    assert cache.key(track, features, elevation) == place.key
    before = sorted(p.name for p in cache_dir.iterdir())

    basemap = fetch(track, cache, features, elevation, style)
    plates = paint(basemap, style, cache.plates_dir(place.key))
    lettering = letter(plates, basemap, None, style)
    card = compose(plates, lettering, basemap, style)

    assert [label.name for label in lettering.labels] == place.labels
    if place.theme:
        assert "Y Fenni" in place.labels
        assert "Abergavenny" not in place.labels
    assert sorted(p.name for p in cache_dir.iterdir() if p.name != "plates") == before
    card.save(tmp_path / "map.png")
    with Image.open(tmp_path / "map.png") as saved:
        assert saved.mode == "RGB"
