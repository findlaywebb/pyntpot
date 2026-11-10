"""A theme's `effect_presets:` and how line effects merge down an `extends` chain."""

from pathlib import Path

import pytest

from pyntpot.ink import Glow
from pyntpot.maps import EffectStack, Style, ThemeError
from pyntpot.maps.line_effects import BUILT_IN_PRESETS
from pyntpot.maps.style import _groups
from pyntpot.maps.theme_check import check_theme_scoped
from pyntpot.maps.theme_scope import ThemeScope

from support.theme_files import theme_file, write_theme


def _problems(root: Path, text: str) -> list[tuple[int | None, str, str]]:
    """The line, key and message of every problem loading the theme `text` raises."""
    with pytest.raises(ThemeError) as caught:
        Style.from_theme(write_theme(root, "t.yaml", text))
    return [(p.line, p.key, p.message) for p in caught.value.problems]


def _style(root: Path, text: str) -> Style:
    """The style the theme `text` builds."""
    return Style.from_theme(write_theme(root, "t.yaml", text))


def _check(text: str) -> tuple[dict[str, object], list[tuple[int | None, str, str]]]:
    """The table and the (line, key, message) problems of checking `text` in the built-in scope."""
    table, problems, _ = check_theme_scoped(theme_file(text), _groups(), ThemeScope.built_in())
    return table, [(p.line, p.key, p.message) for p in problems]


class TestThePresets:
    """`effect_presets` binds theme presets with the built-in and override rules."""

    def test_a_built_in_name_is_refused(self) -> None:
        """A theme preset named `cased` is refused at its line."""
        _, problems = _check("effect_presets:\n  cased: {casing: {width_px: 3}}\n")
        assert problems == [
            (
                2,
                "effect_presets.cased",
                "'cased' is a built-in effect preset; give a preset a name of its own",
            )
        ]

    def test_a_name_must_be_alias_shaped(self) -> None:
        """A preset named `Soft` is refused."""
        _, problems = _check("effect_presets:\n  Soft: {}\n")
        assert problems == [
            (
                2,
                "effect_presets.Soft",
                "'Soft' is not a preset name: lower-case words joined by single _",
            )
        ]

    def test_the_table_must_be_a_table(self) -> None:
        """`effect_presets: soft` is refused."""
        _, problems = _check("effect_presets: soft\n")
        assert problems == [(1, "effect_presets", "is a table of keys")]

    def test_a_preset_must_be_a_table(self) -> None:
        """A preset given as a number is refused."""
        _, problems = _check("effect_presets:\n  soft: 3\n")
        assert problems == [(2, "effect_presets.soft", "is a table of keys")]

    def test_override_with_nothing_to_override_is_refused(self, tmp_path: Path) -> None:
        """`override: true` on a preset no file below defines is a located error."""
        text = "effect_presets:\n  soft: {override: true, glow: {strength: 0.9, spread_px: 1}}\n"
        problems = _problems(tmp_path, text)
        assert problems == [
            (2, "effect_presets.soft", "'soft' overrides no effect preset; drop override: true")
        ]

    def test_replacing_an_inherited_preset_needs_override(self, tmp_path: Path) -> None:
        """A child preset of a parent's name needs `override: true`, and names the parent's line."""
        write_theme(
            tmp_path,
            "parent.yaml",
            "effect_presets:\n  soft: {glow: {strength: 0.5, spread_px: 1}}\n",
        )
        text = (
            "extends: parent.yaml\neffect_presets:\n  soft: {glow: {strength: 0.9, spread_px: 1}}\n"
        )
        problems = _problems(tmp_path, text)
        assert [(line, key) for line, key, _ in problems] == [(3, "effect_presets.soft")]
        assert "already an effect preset" in problems[0][2]
        assert "parent.yaml:2" in problems[0][2]
        assert "add override: true" in problems[0][2]

    def test_override_replaces_an_inherited_preset(self, tmp_path: Path) -> None:
        """With `override: true` the child's preset is the one a class takes."""
        write_theme(
            tmp_path,
            "parent.yaml",
            "effect_presets:\n  soft: {glow: {strength: 0.5, spread_px: 1}}\n",
        )
        text = (
            "extends: parent.yaml\neffect_presets:\n"
            "  soft: {override: true, glow: {strength: 0.9, spread_px: 1}}\n"
            "line_effects:\n  lane: soft\n"
        )
        stack = _style(tmp_path, text).basemap.line_effects["lane"]
        assert stack == EffectStack(effects=(Glow(spread_px=1.0, strength=0.9),))

    def test_a_preset_is_inherited_down_extends(self, tmp_path: Path) -> None:
        """A child names a preset its parent defined."""
        write_theme(
            tmp_path,
            "parent.yaml",
            "effect_presets:\n  soft: {glow: {strength: 0.5, spread_px: 1}}\n",
        )
        style = _style(tmp_path, "extends: parent.yaml\nline_effects:\n  route: soft\n")
        assert style.route_ink.effects == EffectStack(effects=(Glow(spread_px=1.0, strength=0.5),))

    def test_a_preset_is_unknown_to_the_parent_that_comes_before_it(self, tmp_path: Path) -> None:
        """A parent cannot name a preset only its child defines."""
        write_theme(tmp_path, "parent.yaml", "line_effects:\n  lane: soft\n")
        text = (
            "extends: parent.yaml\neffect_presets:\n  soft: {glow: {strength: 0.5, spread_px: 1}}\n"
        )
        problems = _problems(tmp_path, text)
        assert [(line, key) for line, key, _ in problems] == [(2, "line_effects.lane")]

    def test_a_preset_name_is_suggested(self) -> None:
        """A near miss of a theme preset suggests it."""
        text = "effect_presets:\n  softer: {glow: {strength: 0.5, spread_px: 1}}\nline_effects:\n  lane: softr\n"
        _, problems = _check(text)
        assert problems == [
            (4, "line_effects.lane", "'softr' is not an effect preset; did you mean softer?")
        ]

    def test_override_must_be_a_boolean(self) -> None:
        """`override: maybe` is refused at its own key."""
        _, problems = _check("effect_presets:\n  soft: {override: maybe}\n")
        assert [key for _, key, _ in problems] == ["effect_presets.soft.override"]


