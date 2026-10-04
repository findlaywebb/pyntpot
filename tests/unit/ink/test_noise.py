"""Tests for the noise fields: the laid fibre has a direction."""

import numpy as np
import pytest

from pyntpot.ink.noise import fbm, fbm_aniso


def test_the_fibre_field_lies_along_one_axis():
    """Cold press has a direction: a fibre is about three times longer than wide."""
    rng = np.random.default_rng(1)
    iso = fbm(200, 300, 4.2, 3, np.random.default_rng(1))
    laid = fbm_aniso((200, 300), 4.2, 3, rng, 3.0, 0.42)

    def ratio(f: np.ndarray) -> float:
        return float(np.abs(np.diff(f, axis=0)).mean() / np.abs(np.diff(f, axis=1)).mean())

    assert ratio(iso) == pytest.approx(1.0, abs=0.06)
    assert ratio(laid) > 1.4
