"""Tests for how a wash's blooms are sized and which lots seat them."""

import math

import numpy as np
import pytest

from pyntpot.ink.keyed import uniform_at
from pyntpot.ink.wash import bloom_radius, highest

#: Lots with ties at the cut and above it: the cases a bare partition gets wrong.
TIED = np.array([0.5, -1.0, 0.5, 2.0, 0.5, -3.0, 2.0, 0.5])


class TestBloomRadius:
    """A wash's base bloom radius, held on quarter-octave steps."""

    def test_the_radius_is_the_pinned_step(self):
        """The root of the area times the share, taken to the nearest quarter octave."""
        assert bloom_radius(0.17, 10000) == 16.0
        assert bloom_radius(0.17, 95871) == 53.81737057623773
        assert bloom_radius(0.17, 2**20) == 181.01933598375618
        assert bloom_radius(0.17, 1) == 0.1767766952966369

    def test_no_area_or_no_share_is_no_radius(self):
        """An empty wash, or a share of zero, gives a radius of zero rather than an error."""
        assert bloom_radius(0.17, 0) == 0.0
        assert bloom_radius(0.0, 10000) == 0.0
        assert bloom_radius(0.17, -5) == 0.0

    def test_every_radius_is_a_quarter_octave_within_an_eighth_of_one(self):
        """Each radius is a power of two in quarters, and the nearest one to the raw radius."""
        for area in (64, 777, 10_001, 93_210, 1_500_000):
            raw = 0.17 * math.sqrt(area)
            steps = 4 * math.log2(bloom_radius(0.17, area))
            assert math.isclose(steps, round(steps), abs_tol=1e-9)
            assert abs(steps - 4 * math.log2(raw)) <= 0.5

    def test_a_one_pixel_edge_move_rarely_resizes(self):
        """Over a spread of washes, a one-pixel move of one side resizes under 1 in 50."""
        rng = np.random.default_rng(4)
        sides = rng.uniform(100.0, 1200.0, 2000)
        moved = [
            bloom_radius(0.17, int(s * s)) != bloom_radius(0.17, int(s * s - s)) for s in sides
        ]
        rounded = [round(0.17 * s) != round(0.17 * math.sqrt(s * s - s)) for s in sides]
        assert float(np.mean(moved)) < 0.02
        assert float(np.mean(moved)) * 4 < float(np.mean(rounded))


class TestHighest:
    """The top lots, as a stable descending sort's head gives them."""

    @pytest.mark.parametrize("k", [1, 2, 3, 4, 5, 7, 8, 12], ids=lambda k: f"k{k}")
    def test_ties_break_to_the_lower_index(self, k: int):
        """With ties at and above the cut, the pick matches a stable sort's first `k`."""
        assert highest(TIED, k).tolist() == np.argsort(-TIED, kind="stable")[:k].tolist()

    def test_a_ten_thousand_lot_field_matches_the_full_sort(self):
        """Over a field of real lots, partly tied, the head is the full sort's head."""
        lots = np.log(uniform_at(3, np.arange(10_000))) / np.linspace(0.2, 1.0, 10_000)
        lots[::7] = lots[3]
        for k in (1, 6, 50):
            assert np.array_equal(highest(lots, k), np.argsort(-lots, kind="stable")[:k])

    def test_nothing_asked_or_nothing_held_is_empty(self):
        """No lots, or a count of zero or less, gives no indices."""
        assert highest(np.zeros(0), 3).size == 0
        assert highest(TIED, 0).size == 0
        assert highest(TIED, -2).size == 0

    def test_the_indices_are_integers(self):
        """The pick indexes an array, so it comes back as `int64` even when it holds all."""
        assert highest(TIED, 3).dtype == np.int64
        assert highest(TIED, 99).dtype == np.int64