class TestTheMergeDownExtends:
    """Each file's stack replaces its parent's whole; nothing is dropped until the build."""

    def test_a_child_that_sets_one_class_keeps_the_parents_route(self, tmp_path: Path) -> None:
        """The parent sets `route: lifted`, the child sets `major: cased`, and the child has both."""
        write_theme(tmp_path, "parent.yaml", "line_effects:\n  route: lifted\n")
        style = _style(tmp_path, "extends: parent.yaml\nline_effects:\n  major: cased\n")
        assert style.route_ink.effects == BUILT_IN_PRESETS["lifted"]
        assert style.basemap.line_effects == {"major": BUILT_IN_PRESETS["cased"]}

    def test_a_child_class_replaces_the_parents_stack_whole(self, tmp_path: Path) -> None:
        """A child's `major: halo` replaces the parent's `major: cased`, not merges with it."""
        write_theme(tmp_path, "parent.yaml", "line_effects:\n  major: cased\n  lane: cased\n")
        style = _style(tmp_path, "extends: parent.yaml\nline_effects:\n  major: halo\n")
        assert style.basemap.line_effects == {
            "major": BUILT_IN_PRESETS["halo"],
            "lane": BUILT_IN_PRESETS["cased"],
        }

    @pytest.mark.parametrize(
        "off",
        [
            "major: {}",
            "major: {casing: {width_px: 0}}",
            "major: {casing: {width_px: 2, strength: 0}}",
        ],
        ids=["empty", "zero-width", "zero-strength"],
    )
    def test_a_child_turns_off_an_inherited_stack(self, tmp_path: Path, off: str) -> None:
        """The parent sets `major: cased` and the child writes it off: no stack, the default's digests."""
        write_theme(tmp_path, "parent.yaml", "line_effects:\n  major: cased\n")
        style = _style(tmp_path, f"extends: parent.yaml\nline_effects:\n  {off}\n")
        default = Style()
        assert style.basemap.line_effects == {}
        assert style == default
        assert (style.digest(), style.base_digest(), style.lettering_digest()) == (
            default.digest(),
            default.base_digest(),
            default.lettering_digest(),
        )

    def test_a_child_turns_off_the_parents_route(self, tmp_path: Path) -> None:
        """The parent sets `route: lifted` and the child's `route: {}` leaves the route with none."""
        write_theme(tmp_path, "parent.yaml", "line_effects:\n  route: lifted\n")
        style = _style(tmp_path, "extends: parent.yaml\nline_effects:\n  route: {}\n")
        assert style.route_ink.effects == EffectStack()
        assert style.digest() == Style().digest()
