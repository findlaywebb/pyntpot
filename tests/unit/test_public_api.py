"""The top-level package and each layer package export exactly their public names."""

import importlib

import pytest

import pyntpot

PUBLIC: tuple[str, ...] = (
    "Track",
    "Basemap",
    "Style",
    "Plates",
    "Lettering",
    "Annotations",
    "fetch",
    "paint",
    "letter",
    "compose",
    "Sheet",
    "Brush",
    "Canvas",
    "stamp",
    "wash",
    "composite",
    "Hand",
    "__version__",
)

INK_PUBLIC: tuple[str, ...] = (
    "PIGMENTS",
    "TRANSPARENCY",
    "Brush",
    "BrushStyle",
    "Canvas",
    "PaperStyle",
    "PigmentLayer",
    "Sheet",
    "brush_from_id",
    "composite",
    "ink_density",
    "paper_plate",
    "rgb",
    "save_image",
    "stamp",
    "wash",
)

LETTERS_PUBLIC: tuple[str, ...] = (
    "FaceStyle",
    "Hand",
    "HandStyle",
    "Mark",
    "NibGroups",
    "NibStyle",
    "NibSurface",
    "Setting",
    "nib_plate",
)

MAPS_PUBLIC: tuple[str, ...] = (
    "Annotations",
    "Basemap",
    "Cache",
    "FetchError",
    "Lettering",
    "OpenTopoData",
    "OverpassFeatures",
    "Plates",
    "Style",
    "Track",
    "VectorLayers",
    "compose",
    "fetch",
    "letter",
    "paint",
    "vector_layers",
)

LAYERS: dict[str, tuple[str, ...]] = {
    "pyntpot.ink": INK_PUBLIC,
    "pyntpot.letters": LETTERS_PUBLIC,
    "pyntpot.maps": MAPS_PUBLIC,
}


def test_all_is_exactly_the_public_names() -> None:
    """`pyntpot.__all__` holds the pinned public names and no others."""
    assert set(pyntpot.__all__) == set(PUBLIC)
    assert len(pyntpot.__all__) == len(PUBLIC)


@pytest.mark.parametrize("name", PUBLIC, ids=PUBLIC)
def test_every_public_name_resolves(name: str) -> None:
    """Each public name is an attribute of the top-level package."""
    assert getattr(pyntpot, name) is not None


def test_version_is_a_dotted_release() -> None:
    """`__version__` is the installed distribution's dotted version string."""
    assert pyntpot.__version__.split(".")[0].isdigit()


def test_sheet_constructs_from_the_top_level() -> None:
    """`pyntpot.Sheet(64, 64, 8.0)` constructs a sheet."""
    assert pyntpot.Sheet(64, 64, 8.0) is not None


@pytest.mark.parametrize("module", LAYERS, ids=["ink", "letters", "maps"])
def test_each_layer_all_is_exactly_its_public_names(module: str) -> None:
    """Each layer package's `__all__` holds its pinned public names and no others."""
    package = importlib.import_module(module)
    assert set(package.__all__) == set(LAYERS[module])
    assert len(package.__all__) == len(LAYERS[module])


@pytest.mark.parametrize("module", LAYERS, ids=["ink", "letters", "maps"])
def test_every_layer_public_name_resolves(module: str) -> None:
    """Each pinned layer name is an attribute of its package."""
    package = importlib.import_module(module)
    for name in LAYERS[module]:
        assert getattr(package, name) is not None, name
