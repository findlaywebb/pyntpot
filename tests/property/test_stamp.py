"""Properties of `stamp`: seeded determinism, an untouched path, and no mark from a speck of a path."""

import math

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from pyntpot.ink.brush import brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.stamp import stamp

from support.properties import UNTIMED

BRUSH_IDS = st.sampled_from(("RIV1-a", "TRK4-d", "MAJ2-a"))
SEEDS = st.integers(0, 2**32 - 1)
X = st.floats(2, 218, allow_nan=False, allow_infinity=False)
Y = st.floats(2, 58, allow_nan=False, allow_infinity=False)
PATHS = st.lists(st.tuples(X, Y), min_size=2, max_size=30).map(np.array)
STEP = st.floats(-1, 1, allow_nan=False, allow_infinity=False)
LENGTH = st.floats(0, 2.0, exclude_min=True, allow_nan=False, allow_infinity=False)


@st.composite
def specks(draw: st.DrawFn) -> np.ndarray:
    """A path of 2 to 6 points whose total length is a drawn value in (0, 2.0] px."""
    steps = [(draw(STEP), draw(STEP)) for _ in range(draw(st.integers(1, 5)))]
    raw = sum(math.hypot(dx, dy) for dx, dy in steps)
    if raw < 1e-3:
        steps[0], raw = (1.0, 0.0), 1.0
    scale = draw(LENGTH) / raw
    pts = [(draw(X), draw(Y))]
    for dx, dy in steps:
        pts.append((pts[-1][0] + dx * scale, pts[-1][1] + dy * scale))
    return np.array(pts)


def _canvas() -> np.ndarray:
    """A fresh empty accumulator."""
    return np.zeros((60, 220), np.float32)


class TestStamp:
    """One stroke deposited into an accumulator."""

    @UNTIMED
    @given(path=PATHS, brush_id=BRUSH_IDS, seed=SEEDS)
    def test_the_same_seed_gives_the_same_deposit(
        self, path: np.ndarray, brush_id: str, seed: int
    ) -> None:
        """Two canvases stamped from one seed are identical."""
        brush, _ = brush_from_id(brush_id, 3.0, 2.0, BrushStyle())
        first, second = _canvas(), _canvas()
        stamp(first, path, brush, np.random.default_rng(seed))
        stamp(second, path, brush, np.random.default_rng(seed))
        assert np.array_equal(first, second)

    @UNTIMED
    @given(path=PATHS, brush_id=BRUSH_IDS, seed=SEEDS)
    def test_it_leaves_the_path_alone(self, path: np.ndarray, brush_id: str, seed: int) -> None:
        """The path array passed in is unchanged."""
        brush, _ = brush_from_id(brush_id, 3.0, 2.0, BrushStyle())
        before = path.copy()
        stamp(_canvas(), path, brush, np.random.default_rng(seed))
        assert np.array_equal(path, before)

    @UNTIMED
    @given(path=specks(), brush_id=BRUSH_IDS, seed=SEEDS)
    def test_a_speck_of_a_path_deposits_nothing(
        self, path: np.ndarray, brush_id: str, seed: int
    ) -> None:
        """A path no longer than 2 px leaves the canvas empty."""
        brush, _ = brush_from_id(brush_id, 3.0, 2.0, BrushStyle())
        canvas = _canvas()
        stamp(canvas, path, brush, np.random.default_rng(seed))
        assert not canvas.any()
