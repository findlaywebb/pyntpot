"""A theme's `cover.pigments` entry: every form's transparency, the `extends` case and each error."""

from pathlib import Path

import pytest

from pyntpot.ink import Colour
from pyntpot.maps import CoverPigment, Style, ThemeError

from support.theme_files import write_theme

#: Each theme form, its text and the `CoverPigment` it must load as for `water` (built in: 0.04).
FORMS = {
    "entry-transparency": (
        "cover:\n  pigments:\n    water: {pigment: cerulean, transparency: 0.5}\n",
        ("#2a7ab0", 0.5),
    ),
    "pigment-name": ("cover:\n  pigments:\n    water: cerulean\n", ("#2a7ab0", 0.22)),
    "alias-to-name": (
        "colours:\n  sky: cerulean\ncover:\n  pigments:\n    water: sky\n",
        ("#2a7ab0", 0.22),
    ),
    "palette-alias-to-name": (
        "palette: plain\ncover:\n  pigments:\n    water: blue\n",
        ("#2b3d8f", 0.06),
    ),
    "theme-pigment-own": (
        (
            "pigments:\n  slate: {colour: '#111111', transparency: 0.4}\n"
            "cover:\n  pigments:\n    water: slate\n"
        ),
        ("#111111", 0.4),
    ),
    "theme-pigment-none": (
        "pigments:\n  slate: {colour: '#111111'}\ncover:\n  pigments:\n    water: slate\n",
        ("#111111", 0.04),
    ),
    "derived-none": (
        "pigments:\n  my_blue: {base: ultramarine}\ncover:\n  pigments:\n    water: my_blue\n",
        ("#2b3d8f", 0.06),
    ),
    "table-pigment-name": (
        "cover:\n  pigments:\n    water: {pigment: cerulean}\n",
        ("#2a7ab0", 0.22),
    ),
    "derived-own": (
        (
            "pigments:\n  my_blue: {base: ultramarine, transparency: 0.3}\n"
            "cover:\n  pigments:\n    water: my_blue\n"
        ),
        ("#2b3d8f", 0.3),
    ),
    "bare-hex": ("cover:\n  pigments:\n    water: '#112233'\n", ("#112233", 0.04)),
    "alias-to-hex": (
        "colours:\n  sky: '#112233'\ncover:\n  pigments:\n    water: sky\n",
        ("#112233", 0.04),
    ),
    "gpl-alias": (
        "palette: mine.gpl\ncover:\n  pigments:\n    water: sky_blue\n",
        ("#2b3d8f", 0.04),
    ),
    "pigment-table-hex-only": (
        "cover:\n  pigments:\n    water: {pigment: '#112233'}\n",
        ("#112233", 0.04),
    ),
}

GPL = "GIMP Palette\nName: x\n#\n 43  61 143\tSky Blue\n"


def _load(tmp_path: Path, text: str) -> Style:
    """Load the theme `text`, beside a `.gpl` palette it may name."""
    write_theme(tmp_path, "mine.gpl", GPL)
    return Style.from_yaml(write_theme(tmp_path, "theme.yaml", text))


def _problems(tmp_path: Path, text: str) -> list[tuple[str, int | None, str]]:
    """The key, line and message of every problem loading the theme `text` raises."""
    with pytest.raises(ThemeError) as caught:
        _load(tmp_path, text)
    return [(p.key, p.line, p.message) for p in caught.value.problems]


