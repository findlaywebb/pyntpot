"""A theme's `pigments:` table: derived pigments, collisions, overrides and located errors."""

from pathlib import Path

import pytest

from pyntpot.ink import Colour, pigment
from pyntpot.maps import Style, ThemeError
from pyntpot.maps.theme_check import check_theme_scoped
from pyntpot.maps.theme_scope import ThemeScope

from support.theme_files import theme_file


def _load(tmp_path: Path, text: str) -> Style:
    """Load the theme `text` from a file in `tmp_path`."""
    path = tmp_path / "t.yaml"
    path.write_text(text, encoding="utf-8")
    return Style.from_theme(path)


def _problems(tmp_path: Path, text: str) -> list[tuple[int | None, str]]:
    """The line and message of every problem loading `text` raises."""
    with pytest.raises(ThemeError) as caught:
        _load(tmp_path, text)
    return [(p.line, p.message) for p in caught.value.problems]


def _scope(text: str) -> ThemeScope:
    """The scope after checking the theme `text` in the built-in scope."""
    return check_theme_scoped(theme_file(text), {}, ThemeScope.built_in())[2]


class TestADerivedPigment:
    """A pigment with a `base`, a `colour`, or both."""

    def test_a_base_alone_is_the_base_under_a_new_name(self) -> None:
        """`base: ultramarine` holds ultramarine's colour, transparency and Colour Index."""
        scope = _scope("pigments:\n  my_blue: {base: ultramarine}\n")
        made = scope.registry.get("my_blue")
        base = pigment("ultramarine")
        assert (made.colour, made.transparency, made.colour_index) == (
            base.colour,
            base.transparency,
            base.colour_index,
        )
        assert made.name == "my_blue"

    def test_a_base_and_a_colour_keep_the_base_transparency(self) -> None:
        """`{base: ultramarine, colour: "#203070"}` is ultramarine's transparency in the new colour."""
        scope = _scope('pigments:\n  my_blue: {base: ultramarine, colour: "#203070"}\n')
        made = scope.registry.get("my_blue")
        assert made.colour == Colour("#203070")
        assert made.transparency == pigment("ultramarine").transparency
        assert made.colour_index == "PB29"

    def test_the_fields_given_override_the_base(self) -> None:
        """A given transparency and colour index replace the base's."""
        text = "pigments:\n  my_blue: {base: ultramarine, transparency: 0.5, colour_index: X}\n"
        made = _scope(text).registry.get("my_blue")
        assert (made.transparency, made.colour_index) == (0.5, "X")

    def test_a_colour_alone_is_an_anonymous_transparency(self) -> None:
        """A pigment with only a colour has no transparency and no Colour Index."""
        made = _scope('pigments:\n  slate: {colour: "#ABCDEF"}\n').registry.get("slate")
        assert (made.colour, made.transparency, made.colour_index) == ("#abcdef", None, None)

    def test_a_pigment_is_a_name_a_colour_field_takes(self, tmp_path: Path) -> None:
        """A theme pigment resolves in a colour field of the same file."""
        style = _load(
            tmp_path, 'pigments:\n  slate: {colour: "#abcdef"}\nroute_ink:\n  colour: slate\n'
        )
        assert style.route_ink.colour == "#abcdef"

    def test_a_pigment_records_the_file_and_line(self) -> None:
        """The bound entry names its file and its key's line."""
        bound = _scope("\npigments:\n  slate: {colour: '#abcdef'}\n").pigments["slate"]
        assert (bound.path, bound.line) == (Path("t.yaml"), 3)


