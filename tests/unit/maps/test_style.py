"""`Style`: the default theme is the resolved default style, themes are strict, digests are pinned.

The resolved style is pinned as literals for a sample of fields, one or more per
group, and the effective basemap options as the literal overrides the basemap
applies.
"""

import dataclasses
from pathlib import Path
from typing import Any

import pydantic
import pytest

from pyntpot.maps.style import Style
from pyntpot.maps.style_groups import BasemapStyle, RouteInk

from support import REPO_ROOT

THEME = REPO_ROOT / "src" / "pyntpot" / "maps" / "themes" / "default.toml"

#: A sample of resolved default values, as group, field and pinned value.
RESOLVED_SAMPLE: tuple[tuple[str, str, Any], ...] = (
    ("paper", "paper_hex", "#f3ead6"),
    ("paper", "sheet_seed", 11),
    ("paper", "webp_quality", 74),
    ("wash", "wet_bleed_px", 20.0),
    ("wash", "bloom_strength", 0.65),
    ("wash", "fluid_steps", 40),
    ("brush", "ink_seed", 91),
    ("brush", "brush_width_px", {"lane": 1.8, "road_major": 3.6, "track": 2.4}),
    ("face", "label_route", "centreline"),
    ("face", "label_face", ""),
    ("nib", "label_size_px", 20.0),
    ("nib", "label_ink", "#241c14"),
    ("hand", "label_seed", 17),
    ("card", "display_px", 900),
    ("card", "supersample", 2),
    ("card", "dark_grid", (80, 60)),
    ("ribbon", "ribbon_mult", 1.0),
    ("ribbon", "card_pad_frac", 0.09),
    ("cover", "dither_seed", 23),
    ("cover", "wood_texture", 0.75),
    ("route", "route_pen_brush", "MAJ6-e"),
    ("route", "route_pen_width_px", 3.0),
    ("lettering", "label_max", 3),
    ("lettering", "labels", True),
    ("lettering", "home_glyph", True),
    ("lettering", "label_geom_tol_px", 8.0),
)

#: The route ink the reference sheets were painted with, pinned.
RIDE_INK = RouteInk(
    colour="#c22050",
    px=5.4,
    style="solid",
    effect={
        "adaptive_pct": 0.0,
        "blend": "normal",
        "casing_colour": "cream",
        "casing_px": 0.25,
        "glow_opacity": 0.8,
        "glow_px": 2.5,
        "shadow_blur_px": 0.0,
        "shadow_px": 0.0,
    },
)

#: The other sports' route inks share one dotted ink, pinned without its effect.
DOTTED_SPORTS: tuple[str, ...] = ("run", "swim", "other")

#: The default style's three digests, pinned.
DIGEST = "25ae6fee082ebff5"
BASE_DIGEST = "e5a5f1b4b3ca2177"
LETTERING_DIGEST = "d15ae2f30e9ca5ce"


def _theme_with(tmp_path: Path, old: str, new: str) -> Path:
    """Write the default theme with one piece of text replaced."""
    text = THEME.read_text()
    assert old in text
    target = tmp_path / "theme.toml"
    target.write_text(text.replace(old, new, 1))
    return target


