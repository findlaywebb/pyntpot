"""Pytest configuration: the golden options."""

from pathlib import Path

import pytest

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


@pytest.fixture
def golden_tolerance(request: pytest.FixtureRequest) -> bool:
    """Return whether golden comparisons run in tolerance mode."""
    return bool(request.config.getoption("--golden-tolerance"))


@pytest.fixture
def golden_dir(request: pytest.FixtureRequest) -> Path:
    """Return the directory of golden outputs the parity tests compare against."""
    return Path(request.config.getoption("--golden-dir")).resolve()
