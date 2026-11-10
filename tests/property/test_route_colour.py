"""A fed route colour reaches every route-coloured field, in the default style and every theme."""

from hypothesis import given
from hypothesis import strategies as st

from pyntpot.maps import Style

from support.properties import UNTIMED

HEX = st.from_regex("^#[0-9a-fA-F]{6}$", fullmatch=True)
STYLES = st.sampled_from((None, *Style.themes()))


@UNTIMED
@given(colour=HEX, theme=STYLES)
def test_a_fed_route_colour_reaches_every_route_coloured_field(
    colour: str, theme: str | None
) -> None:
    """A fed `#rrggbb`, in either case, is the route's colour and the nib's resolved route ink in lower case."""
    style = Style() if theme is None else Style.named(theme)
    fed = style.with_route_ink(colour=colour)
    assert fed.route_ink.colour == colour.lower()
    assert fed.nib.label_route_ink == colour.lower()
    assert fed.base_digest() == style.base_digest()
