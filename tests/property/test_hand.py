"""Properties of `Hand.write`: one seed writes one set of marks, flat or along a line."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pyntpot.letters.hand import Hand
from pyntpot.letters.setting import Setting
from pyntpot.letters.style import FaceStyle, HandStyle

from support.properties import UNTIMED

NAMES = st.sampled_from(("Grasmere", "Keswick", "Malham", "Bakewell", "Zennor", "Hawes"))
SIZES = st.floats(6, 30, allow_nan=False, allow_infinity=False)
SEEDS = st.integers(0, 2**31 - 1)
COORD = st.floats(10, 200, allow_nan=False, allow_infinity=False)
RUN = st.floats(4, 40, allow_nan=False, allow_infinity=False)
RISE = st.floats(-20, 20, allow_nan=False, allow_infinity=False)


@pytest.fixture(scope="module")
def hand() -> Hand:
    """The default hand, opened once: its face is loaded and never changes."""
    return Hand(FaceStyle(), HandStyle())


@st.composite
def settings_for(draw: st.DrawFn) -> Setting:
    """A name set from an anchor, or along a straight line of 2 to 5 points."""
    text, size = draw(NAMES), draw(SIZES)
    x, y = draw(COORD), draw(COORD)
    if draw(st.booleans()):
        return Setting(text, size, anchor=(x, y))
    dx, dy = draw(RUN), draw(RISE)
    path = tuple((x + i * dx, y + i * dy) for i in range(draw(st.integers(2, 5))))
    return Setting(text, size, path=path)


class TestWrite:
    """The hand's marks depend only on the setting and the generator's seed."""

    @UNTIMED
    @given(setting=settings_for(), seed=SEEDS)
    def test_the_same_seed_writes_the_same_marks(
        self, hand: Hand, setting: Setting, seed: int
    ) -> None:
        """Two generators from one seed write identical marks."""
        assert hand.write(setting, hand.generator(seed)) == hand.write(
            setting, hand.generator(seed)
        )
