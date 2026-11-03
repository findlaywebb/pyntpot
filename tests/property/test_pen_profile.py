"""Properties of the nib's width profile: it follows the stroke's direction continuously, with no flicker.

The rotation property holds for any smoothing that reads the direction and not the
position, so it guards the continuity on a staircase, not the corner floor or the ring's
seam; the V, the nib-turn and the ring properties are the ones that guard those, at any
sample count, so the floor cannot lean on where the samples land.
"""

import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from pyntpot.letters.pen_profile import pen_profile

from support.properties import UNTIMED

ANGLES = st.floats(-math.pi, math.pi, allow_nan=False, allow_infinity=False)
THIN = st.floats(0.0, 1.0, allow_nan=False, allow_infinity=False)
LENGTHS = st.integers(40, 160)
TURNS = st.floats(-0.3, 0.3, allow_nan=False, allow_infinity=False)

#: The window the direction is averaged over, in render pixels: a broad nib's width.
WINDOW = 12.0

#: The window a 52 px glyph is written with under the default nib at a render scale of 2
#: (`nib_brushes`' glyph brush width), in render pixels: narrower than `WINDOW`, so a
#: staircase ripples further about its width.
PRODUCTION_WINDOW = 5.46

#: A V's leg, in render pixels: longer than the window, so each half window at the point is one leg.
LEG = 30.0

#: A V's legs, in render pixels, from shorter than half a window to well past it.
LEG_LENGTHS = st.floats(2.0, 40.0, allow_nan=False, allow_infinity=False)

#: Sample counts, odd and even, so a corner falls on a sample or between two.
SAMPLE_COUNTS = st.integers(2, 90)

#: A small turn of the nib, in radians either way.
NUDGES = st.floats(-0.01, 0.01, allow_nan=False, allow_infinity=False)

#: A ring's sides, and samples round it at two per side, so starting at the next vertex
#: shifts the samples by exactly two.
SIDES = 36
RING_SAMPLES = 2 * SIDES + 1

#: More samples than a stroke this long asks for, so a turned stroke is sampled at the same points.
SAMPLES = 40


def _staircase(heading: float, length: int) -> np.ndarray:
    """A straight line at `heading` as a thinned skeleton draws it: pixel centres, a step at a time."""
    t = np.arange(length + 1, dtype=np.float64)
    raw = np.stack([t * math.cos(heading), t * math.sin(heading)], axis=1)
    cells = np.round(raw)
    keep = np.concatenate([[True], np.any(np.diff(cells, axis=0) != 0, axis=1)])
    return cells[keep]


def _vee(half: float, heading: float, first: float = LEG, second: float = LEG) -> np.ndarray:
    """A V of a `first` and a `second` px leg meeting at the origin, `half` either side of `heading`."""
    into = heading + math.pi + half
    out = heading - half
    start = (first * math.cos(into), first * math.sin(into))
    end = (second * math.cos(out), second * math.sin(out))
    return np.array([start, (0.0, 0.0), end])


def _kinked(turns: list[float], lengths: list[float]) -> np.ndarray:
    """A stroke of straight pieces of `lengths` px, each heading at its angle in `turns`."""
    steps = [(n * math.cos(a), n * math.sin(a)) for a, n in zip(turns, lengths, strict=True)]
    return np.concatenate([[(0.0, 0.0)], np.cumsum(steps, axis=0)])


def _ring(radius: float, sides: int, first: int) -> np.ndarray:
    """A closed regular polygon of `sides` vertices, starting at vertex `first` and ending back on it."""
    k = (np.arange(sides + 1) + first) % sides
    turn = 2.0 * math.pi * k / sides
    return np.stack([radius * np.cos(turn), radius * np.sin(turn)], axis=1)


