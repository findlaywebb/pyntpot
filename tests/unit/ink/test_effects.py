"""The four effect primitives: their maths on small arrays, the threshold and the identities."""

import inspect
from collections.abc import Callable
from typing import Any

import numpy as np
import pytest

from pyntpot.ink.colour import Colour
from pyntpot.ink.effect_casing import casing
from pyntpot.ink.effect_glow import glow
from pyntpot.ink.effect_mask import LINE_THRESHOLD
from pyntpot.ink.effect_pen_casing import pen_casing
from pyntpot.ink.effect_shadow import shadow, shadow_offset
from pyntpot.ink.effect_types import Casing, Glow, PenCasing, Shadow
from pyntpot.ink.noise import F32

SIZE = 21
AZIMUTH = 315.0


def _line() -> np.ndarray:
    """A mask with a vertical line, 3 pixels wide, down the middle."""
    mask = np.zeros((SIZE, SIZE), F32)
    mask[:, 9:12] = 1.0
    return mask


def _wash() -> np.ndarray:
    """A mid-grey wash."""
    return np.full((SIZE, SIZE, 3), 0.5, F32)


def _call_casing(**kw: Any) -> Any:
    """`casing` with an on effect."""
    return casing(_wash(), _line(), Casing(width_px=3.0), **kw)


def _call_glow(**kw: Any) -> Any:
    """`glow` with an on effect."""
    return glow(_wash(), _line(), Glow(spread_px=1.0, blur_px=2.0, strength=0.8), **kw)


def _call_shadow(**kw: Any) -> Any:
    """`shadow` with an on effect."""
    effect = Shadow(offset_px=2.0, blur_px=1.0, strength=0.7)
    return shadow(_wash(), _line(), effect, azimuth_deg=AZIMUTH, **kw)


def _call_pen_casing(**kw: Any) -> Any:
    """`pen_casing` with an on effect."""
    return pen_casing(_wash(), _line(), PenCasing(width_px=2.0, edge_px=1.0), **kw)


CALLS: dict[str, Callable[..., Any]] = {
    "casing": _call_casing,
    "glow": _call_glow,
    "shadow": _call_shadow,
    "pen_casing": _call_pen_casing,
}
FUNCTIONS = {"casing": casing, "glow": glow, "shadow": shadow, "pen_casing": pen_casing}
NAMES = list(CALLS)


def _same(a: Any, b: Any) -> bool:
    """Whether two results (an array, or a tuple of arrays) are equal bit for bit."""
    if isinstance(a, tuple):
        return all(_same(x, y) for x, y in zip(a, b, strict=True))
    return bool(a.dtype == b.dtype and np.array_equal(a.view(np.uint32), b.view(np.uint32)))


class TestThreshold:
    """Every primitive has the same threshold rules."""

    @pytest.mark.parametrize("name", NAMES)
    @pytest.mark.parametrize("bad", [0.0, -0.1, float("nan")], ids=["zero", "negative", "nan"])
    def test_a_threshold_not_above_zero_is_refused(self, name: str, bad: float) -> None:
        """A threshold of 0, below 0 or nan raises a ValueError naming it."""
        with pytest.raises(ValueError, match="threshold"):
            CALLS[name](threshold=bad)

    @pytest.mark.parametrize("name", NAMES)
    def test_the_default_is_the_line_threshold(self, name: str) -> None:
        """The keyword defaults to `LINE_THRESHOLD`, and omitting it equals passing it."""
        default = inspect.signature(FUNCTIONS[name]).parameters["threshold"].default
        assert default == LINE_THRESHOLD
        assert _same(CALLS[name](), CALLS[name](threshold=LINE_THRESHOLD))

    def test_the_line_threshold_is_pinned(self) -> None:
        """The line threshold is 0.3."""
        assert LINE_THRESHOLD == 0.3

    @pytest.mark.parametrize("name", NAMES)
    def test_every_signature_is_short(self, name: str) -> None:
        """No primitive takes more than six parameters."""
        assert len(inspect.signature(FUNCTIONS[name]).parameters) <= 6

    @pytest.mark.parametrize("name", NAMES)
    def test_a_primitive_does_not_touch_its_inputs(self, name: str) -> None:
        """The wash and the mask are as they were after a call."""
        wash, mask = _wash(), _line()
        CALLS[name]()
        assert np.array_equal(wash, _wash())
        assert np.array_equal(mask, _line())