class TestRefusals:
    """Each refusal is located at its key's line with what to write instead."""

    def test_a_built_in_name_points_at_the_derived_form(self, tmp_path: Path) -> None:
        """A pigment named ultramarine is refused, with `my_ultramarine: {base: ultramarine}`."""
        assert _problems(tmp_path, "pigments:\n  ultramarine: {colour: '#000000'}\n") == [
            (
                2,
                "'ultramarine' is a built-in pigment; derive one: my_ultramarine: {base: ultramarine}",
            )
        ]

    def test_a_name_that_is_no_alias_shape_is_refused(self, tmp_path: Path) -> None:
        """A pigment name with a capital or a doubled underscore is refused."""
        problems = _problems(tmp_path, "pigments:\n  Slate: {colour: '#000000'}\n")
        assert problems == [
            (2, "'Slate' is not a pigment name: lower-case words joined by single _")
        ]

    def test_neither_base_nor_colour_is_refused(self, tmp_path: Path) -> None:
        """A pigment with neither is a located error."""
        problems = _problems(tmp_path, "pigments:\n  slate: {transparency: 0.1}\n")
        assert problems == [(2, "needs a base pigment or a colour")]

    def test_an_unknown_base_suggests_the_nearest(self, tmp_path: Path) -> None:
        """A misspelt base names the nearest pigment, at the base's key."""
        problems = _problems(tmp_path, "pigments:\n  slate: {base: ultramarin}\n")
        assert problems == [(2, "no pigment 'ultramarin'; did you mean ultramarine?")]

    def test_a_bad_colour_is_refused(self, tmp_path: Path) -> None:
        """A colour that is no hex is refused with the hex message."""
        problems = _problems(tmp_path, "pigments:\n  slate: {colour: '#abc'}\n")
        assert problems == [(2, "'#abc' is not a # and six hexadecimal digits")]

    @pytest.mark.parametrize("value", ["1.5", "-0.1"], ids=["above", "below"])
    def test_a_transparency_outside_zero_to_one_is_refused(
        self, tmp_path: Path, value: str
    ) -> None:
        """A transparency outside 0 to 1 is refused."""
        text = f"pigments:\n  slate: {{colour: '#000000', transparency: {value}}}\n"
        (problem,) = _problems(tmp_path, text)
        assert problem[1].endswith("is not from 0 to 1")

    def test_an_unknown_field_suggests_the_nearest(self, tmp_path: Path) -> None:
        """An unknown pigment key names the nearest key."""
        problems = _problems(tmp_path, "pigments:\n  slate: {colour: '#000000', colur: 1}\n")
        assert problems == [(2, "unknown key; did you mean colour?")]

    def test_a_pigment_table_that_is_no_table_is_refused(self, tmp_path: Path) -> None:
        """`pigments: 5` is refused as no table."""
        assert _problems(tmp_path, "pigments: 5\n") == [(1, "is a table of keys")]


class TestOverride:
    """Replacing an inherited pigment needs `override: true`."""

    def _parent(self, tmp_path: Path) -> None:
        """Write a parent that defines `slate`."""
        (tmp_path / "parent.yaml").write_text("pigments:\n  slate: {colour: '#111111'}\n", "utf-8")

    def test_replacing_without_override_is_an_error_at_the_key(self, tmp_path: Path) -> None:
        """A child that redefines `slate` is told the parent's file and line."""
        self._parent(tmp_path)
        text = "extends: parent.yaml\npigments:\n  slate: {colour: '#222222'}\n"
        (problem,) = _problems(tmp_path, text)
        assert problem[0] == 3
        assert "'slate' is already a theme pigment" in problem[1]
        assert "parent.yaml:2" in problem[1]
        assert problem[1].endswith("add override: true")

    def test_override_with_nothing_to_override_is_refused(self, tmp_path: Path) -> None:
        """`override: true` on a pigment no file below defines is an error at its key."""
        text = "pigments:\n  slate: {colour: '#222222', override: true}\n"
        assert _problems(tmp_path, text) == [
            (2, "'slate' overrides no pigment; drop override: true")
        ]

    def test_replacing_with_override_takes_the_child(self, tmp_path: Path) -> None:
        """With `override: true` the child's pigment is the one a field resolves to."""
        self._parent(tmp_path)
        text = (
            "extends: parent.yaml\npigments:\n  slate: {colour: '#222222', override: true}\n"
            "route_ink:\n  colour: slate\n"
        )
        assert _load(tmp_path, text).route_ink.colour == "#222222"

    def test_a_child_inherits_a_pigment_and_derives_from_it(self, tmp_path: Path) -> None:
        """A child's `base` may name a parent's pigment."""
        self._parent(tmp_path)
        text = (
            "extends: parent.yaml\npigments:\n  darker: {base: slate, colour: '#050505'}\n"
            "route_ink:\n  colour: darker\n"
        )
        assert _load(tmp_path, text).route_ink.colour == "#050505"
