"""A theme's `effect_presets:` and `line_effects:`: every refusal located, the split, the merge."""

from pathlib import Path

import pytest

from pyntpot.ink import Casing, Glow, Shadow, pigment
from pyntpot.maps import EffectStack, Style, ThemeError
from pyntpot.maps.line_effects import BUILT_IN_PRESETS
from pyntpot.maps.theme_check import check_theme_scoped
from pyntpot.maps.theme_scope import ThemeScope
from pyntpot.maps.theme_vocab import LOADER_FIELDS

from support.theme_files import theme_file

GROUPS = {"basemap": dict, "route_ink": dict}


def _write(root: Path, name: str, text: str) -> Path:
    """Write `text` to `root / name`."""
    path = root / name
    path.write_text(text, encoding="utf-8")
    return path


def _problems(root: Path, text: str) -> list[tuple[int | None, str, str]]:
    """The line, key and message of every problem loading the theme `text` raises."""
    with pytest.raises(ThemeError) as caught:
        Style.from_theme(_write(root, "t.yaml", text))
    return [(p.line, p.key, p.message) for p in caught.value.problems]


def _style(root: Path, text: str) -> Style:
    """The style the theme `text` builds."""
    return Style.from_theme(_write(root, "t.yaml", text))


def _check(text: str) -> tuple[dict[str, object], list[tuple[int | None, str, str]]]:
    """The table and the (line, key, message) problems of checking `text` in the built-in scope."""
    from pyntpot.maps.style import _groups

    table, problems, _ = check_theme_scoped(theme_file(text), _groups(), ThemeScope.built_in())
    return table, [(p.line, p.key, p.message) for p in problems]


class TestTheSplit:
    """`line_effects` is split into the basemap field and the route field, adding only what is written."""

    def test_a_file_without_line_effects_adds_neither_entry(self) -> None:
        """A file that writes no `line_effects` has no `line_effects` or `effects` in its table."""
        table, problems = _check("route_ink:\n  px: 4\nbasemap:\n  roads: all\n")
        assert problems == []
        assert table == {"route_ink": {"px": 4.0}, "basemap": {"roads": "all"}}

    def test_a_basemap_class_adds_only_the_basemap_entry(self) -> None:
        """`major: cased` sets `basemap.line_effects` and leaves `route_ink` out."""
        table, problems = _check("line_effects:\n  major: cased\n")
        assert problems == []
        assert table == {"basemap": {"line_effects": {"major": BUILT_IN_PRESETS["cased"]}}}

    def test_the_route_adds_only_the_route_entry(self) -> None:
        """`route: lifted` sets `route_ink.effects` and leaves `basemap` out."""
        table, problems = _check("line_effects:\n  route: lifted\n")
        assert problems == []
        assert table == {"route_ink": {"effects": BUILT_IN_PRESETS["lifted"]}}

    def test_the_split_merges_into_the_files_group_tables(self) -> None:
        """The split lands beside the file's own group keys."""
        table, _ = _check("route_ink:\n  px: 4\nline_effects:\n  route: cased\n")
        assert table == {"route_ink": {"px": 4.0, "effects": BUILT_IN_PRESETS["cased"]}}

    def test_an_empty_table_adds_nothing(self) -> None:
        """`line_effects: {}` adds neither entry."""
        table, problems = _check("line_effects: {}\n")
        assert (table, problems) == ({}, [])

    def test_an_explicit_empty_stack_is_kept(self) -> None:
        """`major: {}` and an all-off stack stay as explicit empty stacks, dropped nothing here."""
        table, problems = _check("line_effects:\n  major: {}\n  lane: {casing: {width_px: 0}}\n")
        assert problems == []
        stacks = table["basemap"]["line_effects"]  # ty: ignore[invalid-argument-type]
        assert stacks == {"major": EffectStack(), "lane": EffectStack()}

    def test_a_stack_is_the_effects_in_key_order(self) -> None:
        """Effects are applied in the order the stack writes them."""
        text = "line_effects:\n  lane:\n    shadow: {offset_px: 1, strength: 0.4}\n    casing: {width_px: 2}\n"
        table, _ = _check(text)
        effects = table["basemap"]["line_effects"]["lane"].effects  # ty: ignore[invalid-argument-type]
        assert [type(e) for e in effects] == [Shadow, Casing]

    def test_a_colour_resolves_through_the_files_scope(self, tmp_path: Path) -> None:
        """A casing colour may be an alias, a pigment name or a hex."""
        text = (
            "colours:\n  sky: cerulean\n"
            "line_effects:\n  major: {casing: {width_px: 2, colour: sky}}\n"
            "  lane: {shadow: {offset_px: 1, strength: 0.3, colour: indigo}}\n"
        )
        effects = _style(tmp_path, text).basemap.line_effects
        assert effects["major"].effects == (
            Casing(width_px=2.0, colour=pigment("cerulean").colour),
        )
        assert effects["lane"].effects == (
            Shadow(offset_px=1.0, strength=0.3, colour=pigment("indigo").colour),
        )

    def test_a_theme_preset_expands_to_its_stack(self, tmp_path: Path) -> None:
        """A preset the file defines is the stack the line class holds."""
        text = "effect_presets:\n  soft: {glow: {spread_px: 2, strength: 0.5}}\nline_effects:\n  track: soft\n"
        stack = _style(tmp_path, text).basemap.line_effects["track"]
        assert stack == EffectStack(effects=(Glow(spread_px=2.0, strength=0.5),))