class TestCasing:
    """`casing` blends a ring toward the colour laid over the paper."""

    def test_off_returns_the_input_itself(self) -> None:
        """Width 0, strength 0 and an empty mask each return `rgb` itself."""
        wash = _wash()
        assert casing(wash, _line(), Casing(), threshold=0.3) is wash
        assert casing(wash, _line(), Casing(width_px=3.0, strength=0.0)) is wash
        assert casing(wash, np.zeros((SIZE, SIZE), F32), Casing(width_px=3.0)) is wash

    def test_a_white_casing_reaches_the_paper_beside_the_line(self) -> None:
        """Beside the line a full white casing is 1 in wash space, and far away is untouched."""
        out = casing(_wash(), _line(), Casing(width_px=3.0))
        assert out.dtype == F32
        assert out[10, 8, 0] == pytest.approx(1.0)
        assert out[10, 12, 0] == pytest.approx(1.0)
        assert out[10, 10, 0] == 0.5  # the line's own pixel is left
        assert out[10, 0, 0] == 0.5

    def test_the_colour_is_laid_over_the_paper_plate(self) -> None:
        """On a paper plate the casing target is colour times paper."""
        paper = np.full((SIZE, SIZE, 3), 0.8, F32)
        effect = Casing(width_px=3.0, colour=Colour("#808080"))
        out = casing(_wash(), _line(), effect, paper=paper)
        expected = effect.colour.rgb[0] * 0.8
        assert out[10, 12, 0] == pytest.approx(expected, abs=1e-6)

    def test_strength_scales_the_blend(self) -> None:
        """Half strength lands halfway between the wash and the target."""
        out = casing(_wash(), _line(), Casing(width_px=3.0, strength=0.5))
        assert out[10, 12, 0] == pytest.approx(0.75)

    def test_a_pixel_below_the_threshold_is_not_a_line(self) -> None:
        """A faint mask under the threshold casts nothing."""
        faint = _line() * 0.2
        wash = _wash()
        assert casing(wash, faint, Casing(width_px=3.0)) is wash

    def test_the_threshold_selects_the_footprint(self) -> None:
        """A raised threshold drops a faint line that a lowered one casts."""
        faint = _line() * 0.5
        wash = _wash()
        assert casing(wash, faint, Casing(width_px=3.0), threshold=0.6) is wash
        assert casing(wash, faint, Casing(width_px=3.0), threshold=0.4) is not wash


class TestGlow:
    """`glow` lifts toward the paper by a hard spread and a soft blur."""

    def test_off_returns_the_input_itself(self) -> None:
        """Strength 0 returns `rgb` itself."""
        wash = _wash()
        assert glow(wash, _line(), Glow(spread_px=3.0, blur_px=2.0)) is wash

    def test_the_core_lifts_by_strength(self) -> None:
        """Inside the core with no blur the lift is strength times the gap to the paper."""
        out = glow(_wash(), _line(), Glow(spread_px=1.0, strength=0.5))
        assert out[10, 8, 0] == pytest.approx(0.75)
        assert out[10, 12, 0] == pytest.approx(0.75)
        assert out[10, 10, 0] == 0.5  # the line's own pixel is left
        assert out[10, 0, 0] == 0.5

    def test_a_pixel_brighter_than_the_paper_is_left(self) -> None:
        """The floor at 0 leaves a pixel above the paper as it was."""
        paper = np.full((SIZE, SIZE, 3), 0.4, F32)
        out = glow(_wash(), _line(), Glow(spread_px=1.0, strength=1.0), paper=paper)
        assert np.array_equal(out, _wash())

    def test_the_blur_spreads_the_lift_past_the_core(self) -> None:
        """A blur lifts pixels beyond the spread, less beside the line than further out."""
        out = glow(_wash(), _line(), Glow(spread_px=0.0, blur_px=3.0, strength=1.0))
        assert out[10, 10, 0] == 0.5
        assert 0.5 < out[10, 5, 0] < out[10, 8, 0]


