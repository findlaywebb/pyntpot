"""The example themes in `examples/themes/` are full themes that load and differ from the default and each other."""

import tomllib

import pytest

from pyntpot.maps import Style

from support import REPO_ROOT

THEMES_DIR = REPO_ROOT / "examples" / "themes"
THEME_NAMES = (
    "pen-and-ink",
    "sepia",
    "bold",
    "winter",
    "ambleside",
    "ambleside-hero",
    "skye",
    "yr-wyddfa",
    "oxford",
    "y-fenni",
)
#: Each example theme's digests, measured from the TOML files on f34de97 and unchanged by 008 S1.
DIGESTS = {
    "ambleside-hero": ("86ee79977c816d4e", "149792857eb4656a", "6331518a202c936d"),
    "ambleside": ("dbf735ec2626eea1", "1fbd4375dceec789", "6331518a202c936d"),
    "bold": ("93dfd74809cc40ae", "6d77f74215314006", "2a7a209c41fe7df8"),
    "oxford": ("eb46db87c3080b61", "0f73e166ba6ba263", "36480f1b92757e09"),
    "pen-and-ink": ("0295772c0971d18a", "0d40a30d74c111e0", "9c4b7732ec2b6d7d"),
    "sepia": ("5f385631c67344df", "3a2f5fbbd424e347", "9f7523b1ae707038"),
    "skye": ("3a172bc9c6816e7a", "b54086dfe786d1f0", "1976288541cb3b07"),
    "winter": ("6fd3e5385f7bd0c0", "c1b7c47d4ea12d6c", "68d9f8d8810bd9bb"),
    "y-fenni": ("d2e1c4c2ddacb647", "90c968b5e78d7058", "3c27e8f97c00b9c4"),
    "yr-wyddfa": ("53e17a182a7d962b", "58c70051932a610f", "6331518a202c936d"),
}


class TestExampleThemes:
    """Each example theme is a complete theme, as `Style.from_toml` requires."""

    @pytest.mark.parametrize("name", THEME_NAMES, ids=THEME_NAMES)
    def test_the_theme_loads_and_is_not_the_default(self, name: str) -> None:
        """The file loads with every group present, and it changes the style from the default."""
        style = Style.from_toml(THEMES_DIR / f"{name}.toml")

        assert style.digest() != Style.default().digest()

    def test_the_themes_differ_from_each_other(self) -> None:
        """No two example themes load to the same style."""
        digests = {Style.from_toml(THEMES_DIR / f"{name}.toml").digest() for name in THEME_NAMES}

        assert len(digests) == len(THEME_NAMES)

    @pytest.mark.parametrize("name", sorted(DIGESTS), ids=sorted(DIGESTS))
    def test_each_theme_resolves_to_its_pinned_digests(self, name: str) -> None:
        """The theme resolves to its pinned `digest`, `base_digest` and `lettering_digest`."""
        style = Style.from_toml(THEMES_DIR / f"{name}.toml")

        assert (style.digest(), style.base_digest(), style.lettering_digest()) == DIGESTS[name]

    def test_the_directory_holds_exactly_these_themes(self) -> None:
        """No theme file sits in the directory without a test above naming it."""
        found = sorted(path.stem for path in THEMES_DIR.glob("*.toml"))

        assert found == sorted(THEME_NAMES)


SHOWCASE_NAMES = ("ambleside", "skye", "yr-wyddfa", "oxford", "y-fenni")


class TestShowcaseThemes:
    """The five showcase themes share one route ink and keep to their curated landmarks."""

    @pytest.mark.parametrize("name", SHOWCASE_NAMES, ids=SHOWCASE_NAMES)
    def test_the_route_is_the_maroon_wet_pen(self, name: str) -> None:
        """The route is the MAJ1-e pen in maroon, in the normal blend, fully opaque."""
        style = Style.from_toml(THEMES_DIR / f"{name}.toml")
        ink = style.route_ink

        assert style.route.route_pen_brush == "MAJ1-e"
        assert ink.colour == "#7b2335"
        assert style.nib.label_route_ink == "#7b2335"
        assert (ink.blend, ink.opacity) == ("normal", 1.0)

    @pytest.mark.parametrize("name", SHOWCASE_NAMES, ids=SHOWCASE_NAMES)
    def test_the_label_cap_is_the_landmark_count(self, name: str) -> None:
        """`label_max` equals the number of landmarks `examples/places.toml` holds for the place."""
        with (REPO_ROOT / "examples" / "places.toml").open("rb") as handle:
            landmarks = tomllib.load(handle)[name].get("landmarks", [])
        style = Style.from_toml(THEMES_DIR / f"{name}.toml")

        assert style.lettering.label_max == len(landmarks)

    @pytest.mark.parametrize(
        "name", ("ambleside", "skye", "yr-wyddfa"), ids=("ambleside", "skye", "yr-wyddfa")
    )
    def test_the_relief_is_strong(self, name: str) -> None:
        """The landscape themes paint the relief at least 1.6 times the quiet default."""
        style = Style.from_toml(THEMES_DIR / f"{name}.toml")

        assert style.cover.relief_strength >= 1.6
