"""Tests for the pigment stack: multiply stays multiply and glazing keeps hue."""

import numpy as np
import pytest

from pyntpot.ink.pigment import PIGMENTS, TRANSPARENCY, Layer, composite, km_plate, multiply_plate
from pyntpot.ink.sheet import rgb
from pyntpot.ink.style import PaperStyle
from pyntpot.ink.wash import wash

from support.washes import two_squares


def test_multiply_is_still_multiply_when_glazing_is_off():
    """The compositing path with the flag off is the arithmetic it replaced."""
    sheet, left, right = two_squares(80, 120)
    layers: list[Layer] = [
        (wash(left, sheet, 0.52, 0.20), rgb(PIGMENTS["farmland"]), 0.10),
        (wash(right, sheet, 0.72, 0.30), rgb(PIGMENTS["wood"])),
    ]
    base = np.ones((80, 120, 3), np.float32)
    assert np.array_equal(
        composite(layers, base, PaperStyle()),
        np.clip(base * multiply_plate(layers, 80, 120), 0, 1),
    )


def test_a_full_wash_over_white_gives_back_its_own_pigment():
    """The step that is easy to miss: S derived from Rw and Rb, or all goes black."""
    for key in ("wood", "water", "heath", "relief"):
        pig = rgb(PIGMENTS[key])
        thick = np.ones((2, 2), np.float32)
        out = km_plate([(thick, pig, TRANSPARENCY[key])], np.ones((2, 2, 3), np.float32))
        assert out[0, 0] == pytest.approx(pig, abs=2e-3), key
        # And nothing laid down is nothing changed.
        clear = km_plate(
            [(np.zeros((2, 2), np.float32), pig, 0.05)], np.ones((2, 2, 3), np.float32)
        )
        assert clear[0, 0] == pytest.approx([1.0, 1.0, 1.0], abs=1e-4)


def test_a_wash_crossing_another_keeps_its_own_hue_under_glazing():
    """Multiply averages two pigments into an olive; glazing does not."""

    def hue(c: np.ndarray) -> float:
        mx, mn = float(c.max()), float(c.min())
        if mx - mn < 1e-9:
            return 0.0
        r, g, b = (float(v) for v in c)
        i = int(np.argmax(c))
        turn = (
            ((g - b) / (mx - mn)) % 6
            if i == 0
            else (2 + (b - r) / (mx - mn))
            if i == 1
            else (4 + (r - g) / (mx - mn))
        )
        return turn * 60.0

    wood = rgb(PIGMENTS["wood"])
    water = rgb(PIGMENTS["water"])
    under = np.ones((4, 4), np.float32)
    over = np.full((4, 4), 0.6, np.float32)
    base = np.ones((4, 4, 3), np.float32)
    mul = multiply_plate([(under, water), (over, wood)], 4, 4)[0, 0]
    glazed = km_plate([(under, water, 0.04), (over, wood, 0.05)], base)[0, 0]
    # The wood is the top wash, so the crossing should read as wood over water,
    # not as the two colours multiplied into one another.
    assert abs(hue(glazed) - hue(wood)) < abs(hue(mul) - hue(wood)) - 5.0
