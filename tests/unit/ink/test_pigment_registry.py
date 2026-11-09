"""Tests for the pigment registry: 25 pinned entries, one lookup, one miss message."""

import dataclasses

import pytest

from pyntpot.ink import (
    PAINTERS_PIGMENTS,
    PAINTERS_TRANSPARENCY,
    PIGMENT_REGISTRY,
    PIGMENTS,
    TRANSPARENCY,
    Colour,
    Pigment,
    PigmentRegistry,
    pigment,
)

#: (name, hex, transparency, Colour Index code), registry order: 15 map roles, then 10 tubes.
PINNED: tuple[tuple[str, str, float, str | None], ...] = (
    ("farmland", "#dfe0b0", 0.10, None),
    ("meadow", "#cfdfae", 0.09, None),
    ("orchard", "#d5dda2", 0.09, None),
    ("scrub", "#c9d5a4", 0.08, None),
    ("heath", "#e0cda2", 0.14, None),
    ("sand", "#ecdfbe", 0.16, None),
    ("rock", "#dcd6c6", 0.22, None),
    ("wetland", "#bfd2cd", 0.08, None),
    ("built", "#ddd3c3", 0.26, None),
    ("works", "#d2cbc0", 0.28, None),
    ("wood", "#a8c286", 0.05, None),
    ("pale", "#d5e0b4", 0.12, None),
    ("water", "#9ec4de", 0.04, None),
    ("relief", "#c9bda4", 0.30, None),
    ("rim", "#c2ad91", 0.18, None),
    ("ultramarine", "#2b3d8f", 0.06, "PB29"),
    ("cerulean", "#2a7ab0", 0.22, "PB35"),
    ("burnt_sienna", "#8a3b1c", 0.20, "PBr7"),
    ("raw_sienna", "#b8692a", 0.18, "PBr7"),
    ("yellow_ochre", "#c99a3a", 0.24, "PY43"),
    ("sap_green", "#3f6b2a", 0.07, None),
    ("indigo", "#2c3346", 0.05, None),
    ("perylene_maroon", "#5a1f27", 0.04, "PR179"),
    ("quinacridone_rose", "#b8215e", 0.05, "PV19"),
    ("paynes_grey", "#3b4452", 0.10, None),
)


class TestEntries:
    """The shared registry holds exactly the pinned pigments."""

    def test_there_are_twenty_five_in_pinned_order(self):
        """Names come back in registry order."""
        assert PIGMENT_REGISTRY.names() == tuple(row[0] for row in PINNED)

    @pytest.mark.parametrize("row", PINNED, ids=[row[0] for row in PINNED])
    def test_each_entry_equals_its_pinned_literal(self, row: tuple[str, str, float, str | None]):
        """Every pigment carries its pinned colour, transparency and Colour Index."""
        name, hex_s, transparency, index = row
        assert PIGMENT_REGISTRY.get(name) == Pigment(
            name=name, colour=Colour(hex_s), transparency=transparency, colour_index=index
        )

    def test_a_pigment_is_frozen(self):
        """A pigment refuses assignment."""
        with pytest.raises(dataclasses.FrozenInstanceError):
            PIGMENT_REGISTRY.get("wood").name = "forest"  # ty: ignore[invalid-assignment]


