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

from pyntpot.maps.style import Style, _digest_fields
from pyntpot.maps.style_groups import BasemapStyle, CoverStyle, RouteInkStyle
from pyntpot.maps.theme_errors import ThemeError

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
ROUTE_INK = RouteInkStyle(colour="#c22050", px=5.4, style="solid", blend="normal", opacity=1.0)

#: The default style's three digests, pinned.
DIGEST = "1b08804a7f30026b"
BASE_DIGEST = "d9c56c0811177b0f"
LETTERING_DIGEST = "d15ae2f30e9ca5ce"


def _write_theme(tmp_path: Path, text: str) -> Path:
    """Write a theme file holding exactly `text`."""
    target = tmp_path / "theme.toml"
    target.write_text(text)
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

    def test_route_ink_is_pinned(self) -> None:
        """The route ink equals its pinned resolved value, `opacity` read as 1.0 when absent."""
        assert Style.default().route_ink == ROUTE_INK

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


class TestTheModelIsTheDefaultLook:
    """The groups' defaults are the default look, so a theme names only what it changes."""

    def test_a_trimmed_theme_paints_the_default_look(self, tmp_path: Path) -> None:
        """A theme naming one wash key keeps the default look's blooms, glazing and landmarks."""
        theme = tmp_path / "theme.toml"
        theme.write_text("[wash]\nflow_rim = true\n")
        style = Style.from_toml(theme)
        assert (style.wash.blooms, style.paper.km_glazing, style.basemap.landmarks) == (
            True,
            True,
            "all",
        )

    def test_route_ink_builds_with_no_arguments(self) -> None:
        """`RouteInkStyle()` builds, and is the pinned route ink."""
        assert RouteInkStyle() == ROUTE_INK


