"""The effect primitives at their edges: ties, out-of-range input, dtypes and pinned values.

These pin behaviour the broader `test_effects.py` leaves loose: a mask exactly at the
threshold, a colour beneath outside 0 to 1, the soft step's width, the shadow's bearing and
colour, and the dtype of every array the primitives hand back.
"""

import numpy as np
import pytest

from pyntpot.ink.colour import Colour, channels
from pyntpot.ink.effect_casing import casing
from pyntpot.ink.effect_glow import glow
from pyntpot.ink.effect_pen_casing import pen_casing
from pyntpot.ink.effect_shadow import _shifted, shadow, shadow_offset
from pyntpot.ink.effect_types import Casing, Glow, PenCasing, Shadow
from pyntpot.ink.naming import nearest
from pyntpot.ink.noise import F32

GREY = "#808080"
GREY_RGB = 128 / 255


def _row(*values: float) -> np.ndarray:
    """A one-row mask from `values`, padded with zeros to eight columns."""
    mask = np.zeros((1, 8), F32)
    mask[0, : len(values)] = values
    return mask


def _plate(level: float) -> np.ndarray:
    """A one-row, eight-column wash of one level."""
    return np.full((1, 8, 3), level, F32)


class TestTies:
    """A mask value exactly at the threshold counts as the line."""

    def test_casing_counts_a_mask_at_the_threshold(self) -> None:
        """A mask of 0.25 at threshold 0.25 is the line: it is left, and the ring starts beside it."""
        out = casing(_plate(0.5), _row(0.25), Casing(width_px=2.5), threshold=0.25)
        assert out[0, :, 0].tolist() == [0.5, 1.0, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5]

    def test_glow_counts_a_mask_at_the_threshold(self) -> None:
        """A mask of 0.25 at threshold 0.25 is the line: it is left, and the halo starts beside it."""
        effect = Glow(spread_px=2.0, strength=1.0)
        out = glow(_plate(0.5), _row(0.25), effect, threshold=0.25)
        assert out[0, :, 0].tolist() == [0.5, 1.0, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5]


class TestSoftStep:
    """The casing's ring is box-filtered coverage of the ring `[0, width]` beyond the contour."""

    def test_the_ring_is_whole_half_a_pixel_beyond_the_contour(self) -> None:
        """A mask of 1 at threshold 0.5 puts its contour half a pixel out, and the next pixel is whole."""
        out = casing(_plate(0.5), _row(1.0), Casing(width_px=2.5), threshold=0.5)
        assert out[0, 1, 0] == 1.0

    def test_the_ring_is_whole_half_a_pixel_inside_its_width(self) -> None:
        """At a width of 2.5 the pixel two from the contour is fully cast and the next not at all."""
        out = casing(_plate(0.5), _row(1.0), Casing(width_px=2.5), threshold=1.0)
        assert out[0, 2, 0] == 1.0
        assert out[0, 3, 0] == 0.5

    def test_a_quarter_pixel_inside_the_width_is_three_quarters_covered(self) -> None:
        """At a width of 2.25 the pixel two from the contour is cast 0.75 of the way to the paper."""
        out = casing(_plate(0.5), _row(1.0), Casing(width_px=2.25), threshold=1.0)
        assert out[0, 2, 0] == pytest.approx(0.5 + 0.75 * 0.5)


class TestOutOfRangeBeneath:
    """Every primitive clips what it returns to 0 to 1, whatever lies beneath."""

    @pytest.mark.parametrize("level", [-0.5, 1.5], ids=["below", "above"])
    def test_casing_clips_far_from_the_line(self, level: float) -> None:
        """A casing returns the beneath clipped to 0 to 1 beyond its ring."""
        out = casing(_plate(level), _row(1.0), Casing(width_px=2.5))
        assert out[0, 7, 0] == min(max(level, 0.0), 1.0)

    @pytest.mark.parametrize("level", [-0.5, 1.5], ids=["below", "above"])
    def test_glow_clips_far_from_the_line(self, level: float) -> None:
        """A glow returns the beneath clipped to 0 to 1 beyond its core."""
        out = glow(_plate(level), _row(1.0), Glow(spread_px=2.0, strength=1.0))
        assert out[0, 7, 0] == min(max(level, 0.0), 1.0)

    @pytest.mark.parametrize("level", [-0.5, 1.5], ids=["below", "above"])
    def test_pen_casing_clips_outside_the_reserve(self, level: float) -> None:
        """A pen casing returns the beneath clipped to 0 to 1 outside the reserve."""
        out, _ = pen_casing(_plate(level), _row(1.0), PenCasing(width_px=1.0, edge_px=1.0))
        assert out[0, 7, 0] == min(max(level, 0.0), 1.0)

    @pytest.mark.parametrize("level", [-0.5, 1.5], ids=["below", "above"])
    def test_shadow_clips_where_nothing_is_cast(self, level: float) -> None:
        """A shadow returns the beneath clipped to 0 to 1 where it casts none."""
        effect = Shadow(offset_px=2.0, strength=1.0)
        out = shadow(_plate(level), _row(1.0), effect, azimuth_deg=270.0)
        assert out[0, 7, 0] == min(max(level, 0.0), 1.0)


