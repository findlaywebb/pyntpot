"""`pool_band`, `lay_reserve` and the reserve's tie at the threshold, at pinned values."""

import numpy as np
import pytest

from pyntpot.ink.effect_reserve import lay_reserve, pool_band, reserve
from pyntpot.ink.effect_types import Reserve
from pyntpot.ink.noise import F32


class TestPoolBand:
    """The pool's tent from half a pixel inside the ring to 1.5 pixels past it."""

    @pytest.mark.parametrize(
        ("excess", "expected"),
        [
            (-2.0, 0.0),
            (-1.0, 0.0),
            (-0.25, 0.25),
            (0.0, 0.5),
            (0.25, 0.75),
            (0.5, 1.0),
            (1.0, 0.5),
            (1.5, 0.0),
            (3.0, 0.0),
        ],
        ids=["deep", "inside", "rising-in", "edge", "rising", "peak", "falling", "end", "far"],
    )
    def test_the_band_at_an_excess(self, excess: float, expected: float) -> None:
        """The band is 0 well inside, 1 half a pixel past the ring's edge, and 0 from 1.5 past."""
        out = pool_band(np.array([excess], F32))
        assert out[0] == pytest.approx(expected)


def _lay(rgb: float, coverage: float, band: float, pool: float, ground: float = 1.0) -> float:
    """`lay_reserve` on one pixel, returning its first channel."""
    out = lay_reserve(
        np.full((1, 1, 3), rgb, F32),
        np.full((1, 1), coverage, F32),
        np.full((1, 1), band, F32),
        pool,
        F32(ground),
    )
    return float(out[0, 0, 0])


class TestLayReserve:
    """Lay the ground over the colour by the coverage, then pool where the band is above 0."""

    def test_half_coverage_is_halfway_to_the_ground(self) -> None:
        """A coverage of 0.5 over 0.4 on a ground of 1 is 0.7."""
        assert _lay(0.4, 0.5, 0.0, 0.0) == pytest.approx(0.7)

    @pytest.mark.parametrize(("rgb", "expected"), [(-0.5, 0.0), (1.5, 1.0)], ids=["below", "above"])
    def test_the_result_is_clipped_to_zero_to_one(self, rgb: float, expected: float) -> None:
        """A colour outside 0 to 1 comes back inside it."""
        assert _lay(rgb, 0.0, 0.0, 0.0) == expected

    def test_a_pool_deepens_by_the_band(self) -> None:
        """At a band of 1 and a pool of 1, 0.5 on a ground of 1 is 0.5 to the power 2."""
        assert _lay(0.5, 0.0, 1.0, 1.0) == pytest.approx(0.25)

    def test_a_pool_scales_with_the_ground(self) -> None:
        """On a ground of 0.8 a colour of 0.4 deepens to 0.8 times 0.5 squared."""
        assert _lay(0.4, 0.0, 1.0, 1.0, ground=0.8) == pytest.approx(0.2)

    def test_a_pool_with_no_band_leaves_the_colour(self) -> None:
        """Where the band is 0 a pool changes nothing."""
        assert _lay(0.5, 0.0, 0.0, 1.0) == 0.5

    def test_a_pool_of_zero_leaves_the_band_bit_for_bit(self) -> None:
        """A pool of 0 is not run at exponent 1: `ground * (out / ground)` is not `out` in float32."""
        ground = np.linspace(0.6, 0.99, 64, dtype=F32)
        rgb = np.linspace(0.1, 0.59, 64, dtype=F32)
        wash = np.repeat(rgb[:, None, None], 64, axis=1).repeat(3, axis=2)
        plate = np.repeat(ground[None, :, None], 64, axis=0).repeat(3, axis=2)
        ones = np.ones((64, 64), F32)
        out = lay_reserve(wash, np.zeros((64, 64), F32), ones, 0.0, plate)
        assert np.array_equal(out.view(np.uint32), wash.view(np.uint32))


class TestReserveTie:
    """A mask exactly at the threshold is the line, and the reserve leaves it."""

    def test_a_pixel_exactly_at_the_threshold_is_untouched(self) -> None:
        """A one-pixel line at exactly 0.3 keeps its wash, though its contour lies on it."""
        mask = np.zeros((9, 9), F32)
        mask[:, 4] = 0.3
        wash = np.full((9, 9, 3), 0.5, F32)
        out = reserve(wash, mask, Reserve(width_px=2.0))
        assert (out[:, 4] == 0.5).all()
        assert (out[:, 5] > 0.5).all()
