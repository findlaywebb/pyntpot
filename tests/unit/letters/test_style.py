"""The letters style groups: frozen records built by keyword only."""

import dataclasses
from collections.abc import Callable

import pytest

from pyntpot.ink import Colour
from pyntpot.letters import FaceStyle, HandStyle, NibStyle

#: Each group with its first field and a value other than the default.
GROUPS: tuple[tuple[Callable[..., object], str, object], ...] = (
    (FaceStyle, "label_route", "outline"),
    (HandStyle, "label_seed", 3),
    (NibStyle, "label_size_px", 14.0),
)


@pytest.mark.parametrize(
    ("group", "field", "value"), GROUPS, ids=["FaceStyle", "HandStyle", "NibStyle"]
)
def test_a_letters_style_group_takes_only_keywords(
    group: Callable[..., object], field: str, value: object
) -> None:
    """A letters style group refuses a positional field and builds from its keywords."""
    with pytest.raises(TypeError):
        group(value)
    assert getattr(group(**{field: value}), field) == value


def test_nib_style_normalises_its_four_inks() -> None:
    """`NibStyle` holds each ink as a lower-case `Colour`, whatever case it was given."""
    nib = NibStyle(
        label_ink="#ABCDEF",  # ty: ignore[invalid-argument-type]
        label_route_ink="#ABCDE0",  # ty: ignore[invalid-argument-type]
        label_water_ink="#ABCD0F",  # ty: ignore[invalid-argument-type]
        label_in_water_ink="#AB0DEF",  # ty: ignore[invalid-argument-type]
    )
    inks = (nib.label_ink, nib.label_route_ink, nib.label_water_ink, nib.label_in_water_ink)
    assert inks == ("#abcdef", "#abcde0", "#abcd0f", "#ab0def")
    assert all(type(ink) is Colour for ink in inks)


@pytest.mark.parametrize(
    "name",
    ["label_ink", "label_route_ink", "label_water_ink", "label_in_water_ink"],
)
def test_nib_style_refuses_a_bad_ink(name: str) -> None:
    """Each of the four inks raises `ValueError` when it is no hex colour."""
    with pytest.raises(ValueError, match="is not a # and six"):
        dataclasses.replace(NibStyle(), **{name: "ink"})
