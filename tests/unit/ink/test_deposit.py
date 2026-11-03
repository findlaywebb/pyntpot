"""Tests for `deposit`: what it lays into the accumulators, and where.

Each sample's weights go bilinearly into the ink, reservoir and break-texture accumulators,
on those of the four pixels around the sample that fall on the grid; a pen's set-down `pool`
lies on its own stroke.
"""

import dataclasses
import math
from collections.abc import Callable

import numpy as np
import pytest

from pyntpot.ink.brush import brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.deposit import blot_share, deposit, ink_cover, nib_cover
from pyntpot.ink.stamp import stamp
from pyntpot.ink.stroke import Lay, Sampled, StrokeProfile, Tip, Trace


def one_sample(x: float, y: float) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Deposit one sample of weight one at `(x, y)` into fresh 8 by 8 accumulators."""
    acc = np.zeros((8, 8), dtype=np.float32)
    aux = {"res": np.zeros((8, 8), dtype=np.float32), "tooth": np.zeros((8, 8), dtype=np.float32)}
    pos = (np.array([[x]]), np.array([[y]]))
    ones = np.ones((1, 1), dtype=np.float32)
    deposit(acc, aux, pos, ones, ones, ones)
    return acc, aux


@pytest.mark.parametrize("name", ["ink", "res", "tooth"], ids=["ink", "res", "tooth"])
def test_a_sample_off_the_accumulator_lays_nothing(name: str) -> None:
    """A sample wholly off the plate lays no ink on its edge pixels."""
    acc, aux = one_sample(-5.0, 3.0)
    laid = acc if name == "ink" else aux[name]
    assert laid.sum() == 0.0
    assert laid[3, 0] == 0.0


def test_a_sample_half_off_the_edge_keeps_only_its_share_on_the_plate() -> None:
    """Only the corners on the grid receive their bilinear share."""
    acc, _ = one_sample(-0.5, 3.0)
    assert acc[3, 0] == 0.5
    assert acc.sum() == 0.5


def blot(
    path: list[tuple[float, float]], width: float = 60.0, pool: float = 1.0, gain: float = 1.0
) -> np.ndarray:
    """A pen's set-down blot alone: the stroke with its pool less the same stroke without.

    The pen is `width` render pixels wide with the given pool and gain, on a 201 by 221 plate.
    """
    brush, _ = brush_from_id("MAJ1-e", 3.0, 2.0, BrushStyle())
    brush = dataclasses.replace(brush, width=width, pool=pool, pool_gain=gain)
    marks = []
    for b in (brush, dataclasses.replace(brush, pool=0.0)):
        acc = np.zeros((201, 221), dtype=np.float32)
        stamp(acc, np.array(path), b, np.random.default_rng(1))
        marks.append(acc)
    return marks[0] - marks[1]


#: A 60 px pen's blot reaches three radii, half its width each.
SPAN = math.ceil(60.0 * 0.5 * 3)


@pytest.mark.parametrize(
    ("path", "along"),
    [
        ([(20.3, 100.0), (200.0, 100.0)], lambda m: m[100, 20:]),
        ([(110.0, 20.3), (110.0, 200.0)], lambda m: m[20:, 110]),
    ],
    ids=["right", "down"],
)
def test_a_wide_pool_has_faded_to_nothing_at_the_end_of_its_span(
    path: list[tuple[float, float]], along: Callable[[np.ndarray], np.ndarray]
) -> None:
    """Along its own stroke a wide pool, centred on the rounded start, fades under 1.5% of its peak at its span's end."""
    line = along(blot(path))
    assert line[0] > 0
    assert 0 < line[SPAN] < 0.015 * line.max()
    assert not line[SPAN + 1 :].any()


@pytest.mark.parametrize(
    ("path", "edge"),
    [
        ([(60.3, 100.0), (0.0, 100.0)], lambda m: m[100, 0]),
        ([(110.0, 60.3), (110.0, 0.0)], lambda m: m[0, 110]),
    ],
    ids=["left", "up"],
)
def test_a_wide_pool_reaches_the_plate_s_first_row_and_column(
    path: list[tuple[float, float]], edge: Callable[[np.ndarray], np.ndarray]
) -> None:
    """A blot whose span runs off the plate still lays its share on the plate's edge pixel."""
    assert edge(blot(path)) > 0


