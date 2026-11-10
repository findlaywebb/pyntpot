"""Tests for `Colour`: the one `#rrggbb` value, parsed and converted in one place."""

import copy
import dataclasses
import json
import pickle

import numpy as np
import pytest

from pyntpot.ink import Colour, rgb


@dataclasses.dataclass
class _Holder:
    """A plain dataclass holding one colour, to show `asdict` keeps it a string."""

    colour: Colour


class TestConstruction:
    """`Colour(text)` takes only a lower-case `#rrggbb`."""

    def test_a_lower_case_hex_is_kept_as_it_is(self):
        """A valid hex is the same string, and a `str`."""
        c = Colour("#f3ead6")
        assert c == "#f3ead6"
        assert isinstance(c, str)

    @pytest.mark.parametrize(
        "text",
        ["#F3EAD6", "f3ead6", "#f3ead", "#f3ead6f", "#f3ead6\n", "#gggggg", "", " #f3ead6"],
        ids=["upper", "no-hash", "short", "long", "newline", "not-hex", "empty", "space"],
    )
    def test_anything_else_is_refused(self, text: str):
        """Upper case, a missing `#`, a wrong length or a non-hex digit raises `ValueError`."""
        with pytest.raises(ValueError, match="six hexadecimal digits"):
            Colour(text)


class TestParse:
    """`Colour.parse` lower-cases, and refuses what is not a string."""

    def test_parse_lower_cases_a_hex(self):
        """An upper-case hex is stored lower-case."""
        assert Colour.parse("#ABCDEF") == "#abcdef"
        assert type(Colour.parse("#ABCDEF")) is Colour

    def test_parse_returns_a_colour_as_itself(self):
        """A `Colour` passes through as the same object."""
        c = Colour("#abcdef")
        assert Colour.parse(c) is c

    @pytest.mark.parametrize("text", ["red", "#abc", "#12345g", "abcdef", ""], ids=str)
    def test_parse_refuses_a_bad_string(self, text: str):
        """A string that is not a `#` and six hexadecimal digits raises, naming it."""
        with pytest.raises(ValueError, match="is not a # and six hexadecimal digits"):
            Colour.parse(text)

    def test_parse_refuses_an_integer(self):
        """An integer is a `ValueError`, never an `AttributeError`."""
        with pytest.raises(ValueError, match="is not a string"):
            Colour.parse(5)  # ty: ignore[invalid-argument-type]

    def test_parse_refuses_none(self):
        """`None` is a `ValueError`, never an `AttributeError`."""
        with pytest.raises(ValueError, match="is not a string"):
            Colour.parse(None)  # ty: ignore[invalid-argument-type]


class TestChannels:
    """`.rgb` and `.rgb8` read the hex the way `rgb` always has."""

    def test_rgb_is_float32_in_unit_range(self):
        """`.rgb` is three float32 values, each a byte over 255."""
        out = Colour("#ff8000").rgb
        assert out.dtype == np.float32
        assert out.tolist() == pytest.approx([1.0, 128 / 255, 0.0])

    def test_rgb_equals_the_public_rgb_function_bit_for_bit(self):
        """The method and `rgb` share one arithmetic."""
        assert Colour("#a8c286").rgb.tobytes() == rgb("#a8c286").tobytes()

    def test_rgb8_is_the_three_bytes(self):
        """`.rgb8` is the three channels as integers."""
        assert Colour("#2b3d8f").rgb8 == (0x2B, 0x3D, 0x8F)

    def test_rgb_keeps_its_loose_reading_of_the_function(self):
        """`rgb` still takes the `#` as optional and ignores characters after the sixth digit."""
        assert rgb("2b3d8fzz").tobytes() == Colour("#2b3d8f").rgb.tobytes()


class TestRoundTrips:
    """A `Colour` survives copying, pickling and serialising as the string it is."""

    def test_deepcopy_and_copy_keep_the_type(self):
        """`copy` and `deepcopy` give an equal `Colour`."""
        c = Colour("#2b3d8f")
        assert type(copy.deepcopy(c)) is Colour
        assert type(copy.copy(c)) is Colour
        assert copy.deepcopy(c) == c

    def test_pickle_keeps_the_type(self):
        """A pickle round trip gives an equal `Colour`."""
        c = Colour("#2b3d8f")
        back = pickle.loads(pickle.dumps(c))
        assert type(back) is Colour
        assert back == c

    def test_asdict_and_json_hash_it_as_the_string(self):
        """`asdict` keeps the leaf and `json.dumps` writes the plain string."""
        d = dataclasses.asdict(_Holder(Colour("#2b3d8f")))
        assert type(d["colour"]) is Colour
        assert json.dumps(d) == '{"colour": "#2b3d8f"}'

    def test_it_carries_no_instance_dict(self):
        """`__slots__` is empty, so a colour holds only its string."""
        assert not hasattr(Colour("#2b3d8f"), "__dict__")
