"""The plates manifest: its JSON form, and the plates read back from disk."""

from pathlib import Path

import numpy as np

from pyntpot.maps.cache import Cache
from pyntpot.maps.card import Card
from pyntpot.maps.plates import DarkGrid, Manifest, Plates, dark_array

#: The cache key the test plates are written under.
KEY = "iMALHAM"

#: A manifest with every field set, written here rather than read from a golden file.
MANIFEST = Manifest(
    hash="5f1d0c9a7b3e2d41",
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
    wet_px={"major": 9.5, "minor": 2.4},
    gran_px=6.25,
    dark=DarkGrid(w=2, h=1, values=((0.125, 0.5),)),
    wood_px=321,
    water_px=654,
)

#: The bytes `MANIFEST.to_json` writes, pinned.
PINNED_JSON = (
    '{"hash":"5f1d0c9a7b3e2d41",'
    '"files":{"paper":"paper.webp","wash":"wash.webp","pen":"pen.webp"},'
    '"sizes":{"paper":1200,"wash":3400,"pen":560},"bytes":5160,'
    '"card":[-500.0,-300.0,700.0,600.0],"display":[120,90],"render":[240,180],'
    '"mpp":5.0,"mpp_display":10.0,"ribbon_m":180,"span_m":1100,'
    '"wet_px":{"major":9.5,"minor":2.4},"gran_px":6.25,'
    '"dark":{"w":2,"h":1,"v":[[0.125,0.5]]},"wood_px":321,"water_px":654}'
)


def _write_plates(cache_dir: Path, names: tuple[str, ...]) -> None:
    """Write the manifest and one placeholder file for each named plate."""
    root = Cache(cache_dir).plates_dir(KEY)
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
    cache = Cache(tmp_path)
    loaded = cache.load_plates(cache.plates_dir(KEY))
    assert loaded == Plates(cache.plates_dir(KEY), MANIFEST)


def test_load_plates_missing_a_plate_is_none(tmp_path: Path) -> None:
    """A manifest naming a plate no longer on disk reads as no plates."""
    _write_plates(tmp_path, ("paper", "wash"))
    cache = Cache(tmp_path)
    assert cache.load_plates(cache.plates_dir(KEY)) is None


class TestDarkArray:
    """`dark_array` is the one conversion of a darkness grid to a plate-sized array."""

    def test_no_grid_is_a_flat_middling_field(self) -> None:
        """No grid gives 0.35 everywhere at the requested shape."""
        out = dark_array(None, 4, 6)
        assert out.shape == (4, 6)
        assert np.all(out == np.float32(0.35))

    def test_a_grid_without_values_is_a_flat_middling_field(self) -> None:
        """A grid with empty values gives 0.35 everywhere at the requested shape."""
        out = dark_array(DarkGrid(w=0, h=0, values=()), 4, 6)
        assert out.shape == (4, 6)
        assert np.all(out == np.float32(0.35))

    def test_a_uniform_grid_resizes_to_the_same_value(self) -> None:
        """A uniform 2 by 2 grid of 0.5 resizes to 0.5 everywhere."""
        grid = DarkGrid(w=2, h=2, values=((0.5, 0.5), (0.5, 0.5)))
        out = dark_array(grid, 4, 6)
        assert out.shape == (4, 6)
        assert np.allclose(out, 0.5)
