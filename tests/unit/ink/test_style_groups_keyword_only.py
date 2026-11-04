"""The ink style groups and the wash options are built by keyword only."""

import pytest

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.style import PaperStyle, WashStyle
from pyntpot.ink.washing import WashOptions

GROUPS = (PaperStyle, WashStyle, BrushStyle, WashOptions)


@pytest.mark.parametrize("group", GROUPS, ids=[group.__name__ for group in GROUPS])
def test_an_ink_style_group_takes_only_keywords(group: type) -> None:
    """A positional argument to the group raises `TypeError`."""
    with pytest.raises(TypeError):
        group(1.0)
