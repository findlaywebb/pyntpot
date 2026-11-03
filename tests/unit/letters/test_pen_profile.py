"""The broad nib's width along a glyph stroke, read from its smoothed direction against the nib."""

import math

import numpy as np
import pytest

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.letters.hand import Hand
from pyntpot.letters.nib import nib_brushes
from pyntpot.letters.pen_profile import pen_profile
from pyntpot.letters.setting import Setting
from pyntpot.letters.style import FaceStyle, HandStyle, NibStyle


class TestPenProfile:
    """A glyph stroke's width follows its smoothed direction against the nib."""

    @pytest.mark.parametrize(
        ("heading", "nib", "width"),
        [
            (0.0, math.pi / 2, 1.0),
            (0.0, 0.0, 0.15),
            (math.pi / 6, 0.0, 0.575),
            (math.pi, 0.0, 0.15),
        ],
        ids=["across", "along", "thirty-degrees", "reversed-along"],
    )
    def test_a_straight_stroke_keeps_the_sine_of_its_angle(
        self, heading: float, nib: float, width: float
    ) -> None:
        """A straight stroke keeps `1 - thin` along the nib, all of it across, and the sine between, everywhere."""
        pts = np.array([(0.0, 0.0), (60.0 * math.cos(heading), 60.0 * math.sin(heading))])
        prof = pen_profile(pts, nib, 0.85, 8.0)
        assert np.allclose(prof, width, atol=1e-6)

    def test_the_samples_are_never_more_than_half_a_window_apart(self) -> None:
        """A stroke 120 px long under an 8 px window is sampled at 31 points, not the fewest 24."""
        pts = np.array([(0.0, 0.0), (120.0, 0.0)])
        assert len(pen_profile(pts, 0.0, 0.5, 8.0)) == 31
        assert len(pen_profile(pts, 0.0, 0.5, 80.0)) == 24

    def test_a_short_or_degenerate_stroke_has_full_width(self) -> None:
        """A one-point stroke, or one of no length, keeps its full width at both ends."""
        for pts in (np.array([(3.0, 4.0)]), np.array([(3.0, 4.0), (3.0, 4.0)])):
            prof = pen_profile(pts, 0.0, 0.85, 8.0)
            assert prof.dtype == np.float32
            assert prof.tolist() == [1.0, 1.0]

    def test_a_corner_is_smoothed_over_the_window(self) -> None:
        """Where a stroke turns from along the nib to across it, the width climbs through the angles between."""
        pts = np.array([(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)])
        prof = pen_profile(pts, 0.0, 0.85, 8.0)
        assert prof[0] == pytest.approx(0.15, abs=1e-6)
        assert prof[-1] == pytest.approx(1.0, abs=1e-6)
        assert np.all(np.diff(prof) >= -1e-6)
        assert np.abs(np.diff(prof)).max() < 0.5

    @pytest.mark.parametrize("seed", [1, 7, 11], ids=["seed-1", "seed-7", "seed-11"])
    def test_keswick_on_an_upright_nib_has_no_saw_tooth(self, seed: int) -> None:
        """Keswick at 52 px, nib at 90 degrees and thin 0.85, never zigzags wide, thin, wide along a stroke."""
        hand = Hand(FaceStyle(), HandStyle())
        marks = hand.write(Setting("Keswick", 52.0, anchor=(10.0, 80.0)), hand.generator(seed))
        nib = NibStyle(label_pen_angle_deg=90.0, label_pen_thin=0.85, label_pen_width_px=3.4)
        window = nib_brushes(nib, FaceStyle(), BrushStyle(), 2.0)("glyph", 52.0).width
        zigzags = 0
        for mark in marks:
            pts = np.asarray(mark.pts) * 2.0
            step = np.diff(pen_profile(pts, math.radians(90.0) + mark.pen, 0.85, window))
            big = np.abs(step) > 0.05
            turn = step[:-1] * step[1:] < 0
            zigzags += int(np.sum(turn[:-1] & turn[1:] & big[:-2] & big[1:-1] & big[2:]))
        assert zigzags == 0

    def test_a_short_corner_turns_through_the_pinned_widths(self) -> None:
        """An L of two 10 px legs under an 8 px tent climbs from 0.15 to 1.0 by the pinned widths."""
        pts = np.array([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)])
        prof = pen_profile(pts, 0.0, 0.85, 8.0)
        pinned = [
            0.15, 0.15, 0.15, 0.1519, 0.1657, 0.1918, 0.2293, 0.2803, 0.3484, 0.4382, 0.5523, 0.6826,
            0.8125, 0.8988, 0.9496, 0.9765, 0.99, 0.9963, 0.999, 0.9999, 1.0, 1.0, 1.0, 1.0,
        ]  # fmt: skip
        assert prof.dtype == np.float32
        assert prof.tolist() == pytest.approx(pinned, abs=1e-4)

    def test_a_stroke_as_short_as_the_least_length_has_full_width(self) -> None:
        """A stroke exactly the least length long has no direction, so it keeps its full width."""
        prof = pen_profile(np.array([(0.0, 0.0), (1e-6, 0.0)]), 0.0, 0.85, 8.0)
        assert prof.dtype == np.float32
        assert prof.tolist() == [1.0, 1.0]

    def test_a_vee_along_the_nib_keeps_its_legs_width_at_the_point(self) -> None:
        """A V whose legs are 45 degrees either side of a flat nib keeps the legs' 0.751 at the point, not 0.15."""
        pts = np.array([(-30.0, -30.0), (0.0, 0.0), (30.0, -30.0)])
        prof = pen_profile(pts, 0.0, 0.85, 8.0, 25)
        legs = 0.15 + 0.85 * math.sin(math.pi / 4)
        assert prof[12] == pytest.approx(legs, abs=1e-4)
        assert prof.min() >= legs - 0.005

    def test_a_closed_ring_runs_on_round_its_seam(self) -> None:
        """A twelve-sided ring's widths repeat every half turn, its first and last the same 0.962."""
        turn = np.linspace(0.0, 2.0 * math.pi, 13)
        pts = np.stack([20.0 * np.cos(turn), 20.0 * np.sin(turn)], axis=1)
        pts[-1] = pts[0]
        prof = pen_profile(pts, 0.3, 0.85, 8.0)
        assert len(prof) == 33
        assert prof[0] == pytest.approx(0.962, abs=1e-3)
        assert prof[-1] == pytest.approx(prof[0], abs=1e-6)
        assert np.allclose(prof[:16], prof[16:32], atol=1e-5)
