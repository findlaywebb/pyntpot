"""`contour_distance` to the last float32 bit: the one-pixel steps along each axis count."""

import numpy as np

from pyntpot.ink.effect_distance import contour_distance
from pyntpot.ink.noise import F32

# A pixel two steps from two seeds reaches the contour by a one-pixel step or a longer route;
# the routes differ by one float32 ulp, so only an exact comparison sees a skipped step.
_DOWN_STEP = np.array(
    [
        [1.0, 0.0, 1.0, 0.5, 0.5],
        [0.75, 0.25, 1.0, 0.0, 0.25],
        [0.25, 0.5, 0.5, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 0.0],
        [0.75, 0.75, 0.25, 0.25, 0.5],
    ],
    F32,
)
_RIGHT_STEP = np.array(
    [
        [0.0, 0.25, 0.0, 0.0, 0.25],
        [0.75, 0.5, 0.5, 0.0, 0.75],
        [0.75, 0.25, 0.0, 0.25, 0.0],
        [0.75, 0.5, 0.5, 0.25, 0.5],
        [1.0, 0.25, 0.75, 0.0, 0.25],
    ],
    F32,
)


class TestAxisStepsExact:
    """Each axis-aligned one-pixel step can set the last bit of a distance."""

    def test_the_downward_step_sets_the_last_bit(self) -> None:
        """Two pixels reach their contour by a step down, at 0.6666666 and not 0.6666667."""
        d = contour_distance(_DOWN_STEP, threshold=0.5, radius=2.0)
        assert d[3, 0] == F32(0.6666666)
        assert d[3, 1] == F32(0.6666666)

    def test_the_rightward_step_sets_the_last_bit(self) -> None:
        """One pixel reaches its contour by a step right, at 0.6666666 and not 0.6666667."""
        d = contour_distance(_RIGHT_STEP, threshold=0.5, radius=2.0)
        assert d[1, 3] == F32(0.6666666)
