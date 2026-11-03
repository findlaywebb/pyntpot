"""Tests for outline deformation: wobble at two scales, capped, and seeded."""

import math

import numpy as np
import pytest

from pyntpot.ink.raster import deform_ring, deform_rings, fill_cov
from pyntpot.ink.sheet import Canvas


def ring_of(n: int = 96, r: float = 200.0) -> list[tuple[float, float]]:
    """A circle, as the ring the deformation is given."""
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return [(float(r * math.cos(t)), float(r * math.sin(t))) for t in a]


def test_an_outline_given_no_deform_is_the_outline_it_was():
    """The inert path hands back the same objects, not a copy of them."""
    rings = [ring_of(), ring_of(40, 90.0)]
    assert deform_rings(rings, None) is rings


def test_the_deformed_outline_wobbles_at_more_than_one_scale():
    """One frequency everywhere is what the blurred-mask edge already does."""
    ring = np.asarray(ring_of(), float)
    out = deform_ring(ring, (5, 0.26, 4, 0.55, 16.0, 0.5))
    assert len(out) == len(ring) * 16
    rad = np.hypot(out[:, 0], out[:, 1]) - 200.0
    # Split the deviation into what a long smoothing keeps and what it removes.
    k = np.ones(33) / 33.0
    coarse = np.convolve(np.concatenate([rad[-16:], rad, rad[:16]]), k, "same")[16:-16]
    fine = rad - coarse
    assert coarse.std() > 1.0, "no wobble the eye reads as a lobe"
    assert fine.std() > 0.3, "no wobble at the scale of a brush edge"
    # Neither scale swamps the other: that mixture is the whole point of it.
    assert 0.15 < fine.std() / coarse.std() < 6.0
    # And it is a deformation, not a new shape: the ring keeps its place.
    assert abs(float(out[:, 0].mean())) < 12.0
    assert abs(float(np.hypot(out[:, 0], out[:, 1]).mean()) - 200.0) < 12.0


def test_no_one_displacement_runs_away_with_a_long_segment():
    """A field boundary drawn as two points must not be thrown across the canvas."""
    box = [(0.0, 0.0), (4000.0, 0.0), (4000.0, 3000.0), (0.0, 3000.0)]
    out = deform_ring(box, (2, 0.26, 4, 0.55, 16.0, 0.5))
    # Every point stays within the cap of the straight edge it came off, give or
    # take the caps the earlier rounds already spent.
    assert float(np.abs(out[:, 1]).min()) < 1e-9
    assert float(out[:, 1].max()) < 3000.0 + 16.0 * 4


def test_the_deformation_is_the_same_ring_from_the_same_seed():
    """Everything in the painter has to come back the same from its seed."""
    a = deform_ring(ring_of(), (9, 0.26, 4, 0.55, 16.0, 0.5))
    b = deform_ring(ring_of(), (9, 0.26, 4, 0.55, 16.0, 0.5))
    assert np.array_equal(a, b)


class TestFillCoverage:
    """Coverage by the winding rule, on whole rings at once."""

    @staticmethod
    def _canvas() -> Canvas:
        """A 40 by 30 pixel canvas over a 40 by 30 metre card, so a metre is a pixel."""
        return Canvas(0.0, 0.0, 40.0, 30.0, 40, 30)

    def test_a_ring_and_its_reversal_cover_the_same_pixels(self):
        """The winding rule fills by nonzero winding, so the direction of a lone ring does not matter."""
        ring = [(5.3, 4.1), (31.7, 6.2), (27.4, 22.9), (9.8, 18.6)]
        canvas = self._canvas()
        forward = fill_cov([ring], canvas, ss=3)
        assert forward.max() == 1.0
        assert np.array_equal(forward, fill_cov([ring[::-1]], canvas, ss=3))

    def test_a_ring_wholly_off_the_canvas_covers_nothing(self):
        """Rows and columns are clipped before the cast, so a far ring adds no crossing."""
        far = [(5e6, 5e6), (5e6 + 10, 5e6), (5e6 + 10, 5e6 + 10)]
        assert not fill_cov([far], self._canvas()).any()

    @pytest.mark.parametrize("bad", [math.nan, math.inf], ids=["nan", "inf"])
    def test_a_coordinate_that_is_not_finite_raises(self, bad: float):
        """A NaN or infinite point is refused before any crossing is counted."""
        with pytest.raises(ValueError, match="not finite"):
            fill_cov([[(1.0, 1.0), (bad, 2.0), (3.0, 9.0)]], self._canvas())