class TestPenCasingWhite:
    """A pen casing leaves bare paper, which is 1, and returns float32 arrays."""

    def test_the_reserve_is_exactly_one(self) -> None:
        """Inside the reserve a dark wash is knocked out to exactly 1, and the edge pixel is part paper."""
        out, band = pen_casing(_plate(0.2), _row(1.0), PenCasing(width_px=1.0, edge_px=1.0))
        assert out[0, :, 0].tolist() == pytest.approx([1.0, 1.0, 0.36] + [0.2] * 5)
        assert band[0].tolist() == pytest.approx([0.0, 0.0, 0.8, 0.2, 0.0, 0.0, 0.0, 0.0])

    def test_both_arrays_are_float32(self) -> None:
        """The colour and the edge density are float32 whether on or off."""
        on_rgb, on_band = pen_casing(_plate(0.2), _row(1.0), PenCasing(width_px=1.0, edge_px=1.0))
        off_rgb, off_band = pen_casing(_plate(0.2), _row(1.0), PenCasing())
        assert (on_rgb.dtype, on_band.dtype) == (F32, F32)
        assert (off_rgb.dtype, off_band.dtype) == (F32, F32)


class TestShadowOffset:
    """The shadow falls away from the light."""

    @pytest.mark.parametrize(
        ("azimuth", "expected"),
        [
            (0.0, (0, 100)),
            (90.0, (-100, 0)),
            (180.0, (0, -100)),
            (270.0, (100, 0)),
            (45.0, (-71, 71)),
        ],
        ids=["north", "east", "south", "west", "north-east"],
    )
    def test_the_shift_is_pinned(self, azimuth: float, expected: tuple[int, int]) -> None:
        """A hundred pixels falls to the pinned column and row for each bearing."""
        assert shadow_offset(100.0, azimuth) == expected


class TestShifted:
    """The mask moved with a zero fill."""

    def test_the_shifted_mask_is_float32(self) -> None:
        """A shifted mask, even one shifted off the array, is float32."""
        assert _shifted(_row(1.0), 1, 0).dtype == F32
        assert _shifted(_row(1.0), 99, 0).dtype == F32

    @pytest.mark.parametrize(
        ("dx", "dy", "expected"),
        [(1, 0, [0, 1, 2]), (-1, 0, [2, 3, 0]), (3, 0, [0, 0, 0]), (-3, 0, [0, 0, 0])],
        ids=["right", "left", "right-off", "left-off"],
    )
    def test_columns_shift_with_zero_fill(self, dx: int, dy: int, expected: list[int]) -> None:
        """A three-column mask shifts by whole columns and never wraps."""
        mask = np.array([[1, 2, 3]], F32)
        assert _shifted(mask, dx, dy).tolist() == [[float(v) for v in expected]]

    @pytest.mark.parametrize(
        ("dy", "expected"),
        [(1, [0, 1, 2]), (-1, [2, 3, 0]), (3, [0, 0, 0]), (-3, [0, 0, 0])],
        ids=["down", "up", "down-off", "up-off"],
    )
    def test_rows_shift_with_zero_fill(self, dy: int, expected: list[int]) -> None:
        """A three-row mask shifts by whole rows and never wraps."""
        mask = np.array([[1], [2], [3]], F32)
        assert _shifted(mask, 0, dy).ravel().tolist() == [float(v) for v in expected]


class TestShadowValues:
    """The shadow darkens toward its colour, and only where the weight is above 0."""

    def test_the_cast_pixel_multiplies_toward_the_colour(self) -> None:
        """A full shadow of mid grey on white is mid grey, two pixels from the line."""
        effect = Shadow(offset_px=2.0, strength=1.0, colour=Colour(GREY))
        out = shadow(_plate(1.0), _row(1.0), effect, azimuth_deg=270.0)
        assert out[0, 2, 0] == pytest.approx(GREY_RGB)
        assert out[0, 0, 0] == 1.0
        assert out[0, 3, 0] == 1.0

    def test_a_mask_above_one_is_taken_as_one(self) -> None:
        """A mask of 5 casts the same shadow as a mask of 1."""
        effect = Shadow(offset_px=2.0, strength=0.5, colour=Colour(GREY))
        out = shadow(_plate(1.0), _row(5.0), effect, azimuth_deg=270.0)
        assert out[0, 2, 0] == pytest.approx(1.0 - 0.5 * (1.0 - GREY_RGB))

    def test_a_negative_mask_under_the_shadow_counts_as_no_line(self) -> None:
        """A negative mask value is no line at all, so it is no more shadowed than a zero."""
        effect = Shadow(offset_px=2.0, strength=0.25, colour=Colour(GREY))
        out = shadow(_plate(1.0), _row(1.0, 0.0, -1.0), effect, azimuth_deg=270.0)
        assert out[0, 2, 0] == pytest.approx(1.0 - 0.25 * (1.0 - GREY_RGB))


class TestSmallPieces:
    """The naming and colour helpers at the edge."""

    def test_nearest_returns_one_of_several_close_names(self) -> None:
        """Three names all close to the miss yield a single suggestion."""
        assert len(nearest("alpha", ["alpha1", "alpha2", "alpha3"])) == 1

    def test_a_stray_letter_before_the_digits_is_refused(self) -> None:
        """Only a `#` is stripped from the front of a colour, never other characters."""
        with pytest.raises(ValueError, match="invalid literal"):
            channels("Xff0000")