class TestTheRefusals:
    """Every refusal names the file, the key path and the line."""

    def test_an_unknown_line_class_names_the_nearest(self) -> None:
        """`majr` is an unknown key at its own line, suggesting `major`."""
        _, problems = _check("line_effects:\n  majr: cased\n")
        assert problems == [(2, "line_effects.majr", "unknown key; did you mean major?")]

    def test_an_unknown_preset_names_the_nearest(self) -> None:
        """A preset name that misses suggests the nearest built-in."""
        _, problems = _check("line_effects:\n  major: casd\n")
        assert problems == [
            (2, "line_effects.major", "'casd' is not an effect preset; did you mean cased?")
        ]

    def test_an_unknown_effect_kind_names_the_nearest(self) -> None:
        """`cassing` is an unknown key at its line, suggesting `casing`."""
        _, problems = _check("line_effects:\n  major:\n    cassing: {width_px: 1}\n")
        assert problems == [(3, "line_effects.major.cassing", "unknown key; did you mean casing?")]

    def test_a_preset_key_beside_effects_is_refused(self) -> None:
        """A `preset` key in a stack reads that a class takes a name or a stack, not both."""
        _, problems = _check(
            "line_effects:\n  major:\n    preset: cased\n    glow: {strength: 0.5}\n"
        )
        assert problems == [
            (
                3,
                "line_effects.major.preset",
                "a line class takes a preset name or a stack, not both",
            )
        ]

    def test_a_value_that_is_neither_is_refused(self) -> None:
        """A number is no preset name or stack."""
        _, problems = _check("line_effects:\n  major: 3\n")
        assert problems == [
            (2, "line_effects.major", "is a preset name or a table of casing, glow and shadow")
        ]

    def test_the_table_must_be_a_table(self) -> None:
        """`line_effects: cased` is refused at its own line."""
        _, problems = _check("line_effects: cased\n")
        assert problems == [(1, "line_effects", "is a table of keys")]

    def test_an_effect_must_be_a_table(self) -> None:
        """`casing: 3` is refused at its own line."""
        _, problems = _check("line_effects:\n  major:\n    casing: 3\n")
        assert problems == [(3, "line_effects.major.casing", "is a table of keys")]

    def test_an_unknown_effect_field_names_the_nearest(self) -> None:
        """`widht_px` is an unknown key at its line."""
        _, problems = _check("line_effects:\n  major:\n    casing:\n      widht_px: 1\n")
        assert problems == [
            (4, "line_effects.major.casing.widht_px", "unknown key; did you mean width_px?")
        ]

    def test_a_bad_colour_is_refused_at_its_line(self) -> None:
        """A colour that names nothing is refused where written."""
        _, problems = _check("line_effects:\n  major:\n    casing:\n      colour: nothing\n")
        assert [(line, key) for line, key, _ in problems] == [
            (4, "line_effects.major.casing.colour")
        ]

    def test_a_wrong_type_is_refused_at_its_line(self) -> None:
        """A string for a number is refused where written."""
        _, problems = _check("line_effects:\n  major:\n    glow:\n      strength: lots\n")
        assert problems == [(4, "line_effects.major.glow.strength", "'lots' is not a number")]

    @pytest.mark.parametrize(
        ("text", "key", "message"),
        [
            (
                "casing: {strength: 1.4}",
                "casing.strength",
                "strength is 1.4; it must be from 0 to 1",
            ),
            (
                "casing: {strength: -0.1}",
                "casing.strength",
                "strength is -0.1; it must be from 0 to 1",
            ),
            ("glow: {blur_px: .inf}", "glow.blur_px", "blur_px is inf; it must be from 0 to 16"),
            (
                "glow: {spread_px: .nan}",
                "glow.spread_px",
                "spread_px is nan; it must be from 0 to 16",
            ),
            (
                "shadow: {offset_px: -1}",
                "shadow.offset_px",
                "offset_px is -1; it must be from 0 to 16",
            ),
            (
                "casing: {width_px: 16.5}",
                "casing.width_px",
                "width_px is 16.5; it must be from 0 to 16",
            ),
            (
                "shadow: {blur_px: -.inf}",
                "shadow.blur_px",
                "blur_px is -inf; it must be from 0 to 16",
            ),
        ],
        ids=["strength-high", "strength-low", "inf", "nan", "negative", "too-wide", "minus-inf"],
    )
    def test_a_number_out_of_range_is_located_and_never_clipped(
        self, text: str, key: str, message: str
    ) -> None:
        """A value outside its range, or not finite, is a problem at its own key and line."""
        _, problems = _check(f"line_effects:\n  major:\n    {text}\n")
        assert problems == [(3, f"line_effects.major.{key}", message)]

    def test_the_range_bounds_are_inclusive(self) -> None:
        """0 and 16 for a pixel field and 0 and 1 for a strength are accepted."""
        text = "line_effects:\n  major: {glow: {spread_px: 16, blur_px: 0, strength: 1}}\n"
        _, problems = _check(text)
        assert problems == []

    def test_a_refused_effect_keeps_the_others(self) -> None:
        """A stack with one bad effect still holds the good one."""
        text = "line_effects:\n  major:\n    casing: {strength: 2}\n    glow: {strength: 0.5, spread_px: 1}\n"
        table, problems = _check(text)
        assert len(problems) == 1
        stack = table["basemap"]["line_effects"]["major"]  # ty: ignore[invalid-argument-type]
        assert stack.effects == (Glow(spread_px=1.0, strength=0.5),)

    def test_a_range_error_in_a_preset_is_located_in_the_preset(self) -> None:
        """A preset's number is checked where the preset is written."""
        _, problems = _check("effect_presets:\n  soft:\n    glow: {strength: 3}\n")
        assert problems == [
            (3, "effect_presets.soft.glow.strength", "strength is 3; it must be from 0 to 1")
        ]


