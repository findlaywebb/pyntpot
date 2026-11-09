"""A theme naming a brush the sheet lacks is refused with the nearest id suggested."""

import pytest

from pyntpot.maps.style import _groups
from pyntpot.maps.theme_check import check_theme

from support.theme_files import theme_file


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (
            "brush:\n  brushes:\n    lane: RIV1-z\n",
            "'RIV1-z' is not a brush on the sheet; did you mean RIV1-a?",
        ),
        (
            "route:\n  route_pen_brush: MAJ9-a\n",
            "'MAJ9-a' is not a brush on the sheet; did you mean MAJ8-a?",
        ),
        (
            "brush:\n  brushes:\n    lane: zzzzzz\n",
            "'zzzzzz' is not a brush on the sheet",
        ),
    ],
    ids=["colour-column", "row", "nothing-close"],
)
def test_a_missed_brush_id_in_a_theme_carries_the_suggestion(text: str, message: str):
    """The theme-side message names the nearest id, and only when one is close."""
    _, problems = check_theme(theme_file(text), _groups())
    assert [problem.message for problem in problems] == [message]


def test_a_known_brush_id_in_a_theme_is_accepted():
    """A real sheet cell raises no problem."""
    table, problems = check_theme(theme_file("brush:\n  brushes:\n    lane: RIV1-a\n"), _groups())
    assert problems == ()
    assert table == {"brush": {"brushes": {"lane": "RIV1-a"}}}