class TestThemeIsStrict:
    """A theme naming a key no group has is rejected."""

    def test_unknown_top_level_key_is_rejected(self, tmp_path: Path) -> None:
        """A table that is not a style group is rejected."""
        theme = _write_theme(tmp_path, "[weather]\nwind = 3\n")
        with pytest.raises(pydantic.ValidationError, match="weather"):
            Style.from_toml(theme)

    def test_misspelt_wash_key_is_rejected(self, tmp_path: Path) -> None:
        """A misspelt key inside `[wash]` is rejected, not ignored."""
        theme = _write_theme(tmp_path, "[wash]\nwet_bleed_pz = 20.0\n")
        with pytest.raises(pydantic.ValidationError, match="wet_bleed_pz"):
            Style.from_toml(theme)

    def test_misspelt_route_ink_key_is_rejected(self, tmp_path: Path) -> None:
        """A misspelt key inside a route ink is rejected, not ignored."""
        theme = _write_theme(tmp_path, '[route_ink]\nstile = "solid"\n')
        with pytest.raises(pydantic.ValidationError, match="stile"):
            Style.from_toml(theme)

    def test_an_effect_key_in_the_route_ink_is_rejected(self, tmp_path: Path) -> None:
        """A casing key, which nothing paints, is rejected inside `[route_ink]`."""
        theme = _write_theme(tmp_path, '[route_ink]\nblend = "normal"\ncasing_px = 0.25\n')
        with pytest.raises(pydantic.ValidationError, match="casing_px"):
            Style.from_toml(theme)

    def test_an_effect_table_in_the_route_ink_is_rejected(self, tmp_path: Path) -> None:
        """The old free `effect` table is rejected inside `[route_ink]`."""
        theme = _write_theme(tmp_path, '[route_ink.effect]\nblend = "normal"\n')
        with pytest.raises(pydantic.ValidationError, match="effect"):
            Style.from_toml(theme)

    def test_the_four_sport_inks_are_rejected(self, tmp_path: Path) -> None:
        """A theme in the old format, with a `[route_inks.ride]` table, is rejected."""
        theme = _write_theme(tmp_path, "[route_inks.ride]\n")
        with pytest.raises(pydantic.ValidationError, match="route_inks"):
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
        """Changing the route ink moves `digest()` and leaves the base and lettering digests."""
        style = Style.default()
        ink = dataclasses.replace(style.route_ink, px=6.0)
        changed = style.model_copy(update={"route_ink": ink})
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

    def test_a_non_default_name_tags_moves_the_base_and_full_digests(self) -> None:
        """Other `name_tags` move `base_digest()` and `digest()`, and the default's pins hold."""
        style = Style.default()
        basemap = dataclasses.replace(style.basemap, name_tags=("name:cy", "name"))
        changed = style.model_copy(update={"basemap": basemap})
        assert changed.base_digest() != BASE_DIGEST
        assert changed.digest() != DIGEST
        assert changed.lettering_digest() == LETTERING_DIGEST
        assert (style.digest(), style.base_digest()) == (DIGEST, BASE_DIGEST)

    def test_a_default_showcase_field_leaves_every_digest(self) -> None:
        """`minor_road_classes`, `relief_strength` and `min_patch_px` at their defaults leave the pins."""
        style = Style.default()
        assert style.cover.min_patch_px == CoverStyle().min_patch_px == 0.0
        assert style.basemap.minor_road_classes == BasemapStyle().minor_road_classes
        assert style.cover.relief_strength == CoverStyle().relief_strength == 1.0
        assert (style.digest(), style.base_digest(), style.lettering_digest()) == (
            DIGEST,
            BASE_DIGEST,
            LETTERING_DIGEST,
        )

    def test_fewer_minor_road_classes_move_the_base_and_full_digests(self) -> None:
        """A minor road class set without `service` moves `base_digest()` and `digest()` only."""
        style = Style.default()
        basemap = dataclasses.replace(style.basemap, minor_road_classes=("tertiary", "track"))
        changed = style.model_copy(update={"basemap": basemap})
        assert changed.base_digest() != BASE_DIGEST
        assert changed.digest() != DIGEST
        assert changed.lettering_digest() == LETTERING_DIGEST

    def test_a_stronger_relief_moves_the_base_and_full_digests(self) -> None:
        """A relief strength of 2 moves `base_digest()` and `digest()` only."""
        style = Style.default()
        cover = dataclasses.replace(style.cover, relief_strength=2.0)
        changed = style.model_copy(update={"cover": cover})
        assert changed.base_digest() != BASE_DIGEST
        assert changed.digest() != DIGEST
        assert changed.lettering_digest() == LETTERING_DIGEST

    def test_a_factory_default_counts_for_the_digest_rule(self) -> None:
        """A rule field with a default factory is left out at what the factory builds, and kept otherwise."""
        assert _digest_fields(_FactoryGroup()) == {"px": 1.0}
        named = _FactoryGroup(name_tags=("name:cy", "name"))
        assert _digest_fields(named) == {"name_tags": ("name:cy", "name"), "px": 1.0}


@dataclasses.dataclass(frozen=True, kw_only=True)
class _FactoryGroup:
    """A planted group whose digest-rule field has a default factory."""

    name_tags: tuple[str, ...] = dataclasses.field(default_factory=lambda: ("name",))
    px: float = 1.0


