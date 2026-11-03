"""Properties of the nib's width profile: it follows the stroke's direction continuously, with no flicker."""

import math

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from pyntpot.letters.nib import _pen_profile

from support.properties import UNTIMED

ANGLES = st.floats(-math.pi, math.pi, allow_nan=False, allow_infinity=False)
THIN = st.floats(0.0, 1.0, allow_nan=False, allow_infinity=False)
LENGTHS = st.integers(40, 160)
TURNS = st.floats(-0.3, 0.3, allow_nan=False, allow_infinity=False)

#: The window the direction is averaged over, in render pixels: a broad nib's width.
WINDOW = 12.0

#: More samples than a stroke this long asks for, so a turned stroke is sampled at the same points.
SAMPLES = 40


def _staircase(heading: float, length: int) -> np.ndarray:
    """A straight line at `heading` as a thinned skeleton draws it: pixel centres, a step at a time."""
    t = np.arange(length + 1, dtype=np.float64)
    raw = np.stack([t * math.cos(heading), t * math.sin(heading)], axis=1)
    cells = np.round(raw)
    keep = np.concatenate([[True], np.any(np.diff(cells, axis=0) != 0, axis=1)])
    return cells[keep]


def _turned(pts: np.ndarray, by: float) -> np.ndarray:
    """The stroke rotated by `by` radians about its first point."""
    c, s = math.cos(by), math.sin(by)
    rel = pts - pts[0]
    return pts[0] + rel @ np.array([[c, s], [-s, c]])


class TestPenProfile:
    """The width along a stroke is read from its smoothed direction against the nib's."""

    @UNTIMED
    @given(heading=ANGLES, nib=ANGLES, thin=THIN, length=LENGTHS, by=TURNS)
    def test_the_width_varies_continuously_with_the_direction(
        self, heading: float, nib: float, thin: float, length: int, by: float
    ) -> None:
        """Turning a stroke by an angle moves no sample of its width by more than `thin` times that angle."""
        pts = _staircase(heading, length)
        before = _pen_profile(pts, nib, thin, WINDOW, SAMPLES)
        after = _pen_profile(_turned(pts, by), nib, thin, WINDOW, SAMPLES)
        assert before.shape == after.shape
        assert np.abs(after - before).max() <= thin * abs(by) + 1e-5

    @UNTIMED
    @given(heading=ANGLES, nib=ANGLES, length=LENGTHS)
    def test_a_stepped_straight_stroke_does_not_flicker(
        self, heading: float, nib: float, length: int
    ) -> None:
        """A pixel staircase at any angle to the nib keeps one width, not a saw tooth of wide and hairline."""
        thin = 0.85
        prof = _pen_profile(_staircase(heading, length), nib, thin, WINDOW)
        true = (1.0 - thin) + thin * abs(math.sin(heading - nib))
        inner = prof[2:-2]
        assert np.abs(np.diff(prof)).max() <= 0.12
        assert np.abs(inner - true).max() <= 0.12
