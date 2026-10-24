"""The example themes in `examples/themes/` are full themes that load and differ from the default and each other."""

import pytest

from pyntpot.maps import Style

from support import REPO_ROOT

THEMES_DIR = REPO_ROOT / "examples" / "themes"
THEME_NAMES = ("pen-and-ink", "sepia", "bold", "winter", "y-fenni")


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
