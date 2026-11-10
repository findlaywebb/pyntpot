"""Tests for the brush: the brush sheet's cells, the brush with its flags off, the nib rule."""

import pytest

from pyntpot.ink.brush import (
    BRUSH_OVERRIDE_KEYS,
    brush_from_id,
    brush_id_known,
    brush_ids,
    ink_aux,
    scaled_brush,
)
from pyntpot.ink.brush_sheet import BRUSH_COLOURS, BRUSH_TREATMENTS, PEN_ROWS
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.pad import InkPad

from support.flags_off import flags_off


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


@pytest.mark.parametrize("key", sorted(BRUSH_OVERRIDE_KEYS), ids=sorted(BRUSH_OVERRIDE_KEYS))
def test_every_override_key_changes_the_brush(key: str):
    """Each override key, set to a value no treatment holds, changes the brush it builds."""
    plain = BrushStyle(brush_overrides={})
    over = BrushStyle(brush_overrides={"lane": {key: 0.317}})
    without, _ = brush_from_id("LAN5-a", 1.8, 2.0, plain, "lane")
    with_key, _ = brush_from_id("LAN5-a", 1.8, 2.0, over, "lane")
    assert with_key != without


def test_without_an_override_key_the_overrides_are_read_by_the_lower_case_prefix():
    """With no override key, the brush reads the overrides under its id's prefix, lower case."""
    over = BrushStyle(brush_overrides={"riv": {"darkness": 0.317}})
    plain, _ = brush_from_id("RIV1-a", 8.4, 2.0, BrushStyle(brush_overrides={}))
    read, _ = brush_from_id("RIV1-a", 8.4, 2.0, over)
    assert read != plain


@pytest.mark.parametrize(
    ("brush_id", "known"),
    [("MAJ6-e", True), ("TRK4-d", True), ("MAJ9-e", False), ("XXX1-a", False), ("MAJ6", False)],
    ids=["MAJ6-e", "TRK4-d", "no-row", "no-class", "no-colour"],
)
def test_a_brush_id_is_known_only_on_the_sheet(brush_id: str, known: bool):
    """A brush id is known when the sheet has its row and its class has its colour."""
    assert brush_id_known(brush_id) is known


def test_every_phase_1_brush_flag_off_builds_a_plain_brush():
    """With the phase 1 flags off, the brush carries no reservoir, no directional break and no aux."""
    style = flags_off(BrushStyle)
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


def test_every_phase_2_brush_flag_off_but_the_ink_grid_builds_a_plain_pad():
    """With the phase 2 flags off the brush and pad are inert, and `ink_ss` at 1 is the plain pad."""
    style = flags_off(BrushStyle)
    assert style.ink_ss == 3
    assert not (style.brush_organic or style.ink_joins or style.stroke_smooth)
    brush, _ = brush_from_id("TRK4-d", 2.4, 2.0, style, "track")
    assert not brush.organic and brush.smooth == 0.0 and brush.unit == 1.0
    assert scaled_brush(brush, 1) is brush
    pad = InkPad((8, 8), brush, flags_off(BrushStyle, ink_ss=1))
    assert pad.ss == 1 and pad.tol == 0.0 and not pad.any()
    assert InkPad((8, 8), brush, style).ss == 3


def test_a_missed_brush_id_names_the_nearest_one():
    """A brush id one letter off a real cell is refused with that cell suggested."""
    with pytest.raises(ValueError, match="no such brush 'RIV1-z'; did you mean RIV1-a\\?"):
        brush_from_id("RIV1-z", 3.0, 2.0, BrushStyle())


def test_a_brush_id_far_from_every_cell_is_refused_without_a_suggestion():
    """When no id is close, the refusal carries no 'did you mean' clause."""
    with pytest.raises(ValueError, match=r"no such brush 'zzzzzz'$"):
        brush_from_id("zzzzzz", 3.0, 2.0, BrushStyle())


def test_the_catalogue_tables_refuse_assignment():
    """The sheet's tables, outer and inner, are read-only."""
    with pytest.raises(TypeError):
        BRUSH_TREATMENTS["9"] = {}  # ty: ignore[invalid-assignment]
    with pytest.raises(TypeError):
        BRUSH_TREATMENTS["1"]["darkness"] = 0.0  # ty: ignore[invalid-assignment]
    with pytest.raises(TypeError):
        BRUSH_COLOURS["RIV"] = {}  # ty: ignore[invalid-assignment]
    with pytest.raises(TypeError):
        BRUSH_COLOURS["RIV"]["b"] = "#000000"  # ty: ignore[invalid-assignment]


def test_brush_ids_is_the_cross_product_the_sheet_implies():
    """`brush_ids` lists every prefix, row and column once, and `brush_id_known` accepts each."""
    ids = brush_ids()
    assert len(ids) == 112
    assert len(set(ids)) == 112
    assert ids[0] == "RIV1-a"
    assert ids[-1] == "TRK8-f"
    assert "MAJ6-e" in ids
    assert all(brush_id_known(brush_id) for brush_id in ids)
