"""The scoped theme vocabulary: bound entries, lookup order and the extended registry."""

from pathlib import Path

import pytest

from pyntpot.ink import PIGMENT_REGISTRY, Colour, Pigment, pigment
from pyntpot.maps.theme_palette import Palette
from pyntpot.maps.theme_scope import Bound, ThemeScope, resolve_colour, resolve_pigment

FILE = Path("theme.yaml")


def _bound(value: Pigment, line: int = 3) -> Bound[Pigment]:
    """`value` bound at `line` of the test file."""
    return Bound(value, FILE, line)


class TestBound:
    """An entry carries the file and line that wrote it."""

    def test_bound_carries_path_and_line(self):
        """`Bound` holds the value, the file and the line."""
        entry = Bound(pigment("indigo"), FILE, 7)
        assert (entry.value, entry.path, entry.line) == (pigment("indigo"), FILE, 7)


class TestBuiltIn:
    """The empty scope."""

    def test_built_in_has_nothing(self):
        """`built_in()` has no theme pigments, palette, aliases or presets."""
        scope = ThemeScope.built_in()
        assert (scope.pigments, scope.palette, scope.aliases, scope.presets) == ({}, None, {}, {})

    def test_the_built_in_registry_is_the_shared_one(self):
        """With no theme pigment, `registry` has the 25 built-ins."""
        assert ThemeScope.built_in().registry.names() == PIGMENT_REGISTRY.names()

    def test_registry_holds_the_theme_pigments(self):
        """`registry` is the built-ins followed by the theme's own pigments."""
        mine = Pigment(
            name="my_blue", colour=Colour("#102030"), transparency=0.2, colour_index=None
        )
        scope = ThemeScope(pigments={"my_blue": _bound(mine)})
        assert scope.registry.names() == (*PIGMENT_REGISTRY.names(), "my_blue")
        assert resolve_colour("my_blue", scope) == "#102030"

    def test_a_scope_is_frozen(self):
        """A scope refuses assignment."""
        with pytest.raises(AttributeError):
            ThemeScope.built_in().palette = None  # ty: ignore[invalid-assignment]


class TestResolveOrder:
    """A theme alias, then a palette alias, then a registry name."""

    def test_a_theme_alias_beats_a_palette_alias_and_a_name(self):
        """With one name in all three, the theme alias wins."""
        scope = ThemeScope(
            aliases={"indigo": _bound(pigment("#111111"))},
            palette=Bound(Palette("test", {"indigo": pigment("#222222")}), FILE, 1),
        )
        assert resolve_colour("indigo", scope) == "#111111"

    def test_a_palette_alias_beats_a_registry_name(self):
        """A palette alias that is also a registry name wins over the registry."""
        scope = ThemeScope(palette=Bound(Palette("test", {"indigo": pigment("#222222")}), FILE, 1))
        assert resolve_colour("indigo", scope) == "#222222"

    def test_a_registry_name_resolves_last(self):
        """With no alias, a pigment name gives the registry's colour."""
        assert resolve_colour("ultramarine", ThemeScope.built_in()) == "#2b3d8f"

    def test_an_alias_keeps_its_pigment_and_transparency(self):
        """An alias bound to a pigment resolves to that pigment, transparency included."""
        scope = ThemeScope(aliases={"sky": _bound(pigment("cerulean"))})
        assert resolve_pigment("sky", scope) == pigment("cerulean")
        assert resolve_pigment("sky", scope).transparency == pigment("cerulean").transparency

    def test_a_hex_is_the_anonymous_pigment(self):
        """A hex in either case resolves to `pigment("#...")`."""
        assert resolve_pigment("#ABCDEF", ThemeScope.built_in()) == pigment("#abcdef")

    def test_a_bad_hex_is_the_colour_message(self):
        """A `#` that is not six hex digits reads as the colour message."""
        with pytest.raises(ValueError, match="'#a8c28' is not a # and six hexadecimal digits"):
            resolve_colour("#a8c28", ThemeScope.built_in())


class TestMiss:
    """A name nothing binds."""

    def test_a_miss_suggests_the_nearest(self):
        """A near miss names the nearest pigment."""
        with pytest.raises(
            ValueError,
            match="'ultramarin' is not a pigment or a colour alias; did you mean ultramarine",
        ):
            resolve_pigment("ultramarin", ThemeScope.built_in())

    def test_a_far_miss_has_no_suggestion(self):
        """A name near nothing carries no suggestion clause."""
        with pytest.raises(ValueError) as caught:
            resolve_pigment("red", ThemeScope.built_in())
        assert str(caught.value) == "'red' is not a pigment or a colour alias"

    def test_a_miss_suggests_an_alias(self):
        """The suggestion draws on aliases as well as pigment names."""
        scope = ThemeScope(aliases={"hillside": _bound(pigment("sap_green"))})
        with pytest.raises(ValueError, match="did you mean hillside"):
            resolve_pigment("hillsides", scope)
