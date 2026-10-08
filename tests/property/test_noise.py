"""Properties of `chamfer_distance` and `blur`: bounded distances, a blur inside its input."""

import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

from pyntpot.ink.noise import blur, chamfer_distance

from support.properties import UNTIMED

SHAPES = st.tuples(st.integers(1, 12), st.integers(1, 12))
SIGMA = st.floats(0, 6, allow_nan=False, allow_infinity=False)
UNIT32 = st.floats(0, 1, width=32, allow_subnormal=False)


@st.composite
def masks(draw: st.DrawFn) -> np.ndarray:
    """A boolean mask with at least one True cell."""
    shape = draw(SHAPES)
    mask = draw(hnp.arrays(np.bool_, shape))
    mask[draw(st.integers(0, shape[0] - 1)), draw(st.integers(0, shape[1] - 1))] = True
    return mask


@st.composite
def mask_pairs(draw: st.DrawFn) -> tuple[np.ndarray, np.ndarray]:
    """A mask and a second mask of the same shape."""
    shape = draw(SHAPES)
    return draw(hnp.arrays(np.bool_, shape)), draw(hnp.arrays(np.bool_, shape))


def _fields(low: int = 8, high: int = 40) -> st.SearchStrategy[np.ndarray]:
    """A float32 field in [0, 1], each side from `low` to `high`."""
    return st.tuples(st.integers(low, high), st.integers(low, high)).flatmap(
        lambda shape: hnp.arrays(np.float32, shape, elements=UNIT32)
    )


def _brute_distance(mask: np.ndarray) -> np.ndarray:
    """The Euclidean distance to the nearest True cell, by looking at every one."""
    ys, xs = np.nonzero(mask)
    gy, gx = np.indices(mask.shape)
    return np.min(np.hypot(gy[..., None] - ys, gx[..., None] - xs), axis=-1)


class TestEdt:
    """The chamfer distance is zero on the mask and within a fixed factor of the true one."""

    @UNTIMED
    @given(mask=masks())
    def test_it_is_zero_on_every_true_cell(self, mask: np.ndarray) -> None:
        """Each True cell is at distance zero."""
        assert np.all(chamfer_distance(mask)[mask] == 0)

    @UNTIMED
    @given(mask=masks())
    def test_it_is_bounded_by_the_true_distance(self, mask: np.ndarray) -> None:
        """The chamfer never undershoots the Euclidean distance and overshoots by at most 1.0825."""
        d = _brute_distance(mask)
        out = chamfer_distance(mask)
        assert np.all(out >= d - 1e-4)
        assert np.all(out <= 1.0825 * d + 1e-4)

    @UNTIMED
    @given(pair=mask_pairs())
    def test_more_true_cells_never_raise_it(self, pair: tuple[np.ndarray, np.ndarray]) -> None:
        """Adding True cells can only shorten the distance, cell by cell."""
        mask, extra = pair
        assert np.all(chamfer_distance(mask | extra) <= chamfer_distance(mask))

    @UNTIMED
    @given(shape=SHAPES)
    def test_an_empty_mask_is_far_everywhere(self, shape: tuple[int, int]) -> None:
        """With nothing True every cell reads 1e6."""
        assert np.all(chamfer_distance(np.zeros(shape, bool)) == 1e6)

    @UNTIMED
    @given(pair=mask_pairs())
    def test_it_leaves_its_input_alone(self, pair: tuple[np.ndarray, np.ndarray]) -> None:
        """The mask passed in is unchanged."""
        mask, _ = pair
        before = mask.copy()
        chamfer_distance(mask)
        assert np.array_equal(mask, before)


class TestBlur:
    """Three box passes keep the shape and dtype, stay in range and keep mass off the border."""

    @UNTIMED
    @given(a=_fields(), sigma=SIGMA)
    def test_it_keeps_shape_and_dtype(self, a: np.ndarray, sigma: float) -> None:
        """The result has the input's shape and is float32."""
        out = blur(a, sigma)
        assert out.shape == a.shape
        assert out.dtype == np.float32

    @UNTIMED
    @given(a=_fields(), sigma=SIGMA)
    def test_it_stays_within_the_input_range(self, a: np.ndarray, sigma: float) -> None:
        """No output value leaves the input's range by more than rounding."""
        out = blur(a, sigma)
        assert out.min() >= a.min() - 1e-5
        assert out.max() <= a.max() + 1e-5

    @UNTIMED
    @given(
        shape=st.tuples(st.integers(8, 40), st.integers(8, 40)),
        value=UNIT32,
        sigma=SIGMA,
    )
    def test_a_constant_field_is_unchanged(
        self, shape: tuple[int, int], value: float, sigma: float
    ) -> None:
        """Blurring a constant field gives the constant back."""
        a = np.full(shape, value, np.float32)
        assert blur(a, sigma) == pytest.approx(a, rel=1e-5)

    @UNTIMED
    @given(interior=_fields(4, 16), sigma=SIGMA)
    def test_it_preserves_mass_away_from_the_border(
        self, interior: np.ndarray, sigma: float
    ) -> None:
        """A field padded with zeros beyond the blur's reach keeps its sum."""
        m = 3 * math.ceil(sigma) + 2
        a = np.pad(interior, m)
        assert blur(a, sigma).sum() == pytest.approx(a.sum(), rel=1e-4)

    @UNTIMED
    @given(a=_fields(), sigma=SIGMA)
    def test_it_leaves_its_input_alone(self, a: np.ndarray, sigma: float) -> None:
        """The array passed in is unchanged."""
        before = a.copy()
        blur(a, sigma)
        assert np.array_equal(a, before)
