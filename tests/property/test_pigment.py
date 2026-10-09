"""Properties of `composite`: a plate stays in range, no layers is a clip, multiply never lightens."""

import dataclasses

import numpy as np
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

from pyntpot.ink.pigment import PigmentLayer, composite
from pyntpot.ink.style import PaperStyle

from support.properties import UNTIMED

UNIT32 = st.floats(0, 1, width=32)
UNIT = st.floats(0, 1, allow_nan=False, allow_infinity=False)


@st.composite
def plates(draw: st.DrawFn) -> tuple[np.ndarray, list[PigmentLayer]]:
    """A float32 base in [0, 1] and 0 to 4 layers over it."""
    h, w = draw(st.integers(1, 16)), draw(st.integers(1, 16))
    base = draw(hnp.arrays(np.float32, (h, w, 3), elements=UNIT32))
    layers: list[PigmentLayer] = []
    for _ in range(draw(st.integers(0, 4))):
        density = draw(st.none() | hnp.arrays(np.float32, (h, w), elements=UNIT32))
        pigment = draw(hnp.arrays(np.float32, (3,), elements=UNIT32))
        if draw(st.booleans()):
            layers.append((density, pigment, draw(UNIT)))
        else:
            layers.append((density, pigment))
    return base, layers


def _style(glazing: bool) -> PaperStyle:
    """The default paper with Kubelka-Munk glazing on or off."""
    return dataclasses.replace(PaperStyle(), km_glazing=glazing)


class TestComposite:
    """Both compositing modes over a float32 backing."""

    @UNTIMED
    @given(plate=plates(), glazing=st.booleans())
    def test_the_output_is_in_range(
        self, plate: tuple[np.ndarray, list[PigmentLayer]], glazing: bool
    ) -> None:
        """Every channel of the composite lies in [0, 1]."""
        base, layers = plate
        out = composite(layers, base, _style(glazing))
        assert out.min() >= 0.0
        assert out.max() <= 1.0

    @UNTIMED
    @given(plate=plates(), glazing=st.booleans())
    def test_no_layers_is_the_clipped_base(
        self, plate: tuple[np.ndarray, list[PigmentLayer]], glazing: bool
    ) -> None:
        """With nothing laid down the composite is the base clipped to [0, 1]."""
        base, _ = plate
        assert np.array_equal(composite([], base, _style(glazing)), np.clip(base, 0, 1))

    @UNTIMED
    @given(plate=plates())
    def test_multiply_never_lightens(self, plate: tuple[np.ndarray, list[PigmentLayer]]) -> None:
        """Without glazing no channel ends lighter than the base."""
        base, layers = plate
        assert np.all(composite(layers, base, _style(False)) <= base + 1e-6)
