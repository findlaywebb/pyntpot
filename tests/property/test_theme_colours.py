"""Properties of aliases: an alias to a name stands for that pigment, a hex for the anonymous one."""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from pyntpot.ink import PIGMENT_REGISTRY, pigment
from pyntpot.maps.theme_check import check_theme_scoped
from pyntpot.maps.theme_scope import ThemeScope, resolve_colour, resolve_pigment

from support.properties import UNTIMED
from support.theme_files import theme_file

SLOW_DRAWS = settings(
    UNTIMED, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
)

ALIASES = st.from_regex("^[a-z][a-z0-9]*(_[a-z0-9]+)*$", fullmatch=True).filter(
    lambda name: name not in PIGMENT_REGISTRY
)
NAMES = st.sampled_from(PIGMENT_REGISTRY.names())
HEX = st.from_regex("^#[0-9a-f]{6}$", fullmatch=True)


def _scope(alias: str, value: str) -> ThemeScope:
    """The scope after a theme binding `alias` to `value`, with no problem."""
    _, problems, scope = check_theme_scoped(
        theme_file(f"colours:\n  {alias}: '{value}'\n"), {}, ThemeScope.built_in()
    )
    assert problems == ()
    return scope


@SLOW_DRAWS
@given(alias=ALIASES, name=NAMES)
def test_an_alias_to_a_name_yields_that_pigments_colour_and_transparency(
    alias: str, name: str
) -> None:
    """An alias to a pigment name binds `pigment(name)` itself."""
    scope = _scope(alias, name)
    assert scope.aliases[alias].value == pigment(name)
    assert resolve_colour(alias, scope) == pigment(name).colour
    assert resolve_pigment(alias, scope).transparency == pigment(name).transparency


@SLOW_DRAWS
@given(alias=ALIASES, hex_s=HEX)
def test_an_alias_to_a_hex_binds_the_anonymous_pigment(alias: str, hex_s: str) -> None:
    """An alias to a lower-case hex binds `pigment(hex)`."""
    assert _scope(alias, hex_s).aliases[alias].value == pigment(hex_s)