def test_the_blot_is_as_dark_as_its_pool_times_its_gain() -> None:
    """A pool of 2 at a gain of 3 lays six times the blot a pool and gain of 1 lay."""
    path = [(20.0, 100.0), (200.0, 100.0)]
    np.testing.assert_allclose(blot(path, pool=2.0, gain=3.0), 6.0 * blot(path), atol=1e-5)


def test_a_narrow_pool_keeps_its_floor_radius() -> None:
    """A 1 px pen's blot has the 1.2 px floor radius: it reaches 4 px along its stroke and no further."""
    line = blot([(20.0, 100.0), (200.0, 100.0)], width=1.0)[100, 20:]
    assert line[4] > 0
    assert not line[5:].any()


def test_a_wide_pool_lays_nothing_beside_its_stroke() -> None:
    """A wide pool reaches 90 px but lays nothing past the 60 px pen's own edge."""
    laid = blot([(20.0, 100.0), (200.0, 100.0)])
    beside = np.ones(laid.shape, dtype=bool)
    beside[60:141] = False
    assert laid[60:141, 20 : 20 + SPAN].any()
    assert not laid[beside].any()


class TestTheFlatIndex:
    """On a non-square plate the flat index lands each share where the row and column pair does."""

    @staticmethod
    def _deposit(contiguous: bool) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        """Lay a scatter of samples into fresh 5 by 9 accumulators, or into transposed views."""

        def plate() -> np.ndarray:
            return np.zeros((5, 9), np.float32) if contiguous else np.zeros((9, 5), np.float32).T

        acc, aux = plate(), {"res": plate(), "tooth": plate()}
        rng = np.random.default_rng(3)
        px = rng.uniform(-1.0, 9.5, (4, 6))
        py = rng.uniform(-1.0, 5.5, (4, 6))
        wgt = rng.random((4, 6), dtype=np.float32)
        deposit(acc, aux, (px, py), wgt, wgt * np.float32(0.5), wgt * np.float32(0.25))
        return acc, aux

    def test_a_view_that_is_not_contiguous_lays_the_same_bits(self) -> None:
        """A caller's transposed view takes the pair and lays exactly what a plain plate does."""
        assert not self._deposit(contiguous=False)[0].flags.c_contiguous
        flat_acc, flat_aux = self._deposit(contiguous=True)
        pair_acc, pair_aux = self._deposit(contiguous=False)
        assert np.array_equal(flat_acc, pair_acc)
        for name in ("res", "tooth"):
            assert np.array_equal(flat_aux[name], pair_aux[name]), name

    def test_one_sample_lands_on_its_four_pixels_of_a_non_square_plate(self) -> None:
        """A sample at (7.25, 3.5) on a 5 by 9 plate shares itself among rows 3, 4 and columns 7, 8."""
        acc = np.zeros((5, 9), np.float32)
        aux = {"res": np.zeros((5, 9), np.float32), "tooth": np.zeros((5, 9), np.float32)}
        ones = np.ones((1, 1), np.float32)
        deposit(acc, aux, (np.array([[7.25]]), np.array([[3.5]])), ones, ones, ones)
        want = np.zeros((5, 9), np.float32)
        want[3:5, 7:9] = [[0.375, 0.125], [0.375, 0.125]]
        for laid in (acc, aux["res"], aux["tooth"]):
            assert np.array_equal(laid, want)


def straight_lay(squeeze: float = 1.0) -> tuple[Lay, tuple[np.ndarray, np.ndarray]]:
    """A 10 px stroke along y 20 from x 5, 2 px wide, sampled every half pixel both ways.

    Each of its 21 stamps by 5 samples stands for a quarter of a pixel. A `squeeze` of 2 lands
    the samples across half the width, so the paper under them is passed over twice.
    """
    n, m = 21, 5
    t = np.linspace(0.0, 10.0, n).astype(np.float32)
    u = np.linspace(-1.0, 1.0, m).astype(np.float32)
    one, flat = np.ones(n, np.float32), np.zeros(n, np.float32)
    tr = Trace(5.0 + t, np.full(n, 20.0, np.float32), flat, one, t, 10.0)
    ink = StrokeProfile(one, np.full(n, 2.0, np.float32), None)
    tip = Tip(m, u, np.ones(m), np.zeros((2, m)), np.zeros(m), np.ones(m), None, None, None, None)
    smp = Sampled(m, u, *(np.ones(m, np.float32),) * 5, None, np.ones(m, np.float32), 2.0)
    off = np.broadcast_to(u[None, :], (n, m)).astype(np.float32)
    px = tr.x[:, None] + 0.0 * off
    py = tr.y[:, None] + off / squeeze
    return Lay(tr, ink, tip, smp, off), (px, py)


