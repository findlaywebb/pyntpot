"""The letters style groups: frozen records built by keyword only."""

from collections.abc import Callable

import pytest

from pyntpot.letters import FaceStyle, HandStyle, NibStyle

#: Each group with its first field and a value other than the default.
GROUPS: tuple[tuple[Callable[..., object], str, object], ...] = (
    (FaceStyle, "label_route", "outline"),
    (HandStyle, "label_seed", 3),
    (NibStyle, "label_size_px", 14.0),
)


@pytest.mark.parametrize(
    ("group", "field", "value"), GROUPS, ids=["FaceStyle", "HandStyle", "NibStyle"]
)
def test_a_letters_style_group_takes_only_keywords(
    group: Callable[..., object], field: str, value: object
) -> None:
    """A letters style group refuses a positional field and builds from its keywords."""
    with pytest.raises(TypeError):
        group(value)
    assert getattr(group(**{field: value}), field) == value