class TestFromYaml:
    """`Style.from_yaml` loads a YAML theme over the default look."""

    def test_a_minimal_file_loads(self, tmp_path: Path) -> None:
        """A theme naming one key gives the default look with that key changed."""
        theme = tmp_path / "t.yaml"
        theme.write_text("card:\n  display_px: 120\n", encoding="utf-8")
        style = Style.from_yaml(theme)
        assert style.card.display_px == 120
        assert style.wash == Style().wash

    def test_an_error_is_located_at_its_line(self, tmp_path: Path) -> None:
        """A wrong value raises `ThemeError` whose problem names the value's line."""
        theme = tmp_path / "t.yaml"
        theme.write_text("card:\n  supersample: 2\n  display_px: '5'\n", encoding="utf-8")
        with pytest.raises(ThemeError) as caught:
            Style.from_yaml(theme)
        assert (caught.value.problems[0].key, caught.value.problems[0].line) == (
            "card.display_px",
            3,
        )

    def test_extends_default_alone_is_the_default_look(self, tmp_path: Path) -> None:
        """A file holding only `extends: default` loads to `Style()`."""
        theme = tmp_path / "t.yaml"
        theme.write_text("extends: default\n", encoding="utf-8")
        assert Style.from_yaml(theme) == Style()

    def test_a_toml_path_is_refused_with_the_conversion_pointer(self) -> None:
        """A `.toml` path raises `ThemeError` pointing at ADR 0069's conversion."""
        with pytest.raises(ThemeError, match="ADR 0069"):
            Style.from_yaml(Path("old.toml"))


#: Fed colours that are not a `#` and six hexadecimal digits.
BAD_COLOURS: tuple[str, ...] = ("#abc", "c22050", "#zz0000", "#c22050x")

#: Fed widths that are not a finite number above zero.
BAD_WIDTHS: tuple[float, ...] = (0.0, -1.0, float("inf"), float("nan"), True)


class TestFedRouteInk:
    """`with_route_ink` feeds the route's colour and width and keeps the rest of the style."""

    def test_a_fed_ink_sets_the_colour_and_width(self) -> None:
        """A fed colour and width reach `route_ink`; its treatment, blend and opacity stay the theme's."""
        style = Style.default()
        ink = style.with_route_ink(colour="#2050c2", width_px=4.8).route_ink
        assert (ink.colour, ink.px) == ("#2050c2", 4.8)
        theme = style.route_ink
        assert (ink.style, ink.blend, ink.opacity) == (theme.style, theme.blend, theme.opacity)

    def test_feeding_nothing_keeps_the_style(self) -> None:
        """Feeding nothing, or the default ink's own colour and width, gives an equal style."""
        style = Style.default()
        assert style.with_route_ink() == style
        assert style.with_route_ink(colour="#c22050", width_px=5.4) == style

    def test_a_fed_ink_moves_only_the_full_digest(self) -> None:
        """A fed ink moves `digest()` and leaves the base and lettering digests at their pins."""
        fed = Style.default().with_route_ink(colour="#2050c2", width_px=4.8)
        assert fed.digest() != DIGEST
        assert (fed.base_digest(), fed.lettering_digest()) == (BASE_DIGEST, LETTERING_DIGEST)

    @pytest.mark.parametrize(
        "colour", BAD_COLOURS, ids=["three-digits", "no-hash", "not-hex", "trailing"]
    )
    def test_a_fed_colour_must_be_six_hex_digits(self, colour: str) -> None:
        """A colour that is not a `#` and six hexadecimal digits raises `ValueError`."""
        with pytest.raises(ValueError, match="colour"):
            Style.default().with_route_ink(colour=colour)

    @pytest.mark.parametrize(
        "width_px", BAD_WIDTHS, ids=["zero", "negative", "infinite", "not-a-number", "bool"]
    )
    def test_a_fed_width_must_be_above_zero(self, width_px: float) -> None:
        """A width that is not a finite number above zero, or is a bool, raises `ValueError`."""
        with pytest.raises(ValueError, match="width"):
            Style.default().with_route_ink(width_px=width_px)

    def test_equal_fed_values_give_equal_digests(self) -> None:
        """A whole-number width equals its float, and a colour's case does not move `digest()`."""
        style = Style.default()
        assert (
            style.with_route_ink(width_px=5).digest() == style.with_route_ink(width_px=5.0).digest()
        )
        assert (
            style.with_route_ink(colour="#C22050").digest()
            == style.with_route_ink(colour="#c22050").digest()
            == DIGEST
        )
