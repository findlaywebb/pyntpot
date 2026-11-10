"""The fields left out of a digest at their default: unique names, and which digest an effect moves."""

import dataclasses
from collections import Counter

import pytest

from pyntpot.ink import Casing
from pyntpot.maps import EffectStack, Style
from pyntpot.maps.line_effects import BUILT_IN_PRESETS
from pyntpot.maps.style import DIGEST_OMITS_AT_DEFAULT

#: The default style's `digest`, `base_digest` and `lettering_digest`, measured before the effect fields.
DEFAULT_DIGESTS = ("88b356ada294ff60", "d9c56c0811177b0f", "d15ae2f30e9ca5ce")


def _digests(style: Style) -> tuple[str, str, str]:
    """The style's `digest`, `base_digest` and `lettering_digest`."""
    return style.digest(), style.base_digest(), style.lettering_digest()


def _with_basemap_stack() -> Style:
    """The default style with a `cased` stack on `major`."""
    default = Style()
    basemap = dataclasses.replace(
        default.basemap, line_effects={"major": BUILT_IN_PRESETS["cased"]}
    )
    return default.model_copy(update={"basemap": basemap})


def _with_route_stack() -> Style:
    """The default style with a `cased` stack on the route."""
    default = Style()
    ink = dataclasses.replace(default.route_ink, effects=BUILT_IN_PRESETS["cased"])
    return default.model_copy(update={"route_ink": ink})


class TestTheOmitNames:
    """The names the digest leaves out at the default."""

    def test_the_two_effect_fields_are_named(self) -> None:
        """`line_effects` and `effects` are in `DIGEST_OMITS_AT_DEFAULT`."""
        assert "line_effects" in DIGEST_OMITS_AT_DEFAULT
        assert "effects" in DIGEST_OMITS_AT_DEFAULT

    @pytest.mark.parametrize("name", DIGEST_OMITS_AT_DEFAULT, ids=DIGEST_OMITS_AT_DEFAULT)
    def test_each_name_matches_exactly_one_field_across_all_groups(self, name: str) -> None:
        """The rule matches by name, so a name two groups share would omit both."""
        fields = Counter(
            spec.name
            for group in Style.model_fields
            for spec in dataclasses.fields(getattr(Style(), group))
        )
        assert fields[name] == 1

    def test_the_names_are_listed_once(self) -> None:
        """No name appears twice in the tuple."""
        assert len(set(DIGEST_OMITS_AT_DEFAULT)) == len(DIGEST_OMITS_AT_DEFAULT)


class TestWhatAnEffectMoves:
    """A set stack moves the digests of the group that holds it, and no other."""

    def test_the_default_digests_are_pinned(self) -> None:
        """The default style's three digests are the ones measured before the fields existed."""
        assert _digests(Style()) == DEFAULT_DIGESTS

    def test_a_basemap_stack_moves_the_base_and_the_whole_digest(self) -> None:
        """A set `basemap.line_effects` moves `base_digest` and `digest`, not `lettering_digest`."""
        digest, base, lettering = _digests(_with_basemap_stack())
        assert digest != DEFAULT_DIGESTS[0]
        assert base != DEFAULT_DIGESTS[1]
        assert lettering == DEFAULT_DIGESTS[2]

    def test_a_route_stack_moves_only_the_whole_digest(self) -> None:
        """A set `route_ink.effects` moves `digest` and neither of the other two."""
        digest, base, lettering = _digests(_with_route_stack())
        assert digest != DEFAULT_DIGESTS[0]
        assert (base, lettering) == DEFAULT_DIGESTS[1:]

    def test_two_different_stacks_give_two_digests(self) -> None:
        """A change of a number inside a stack moves the digest."""
        wide = EffectStack(effects=(Casing(width_px=2.4),))
        basemap = dataclasses.replace(Style().basemap, line_effects={"major": wide})
        other = Style().model_copy(update={"basemap": basemap})
        assert other.base_digest() != _with_basemap_stack().base_digest()

    def test_a_value_equal_to_off_moves_nothing(self) -> None:
        """An empty or all-off stack is dropped when built, so every digest is the default's."""
        off = EffectStack(effects=(Casing(width_px=0.0),))
        basemap = dataclasses.replace(Style().basemap, line_effects={"major": off})
        ink = dataclasses.replace(Style().route_ink, effects=off)
        style = Style().model_copy(update={"basemap": basemap, "route_ink": ink})
        assert _digests(style) == DEFAULT_DIGESTS
