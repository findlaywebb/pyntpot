"""Properties of the pigment registry: extension is safe, and a hex is an anonymous pigment."""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from pyntpot.ink import PIGMENT_REGISTRY, Colour, Pigment, pigment, rgb

from support.properties import UNTIMED

#: Drawing names from a regex is slow, and the properties are about the registry, not speed.
SLOW_DRAWS = settings(
    UNTIMED, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
)

NAMES = st.from_regex("^[a-z][a-z0-9]*(_[a-z0-9]+)*$", fullmatch=True)
HEX = st.from_regex("^#[0-9a-f]{6}$", fullmatch=True)
HEX_ANY_CASE = st.from_regex("^#[0-9a-fA-F]{6}$", fullmatch=True)
TRANSPARENCY = st.none() | st.floats(0, 1)
BUILT_IN = st.sampled_from(PIGMENT_REGISTRY.names())


def _pigments(names: st.SearchStrategy[str]) -> st.SearchStrategy[Pigment]:
    return st.builds(
        Pigment,
        name=names,
        colour=HEX.map(Colour),
        transparency=TRANSPARENCY,
        colour_index=st.none() | st.text(min_size=1, max_size=6),
    )


NEW = _pigments(NAMES.filter(lambda n: n not in PIGMENT_REGISTRY))


@SLOW_DRAWS
@given(name=BUILT_IN)
def test_an_empty_extension_resolves_every_name_identically(name: str):
    """`extended(())` is the identity on lookups."""
    assert PIGMENT_REGISTRY.extended(()).get(name) == PIGMENT_REGISTRY.get(name)


@SLOW_DRAWS
@given(clash=_pigments(BUILT_IN))
def test_an_extension_naming_a_built_in_raises(clash: Pigment):
    """A caller's pigment never shadows a built-in."""
    with pytest.raises(ValueError, match="with base: "):
        PIGMENT_REGISTRY.extended((clash,))


@SLOW_DRAWS
@given(added=st.lists(NEW, max_size=3, unique_by=lambda p: p.name), name=BUILT_IN)
def test_a_non_colliding_extension_leaves_built_ins_and_the_base_alone(
    added: list[Pigment], name: str
):
    """Every built-in lookup is equal in the extension, and the base keeps its 25."""
    bigger = PIGMENT_REGISTRY.extended(tuple(added))
    assert bigger.get(name) == PIGMENT_REGISTRY.get(name)
    assert all(bigger.get(p.name) == p for p in added)
    assert len(PIGMENT_REGISTRY.names()) == 25


@SLOW_DRAWS
@given(h=HEX_ANY_CASE)
def test_colour_rgb_equals_the_rgb_function(h: str):
    """`Colour.parse(h).rgb` is `rgb(h)`, byte for byte."""
    assert Colour.parse(h).rgb.tobytes() == rgb(h).tobytes()


@SLOW_DRAWS
@given(h=HEX_ANY_CASE)
def test_a_hex_is_an_anonymous_pigment(h: str):
    """`pigment(h)` is named by the lower-case hex, with no transparency or index."""
    assert pigment(h) == Pigment(
        name=h.lower(), colour=Colour.parse(h), transparency=None, colour_index=None
    )
