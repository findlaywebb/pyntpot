"""Tests for the pigment stack: multiply stays multiply and glazing keeps hue."""

import numpy as np
import pytest

from pyntpot.ink.pigment import (
    PAINTERS_PIGMENTS,
    PAINTERS_TRANSPARENCY,
    PIGMENTS,
    TRANSPARENCY,
    PigmentLayer,
    composite,
    km_plate,
    km_rt,
    multiply_plate,
)
from pyntpot.ink.sheet import rgb
from pyntpot.ink.style import PaperStyle
from pyntpot.ink.wash import wash

from support.washes import two_squares


def test_multiply_is_still_multiply_when_glazing_is_off():
    """The compositing path with the flag off is the arithmetic it replaced."""
    sheet, left, right = two_squares(80, 120)
    layers: list[PigmentLayer] = [
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


class TestPaintersPigments:
    """The painter's pigments are a separate table beside the map-role one."""

    def test_the_two_tables_have_the_same_keys(self):
        """Every painter's pigment names a transparency and no transparency is orphaned."""
        assert PAINTERS_PIGMENTS.keys() == PAINTERS_TRANSPARENCY.keys()

    def test_the_keys_are_the_ten_painters_pigments(self):
        """The table holds exactly the ten pigments ADR 0039 names, in that order."""
        assert list(PAINTERS_PIGMENTS) == [
            "ultramarine",
            "cerulean",
            "burnt_sienna",
            "raw_sienna",
            "yellow_ochre",
            "sap_green",
            "indigo",
            "perylene_maroon",
            "quinacridone_rose",
            "paynes_grey",
        ]

    def test_every_transparency_is_a_share(self):
        """A transparency is a share of what the pigment shows over white, in 0 to 1."""
        assert all(0.0 <= t <= 1.0 for t in PAINTERS_TRANSPARENCY.values())

    @pytest.mark.parametrize("key", list(PAINTERS_PIGMENTS), ids=list(PAINTERS_PIGMENTS))
    def test_each_paints_a_dark_swatch(self, key: str):
        """A full wash of each painter's pigment, glazed over white, gives back its own dark masstone."""
        pig = rgb(PAINTERS_PIGMENTS[key])
        thick = np.ones((2, 2), np.float32)
        out = km_plate([(thick, pig, PAINTERS_TRANSPARENCY[key])], np.ones((2, 2, 3), np.float32))
        assert out[0, 0] == pytest.approx(pig, abs=2e-3), key
        assert out[0, 0].mean() < 0.55, key

    def test_the_map_role_tables_are_unchanged(self):
        """PIGMENTS and TRANSPARENCY keep their pinned values; the new table never touches them."""
        assert PIGMENTS == {
            "farmland": "#dfe0b0",
            "meadow": "#cfdfae",
            "orchard": "#d5dda2",
            "scrub": "#c9d5a4",
            "heath": "#e0cda2",
            "sand": "#ecdfbe",
            "rock": "#dcd6c6",
            "wetland": "#bfd2cd",
            "built": "#ddd3c3",
            "works": "#d2cbc0",
            "wood": "#a8c286",
            "pale": "#d5e0b4",
            "water": "#9ec4de",
            "relief": "#c9bda4",
            "rim": "#c2ad91",
        }
        assert TRANSPARENCY == {
            "farmland": 0.10,
            "meadow": 0.09,
            "orchard": 0.09,
            "scrub": 0.08,
            "heath": 0.14,
            "sand": 0.16,
            "rock": 0.22,
            "wetland": 0.08,
            "built": 0.26,
            "works": 0.28,
            "wood": 0.05,
            "pale": 0.12,
            "water": 0.04,
            "relief": 0.30,
            "rim": 0.18,
        }


class TestGlazingSkipsWhatIsNotPainted:
    """Glazing works only on painted pixels, so a pixel with no density keeps its exact bits."""

    @staticmethod
    def _base(h: int, w: int) -> np.ndarray:
        """A backing with every pixel different, so a moved bit shows."""
        return np.random.default_rng(7).random((h, w, 3), dtype=np.float32)

    def test_a_layer_of_no_density_leaves_the_base_bit_for_bit(self):
        """Zero density glazes to r = 0 and tr = 1 exactly, so the base comes back unchanged."""
        base = self._base(9, 13)
        out = km_plate([(np.zeros((9, 13), np.float32), rgb(PIGMENTS["wood"]), 0.05)], base)
        assert np.array_equal(out, np.clip(base, 0.0, 1.0))

    def test_a_patch_moves_only_its_own_pixels(self):
        """Outside a painted patch the base is untouched; inside it is the full-plate formula."""
        base = self._base(9, 13)
        dens = np.zeros((9, 13), np.float32)
        dens[2:5, 3:8] = np.linspace(0.1, 0.9, 15, dtype=np.float32).reshape(3, 5)
        pig = rgb(PIGMENTS["water"])
        out = km_plate([(dens, pig, 0.04)], base)

        r, tr = km_rt(dens, pig, 0.04)
        want = np.clip(r + tr * tr * base / np.maximum(1.0 - r * base, 1e-6), 0.0, 1.0)
        painted = dens > 0
        assert np.array_equal(out[~painted], np.clip(base, 0.0, 1.0)[~painted])
        assert np.array_equal(out[painted], want[painted])
