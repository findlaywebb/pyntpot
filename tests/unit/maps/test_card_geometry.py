"""Tests for the card's fitted geometry: the ribbon's radius follows the route and the slider."""

import math

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.maps.card_geometry import journal_geometry
from pyntpot.maps.style_groups import CardStyle, RibbonStyle


def test_the_ribbon_radius_is_the_fitted_curve_times_the_slider():
    """7.15 times the root of the box plus 158 m, then the slider."""
    card, brush = CardStyle(), BrushStyle()
    route = [(0.0, 0.0), (3200.0, 0.0), (3200.0, 900.0)]
    fitted = journal_geometry(route, card, RibbonStyle(), brush)
    want = 7.15 * math.sqrt(3200.0) + 158.0
    assert fitted["ribbon_m"] == round(want)
    wider = journal_geometry(route, card, RibbonStyle(ribbon_mult=1.25), brush)
    assert wider["ribbon_m"] == round(want * 1.25)
    assert wider["card"] == fitted["card"]  # the card is framed the same either way
