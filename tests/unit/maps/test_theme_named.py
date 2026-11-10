"""The packaged themes: listed, named, loaded by `Style.named` and `Style.from_theme`, and painted."""

import dataclasses
import shutil
from importlib import resources
from pathlib import Path

import pytest
from PIL import Image

from pyntpot.ink import Colour
from pyntpot.ink.effect_types import Casing
from pyntpot.maps import Style
from pyntpot.maps.cli import main
from pyntpot.maps.line_effects import BUILT_IN_PRESETS, EffectStack
from pyntpot.maps.theme_errors import ThemeError, ThemeProblem

from support.paths import FIXTURE_DIR

NAMES = ("bold", "default", "pen-and-ink", "sepia", "winter")
PACKAGED = ("bold", "pen-and-ink", "sepia", "winter")
#: Each packaged theme's digests, measured from the TOML files on f34de97 and unchanged by 008 S1.
DIGESTS = {
    "bold": ("739a529eb5151ef0", "bc7323df2b3f6430", "2a7a209c41fe7df8"),
    "pen-and-ink": ("d6cd7f31218e42a5", "73a44bc9875190e1", "9c4b7732ec2b6d7d"),
    "sepia": ("7c12a224dea23ddd", "bb3e691b4240decb", "9f7523b1ae707038"),
    "winter": ("7a964582841d2c30", "4106da33e2e6f96d", "68d9f8d8810bd9bb"),
}
ADR_POINTER = "themes are YAML since ADR 0069"


def _message(theme: str | Path) -> str:
    """The message of the `ThemeError` `Style.from_theme(theme)` raises."""
    with pytest.raises(ThemeError) as caught:
        Style.from_theme(theme)
    return str(caught.value)


def test_the_packaged_themes_are_listed() -> None:
    """`Style.themes` lists the packaged themes, `default` among them, sorted."""
    assert Style.themes() == NAMES


def test_default_is_the_model() -> None:
    """The theme named `default` is the model with nothing overridden."""
    assert Style.named("default") == Style()


@pytest.mark.parametrize("name", sorted(DIGESTS), ids=sorted(DIGESTS))
def test_each_named_theme_keeps_its_digests(name: str) -> None:
    """Each packaged theme loads by name to its pinned `digest`, `base_digest` and `lettering_digest`."""
    style = Style.named(name)

    assert (style.digest(), style.base_digest(), style.lettering_digest()) == DIGESTS[name]


def test_bold_cases_its_route_and_nothing_else() -> None:
    """Bold's route ink carries its own wider cream `bold_cased` casing, which is not the built-in `cased`, no basemap class has an effect, and the plates' digests are those of a bold that sets none."""
    bold = Style.named("bold")
    plain = bold.model_copy(
        update={"route_ink": dataclasses.replace(bold.route_ink, effects=EffectStack())}
    )

    assert bold.route_ink.effects == EffectStack(
        effects=(Casing(width_px=3.4, colour=Colour("#fbf6e8"), strength=1.0),)
    )
    assert bold.route_ink.effects != BUILT_IN_PRESETS["cased"]
    assert bold.basemap.line_effects == {}
    assert bold.digest() != plain.digest()
    assert bold.base_digest() == plain.base_digest()
    assert bold.lettering_digest() == plain.lettering_digest()


def test_an_unknown_name_lists_the_names() -> None:
    """A well-formed name that is not packaged is refused with the available names."""
    with pytest.raises(ThemeError) as caught:
        Style.named("sepia-two")

    assert "available: bold, default, pen-and-ink, sepia, winter" in str(caught.value)


@pytest.mark.parametrize("name", ["Sepia", "sepia_2", "2sepia"], ids=["upper", "under", "digit"])
def test_a_name_must_be_lower_case_and_hyphenated(name: str) -> None:
    """A name that is not lower-case letters, digits and hyphens is refused as no theme name."""
    with pytest.raises(ThemeError) as caught:
        Style.named(name)

    assert f"'{name}' is neither a theme name nor a .yaml path" in str(caught.value)