class TestLookup:
    """`pigment` is the one lookup, and the registry writes the one miss message."""

    def test_a_name_gives_its_entry(self):
        """A canonical name resolves through the registry."""
        assert pigment("ultramarine") is PIGMENT_REGISTRY.get("ultramarine")

    def test_a_pigment_gives_itself(self):
        """A `Pigment` returns as the same object."""
        p = PIGMENT_REGISTRY.get("wood")
        assert pigment(p) is p

    def test_a_hex_gives_an_anonymous_pigment(self):
        """A `#rrggbb` gives a pigment named by the hex, with no transparency or index."""
        assert pigment("#ABCDEF") == Pigment(
            name="#abcdef", colour=Colour("#abcdef"), transparency=None, colour_index=None
        )

    def test_a_miss_suggests_the_nearest_name(self):
        """The registry's message names the nearest pigment."""
        with pytest.raises(ValueError) as caught:
            pigment("ultramarin")
        assert str(caught.value) == "no pigment 'ultramarin'; did you mean ultramarine?"

    def test_a_far_miss_has_no_suggestion(self):
        """With nothing near, the message carries no clause."""
        with pytest.raises(ValueError) as caught:
            PIGMENT_REGISTRY.get("zzzzzz")
        assert str(caught.value) == "no pigment 'zzzzzz'"

    def test_a_bad_hex_is_refused_by_colour(self):
        """A `#` reference that is not six hexadecimal digits raises."""
        with pytest.raises(ValueError, match="six hexadecimal digits"):
            pigment("#abc")

    def test_a_name_looks_in_the_registry_it_is_given(self):
        """The second argument replaces the shared registry."""
        extra = Pigment(
            name="my_blue", colour=Colour("#102030"), transparency=0.5, colour_index=None
        )
        registry = PIGMENT_REGISTRY.extended((extra,))
        assert pigment("my_blue", registry) is extra
        with pytest.raises(ValueError, match="no pigment 'my_blue'"):
            pigment("my_blue")


class TestRegistry:
    """A registry refuses duplicates and is extended into a new one."""

    def test_contains_reads_names(self):
        """`in` asks for a name."""
        assert "ultramarine" in PIGMENT_REGISTRY
        assert "blue" not in PIGMENT_REGISTRY

    def test_a_duplicate_name_is_refused(self):
        """Two entries of one name raise, naming it."""
        wood = PIGMENT_REGISTRY.get("wood")
        with pytest.raises(ValueError, match="duplicate pigment 'wood'"):
            PigmentRegistry((wood, wood))

    def test_extending_with_a_built_in_name_is_refused(self):
        """A built-in name cannot be added."""
        clash = dataclasses.replace(PIGMENT_REGISTRY.get("wood"), colour=Colour("#000000"))
        with pytest.raises(ValueError, match="duplicate pigment 'wood'"):
            PIGMENT_REGISTRY.extended((clash,))

    def test_extending_leaves_the_base_alone(self):
        """`extended` returns a new registry; the shared one keeps 25."""
        extra = Pigment(
            name="my_blue", colour=Colour("#102030"), transparency=None, colour_index=None
        )
        bigger = PIGMENT_REGISTRY.extended((extra,))
        assert len(bigger.names()) == 26
        assert len(PIGMENT_REGISTRY.names()) == 25
        assert bigger.names()[-1] == "my_blue"


class TestTables:
    """The four exported tables are the registry's projection, in its order."""

    def test_map_roles(self):
        """`PIGMENTS` and `TRANSPARENCY` are the first fifteen entries."""
        roles = PIGMENT_REGISTRY.pigments[:15]
        assert list(PIGMENTS.items()) == [(p.name, p.colour) for p in roles]
        assert list(TRANSPARENCY.items()) == [(p.name, p.transparency) for p in roles]

    def test_painters_pigments(self):
        """`PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY` are the last ten."""
        tubes = PIGMENT_REGISTRY.pigments[15:]
        assert list(PAINTERS_PIGMENTS.items()) == [(p.name, p.colour) for p in tubes]
        assert list(PAINTERS_TRANSPARENCY.items()) == [(p.name, p.transparency) for p in tubes]

    def test_the_tables_equal_pinned_literals(self):
        """The tables hold today's plain values, independent of the registry."""
        assert {k: str(v) for k, v in PIGMENTS.items()} == {r[0]: r[1] for r in PINNED[:15]}
        assert {r[0]: r[2] for r in PINNED[:15]} == TRANSPARENCY
        assert {k: str(v) for k, v in PAINTERS_PIGMENTS.items()} == {
            r[0]: r[1] for r in PINNED[15:]
        }
        assert {r[0]: r[2] for r in PINNED[15:]} == PAINTERS_TRANSPARENCY
