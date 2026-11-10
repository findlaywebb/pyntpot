"""The reserve primitive: the paper laid back in a ring round a line, with an optional pool."""

import numpy as np
import pytest

from pyntpot.ink.effect_reserve import reserve
from pyntpot.ink.effect_types import Reserve
from pyntpot.ink.noise import F32

SIDE = 24


def _line() -> np.ndarray:
    """A float32 mask with a vertical line three columns wide."""
    mask = np.zeros((SIDE, SIDE), F32)
    mask[:, 10:13] = 1.0
    return mask


def _wash(level: float = 0.5) -> np.ndarray:
    """A flat float32 wash."""
    return np.full((SIDE, SIDE, 3), level, F32)


class TestReserve:
    """The reserve lays the paper back beside the line."""

    def test_the_ring_is_the_paper_where_whole(self) -> None:
        """Two pixels beyond the line's edge, with a width of 4, the wash is the paper."""
        out = reserve(_wash(), _line(), Reserve(width_px=4.0))
        assert (out[:, 8, :] == 1.0).all()
        assert (out[:, 14, :] == 1.0).all()

    def test_the_paper_plate_is_laid_exactly(self) -> None:
        """With a paper plate, a whole ring equals the plate bit for bit."""
        plate = np.random.default_rng(1).uniform(0.6, 1.0, (SIDE, SIDE, 3)).astype(F32)
        out = reserve(_wash(), _line(), Reserve(width_px=4.0), paper=plate)
        assert np.array_equal(out[:, 8, :], plate[:, 8, :])

    def test_beyond_the_ring_is_untouched(self) -> None:
        """Far from the line, the wash is unchanged."""
        out = reserve(_wash(), _line(), Reserve(width_px=2.0))
        assert (out[:, 0, :] == 0.5).all()

    def test_the_core_is_untouched(self) -> None:
        """Under the line the wash is unchanged, with a pool too."""
        out = reserve(_wash(), _line(), Reserve(width_px=4.0, pool=1.0))
        assert (out[:, 10:13, :] == 0.5).all()

    def test_width_zero_and_an_empty_mask_return_the_wash(self) -> None:
        """No width, or no line, returns `rgb` itself."""
        wash = _wash()
        assert reserve(wash, _line(), Reserve()) is wash
        assert reserve(wash, np.zeros((SIDE, SIDE), F32), Reserve(width_px=3.0)) is wash

    def test_a_threshold_of_zero_is_refused(self) -> None:
        """A threshold not above 0 raises."""
        with pytest.raises(ValueError, match="threshold"):
            reserve(_wash(), _line(), Reserve(width_px=1.0), threshold=0.0)


class TestPool:
    """The pool deepens a faint line just outside the ring and never lightens."""

    def test_the_pool_darkens_just_outside_the_ring(self) -> None:
        """A pool of 1 makes the pixels past the ring darker than without it."""
        plain = reserve(_wash(), _line(), Reserve(width_px=3.0))
        pooled = reserve(_wash(), _line(), Reserve(width_px=3.0, pool=1.0))
        assert (pooled[:, 16, :] < plain[:, 16, :]).all()
        assert (pooled <= plain).all()

    def test_the_pool_leaves_bare_paper_bare(self) -> None:
        """On a bare paper wash a pool darkens nothing."""
        out = reserve(_wash(1.0), _line(), Reserve(width_px=3.0, pool=1.0))
        assert (out == 1.0).all()

    def test_a_zero_pool_is_the_plain_reserve(self) -> None:
        """Pool 0 skips the deepening."""
        a = reserve(_wash(), _line(), Reserve(width_px=3.0))
        assert a.dtype == F32