class TestTheForms:
    """Whatever form an entry takes, one rule gives its transparency."""

    @pytest.mark.parametrize("form", FORMS, ids=list(FORMS))
    def test_each_entry_form_resolves_its_transparency(self, tmp_path: Path, form: str) -> None:
        """The entry loads as the pinned colour and the transparency the precedence rule gives."""
        text, (colour, transparency) = FORMS[form]
        entry = _load(tmp_path, text).cover.pigments["water"]
        assert entry == CoverPigment(Colour(colour), transparency)
        assert type(entry) is CoverPigment

    def test_an_integer_transparency_loads_as_a_float(self, tmp_path: Path) -> None:
        """`transparency: 1` is accepted and stored as `1.0`."""
        text = "cover:\n  pigments:\n    water: {pigment: '#112233', transparency: 1}\n"
        entry = _load(tmp_path, text).cover.pigments["water"]
        assert entry.transparency == 1.0
        assert type(entry.transparency) is float

    def test_an_extends_child_bare_hex_takes_the_built_in_not_its_parents(
        self, tmp_path: Path
    ) -> None:
        """A child's bare hex replaces its parent's `{pigment, transparency}` whole."""
        write_theme(
            tmp_path,
            "parent.yaml",
            "cover:\n  pigments:\n    wood: {pigment: '#111111', transparency: 0.4}\n",
        )
        child = write_theme(
            tmp_path,
            "child.yaml",
            "extends: parent.yaml\ncover:\n  pigments:\n    wood: '#222222'\n",
        )
        pigments = Style.from_yaml(child).cover.pigments
        assert pigments["wood"] == CoverPigment(Colour("#222222"), 0.05)
        assert pigments["farmland"] == CoverPigment(Colour("#dfe0b0"), 0.10)

    def test_an_extends_child_keeps_the_parents_other_entries(self, tmp_path: Path) -> None:
        """A child naming one class leaves the parent's table entry for another untouched."""
        write_theme(
            tmp_path,
            "parent.yaml",
            "cover:\n  pigments:\n    wood: {pigment: '#111111', transparency: 0.4}\n",
        )
        child = write_theme(
            tmp_path,
            "child.yaml",
            "extends: parent.yaml\ncover:\n  pigments:\n    rim: '#222222'\n",
        )
        assert Style.from_yaml(child).cover.pigments["wood"] == CoverPigment(Colour("#111111"), 0.4)


class TestTheErrors:
    """Each problem of the table form lands at its own key and line."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (
                "paper:\n  pigment_transparency:\n    wood: 0.1\n",
                ("paper.pigment_transparency", 2, "renamed to cover.pigments.<class>.transparency"),
            ),
            (
                "cover:\n  pigments:\n    wood:\n      pigment: ultramarin\n",
                (
                    "cover.pigments.wood.pigment",
                    4,
                    "'ultramarin' is not a pigment or a colour alias; did you mean ultramarine?",
                ),
            ),
            (
                (
                    "cover:\n  pigments:\n    wood:\n      pigment: ultramarine\n"
                    "      transparancy: 0.1\n"
                ),
                (
                    "cover.pigments.wood.transparancy",
                    5,
                    "unknown key; did you mean transparency?",
                ),
            ),
            (
                (
                    "cover:\n  pigments:\n    wood:\n      pigment: ultramarine\n"
                    "      pigmant: ultramarine\n"
                ),
                ("cover.pigments.wood.pigmant", 5, "unknown key; did you mean pigment?"),
            ),
            (
                "cover:\n  pigments:\n    wood: {pigment: ultramarine, transparency: 1.5}\n",
                ("cover.pigments.wood.transparency", 3, "1.5 is not from 0 to 1"),
            ),
            (
                "cover:\n  pigments:\n    wood: {pigment: ultramarine, transparency: -0.1}\n",
                ("cover.pigments.wood.transparency", 3, "-0.1 is not from 0 to 1"),
            ),
            (
                "cover:\n  pigments:\n    wood: {pigment: ultramarine, transparency: true}\n",
                ("cover.pigments.wood.transparency", 3, "True is not a number"),
            ),
            (
                "cover:\n  pigments:\n    wood: {pigment: ultramarine, transparency: '0.1'}\n",
                ("cover.pigments.wood.transparency", 3, "'0.1' is not a number"),
            ),
            (
                "cover:\n  pigments:\n    wood: {transparency: 0.1}\n",
                ("cover.pigments.wood", 3, "pigment is required"),
            ),
            (
                "cover:\n  pigments:\n    wood: ['#dfe0b0', 0.06]\n",
                (
                    "cover.pigments.wood",
                    3,
                    (
                        "a list is not a pigment; write a colour reference or a table of pigment"
                        " and transparency"
                    ),
                ),
            ),
        ],
        ids=[
            "renamed-key",
            "unknown-pigment",
            "unknown-inner-key",
            "unknown-inner-key-pigment",
            "transparency-above-one",
            "transparency-below-zero",
            "transparency-bool",
            "transparency-str",
            "no-pigment",
            "list-form",
        ],
    )
    def test_each_table_error_is_at_its_own_key(
        self, tmp_path: Path, text: str, expected: tuple[str, int, str]
    ) -> None:
        """The one problem names its dotted key, its line and its message."""
        assert _problems(tmp_path, text) == [expected]

    def test_a_bad_inner_value_does_not_hide_another(self, tmp_path: Path) -> None:
        """A bad `pigment` and a bad `transparency` in one table are both reported."""
        text = "cover:\n  pigments:\n    wood: {pigment: nope, transparency: 2}\n"
        keys = [key for key, _line, _message in _problems(tmp_path, text)]
        assert keys == ["cover.pigments.wood.pigment", "cover.pigments.wood.transparency"]
