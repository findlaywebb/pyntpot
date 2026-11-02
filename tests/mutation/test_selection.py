"""The mutation test selection: unit tests only from the packages mutmut mutates."""

import tomllib
from pathlib import PurePosixPath

from support import REPO_ROOT

MUTMUT = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["tool"]["mutmut"]
SELECTION = MUTMUT["pytest_add_cli_args_test_selection"]


def _mutated_packages() -> set[str]:
    """Return the subpackage names under `src/pyntpot` that `only_mutate` globs name."""
    return {PurePosixPath(glob).parts[2] for glob in MUTMUT["only_mutate"]}


def _unit_directories() -> set[str]:
    """Return the `tests/unit` subdirectories named in the test selection."""
    return {
        PurePosixPath(path).parts[2]
        for path in SELECTION
        if PurePosixPath(path).parts[:2] == ("tests", "unit")
        and len(PurePosixPath(path).parts) == 3
    }


def test_the_unit_tests_mirror_the_mutated_packages() -> None:
    """The selection's unit test directories are exactly the mutated subpackages' mirrors."""
    assert _unit_directories() == _mutated_packages()


def test_the_whole_unit_tree_is_not_selected() -> None:
    """The selection never names all of `tests/unit`, whose pipeline tests reach every layer."""
    assert "tests/unit" not in SELECTION


def test_every_selected_path_exists() -> None:
    """Every path in the selection exists, so a renamed test directory cannot drop out silently."""
    paths = [path for path in SELECTION if path.startswith("tests/")]
    assert paths
    for path in paths:
        assert (REPO_ROOT / path).exists(), path