def all_live(pos: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    """Every sample laying ink, in the samples' shape."""
    return np.ones(pos[0].shape, dtype=bool)


class TestNibCover:
    """How much of each pixel the nib passes over: each sample its own patch of paper."""

    def test_a_sample_that_lays_no_ink_covers_nothing(self) -> None:
        """The first five stamps laying no ink, the cover starts at the sixth, 2.5 px in."""
        lay, pos = straight_lay()
        live = all_live(pos)
        live[:5] = False
        cover = nib_cover(lay, pos, live, (15, 25, 2, 20))
        assert float(cover.sum()) == pytest.approx(26.25 - 5 * 5 * 0.25)
        assert not cover[:, : 7 - 2].any()
        assert cover[:, 7 - 2].any()

    def test_the_cover_holds_the_paper_the_samples_stand_for(self) -> None:
        """A stroke of 105 quarter-pixel patches covers 26.25 pixels, one in its middle, none before it."""
        lay, pos = straight_lay()
        cover = nib_cover(lay, pos, all_live(pos), (15, 25, 2, 20))
        assert float(cover.sum()) == pytest.approx(26.25)
        assert cover[20 - 15, 10 - 2] == pytest.approx(1.0)
        assert cover[:, 5 - 2].any()
        assert not cover[:, : 5 - 2].any()
        assert not cover[:, 15 - 2 + 1 :].any()

    def test_a_pixel_passed_over_twice_is_covered_once(self) -> None:
        """Cover is a share of the pixel, so paper the samples pass over twice reads 1, not 2."""
        lay, pos = straight_lay(squeeze=2.0)
        cover = nib_cover(lay, pos, all_live(pos), (15, 25, 2, 20))
        assert float(cover.max()) == 1.0
        assert cover[20 - 15, 10 - 2] == 1.0


class TestBlotShare:
    """The share of the blot each pixel takes: a thin nib's cover grown, a wide one's not."""

    def test_a_nib_3_px_wide_is_not_grown(self) -> None:
        """At 3 render px one pixel covered an eighth takes the blot whole, and its neighbours nothing."""
        cover = np.zeros((6, 7), dtype=np.float32)
        cover[2, 4] = 0.125
        expected = np.zeros((6, 7), dtype=np.float32)
        expected[2, 4] = 1.0
        assert np.array_equal(blot_share(cover, 3.0), expected)

    def test_a_nib_under_3_px_wide_is_grown_by_a_pixel(self) -> None:
        """Just under 3 render px, one pixel covered a sixteenth gives its 3 by 3 block half."""
        cover = np.zeros((6, 7), dtype=np.float32)
        cover[2, 4] = 0.0625
        expected = np.zeros((6, 7), dtype=np.float32)
        expected[1:4, 3:6] = 0.5
        assert np.array_equal(blot_share(cover, 2.99), expected)

    def test_a_wide_nib_s_share_is_at_most_whole(self) -> None:
        """At 12 render px a pixel covered half or whole takes the blot once, not more."""
        cover = np.array([[0.5, 1.0]], dtype=np.float32)
        assert np.array_equal(blot_share(cover, 12.0), np.ones((1, 2), dtype=np.float32))

    def test_a_wide_nib_s_share_is_in_proportion_under_an_eighth(self) -> None:
        """At 12 render px a pixel covered a sixteenth takes half the blot."""
        cover = np.full((2, 2), 0.0625, dtype=np.float32)
        assert np.array_equal(blot_share(cover, 12.0), np.full((2, 2), 0.5, dtype=np.float32))


class TestInkCover:
    """The paper the stroke's own ink lies on: the nib's cover grown by a pixel."""

    @pytest.mark.parametrize(
        ("share", "laid"),
        [(0.0625, 0.5), (0.125, 1.0), (1.0, 1.0)],
        ids=["sixteenth", "eighth", "whole"],
    )
    def test_one_covered_pixel_lays_on_its_3_by_3_neighbourhood(
        self, share: float, laid: float
    ) -> None:
        """A pixel covered by `share` gives its 3 by 3 block `share` times 8, at most 1, and nothing else."""
        cover = np.zeros((6, 7), dtype=np.float32)
        cover[2, 4] = share
        expected = np.zeros((6, 7), dtype=np.float32)
        expected[1:4, 3:6] = laid
        assert np.array_equal(ink_cover(cover), expected)