class TestTheLoaderFields:
    """The two group fields cannot be set inside their group."""

    def test_the_two_messages_are_pinned(self) -> None:
        """Naming `basemap.line_effects` or `route_ink.effects` is refused at that key."""
        text = "basemap:\n  roads: all\n  line_effects: {}\nroute_ink:\n  effects: {}\n"
        table, problems = _check(text)
        assert problems == [
            (3, "basemap.line_effects", "set only by the top-level line_effects.<class>"),
            (5, "route_ink.effects", "set only by the top-level line_effects.route"),
        ]
        assert table == {"basemap": {"roads": "all"}, "route_ink": {}}

    def test_the_fields_are_the_two_loader_ones(self) -> None:
        """`LOADER_FIELDS` names exactly the two fields and the keys that set them."""
        assert LOADER_FIELDS == {
            ("basemap", "line_effects"): "line_effects.<class>",
            ("route_ink", "effects"): "line_effects.route",
        }

    def test_a_loader_field_is_refused_when_loading(self, tmp_path: Path) -> None:
        """The refusal reaches the loader as a located error."""
        problems = _problems(tmp_path, "route_ink:\n  effects:\n    effects: []\n")
        assert problems == [
            (2, "route_ink.effects", "set only by the top-level line_effects.route")
        ]


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

    def test_replacing_an_inherited_preset_needs_override(self, tmp_path: Path) -> None:
        """A child preset of a parent's name needs `override: true`, and names the parent's line."""
        _write(
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
        _write(
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
        _write(
            tmp_path,
            "parent.yaml",
            "effect_presets:\n  soft: {glow: {strength: 0.5, spread_px: 1}}\n",
        )
        style = _style(tmp_path, "extends: parent.yaml\nline_effects:\n  route: soft\n")
        assert style.route_ink.effects == EffectStack(effects=(Glow(spread_px=1.0, strength=0.5),))

    def test_a_preset_is_unknown_to_the_parent_that_comes_before_it(self, tmp_path: Path) -> None:
        """A parent cannot name a preset only its child defines."""
        _write(tmp_path, "parent.yaml", "line_effects:\n  lane: soft\n")
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
        _write(tmp_path, "parent.yaml", "line_effects:\n  route: lifted\n")
        style = _style(tmp_path, "extends: parent.yaml\nline_effects:\n  major: cased\n")
        assert style.route_ink.effects == BUILT_IN_PRESETS["lifted"]
        assert style.basemap.line_effects == {"major": BUILT_IN_PRESETS["cased"]}

    def test_a_child_class_replaces_the_parents_stack_whole(self, tmp_path: Path) -> None:
        """A child's `major: halo` replaces the parent's `major: cased`, not merges with it."""
        _write(tmp_path, "parent.yaml", "line_effects:\n  major: cased\n  lane: cased\n")
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
        _write(tmp_path, "parent.yaml", "line_effects:\n  major: cased\n")
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
        _write(tmp_path, "parent.yaml", "line_effects:\n  route: lifted\n")
        style = _style(tmp_path, "extends: parent.yaml\nline_effects:\n  route: {}\n")
        assert style.route_ink.effects == EffectStack()
        assert style.digest() == Style().digest()