class TestDefaultIsResolved:
    """The packaged default theme reproduces the resolved default style."""

    @pytest.mark.parametrize(
        ("group", "name", "value"),
        RESOLVED_SAMPLE,
        ids=[f"{group}.{name}" for group, name, _ in RESOLVED_SAMPLE],
    )
    def test_sampled_field_equals_its_pinned_value(self, group: str, name: str, value: Any) -> None:
        """A sampled group field equals its pinned resolved value, a tuple read as a tuple."""
        got = getattr(getattr(Style.default(), group), name)
        assert got == value
        assert type(got) is type(value)

    def test_ride_ink_is_pinned(self) -> None:
        """The ride ink equals its pinned resolved value."""
        assert Style.default().route_inks.ride == RIDE_INK

    @pytest.mark.parametrize("sport", DOTTED_SPORTS, ids=DOTTED_SPORTS)
    def test_other_inks_are_the_dotted_ink(self, sport: str) -> None:
        """Every other sport's ink is the resolved dotted ink in the same colour."""
        ink = getattr(Style.default().route_inks, sport)
        assert (ink.colour, ink.px, ink.style) == ("#c22050", 4.8, "dotted")

    def test_basemap_is_the_effective_options(self) -> None:
        """The basemap group equals the options the basemap is drawn with, field by field."""
        expected = dataclasses.asdict(
            dataclasses.replace(
                BasemapStyle(),
                hillshade_mode="off",
                roads="key",
                rivers="key",
                generalise=False,
                landmarks="all",
                landmark_max=40,
            )
        )
        got = dataclasses.asdict(Style.default().basemap)
        assert got.keys() == expected.keys()
        for name, value in got.items():
            assert value == expected[name], name


class TestEngineAdapters:
    """The route ink handed to the compose step."""

    def test_route_ink_is_the_ride_ink(self) -> None:
        """`route_ink()` is the resolved ride ink the reference sheets were painted with."""
        assert Style.default().route_ink() == RIDE_INK


class TestThemeIsStrict:
    """A theme naming a key no group has is rejected."""

    def test_packaged_theme_reads_from_a_path(self) -> None:
        """Reading the packaged theme file by path gives the default style."""
        assert Style.from_toml(THEME) == Style.default()

    def test_unknown_top_level_key_is_rejected(self, tmp_path: Path) -> None:
        """A table that is not a style group is rejected."""
        theme = _theme_with(tmp_path, "[paper]\n", "[weather]\nwind = 3\n\n[paper]\n")
        with pytest.raises(pydantic.ValidationError, match="weather"):
            Style.from_toml(theme)

    def test_misspelt_wash_key_is_rejected(self, tmp_path: Path) -> None:
        """A misspelt key inside `[wash]` is rejected, not ignored."""
        theme = _theme_with(tmp_path, "wet_bleed_px = ", "wet_bleed_pz = ")
        with pytest.raises(pydantic.ValidationError, match="wet_bleed_pz"):
            Style.from_toml(theme)

    def test_misspelt_route_ink_key_is_rejected(self, tmp_path: Path) -> None:
        """A misspelt key inside a route ink is rejected, not ignored."""
        theme = _theme_with(tmp_path, 'style = "solid"', 'stile = "solid"')
        with pytest.raises(pydantic.ValidationError, match="stile"):
            Style.from_toml(theme)


class TestDigests:
    """The three digests and what moves them."""

    def test_default_digests_are_pinned(self) -> None:
        """The default style's full, base and lettering digests equal their pinned values."""
        style = Style.default()
        assert (style.digest(), style.base_digest(), style.lettering_digest()) == (
            DIGEST,
            BASE_DIGEST,
            LETTERING_DIGEST,
        )

    def test_route_ink_change_moves_only_the_full_digest(self) -> None:
        """Changing a route ink moves `digest()` and leaves the base and lettering digests."""
        style = Style.default()
        inks = dataclasses.replace(
            style.route_inks, run=dataclasses.replace(style.route_inks.run, px=6.0)
        )
        changed = style.model_copy(update={"route_inks": inks})
        assert changed.base_digest() == style.base_digest()
        assert changed.lettering_digest() == style.lettering_digest()
        assert changed.digest() != style.digest()

    def test_lettering_change_leaves_the_base_digest(self) -> None:
        """Changing a lettering-only field moves the lettering digest and not the base digest."""
        style = Style.default()
        nib = dataclasses.replace(style.nib, label_size_px=22.0)
        changed = style.model_copy(update={"nib": nib})
        assert changed.base_digest() == style.base_digest()
        assert changed.lettering_digest() != style.lettering_digest()
