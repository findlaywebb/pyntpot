"""Properties of `stamp`: determinism, an untouched path, specks, the set-down blot, a smooth reload.

One seed gives one deposit, the caller's path is left alone, a path no longer than 2 px lays
nothing, a nib's set-down blot stays on its own stroke, and a reloaded nib's spent share is
continuous at every dip.
"""

import math
from dataclasses import replace

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from pyntpot.ink.brush import brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.noise import chamfer_distance
from pyntpot.ink.stamp import _nib_spent, stamp

from support.properties import UNTIMED

BRUSH_IDS = st.sampled_from(("RIV1-a", "TRK4-d", "MAJ2-a"))
SEEDS = st.integers(0, 2**32 - 1)
X = st.floats(2, 218, allow_nan=False, allow_infinity=False)
Y = st.floats(2, 58, allow_nan=False, allow_infinity=False)
PATHS = st.lists(st.tuples(X, Y), min_size=2, max_size=30).map(np.array)
STEP = st.floats(-1, 1, allow_nan=False, allow_infinity=False)
RESERVOIRS = st.floats(0.1, 60.0, allow_nan=False, allow_infinity=False)
DIP_MULTS = st.floats(1.05, 4.0, allow_nan=False, allow_infinity=False)
WIDTHS = st.floats(0.5, 12.0, allow_nan=False, allow_infinity=False)
LENGTH = st.floats(0, 2.0, exclude_min=True, allow_nan=False, allow_infinity=False)
#: Pen widths in display pixels, from a hairline to a heavy route pen.
PEN_WIDTHS = st.floats(1.0, 8.0, allow_nan=False, allow_infinity=False)
#: How far past the stroke's own ink the blot may reach: the nib's zero-weight samples at the
#: very start, the bilinear splat's one pixel, and the pixel `ink_cover` grows the nib's cover by.
BLOT_SLACK_PX = 3.0


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

    @UNTIMED
    @given(path=PATHS, width=PEN_WIDTHS, seed=SEEDS)
    def test_a_pen_s_set_down_blot_stays_on_its_own_stroke(
        self, path: np.ndarray, width: float, seed: int
    ) -> None:
        """A nib's set-down blot lays no ink more than 3 px past the stroke's own ink, at any width."""
        pen, _ = brush_from_id("MAJ6-e", width, 2.0, BrushStyle())
        assert pen.pool > 0
        with_blot, without = _canvas(), _canvas()
        stamp(with_blot, path, pen, np.random.default_rng(seed))
        stamp(without, path, replace(pen, pool=0.0), np.random.default_rng(seed))
        far = chamfer_distance(without > 0) > BLOT_SLACK_PX
        assert not (with_blot - without)[far].any()


class TestNibReload:
    """A nib that runs dry and is dipped again: its spent share, `_nib_spent`."""

    @UNTIMED
    @given(reservoir=RESERVOIRS, dip_mult=DIP_MULTS, width=WIDTHS)
    def test_the_spent_share_is_continuous_and_below_one_at_every_dip(
        self, reservoir: float, dip_mult: float, width: float
    ) -> None:
        """At each of the first eight dips the share either side agrees, and stays in [0, 1)."""
        style = replace(
            BrushStyle(),
            pen_starve=True,
            pen_reservoir=reservoir,
            pen_thin=1.0,
            ink_dip_mult=dip_mult,
        )
        pen, _ = brush_from_id("MAJ6-e", width, 1.0, style)
        dips = pen.dip_px * np.arange(1, 9)
        eps = 1e-7 * pen.dip_px
        before, after = _nib_spent(dips - eps, pen), _nib_spent(dips + eps, pen)
        np.testing.assert_allclose(before, after, atol=1e-4)
        assert np.all(after >= 0.0) and np.all(after < 1.0)
