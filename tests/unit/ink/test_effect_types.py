"""The line effect value types: defaults, the pinned ranges, and what `__post_init__` refuses."""

import dataclasses

import pytest

from pyntpot.ink.colour import Colour
from pyntpot.ink.effect_types import EFFECT_RANGES, Casing, Glow, PenCasing, Shadow
from pyntpot.ink.pigment_registry import pigment

NUMERIC = [
    (Casing, "width_px"),
    (Casing, "strength"),
    (Glow, "spread_px"),
    (Glow, "blur_px"),
    (Glow, "strength"),
    (Shadow, "offset_px"),
    (Shadow, "blur_px"),
    (Shadow, "strength"),
    (PenCasing, "width_px"),
    (PenCasing, "edge_px"),
]
NUMERIC_IDS = [f"{cls.__name__}-{name}" for cls, name in NUMERIC]


class TestDefaults:
    """Each type is default-constructible and off."""

    def test_casing(self) -> None:
        """A default casing is white, full strength and zero wide."""
        c = Casing()
        assert (c.width_px, c.colour, c.strength) == (0.0, "#ffffff", 1.0)
        assert isinstance(c.colour, Colour)

    def test_glow(self) -> None:
        """A default glow has no spread, no blur and no strength."""
        assert dataclasses.astuple(Glow()) == (0.0, 0.0, 0.0)

    def test_shadow(self) -> None:
        """A default shadow is Payne's grey, with no offset, blur or strength."""
        s = Shadow()
        assert (s.offset_px, s.blur_px, s.strength) == (0.0, 0.0, 0.0)
        assert s.colour == pigment("paynes_grey").colour

    def test_pen_casing(self) -> None:
        """A default pen casing has no width and no edge."""
        assert dataclasses.astuple(PenCasing()) == (0.0, 0.0)

    def test_the_types_are_frozen_and_keyword_only(self) -> None:
        """A type refuses assignment and positional arguments."""
        with pytest.raises(dataclasses.FrozenInstanceError):
            Glow().strength = 0.5  # type: ignore[misc]  # ty: ignore[invalid-assignment]
        with pytest.raises(TypeError):
            Glow(1.0)  # type: ignore[misc]  # ty: ignore[too-many-positional-arguments]


class TestRanges:
    """`EFFECT_RANGES` and what the types refuse."""

    def test_the_table_is_pinned(self) -> None:
        """The ranges are the literal table: pixels 0 to 16, strength 0 to 1."""
        assert dict(EFFECT_RANGES) == {
            "width_px": (0.0, 16.0),
            "edge_px": (0.0, 16.0),
            "spread_px": (0.0, 16.0),
            "blur_px": (0.0, 16.0),
            "offset_px": (0.0, 16.0),
            "strength": (0.0, 1.0),
        }

    def test_the_table_is_read_only(self) -> None:
        """The ranges cannot be edited in place."""
        with pytest.raises(TypeError):
            EFFECT_RANGES["width_px"] = (0.0, 1.0)  # type: ignore[index]  # ty: ignore[invalid-assignment]

    @pytest.mark.parametrize(("cls", "name"), NUMERIC, ids=NUMERIC_IDS)
    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")], ids=str)
    def test_a_non_finite_number_is_refused(self, cls: type, name: str, bad: float) -> None:
        """A nan or an infinity names its field and is refused."""
        with pytest.raises(ValueError, match=name):
            cls(**{name: bad})

    @pytest.mark.parametrize(("cls", "name"), NUMERIC, ids=NUMERIC_IDS)
    def test_a_negative_number_is_refused(self, cls: type, name: str) -> None:
        """A value below 0 names its field and is refused."""
        with pytest.raises(ValueError, match=name):
            cls(**{name: -0.5})

    @pytest.mark.parametrize("cls", [Casing, Glow, Shadow], ids=lambda c: c.__name__)
    def test_a_strength_above_one_is_refused(self, cls: type) -> None:
        """A strength of 1.5 is refused with its range."""
        with pytest.raises(ValueError, match=r"strength must be in 0\.0 to 1\.0"):
            cls(strength=1.5)

    def test_negative_zero_is_accepted(self) -> None:
        """A width of -0.0 is zero, not negative."""
        assert Casing(width_px=-0.0).width_px == 0

    def test_the_bounds_are_accepted(self) -> None:
        """Both ends of each range are accepted."""
        assert Glow(spread_px=16.0, strength=1.0).spread_px == 16.0
        assert Glow(spread_px=0.0, strength=0.0).strength == 0.0

    def test_array_pixels_have_no_upper_bound(self) -> None:
        """A width above 16 is accepted: the bound is a display-pixel bound checked at load."""
        assert Casing(width_px=100.0).width_px == 100.0
        assert PenCasing(width_px=100.0, edge_px=40.0).edge_px == 40.0


class TestColours:
    """`Casing` and `Shadow` hold a `Colour`."""

    @pytest.mark.parametrize("cls", [Casing, Shadow], ids=lambda c: c.__name__)
    def test_a_string_colour_is_normalised(self, cls: type) -> None:
        """An upper-case `str` becomes a lower-case `Colour`."""
        c = cls(colour="#AABBCC").colour
        assert type(c) is Colour
        assert c == "#aabbcc"

    @pytest.mark.parametrize("cls", [Casing, Shadow], ids=lambda c: c.__name__)
    def test_a_bad_colour_is_refused(self, cls: type) -> None:
        """A string that is not a hex colour is refused."""
        with pytest.raises(ValueError, match="hexadecimal"):
            cls(colour="red")