def test_a_theme_can_extend_a_named_theme(tmp_path: Path) -> None:
    """A file extending `sepia` with one override is sepia with that one field replaced."""
    theme = tmp_path / "t.yaml"
    theme.write_text("extends: sepia\ncard:\n  display_px: 120\n", encoding="utf-8")
    sepia = Style.named("sepia")
    expected = sepia.model_copy(update={"card": dataclasses.replace(sepia.card, display_px=120)})

    assert Style.from_yaml(theme) == expected


@pytest.mark.parametrize("name", NAMES, ids=NAMES)
def test_every_named_theme_paints_the_lynmouth_card(tmp_path: Path, name: str) -> None:
    """`pyntpot map` paints the fixture card at 120 pixels in a theme extending each name."""
    style = tmp_path / "small.yaml"
    style.write_text(f"extends: {name}\ncard:\n  display_px: 120\n", encoding="utf-8")
    cache = tmp_path / "cache"
    shutil.copytree(FIXTURE_DIR, cache)
    out = tmp_path / "out.png"
    argv = ["map", str(FIXTURE_DIR / "track.gpx"), "--cache", str(cache), "--contact", "t"]
    argv += ["--style", str(style), "--no-attribution", "-o", str(out)]

    assert main(argv) == 0
    with Image.open(out) as image:
        assert image.width == 240


def test_named_refuses_a_file() -> None:
    """`Style.named` refuses a name with a suffix and points to `Style.from_yaml`."""
    with pytest.raises(ThemeError) as caught:
        Style.named("sepia.yaml")

    assert "Style.named takes a name; use Style.from_yaml for a file" in str(caught.value)


def test_named_refuses_a_file_at_the_name_alone() -> None:
    """The refusal is one problem at the name, with no key or line, and the exact message."""
    with pytest.raises(ThemeError) as caught:
        Style.named("sepia.yaml")
    assert caught.value.problems == (
        ThemeProblem(
            path=Path("sepia.yaml"),
            key="",
            line=None,
            message="Style.named takes a name; use Style.from_yaml for a file",
        ),
    )


@pytest.mark.parametrize("name", PACKAGED, ids=PACKAGED)
def test_each_named_theme_is_package_data(name: str) -> None:
    """Each packaged theme's file is package data of `pyntpot.maps`."""
    assert resources.files("pyntpot.maps").joinpath("themes", f"{name}.yaml").is_file()


class TestFromTheme:
    """`Style.from_theme` takes a packaged name or a `.yaml` file."""

    def test_a_name_is_the_named_theme(self) -> None:
        """A name loads the packaged theme `Style.named` loads."""
        assert Style.from_theme("sepia") == Style.named("sepia")

    def test_a_relative_path_is_read_from_relative_to(self, tmp_path: Path) -> None:
        """A relative `.yaml` path is read from the directory `relative_to` names."""
        (tmp_path / "t.yaml").write_text("card:\n  display_px: 120\n", encoding="utf-8")

        assert Style.from_theme("t.yaml", relative_to=tmp_path).card.display_px == 120

    def test_a_path_loads_the_same(self, tmp_path: Path) -> None:
        """A `Path` to the file loads the style its relative name does."""
        (tmp_path / "t.yaml").write_text("card:\n  display_px: 120\n", encoding="utf-8")

        assert Style.from_theme(tmp_path / "t.yaml") == Style.from_theme(
            "t.yaml", relative_to=tmp_path
        )

    @pytest.mark.parametrize("theme", ["old.toml", Path("old.toml")], ids=["str", "path"])
    def test_a_toml_theme_points_to_the_adr(self, theme: str | Path) -> None:
        """A `.toml` theme, as a `str` or a `Path`, is refused with the ADR 0069 pointer."""
        assert ADR_POINTER in _message(theme)
