"""Tests for the brush: the brush sheet's cells, the flags that are off by default, the nib rule."""

import pytest

from pyntpot.ink.brush import PEN_ROWS, brush_from_id, ink_aux, scaled_brush
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.pad import InkPad


def test_a_brush_id_names_a_treatment_and_a_colour():
    """The five approved picks resolve to the rows and inks they name."""
    style = BrushStyle()
    major, colour = brush_from_id("MAJ2-a", 3.6, 2.0, style)
    assert colour == "#b5623f"
    assert major.width == pytest.approx(7.2)
    track, olive = brush_from_id("TRK4-d", 2.4, 2.0, style)
    assert olive == "#6f6636"
    assert track.dry > major.dry  # the track is the dry, broken brush
    lane, umber = brush_from_id("LAN5-a", 1.8, 2.0, style, "lane")
    assert umber == "#6b4423"
    assert lane.pool == pytest.approx(1.4)  # the pen touch-down, as last tuned
    river, cobalt = brush_from_id("RIV1-a", 8.4, 2.0, style)
    assert cobalt == "#255d80"
    assert river.dry < track.dry


def test_a_brush_id_that_names_nothing_is_refused():
    """A style naming a brush the sheet does not carry fails where it is set."""
    with pytest.raises(ValueError, match="no such brush"):
        brush_from_id("MAJ9-a", 3.0, 2.0, BrushStyle())
    with pytest.raises(ValueError, match="no such brush"):
        brush_from_id("RIV1-z", 3.0, 2.0, BrushStyle())


def test_every_phase_1_brush_flag_is_off_by_default():
    """A field added here must not move a plate until a theme asks for it."""
    style = BrushStyle()
    assert not (style.ink_starve or style.dry_directional or style.pen_starve)
    brush, _ = brush_from_id("TRK4-d", 2.4, 2.0, style, "track")
    assert not (brush.starve or brush.dir_dry or brush.pen_starve)
    assert ink_aux((8, 8), brush) is None


def test_a_brush_never_takes_the_nib_treatment_or_the_other_way_round():
    """The two reservoirs are separate flags on separate tools."""
    both = BrushStyle(ink_starve=True, pen_starve=True)
    track, _ = brush_from_id("TRK4-d", 2.4, 2.0, both, "track")
    lane, _ = brush_from_id("LAN5-a", 1.8, 2.0, both, "lane")
    assert track.starve and not track.pen_starve
    assert lane.pen_starve and not lane.starve
    assert frozenset({"5", "6", "8"}) == PEN_ROWS


def test_every_phase_2_brush_flag_but_the_ink_grid_is_off_by_default():
    """A field added here must not move a plate until a theme asks for it.

    `ink_ss` is the one exception and is on at 3, because a mark under four
    render pixels wide cannot be held by the plate's own grid: that is the
    stair that reads as scratchiness. The rest still have to be
    inert, and `ink_ss` back at 1 still has to be the pad it always was.
    """
    style = BrushStyle()
    assert style.ink_ss == 3
    assert not (style.brush_organic or style.ink_joins or style.stroke_smooth)
    brush, _ = brush_from_id("TRK4-d", 2.4, 2.0, style, "track")
    assert not brush.organic and brush.smooth == 0.0 and brush.unit == 1.0
    assert scaled_brush(brush, 1) is brush
    pad = InkPad((8, 8), brush, BrushStyle(ink_ss=1))
    assert pad.ss == 1 and pad.tol == 0.0 and not pad.any()
    assert InkPad((8, 8), brush, style).ss == 3
