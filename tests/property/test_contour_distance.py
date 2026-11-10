"""Properties of `contour_distance`: it agrees with the exact distance outside the line, and its sign is exact."""

import numpy as np
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

from pyntpot.ink.effect_distance import contour_distance
from pyntpot.ink.noise import F32

from support.properties import UNTIMED

#: The widest error outside the line the distance claims, in pixels, for a threshold 0.2 to 0.5.
TOLERANCE = 0.4

#: The side of the test array, big enough for a margin of `radius + 2` round a disc of radius 12.
SIDE = 56


@st.composite
def shapes(draw: st.DrawFn) -> tuple[np.ndarray, np.ndarray, float, int]:
    """An anti-aliased half-plane or disc as a float32 mask, with its exact signed distance.

    Returns:
        The mask, the exact signed distance from each pixel to the contour at the drawn
        threshold (negative inside), the threshold and the radius.
    """
    tau = draw(st.floats(0.2, 0.5))
    radius = draw(st.integers(3, 8))
    yy, xx = np.mgrid[0:SIDE, 0:SIDE].astype(np.float64)
    if draw(st.booleans()):
        angle = draw(st.floats(0, 2 * np.pi))
        offset = draw(st.floats(-3, 3))
        s = (xx - SIDE / 2) * np.cos(angle) + (yy - SIDE / 2) * np.sin(angle) - offset
    else:
        r = draw(st.floats(3, 12))
        cx, cy = draw(st.floats(-0.5, 0.5)), draw(st.floats(-0.5, 0.5))
        s = np.hypot(xx - SIDE / 2 - cx, yy - SIDE / 2 - cy) - r
    mask = np.clip(0.5 - s, 0.0, 1.0).astype(F32)
    return mask, s - (0.5 - tau), tau, radius


class TestAgainstTheExactDistance:
    """Outside the line the distance is the geometry's, to a fraction of a pixel."""

    @UNTIMED
    @given(shape=shapes())
    def test_outside_the_line_it_is_within_tolerance_of_the_exact_distance(
        self, shape: tuple[np.ndarray, np.ndarray, float, int]
    ) -> None:
        """Every pixel the exact distance puts 0 to `radius` outside is within 0.4 px, clear of the array edge."""
        mask, exact, tau, radius = shape
        d = contour_distance(mask, threshold=tau, radius=radius)
        pick = (exact >= 0) & (exact <= radius)
        margin = radius + 2
        pick[:margin] = pick[-margin:] = False
        pick[:, :margin] = pick[:, -margin:] = False
        assert float(np.abs(d - exact)[pick].max(initial=0.0)) <= TOLERANCE

    @UNTIMED
    @given(shape=shapes())
    def test_the_result_is_float32_of_the_masks_shape(
        self, shape: tuple[np.ndarray, np.ndarray, float, int]
    ) -> None:
        """The distance is float32 and as large as the mask."""
        mask, _, tau, radius = shape
        d = contour_distance(mask, threshold=tau, radius=radius)
        assert (d.dtype, d.shape) == (F32, mask.shape)


class TestSign:
    """Inside the line the value is at most 0, outside at least 0, for any threshold."""

    @UNTIMED
    @given(
        mask=hnp.arrays(
            np.float32,
            st.tuples(st.integers(1, 24), st.integers(1, 24)),
            elements=st.floats(0, 1, width=32),
        ),
        tau=st.floats(0.01, 1),
        radius=st.floats(0.5, 6),
    )
    def test_the_sign_follows_the_threshold_bit_for_bit(
        self, mask: np.ndarray, tau: float, radius: float
    ) -> None:
        """No core pixel is positive and no other pixel is negative, and none is above the cap."""
        d = contour_distance(mask, threshold=tau, radius=radius)
        core = mask >= tau
        assert not (d[core] > 0).any()
        assert not (d[~core] < 0).any()
        assert d.max() <= F32(radius + 2)