class TestShadow:
    """`shadow` falls away from the light and never covers its own line."""

    @pytest.mark.parametrize(
        ("offset", "expected"),
        [(1.2, (1, 1)), (2.5, (2, 2)), (0.0, (0, 0)), (0.5, (0, 0))],
        ids=["1.2", "2.5", "zero", "half-to-even"],
    )
    def test_the_offset_is_rounded_to_whole_pixels_at_315_degrees(
        self, offset: float, expected: tuple[int, int]
    ) -> None:
        """Light from the north-west casts down and right by the rounded components."""
        assert shadow_offset(offset, 315.0) == expected

    @pytest.mark.parametrize(
        ("azimuth", "expected"),
        [(0.0, (0, 3)), (90.0, (-3, 0)), (180.0, (0, -3)), (270.0, (3, 0))],
        ids=["north", "east", "south", "west"],
    )
    def test_the_shadow_falls_away_from_the_light(
        self, azimuth: float, expected: tuple[int, int]
    ) -> None:
        """Light from the north casts down; from the east, left."""
        dx, dy = shadow_offset(3.0, azimuth)
        assert (dx, dy) == expected

    def test_the_shadow_lies_beside_the_line(self) -> None:
        """With light from the west the shadow falls right of the line, and not under it."""
        effect = Shadow(offset_px=3.0, strength=1.0, colour=Colour("#000000"))
        out = shadow(_wash(), _line(), effect, azimuth_deg=270.0)
        assert out[10, 13, 0] == 0.0
        assert out[10, 10, 0] == 0.5
        assert out[10, 0, 0] == 0.5

    def test_zero_strength_is_the_input_values(self) -> None:
        """A default shadow changes no value."""
        assert np.array_equal(shadow(_wash(), _line(), Shadow(), azimuth_deg=AZIMUTH), _wash())

    def test_a_shift_past_the_array_zero_fills(self) -> None:
        """An offset larger than the array leaves nothing, and does not wrap."""
        out = shadow(_wash(), _line(), Shadow(offset_px=16.0, strength=1.0), azimuth_deg=270.0)
        assert np.array_equal(out, _wash())


class TestPenCasing:
    """`pen_casing` knocks the wash out to the paper and returns the edge lines."""

    def test_width_zero_is_the_identity_and_no_edges(self) -> None:
        """Width 0 returns `rgb` itself and zero edges."""
        wash = _wash()
        out, edges = pen_casing(wash, _line(), PenCasing(edge_px=2.0))
        assert out is wash
        assert edges.shape == (SIZE, SIZE)
        assert not edges.any()

    def test_the_reserve_is_paper_and_the_edge_band_lies_outside(self) -> None:
        """Inside the reserve the result is the paper; the next edge_px is the edge band."""
        out, edges = pen_casing(_wash(), _line(), PenCasing(width_px=2.0, edge_px=1.0))
        assert out[10, 7, 0] == 1.0
        assert out[10, 6, 0] == 0.5
        assert edges[10, 6] == 1.0
        assert edges[10, 7] == 0.0
        assert edges[10, 0] == 0.0
        assert edges.dtype == F32

    def test_the_paper_plate_is_laid_in_the_reserve(self) -> None:
        """With a paper plate the reserve takes the plate's pixels."""
        paper = np.full((SIZE, SIZE, 3), 0.9, F32)
        out, _ = pen_casing(_wash(), _line(), PenCasing(width_px=2.0), paper=paper)
        assert out[10, 10, 0] == pytest.approx(0.9)
