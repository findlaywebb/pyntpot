"""Properties of the `.gpl` round trip: colours survive, and an import is anonymous."""

from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from pyntpot.ink import PIGMENT_REGISTRY, pigment
from pyntpot.maps.theme_palette import Palette
from pyntpot.maps.theme_palette_gpl import parse_gpl

from support.properties import UNTIMED

SLOW_DRAWS = settings(
    UNTIMED, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
)

ALIASES = st.from_regex("^[a-z][a-z0-9]*(_[a-z0-9]+)*$", fullmatch=True).filter(
    lambda name: name not in PIGMENT_REGISTRY
)
HEX = st.from_regex("^#[0-9a-f]{6}$", fullmatch=True)


@SLOW_DRAWS
@given(table=st.dictionaries(ALIASES, HEX, max_size=8))
def test_a_gpl_round_trip_keeps_every_alias_colour(table: dict[str, str]) -> None:
    """Export then import is equal at the colour level, and every imported pigment is anonymous."""
    palette = Palette("p", {alias: pigment(hex_s) for alias, hex_s in table.items()})
    aliases, problems = parse_gpl(Path("p.gpl"), palette.to_gpl())
    assert problems == ()
    assert {alias: one.colour for alias, one in aliases.items()} == {
        alias: one.colour for alias, one in palette.pigments.items()
    }
    assert all(one.transparency is None and one.colour_index is None for one in aliases.values())
