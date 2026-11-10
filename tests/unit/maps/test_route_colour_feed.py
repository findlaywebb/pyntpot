"""A fed route colour is every route-coloured field's colour, and moves the lettering digest."""

import pytest

from pyntpot.maps import Style

from support.colour_fields import colour_paths

FED = "#2050c2"

#: The default style fed `FED`, its lettering digest measured, pinned.
FED_LETTERING_DIGEST = "925e40ac5a5d8bd8"
FED_DIGEST = "be95e8d02d455997"


def test_every_colour_field_defaulting_to_the_route_colour_follows_a_fed_one() -> None:
    """Each `Colour` field that defaults to the route's colour is the fed colour; no other `Colour` field moves."""
    style = Style()
    fed = style.with_route_ink(colour=FED)
    route = style.route_ink.colour
    follow = []
    for path in colour_paths(style):
        if path[-1] == "*":
            # A dict of colours is keyed by role; none of them defaults to the route's colour.
            continue
        group, name = path
        before = getattr(getattr(style, group), name)
        after = getattr(getattr(fed, group), name)
        if before == route:
            follow.append(path)
            assert after == FED, path
        else:
            assert after == before, path
    assert follow == [("nib", "label_route_ink"), ("route_ink", "colour")]


@pytest.mark.parametrize("theme", ["bold", "sepia", "winter"])
def test_a_fed_colour_overrides_a_themes_marker_shade(theme: str) -> None:
    """A theme's own `label_route_ink`, differing from its route colour, is replaced by a fed colour."""
    style = Style.named(theme)
    assert style.nib.label_route_ink != style.route_ink.colour
    fed = style.with_route_ink(colour=FED)
    assert fed.nib.label_route_ink == FED
    assert style.with_route_ink(width_px=4.8).nib.label_route_ink == style.nib.label_route_ink


def test_a_fed_colour_moves_the_lettering_digest() -> None:
    """A fed colour moves `digest` and `lettering_digest` to their pins and leaves `base_digest`."""
    style = Style.default()
    fed = style.with_route_ink(colour=FED)
    assert fed.lettering_digest() == FED_LETTERING_DIGEST
    assert fed.digest() == FED_DIGEST
    assert fed.lettering_digest() != style.lettering_digest()
    assert fed.base_digest() == style.base_digest()


def test_feeding_the_default_colour_moves_nothing() -> None:
    """Feeding the default style its own colour leaves all three digests where they were."""
    style = Style.default()
    fed = style.with_route_ink(colour=str(style.route_ink.colour))
    assert (fed.digest(), fed.base_digest(), fed.lettering_digest()) == (
        style.digest(),
        style.base_digest(),
        style.lettering_digest(),
    )
