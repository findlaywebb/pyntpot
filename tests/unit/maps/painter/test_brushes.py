"""A plate's brushes and the cover classes' default darkness."""

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.maps.painter.brushes import COVER_CFG, plate_brushes
from pyntpot.maps.style_groups import CoverStyle


def test_every_class_the_plate_paints_has_a_brush():
    """The plate's brush table covers every class the layers can carry."""
    brushes = plate_brushes(BrushStyle(), 2.0, {"major": 8.0, "medium": 5.0, "minor": 2.0})
    assert set(brushes) == {"major", "medium", "minor", "coast", "road_major", "lane", "track"}
    assert brushes["coast"][0].width < brushes["medium"][0].width


def test_the_default_cover_classes_match_the_cover_group():
    """The painter's cover table and the style group's default carry the same classes and values."""
    assert CoverStyle().cover_cfg == COVER_CFG
