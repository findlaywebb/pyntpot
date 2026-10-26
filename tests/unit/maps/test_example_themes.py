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

    def test_the_directory_holds_exactly_these_themes(self) -> None:
        """No theme file sits in the directory without a test above naming it."""
        found = sorted(path.stem for path in THEMES_DIR.glob("*.toml"))

        assert found == sorted(THEME_NAMES)


SHOWCASE_NAMES = ("ambleside", "skye", "yr-wyddfa", "oxford", "y-fenni")


class TestShowcaseThemes:
    """The five showcase themes share one route ink and keep to their curated callouts."""

    @pytest.mark.parametrize("name", SHOWCASE_NAMES, ids=SHOWCASE_NAMES)
    def test_the_route_is_the_maroon_wet_pen(self, name: str) -> None:
        """The route is the MAJ1-e pen in maroon, in the normal blend, with no glow, casing or shadow."""
        style = Style.from_toml(THEMES_DIR / f"{name}.toml")
        ink = style.route_ink()

        assert style.route.route_pen_brush == "MAJ1-e"
        assert ink.colour == "#7b2335"
        assert style.nib.label_route_ink == "#7b2335"
        assert ink.effect["blend"] == "normal"
        assert {ink.effect[key] for key in ("glow_px", "casing_px", "shadow_px")} == {0}

    @pytest.mark.parametrize("name", SHOWCASE_NAMES, ids=SHOWCASE_NAMES)
    def test_the_label_cap_is_the_callout_count(self, name: str) -> None:
        """`label_max` equals the number of callouts `examples/places.toml` holds for the place."""
        with (REPO_ROOT / "examples" / "places.toml").open("rb") as handle:
            callouts = tomllib.load(handle)[name].get("callouts", [])
        style = Style.from_toml(THEMES_DIR / f"{name}.toml")

        assert style.lettering.label_max == len(callouts)

    @pytest.mark.parametrize(
        "name", ("ambleside", "skye", "yr-wyddfa"), ids=("ambleside", "skye", "yr-wyddfa")
    )
    def test_the_relief_is_strong(self, name: str) -> None:
        """The landscape themes paint the relief at least 1.6 times the quiet default."""
        style = Style.from_toml(THEMES_DIR / f"{name}.toml")

        assert style.cover.relief_strength >= 1.6
