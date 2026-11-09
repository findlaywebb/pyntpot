"""The map's pigment defaults are the registry's, not copies: keys, values and order tie."""

from pyntpot.ink import PIGMENTS, TRANSPARENCY, Colour, PaperStyle
from pyntpot.maps.style_groups import CoverStyle
from pyntpot.maps.theme_vocab import VOCABULARIES

ROLES = [
    "farmland",
    "meadow",
    "orchard",
    "scrub",
    "heath",
    "sand",
    "rock",
    "wetland",
    "built",
    "works",
    "wood",
    "pale",
    "water",
    "relief",
    "rim",
]


def test_cover_pigments_equal_the_registry_in_pinned_order():
    """`CoverStyle().pigments` is `PIGMENTS`, in the registry's key order."""
    pigments = CoverStyle().pigments
    assert list(pigments) == ROLES
    assert pigments == PIGMENTS


def test_paper_transparency_equals_the_registry_in_pinned_order():
    """`PaperStyle().pigment_transparency` is `TRANSPARENCY`, in the registry's key order."""
    transparency = PaperStyle().pigment_transparency
    assert list(transparency) == ROLES
    assert transparency == TRANSPARENCY


def test_a_default_is_a_fresh_dict_each_time():
    """Editing one group's default leaves the next group and the registry alone."""
    first = CoverStyle().pigments
    first["farmland"] = Colour("#000000")
    assert CoverStyle().pigments["farmland"] == "#dfe0b0"
    assert PIGMENTS["farmland"] == "#dfe0b0"


def test_the_theme_pigment_vocabulary_is_the_role_names():
    """The keys a theme may give the three pigment fields are the registry's role names."""
    for path in (
        ("paper", "pigment_transparency"),
        ("wash", "separation_pigments"),
        ("cover", "pigments"),
    ):
        assert VOCABULARIES[path] == frozenset(ROLES)