class TestDeformRingExactly:
    """The deformation's own draws, pinned, and the cases it hands back unchanged."""

    SQUARE = ((0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0))

    def test_a_square_deforms_to_the_pinned_points(self):
        """Three rounds on a square, the cap binding, give the pinned points."""
        out = deform_ring(self.SQUARE, (9, 0.26, 3, 0.55, 4.0, 0.5))
        assert len(out) == 32
        assert out[1].tolist() == [12.594983122532152, 0.2621447378270182]
        assert out[5].tolist() == [62.70499850434101, -4.413828694322792]
        assert out[-1].tolist() == [-4.239172682310188, 12.434463821657026]
        assert float(out.sum()) == 3218.9794857326724

    def test_a_ring_of_sub_metre_edges_deforms_to_the_pinned_points(self):
        """Edges under a metre are divided by their own length, not by a metre."""
        small = [(0.0, 0.0), (0.6, 0.0), (0.6, 0.6), (0.0, 0.6)]
        out = deform_ring(small, (4, 0.26, 2, 0.55, 16.0, 0.3))
        assert len(out) == 16
        assert out[1].tolist() == [0.05920894661291781, 0.23484089545159872]
        assert float(out.sum()) == 9.751449298444236

    @pytest.mark.parametrize(
        ("ring", "deform"),
        [
            (SQUARE, (9, 0.26, 0, 0.55, 16.0, 0.5)),
            (SQUARE, (9, 0.26, 3, 0.55, 16.0, 200.0)),
            (((0.0, 0.0), (100.0, 0.0)), (9, 0.26, 3, 0.55, 16.0, 0.5)),
        ],
        ids=["no-rounds", "edges-under-the-stop", "two-points"],
    )
    def test_what_is_not_deformed_comes_back_as_it_was(self, ring, deform):
        """No rounds, edges already under the stop, or too few points leave the ring as given."""
        assert np.array_equal(deform_ring(ring, deform), np.asarray(ring, float))

    def test_a_negative_amount_only_divides_the_edges(self):
        """A variance below zero is none: each new point is its edge's midpoint."""
        out = deform_ring(self.SQUARE, (9, -0.5, 1, 0.55, 16.0, 0.5))
        assert out.tolist() == [
            [0.0, 0.0], [50.0, 0.0], [100.0, 0.0], [100.0, 50.0],
            [100.0, 100.0], [50.0, 100.0], [0.0, 100.0], [0.0, 50.0],
        ]  # fmt: skip

    def test_a_triangle_is_deformed(self):
        """Three points are enough to enclose something, so a triangle is deformed."""
        tri = [(0.0, 0.0), (100.0, 0.0), (50.0, 80.0)]
        assert len(deform_ring(tri, (9, 0.26, 1, 0.55, 16.0, 0.5))) == 6

    def test_a_ring_at_the_point_ceiling_is_doubled_once_more_and_past_it_not(self):
        """At the ceiling a ring still doubles; one point past it comes back as it was."""

        def ring(n: int) -> list[tuple[float, float]]:
            return ring_of(n, 4000.0)

        assert len(deform_ring(ring(24000), (9, 0.26, 1, 0.55, 16.0, 0.5))) == 48000
        past = ring(24001)
        assert np.array_equal(deform_ring(past, (9, 0.26, 1, 0.55, 16.0, 0.5)), np.asarray(past))
