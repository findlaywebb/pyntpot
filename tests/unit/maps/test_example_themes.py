"""The example themes in `examples/themes/` are YAML overrides that load and differ from the default and each other."""

import tomllib

import pytest

from pyntpot.maps import Style

from support import REPO_ROOT

THEMES_DIR = REPO_ROOT / "examples" / "themes"
THEME_NAMES = (
    "ambleside",
    "ambleside-hero",
    "skye",
    "yr-wyddfa",
    "oxford",
    "y-fenni",
)
#: Each example theme's digests, measured from the TOML files on f34de97 and unchanged by 008 S1.
DIGESTS = {
    "ambleside-hero": ("f49b10327a58beed", "1e300b93eaba4ce5", "6331518a202c936d"),
    "ambleside": ("6a2060ec26882818", "2638b1097f7bac8d", "6331518a202c936d"),
    "oxford": ("3f795f42c5f1efd5", "794a835c65896141", "36480f1b92757e09"),
    "skye": ("fce43b2d9bdce6c8", "dfb1acedf43e4ef3", "1976288541cb3b07"),
    "y-fenni": ("9d5cc74518f3604b", "a5f39ceb2159f991", "3c27e8f97c00b9c4"),
    "yr-wyddfa": ("b92de309113988aa", "42009863a90a036b", "6331518a202c936d"),
}


class TestExampleThemes:
    """Each example theme is an override file that `Style.from_yaml` loads."""

    @pytest.mark.parametrize("name", THEME_NAMES, ids=THEME_NAMES)
    def test_the_theme_loads_and_is_not_the_default(self, name: str) -> None:
        """The file loads, and it changes the style from the default."""
        style = Style.from_yaml(THEMES_DIR / f"{name}.yaml")

        assert style.digest() != Style.default().digest()

    def test_the_themes_differ_from_each_other(self) -> None:
        """No two example themes load to the same style."""
        digests = {Style.from_yaml(THEMES_DIR / f"{name}.yaml").digest() for name in THEME_NAMES}

        assert len(digests) == len(THEME_NAMES)

    @pytest.mark.parametrize("name", sorted(DIGESTS), ids=sorted(DIGESTS))
    def test_each_theme_resolves_to_its_pinned_digests(self, name: str) -> None:
        """The theme resolves to its pinned `digest`, `base_digest` and `lettering_digest`."""
        style = Style.from_yaml(THEMES_DIR / f"{name}.yaml")

        assert (style.digest(), style.base_digest(), style.lettering_digest()) == DIGESTS[name]

    def test_the_directory_holds_exactly_these_themes(self) -> None:
        """No theme file sits in the directory without a test above naming it."""
        found = sorted(path.stem for path in THEMES_DIR.glob("*.yaml"))

        assert found == sorted(THEME_NAMES)


SHOWCASE_NAMES = ("ambleside", "skye", "yr-wyddfa", "oxford", "y-fenni")


class TestShowcaseThemes:
    """The five showcase themes share one route ink and keep to their curated landmarks."""

    @pytest.mark.parametrize("name", SHOWCASE_NAMES, ids=SHOWCASE_NAMES)
    def test_the_route_is_the_maroon_wet_pen(self, name: str) -> None:
        """The route is the MAJ1-e pen in maroon, in the normal blend, fully opaque."""
        style = Style.from_yaml(THEMES_DIR / f"{name}.yaml")
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
        style = Style.from_yaml(THEMES_DIR / f"{name}.yaml")

        assert style.lettering.label_max == len(landmarks)

    @pytest.mark.parametrize(
        "name", ("ambleside", "skye", "yr-wyddfa"), ids=("ambleside", "skye", "yr-wyddfa")
    )
    def test_the_relief_is_strong(self, name: str) -> None:
        """The landscape themes paint the relief at least 1.6 times the quiet default."""
        style = Style.from_yaml(THEMES_DIR / f"{name}.yaml")

        assert style.cover.relief_strength >= 1.6
