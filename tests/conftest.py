"""Pytest configuration: the golden options and the gates-off exemption hook."""

from pathlib import Path

import pytest

from support.exemptions import read_exemption_lines
from support.paths import GOLDEN_DIR


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register --golden-tolerance, which relaxes golden parity from exact to tolerant."""
    parser.addoption(
        "--golden-tolerance",
        action="store_true",
        default=False,
        help="compare golden plates within a tolerance instead of exactly",
    )
    parser.addoption(
        "--golden-dir",
        type=Path,
        default=GOLDEN_DIR,
        help="directory of golden outputs to compare against (default: the committed goldens)",
    )
    parser.addini(
        "personal_terms_file",
        help="path to the private banned-term list kept outside the repository",
        default="",
    )


@pytest.fixture
def golden_tolerance(request: pytest.FixtureRequest) -> bool:
    """Return whether golden comparisons run in tolerance mode."""
    return bool(request.config.getoption("--golden-tolerance"))


@pytest.fixture
def golden_dir(request: pytest.FixtureRequest) -> Path:
    """Return the directory of golden outputs the parity tests compare against."""
    return Path(request.config.getoption("--golden-dir")).resolve()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip every test whose node id is listed in exemptions/gates_off.txt."""
    switched_off = set(read_exemption_lines("gates_off.txt"))
    skip = pytest.mark.skip(reason="gate off, see exemptions")
    for item in items:
        if item.nodeid in switched_off:
            item.add_marker(skip)
