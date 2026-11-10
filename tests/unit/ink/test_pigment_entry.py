"""The pigment table's row builder keeps every field it is given."""

from pyntpot.ink.colour import Colour
from pyntpot.ink.pigment_table import ROLE_PIGMENTS, TRANSPARENCY, _entry, role_transparencies


def test_an_entry_keeps_its_name_colour_transparency_and_index() -> None:
    """A row built from four values holds each of them, the hex as a `Colour`."""
    pigment = _entry("ultramarine", "#2b3d8f", 0.4, "PB29")
    assert pigment.name == "ultramarine"
    assert isinstance(pigment.colour, Colour)
    assert pigment.colour == "#2b3d8f"
    assert pigment.transparency == 0.4
    assert pigment.colour_index == "PB29"


def test_an_entry_without_an_index_has_none() -> None:
    """The colour index defaults to `None`."""
    assert _entry("sand", "#ecdfbe", 0.16).colour_index is None


def test_role_transparencies_is_a_fresh_copy_of_the_role_table() -> None:
    """A direct call returns each role pigment's transparency, in a dict of its own."""
    first = role_transparencies()
    assert first == TRANSPARENCY
    assert list(first) == [p.name for p in ROLE_PIGMENTS]
    assert first is not TRANSPARENCY
    assert role_transparencies() is not first