def _width(heading: float, nib: float, thin: float) -> float:
    """The width a straight stroke at `heading` keeps under the nib: the sine law."""
    return (1.0 - thin) + thin * abs(math.sin(heading - nib))


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
        before = pen_profile(pts, nib, thin, WINDOW, SAMPLES)
        after = pen_profile(_turned(pts, by), nib, thin, WINDOW, SAMPLES)
        assert before.shape == after.shape
        assert np.abs(after - before).max() <= thin * abs(by) + 1e-5

    @UNTIMED
    @given(heading=ANGLES, nib=ANGLES, length=LENGTHS)
    def test_a_stepped_straight_stroke_does_not_flicker(
        self, heading: float, nib: float, length: int
    ) -> None:
        """A pixel staircase at any angle to the nib keeps one width, not a saw tooth of wide and hairline."""
        thin = 0.85
        prof = pen_profile(_staircase(heading, length), nib, thin, WINDOW)
        true = (1.0 - thin) + thin * abs(math.sin(heading - nib))
        inner = prof[2:-2]
        assert np.abs(np.diff(prof)).max() <= 0.12
        assert np.abs(inner - true).max() <= 0.12

    @UNTIMED
    @given(heading=ANGLES, nib=ANGLES, length=LENGTHS)
    def test_a_stepped_straight_stroke_holds_near_its_width_at_the_production_window(
        self, heading: float, nib: float, length: int
    ) -> None:
        """At a 52 px glyph's own window a pixel staircase keeps within 0.3 of its width, sample to sample and against the true width."""
        thin = 0.85
        prof = pen_profile(_staircase(heading, length), nib, thin, PRODUCTION_WINDOW)
        true = (1.0 - thin) + thin * abs(math.sin(heading - nib))
        inner = prof[2:-2]
        assert np.abs(np.diff(prof)).max() <= 0.3
        assert np.abs(inner - true).max() <= 0.3

    @UNTIMED
    @given(
        half=st.floats(0.05, 1.5, allow_nan=False, allow_infinity=False),
        heading=ANGLES,
        nib=ANGLES,
        thin=THIN,
        legs=st.tuples(LEG_LENGTHS, LEG_LENGTHS),
        samples=SAMPLE_COUNTS,
    )
    def test_a_corner_is_never_thinner_than_both_its_legs(
        self,
        half: float,
        heading: float,
        nib: float,
        thin: float,
        legs: tuple[float, float],
        samples: int,
    ) -> None:
        """No sample of a V is thinner than its narrower leg, at any turn, nib, leg lengths and sample count."""
        pts = _vee(half, heading, *legs)
        prof = pen_profile(pts, nib, thin, WINDOW, samples)
        narrower = min(_width(heading - half, nib, thin), _width(heading + half, nib, thin))
        assert prof.min() >= narrower - 1e-5

    @UNTIMED
    @given(
        turns=st.lists(ANGLES, min_size=1, max_size=5),
        lengths=st.lists(
            st.floats(0.5, 30.0, allow_nan=False, allow_infinity=False), min_size=5, max_size=5
        ),
        nib=ANGLES,
        thin=THIN,
        nudge=NUDGES,
        samples=SAMPLE_COUNTS,
    )
    def test_turning_the_nib_moves_no_sample_more_than_thin_times_the_turn(
        self,
        turns: list[float],
        lengths: list[float],
        nib: float,
        thin: float,
        nudge: float,
        samples: int,
    ) -> None:
        """On any kinked stroke, turning the nib by an angle moves no sample by more than `thin` times that angle."""
        pts = _kinked(turns, lengths[: len(turns)])
        before = pen_profile(pts, nib, thin, WINDOW, samples)
        after = pen_profile(pts, nib + nudge, thin, WINDOW, samples)
        assert np.abs(after - before).max() <= thin * abs(nudge) + 1e-5

    @UNTIMED
    @given(
        radius=st.floats(8.0, 30.0, allow_nan=False, allow_infinity=False),
        first=st.integers(0, SIDES - 1),
        nib=ANGLES,
        thin=THIN,
    )
    def test_a_closed_ring_has_no_seam(
        self, radius: float, first: int, nib: float, thin: float
    ) -> None:
        """Starting a closed ring one vertex on shifts its widths along by one side and changes none of them."""
        here = pen_profile(_ring(radius, SIDES, first), nib, thin, WINDOW, RING_SAMPLES)
        on = pen_profile(_ring(radius, SIDES, first + 1), nib, thin, WINDOW, RING_SAMPLES)
        assert here[0] == pytest.approx(here[-1], abs=1e-5)
        assert np.allclose(on[:-1], np.roll(here[:-1], -2), atol=1e-5)
