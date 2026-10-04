"""`Style`: the default theme is the resolved default style, themes are strict, digests are pinned.

The resolved style is read from the interim engine's own dump of it, and the
effective basemap options from the literal overrides the basemap applies.
"""

import dataclasses
import json
from pathlib import Path
from typing import Any

import pydantic
import pytest

from pyntpot._port import paint
from pyntpot._port.geo import GeoOptions
from pyntpot._port.style import RouteInk
from pyntpot.maps.style import Style
from pyntpot.maps.style_groups import CONSUMER_ONLY

from support import REPO_ROOT

RESOLVED = Path(paint.__file__).parent / "themes" / "default.json"
THEME = REPO_ROOT / "src" / "pyntpot" / "maps" / "themes" / "default.toml"

#: The `Style` fields whose values come from the resolved `paint` section.
PAINT_GROUPS: tuple[str, ...] = (
    "paper",
    "wash",
    "brush",
    "face",
    "nib",
    "hand",
    "card",
    "ribbon",
    "cover",
    "route",
    "lettering",
)

#: The resolved `route_ink` section's sport names, with the `RouteInks` field for each.
SPORTS: tuple[tuple[str, str], ...] = (
    ("Run", "run"),
    ("Ride", "ride"),
    ("Swim", "swim"),
    ("Other", "other"),
)

#: The default style's three digests, pinned.
DIGEST = "25ae6fee082ebff5"
BASE_DIGEST = "e5a5f1b4b3ca2177"
LETTERING_DIGEST = "d15ae2f30e9ca5ce"


def _resolved() -> dict[str, Any]:
    """Return the interim engine's resolved default style dump."""
    return json.loads(RESOLVED.read_text())


def _tuples(value: Any) -> Any:
    """Return a JSON value with every list turned into a tuple, recursively."""
    if isinstance(value, list):
        return tuple(_tuples(item) for item in value)
    if isinstance(value, dict):
        return {key: _tuples(item) for key, item in value.items()}
    return value


def _theme_with(tmp_path: Path, old: str, new: str) -> Path:
    """Write the default theme with one piece of text replaced."""
    text = THEME.read_text()
    assert old in text
    target = tmp_path / "theme.toml"
    target.write_text(text.replace(old, new, 1))
    return target


class TestDefaultIsResolved:
    """The packaged default theme reproduces the resolved default style."""

    @pytest.mark.parametrize("group", PAINT_GROUPS, ids=PAINT_GROUPS)
    def test_group_matches_the_resolved_paint_section(self, group: str) -> None:
        """Each group field equals the resolved `paint` value, lists read as tuples."""
        resolved = _resolved()["paint"]
        values = dataclasses.asdict(getattr(Style.default(), group))
        for name, value in values.items():
            assert value == _tuples(resolved[name]), name

    def test_every_resolved_paint_field_is_grouped(self) -> None:
        """Every resolved `paint` field but the consumer-only ones is in some group."""
        style = Style.default()
        grouped = {
            name for group in PAINT_GROUPS for name in dataclasses.asdict(getattr(style, group))
        }
        assert grouped == set(_resolved()["paint"]) - set(CONSUMER_ONLY)

    @pytest.mark.parametrize(("sport", "field"), SPORTS, ids=[field for _, field in SPORTS])
    def test_route_ink_matches_the_resolved_route_ink(self, sport: str, field: str) -> None:
        """Each sport's route ink equals the resolved `route_ink` entry."""
        expected = RouteInk(**_resolved()["route_ink"][sport])
        assert getattr(Style.default().route_inks, field) == expected

    def test_basemap_is_the_effective_options(self) -> None:
        """The basemap group equals the options the basemap is drawn with, field by field."""
        effective = GeoOptions(
            hillshade_mode="off",
            roads="key",
            rivers="key",
            generalise=False,
            landmarks="all",
            landmark_max=40,
        )
        expected = dataclasses.asdict(effective)
        del expected["clip_margin_m"]
        got = dataclasses.asdict(Style.default().basemap)
        assert got.keys() == expected.keys()
        for name, value in got.items():
            assert value == expected[name], name


class TestEngineAdapters:
    """The flat painter style and the route ink handed to the interim engine."""

    def test_paint_style_matches_the_resolved_painter_style(self) -> None:
        """`paint_style()` equals the engine's own resolved style on every grouped field."""
        expected = paint.PaintStyle.from_resolved(_resolved()["paint"])
        got = Style.default().paint_style()
        for spec in dataclasses.fields(paint.PaintStyle):
            if spec.name not in CONSUMER_ONLY:
                assert getattr(got, spec.name) == getattr(expected, spec.name), spec.name

    def test_route_ink_is_the_ride_ink(self) -> None:
        """`route_ink()` is the resolved ride ink the reference sheets were painted with."""
        assert Style.default().route_ink() == RouteInk(**_resolved()["route_ink"]["Ride"])


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
