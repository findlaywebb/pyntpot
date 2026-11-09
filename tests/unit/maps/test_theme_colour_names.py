"""A theme names its colours by pigment as well as by hex, and a miss is located."""

from pathlib import Path

import pytest

from pyntpot.ink import Colour
from pyntpot.maps import Style
from pyntpot.maps.theme_errors import ThemeError


def _theme(tmp_path: Path, text: str) -> Path:
    """Write a theme file holding exactly `text`."""
    target = tmp_path / "theme.yaml"
    target.write_text(text, encoding="utf-8")
    return target


def test_a_pigment_name_loads_as_its_hex(tmp_path):
    """`cover.pigments.built: ultramarine` loads as ultramarine's `#2b3d8f`."""
    style = Style.from_yaml(_theme(tmp_path, "cover:\n  pigments:\n    built: ultramarine\n"))
    assert style.cover.pigments["built"] == "#2b3d8f"
    assert type(style.cover.pigments["built"]) is Colour


def test_a_pigment_name_loads_into_a_scalar_field(tmp_path):
    """A pigment name in `route_ink.colour` loads as that pigment's hex."""
    style = Style.from_yaml(_theme(tmp_path, "route_ink:\n  colour: ultramarine\n"))
    assert style.route_ink.colour == "#2b3d8f"


def test_a_misspelt_pigment_is_a_located_error_with_the_suggestion(tmp_path):
    """`ultramarin` is refused at its key and line, naming `ultramarine`."""
    theme = _theme(tmp_path, "cover:\n  pigments:\n    built: ultramarin\n")
    with pytest.raises(ThemeError) as caught:
        Style.from_yaml(theme)
    [problem] = caught.value.problems
    assert (problem.key, problem.line) == ("cover.pigments.built", 3)
    assert (
        problem.message
        == "'ultramarin' is not a pigment or a colour alias; did you mean ultramarine?"
    )


def test_upper_case_hex_is_stored_lower_case(tmp_path):
    """`#C22050` in a theme is stored as `#c22050`."""
    style = Style.from_yaml(_theme(tmp_path, "route_ink:\n  colour: '#C22050'\n"))
    assert style.route_ink.colour == "#c22050"
    assert type(style.route_ink.colour) is Colour


def test_a_non_string_colour_is_refused(tmp_path):
    """A number given for a colour reads as not a string."""
    theme = _theme(tmp_path, "route_ink:\n  colour: 5\n")
    with pytest.raises(ThemeError) as caught:
        Style.from_yaml(theme)
    assert [p.message for p in caught.value.problems] == ["5 is not a string"]
