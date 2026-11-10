"""`nib_cover` exactly: which stamps the set-down counts, its edges, its dtype and its precision.

Each test places the samples by hand (the positions are an argument of their own), so the
count of stamps the cover reads, and where their paper lands, is known exactly.
"""

import dataclasses

import numpy as np
import pytest

from pyntpot.ink.deposit import nib_cover

from support.lays import all_live, straight_lay


def _stamps_counted(slope: float, box: tuple[int, int, int, int], width: float = 0.01) -> float:
    """How many stamps the cover of a two-sample nib reads, every sample put on one pixel of `box`.

    The stroke runs from (5, 5) at 45 degrees, its stamps half a pixel apart. Each sample stands
    for half a pixel along by `width` across, so a stamp of two is `width` of a pixel, and a
    thin nib keeps the whole far below the cap of 1.
    """
    lay, pos = straight_lay(m=2, width=width, slope=slope)
    y0, _, x0, _ = box
    on = (np.full_like(pos[0], x0), np.full_like(pos[1], y0))
    cover = nib_cover(lay, on, all_live(on), box)
    return float(cover.sum()) / width


class TestTheStampsCounted:
    """The set-down is every stamp no further along than the window reaches from the start, plus the tip."""

    @pytest.mark.parametrize(
        ("box", "stamps"),
        [((4, 6, 2, 4), 9), ((2, 4, 4, 6), 9)],
        ids=["reach-across", "reach-down"],
    )
    def test_the_reach_is_measured_from_the_start_to_the_window_s_far_side(self, box, stamps):
        """From (5, 5), a window from column (or row) 2 reaches 4 px one way and 2 px the other: 4.47 px, so 9 stamps count."""
        assert _stamps_counted(1.0, box) == pytest.approx(stamps)

    def test_a_stamp_exactly_at_the_reach_is_counted(self):
        """A window 5 px from the start plus a 0.5 px tip reaches 5.5 px, and the stamp at 5.5 px counts: 12 stamps."""
        lay, pos = straight_lay(m=3, width=1.0, slope=1.0)
        box = (2, 6, 3, 6)
        rows, cols = np.divmod(np.arange(pos[0].shape[0]) % 12, 3)
        on_x = np.repeat((cols + box[2])[:, None], 3, axis=1).astype(np.float32)
        on_y = np.repeat((rows + box[0])[:, None], 3, axis=1).astype(np.float32)
        cover = nib_cover(lay, (on_x, on_y), all_live(pos), box)
        assert float(cover.sum()) == pytest.approx(12 * 3 * 0.5 * 0.5)

    def test_a_stroke_of_two_stamps_stands_for_its_whole_length(self):
        """Two stamps half a pixel apart each stand for half a pixel along, not a quarter."""
        lay, pos = straight_lay(m=2, width=0.01, n=2)
        on = (np.full_like(pos[0], 6.0), np.full_like(pos[1], 20.0))
        cover = nib_cover(lay, on, all_live(on), (18, 22, 4, 8))
        assert float(cover.sum()) == pytest.approx(2 * 2 * 0.5 * 0.01)


class TestTheWindowEdges:
    """A sample on the window's far edge lies wholly outside it, and lays nothing."""

    @pytest.mark.parametrize(
        "where", [(20.0, 23.5), (16.0, 24.0)], ids=["right-edge", "bottom-edge"]
    )
    def test_a_sample_on_the_far_edge_lays_nothing(self, where):
        """Samples at x = 20 (the window's x1) or y = 24 (its y1) leave the cover empty and its shape whole."""
        lay, pos = straight_lay()
        on = (np.full_like(pos[0], where[0]), np.full_like(pos[1], where[1]))
        cover = nib_cover(lay, on, all_live(on), (15, 24, 2, 20))
        assert cover.shape == (9, 18)
        assert not cover.any()


class TestTheResult:
    """The cover is float32, and its splat reads the positions at float64 whatever they arrive as."""

    def test_the_cover_is_float32(self):
        """The cover comes back as float32, the accumulator's type."""
        lay, pos = straight_lay()
        assert nib_cover(lay, pos, all_live(pos), (15, 25, 2, 20)).dtype == np.float32

    def test_float32_and_float64_positions_give_the_same_cover_bit_for_bit(self):
        """Positions far from the origin, as float32 or as the same values in float64, splat identically."""
        lay, pos = straight_lay(squeeze=2.0, m=6, width=3.7578239, slope=0.6884897, n=40)
        shift = np.float32(2805.2173)
        moved = dataclasses.replace(lay.tr, x=lay.tr.x + shift, y=lay.tr.y + shift)
        lay = dataclasses.replace(lay, tr=moved)
        narrow = (pos[0] + shift, pos[1] + shift)
        wide = (narrow[0].astype(np.float64), narrow[1].astype(np.float64))
        cx, cy = round(float(moved.x[0])), round(float(moved.y[0]))
        box = (cy - 7, cy + 8, cx - 7, cx + 8)
        a = nib_cover(lay, narrow, all_live(narrow), box)
        b = nib_cover(lay, wide, all_live(wide), box)
        assert a.tobytes() == b.tobytes()
