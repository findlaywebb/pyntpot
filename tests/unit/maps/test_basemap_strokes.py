"""Tests for the card's river strokes: where a watercourse is cut to the card."""

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.maps.basemap_strokes import Frame, rivers_from_paths

#: The card box, in metres.
CLIP = (0.0, 0.0, 1000.0, 800.0)


def frame() -> Frame:
    """A card frame over `CLIP` at 6 display metres a pixel."""
    geometry = {"mpp_display": 6.0, "wet_px": {"major": 8.0, "medium": 6.0, "minor": 4.0}}
    return Frame(CLIP, 1.0, geometry, BrushStyle())


def test_a_river_that_enters_from_beyond_the_card_starts_on_its_edge() -> None:
    """A watercourse crossing the card's west edge is cut there, not at its first point inside."""
    row = {"c": "river", "n": "Afon Wysg", "d": "M-300,400 L250,420 L700,380"}
    (river,) = rivers_from_paths([row], [], frame())
    assert river.line[0][0] == CLIP[0]
    assert 400.0 < river.line[0][1] < 420.0
    assert river.line[-1] == (700.0, 380.0)


def test_a_river_that_leaves_and_comes_back_is_two_strokes_cut_at_the_edge() -> None:
    """A stream that runs off the south edge and back is two strokes, each cut on that edge."""
    row = {"c": "stream", "n": "Afon Wysg", "d": "M100,300 L300,-200 L600,-200 L800,300"}
    first, second = rivers_from_paths([row], [], frame())
    ends = sorted([first.line[0], first.line[-1], second.line[0], second.line[-1]])
    assert [p for p in ends if p[1] == CLIP[1]] == [(220.0, 0.0), (680.0, 0.0)]
