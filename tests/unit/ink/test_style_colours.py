"""`normalise_colours` and the ink groups that call it."""

import dataclasses

import pytest

from pyntpot.ink import Colour, PaperStyle, WashStyle
from pyntpot.ink.colour import normalise_colours


@dataclasses.dataclass(frozen=True)
class _Inked:
    """A frozen group with a scalar and a dict colour field."""

    one: object
    many: object


class TestNormaliseColours:
    """The one coercion."""

    def test_a_plain_field_becomes_a_lower_case_colour(self):
        """A named scalar field is set to the parsed `Colour`."""
        group = _Inked(one="#ABCDEF", many={})
        normalise_colours(group, "one")
        assert type(group.one) is Colour
        assert group.one == "#abcdef"

    def test_a_dict_field_is_rebuilt_with_parsed_values(self):
        """A named dict field keeps its keys and parses every value."""
        group = _Inked(one="#000000", many={"a": "#ABCDEF", "b": "#012345"})
        normalise_colours(group, "many")
        assert group.many == {"a": "#abcdef", "b": "#012345"}
        assert isinstance(group.many, dict)
        assert all(type(v) is Colour for v in group.many.values())

    def test_a_colour_comes_back_as_itself(self):
        """A field already holding a `Colour` keeps that very object."""
        colour = Colour("#abcdef")
        group = _Inked(one=colour, many={})
        normalise_colours(group, "one")
        assert group.one is colour

    def test_an_unnamed_field_is_left_alone(self):
        """A field not named is not parsed."""
        group = _Inked(one="#ABCDEF", many={})
        normalise_colours(group, "many")
        assert group.one == "#ABCDEF"

    @pytest.mark.parametrize("bad", ["red", "#abc", 5], ids=["name", "short", "number"])
    def test_a_bad_value_raises(self, bad):
        """A value that is no hex colour raises `ValueError`."""
        with pytest.raises(ValueError, match="is not"):
            normalise_colours(_Inked(one=bad, many={}), "one")

    def test_a_bad_dict_value_raises(self):
        """A bad value inside a dict field raises `ValueError`."""
        with pytest.raises(ValueError, match="is not a # and six"):
            normalise_colours(_Inked(one="#000000", many={"a": "blue"}), "many")


class TestGroupHooks:
    """`PaperStyle` and `WashStyle` normalise on construction."""

    def test_paper_normalises_its_colour(self):
        """`PaperStyle(paper_hex="#ABCDEF")` holds a lower-case `Colour`."""
        paper = PaperStyle(paper_hex="#ABCDEF")  # ty: ignore[invalid-argument-type]
        assert type(paper.paper_hex) is Colour
        assert paper.paper_hex == "#abcdef"

    def test_wash_normalises_its_separation_pigments(self):
        """`WashStyle` holds its separation pigments as lower-case `Colour` values."""
        wash = WashStyle(separation_pigments={"wood": "#ABCDEF"})  # ty: ignore[invalid-argument-type]
        assert type(wash.separation_pigments["wood"]) is Colour
        assert wash.separation_pigments == {"wood": "#abcdef"}

    def test_a_bad_paper_colour_raises(self):
        """A paper colour that is no hex raises at construction."""
        with pytest.raises(ValueError, match="is not a # and six"):
            PaperStyle(paper_hex="cream")  # ty: ignore[invalid-argument-type]
