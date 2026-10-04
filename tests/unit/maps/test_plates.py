"""The plates manifest: its JSON form, and the plates read back from disk."""

from pathlib import Path

from pyntpot._port import paint
from pyntpot.maps.card import Card
from pyntpot.maps.plates import DarkGrid, Manifest, Plates

#: A manifest with every field set, written here rather than read from a golden file.
MANIFEST = Manifest(
    key="iMALHAM",
    hash="5f1d0c9a7b3e2d41",
    route0=(12.5, -40.25),
    files={"paper": "paper.webp", "wash": "wash.webp", "pen": "pen.webp"},
    sizes={"paper": 1200, "wash": 3400, "pen": 560},
    bytes=5160,
    card=Card(
        box=(-500.0, -300.0, 700.0, 600.0),
        display=(120, 90),
        render=(240, 180),
        mpp=5.0,
        mpp_display=10.0,
    ),
    ribbon_m=180,
    span_m=1100,
    places=({"n": "Settle", "x": 10.0, "y": 20.0, "sym": "house"},),
    candidates=(
        {"name": "Malham", "class": "place", "lat": 51.2312, "lng": -3.8301, "x": 5.0, "y": 6.0},
    ),
    label_geom={"roads": [{"n": "A591", "c": "major", "d": [[0.0, 1.5], [2.0, 3.0]]}]},
    wet_px={"major": 9.5, "minor": 2.4},
    gran_px=6.25,
    labels_hash="0a1b2c3d4e5f6071",
    sources=("osm", "srtm"),
    dark=DarkGrid(w=2, h=1, values=((0.125, 0.5),)),
    wood_px=321,
    water_px=654,
    timing={"water_ms": 3, "total_ms": 9},
)

#: The bytes `MANIFEST.to_json` writes, pinned.
PINNED_JSON = (
    '{"id":"iMALHAM","hash":"5f1d0c9a7b3e2d41","route0":[12.5,-40.25],'
    '"files":{"paper":"paper.webp","wash":"wash.webp","pen":"pen.webp"},'
    '"sizes":{"paper":1200,"wash":3400,"pen":560},"bytes":5160,'
    '"card":[-500.0,-300.0,700.0,600.0],"display":[120,90],"render":[240,180],'
    '"mpp":5.0,"mpp_display":10.0,"ribbon_m":180,"span_m":1100,'
    '"places":[{"n":"Settle","x":10.0,"y":20.0,"sym":"house"}],'
    '"candidates":[{"name":"Malham","class":"place","lat":51.2312,"lng":-3.8301,"x":5.0,"y":6.0}],'
    '"label_geom":{"roads":[{"n":"A591","c":"major","d":[[0.0,1.5],[2.0,3.0]]}]},'
    '"wet_px":{"major":9.5,"minor":2.4},"gran_px":6.25,"labels_hash":"0a1b2c3d4e5f6071",'
    '"sources":["osm","srtm"],"dark":{"w":2,"h":1,"v":[[0.125,0.5]]},'
    '"wood_px":321,"water_px":654,"timing":{"water_ms":3,"total_ms":9}}'
)


def _write_plates(cache_dir: Path, names: tuple[str, ...]) -> None:
    """Write the manifest and one placeholder file for each named plate."""
    root = paint.plates_dir(MANIFEST.key, cache_dir)
    root.mkdir(parents=True)
    (root / "plates.json").write_text(MANIFEST.to_json())
    for name in names:
        (root / MANIFEST.files[name]).write_bytes(b"\x00")


def test_to_json_writes_the_pinned_bytes() -> None:
    """The manifest is written in the fixed key order with the card as five frame keys."""
    assert MANIFEST.to_json() == PINNED_JSON


def test_from_json_round_trips_to_an_equal_manifest() -> None:
    """Reading back what `to_json` wrote gives an equal manifest and the same bytes."""
    back = Manifest.from_json(MANIFEST.to_json())
    assert back == MANIFEST
    assert back.to_json() == PINNED_JSON


def test_to_dict_is_the_parsed_json() -> None:
    """The plain mapping carries the card's frame keys at the top level."""
    record = MANIFEST.to_dict()
    assert record["render"] == [240, 180]
    assert record["dark"] == {"w": 2, "h": 1, "v": [[0.125, 0.5]]}
    assert "offset" not in record


def test_paths_name_every_plate_under_the_directory(tmp_path: Path) -> None:
    """Each plate in the manifest maps to its file in the plates directory."""
    plates = Plates(tmp_path, MANIFEST)
    assert list(plates.paths) == ["paper", "wash", "pen"]
    assert plates.paths["wash"] == tmp_path / "wash.webp"
    assert plates.hash == MANIFEST.hash
    assert plates.card == MANIFEST.card


def test_load_plates_reads_back_a_complete_set(tmp_path: Path) -> None:
    """A manifest whose plates are all on disk loads as those plates."""
    _write_plates(tmp_path, ("paper", "wash", "pen"))
    loaded = paint.load_plates(MANIFEST.key, tmp_path)
    assert loaded == Plates(paint.plates_dir(MANIFEST.key, tmp_path), MANIFEST)


def test_load_plates_missing_a_plate_is_none(tmp_path: Path) -> None:
    """A manifest naming a plate no longer on disk reads as no plates."""
    _write_plates(tmp_path, ("paper", "wash"))
    assert paint.load_plates(MANIFEST.key, tmp_path) is None
