"""The top-level package exports exactly the public names."""

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
