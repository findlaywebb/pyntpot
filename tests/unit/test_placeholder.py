"""Smoke test that the package imports under its own name."""

import pyntpot


def test_package_imports() -> None:
    """The package imports under its own name."""
    assert pyntpot.__name__ == "pyntpot"
