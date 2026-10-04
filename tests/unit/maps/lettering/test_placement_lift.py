"""How far a name is lifted off its line, and the boxes a curved name takes."""

import pytest

from pyntpot.maps.lettering.label import TIER_RIVER, TIER_ROAD, WET_SPREAD, Label, feature_px
from pyntpot.maps.lettering.placement_lift import (
    INK_ASCENT_CAPS,
    INK_DESCENT_CAPS,
    LIFT_CAPS,
    LIFT_FEATURE_FRAC,
    _reading,
    lift_baseline,
    lift_middle,
    lift_px,
)

from support.basemaps import label_basemap, river_label


def test_a_name_on_a_line_that_runs_upwards_is_turned_to_read_downwards():
    """Turning a window round is not rejecting it, which is the whole rule."""
    up = [(100.0, float(y)) for y in range(300, 100, -5)]
    assert _reading(up)[-1][1] > _reading(up)[0][1]
    leftwards = [(float(x), 100.0) for x in range(300, 100, -5)]
    assert _reading(leftwards)[-1][0] > _reading(leftwards)[0][0]
    assert len(_reading(up)) == len(up), "a window was dropped, not turned"


def test_a_river_name_is_lifted_clear_of_the_water_it_names():
    """The centreline is not the water: the Lyn is painted nine pixels wide."""
    # The name was lifted half a type size off the middle of the river, which put
    # the letters in it. The clearance carries the painted half-width of the
    # watercourse now, so a wide river pushes its name further out than a thin
    # one and a card drawn at another size scales with it.
    thin = Label(name="Heddon", kind="river", size=18.0, feature_px=2.2)
    wide = Label(name="Lyn", kind="river", size=18.0, feature_px=8.4)
    assert lift_px(wide) > lift_px(thin), "a wide river lifts no further"
    # And both clear their own water: the baseline is off the centreline by
    # more than half the mark is wide.
    for label in (thin, wide):
        assert lift_px(label) > label.feature_px * 0.5


def test_a_wide_river_carries_its_name_on_the_water():
    """Now that the Severn is drawn at the width it occupies, the name goes in it."""
    wide = river_label(40.0)
    assert wide.in_water
    assert lift_px(wide) == 0.0
    # The band of ink straddles the centreline rather than sitting off it.
    assert lift_middle(wide, 1.0) == pytest.approx(0.0, abs=0.01)


def test_a_river_drawn_at_the_floor_keeps_its_name_beside_the_water():
    """A brook exaggerated up to be visible has no room for its own name."""
    thin = river_label(11.0)
    assert not thin.in_water
    assert lift_px(thin) > 0.0
    assert lift_middle(thin, 1.0) != pytest.approx(0.0, abs=0.01)


def test_a_name_clears_its_own_feature_on_whichever_side_it_takes():
    """The clearance is a fact about the ink, and a baseline is not the ink."""
    # The lift used to be applied to the baseline, and letters sit above their
    # baseline rather than straddling it: one side cleared the feature and the
    # other wrote the whole ascent back across it. Both "Lyn" labels
    # took the second side and seven glyph pixels in ten were in the river.
    river = Label(
        name="Lyn",
        kind="river",
        why="",
        px=0.0,
        py=0.0,
        tier=TIER_RIVER,
        size=18.0,
        feature_px=11.4,
    )
    want = lift_px(river)
    for side in (1.0, -1.0):
        base = lift_baseline(river, side)
        # Letters sit above their baseline whichever side of the line the
        # baseline was put on, so the ink band is the same way up both times
        # and only one of its two edges is the near one.
        edges = (base + river.size * INK_ASCENT_CAPS, base - river.size * INK_DESCENT_CAPS)
        near = min(abs(e) for e in edges)
        assert near == pytest.approx(want), f"side {side} does not clear"
        assert base * side > 0.0, "the baseline is on the side that was chosen"


def test_the_box_a_curved_name_reserves_is_centred_on_its_own_ink():
    """The placer defends boxes and the pen writes glyphs, and they are one thing."""
    road = Label(
        name="A361",
        kind="road",
        why="",
        px=0.0,
        py=0.0,
        tier=TIER_ROAD,
        size=14.0,
        feature_px=6.75,
    )
    for side in (1.0, -1.0):
        base = lift_baseline(road, side)
        middle = lift_middle(road, side)
        top = base + road.size * INK_ASCENT_CAPS
        bottom = base - road.size * INK_DESCENT_CAPS
        assert middle == pytest.approx((top + bottom) / 2)


def test_the_clearance_scales_with_the_water_the_painter_actually_laid_down():
    """The layers carry the brush's nominal width, not its footprint."""
    # A brush bleeds, smooths and drifts past its own nominal edge, so a
    # clearance taken against the nominal width stands the name off less water
    # than it has to clear.
    assert WET_SPREAD > 1.0
    wide = label_basemap(wet_px={"major": 12.0, "medium": 3.0, "minor": 1.0})
    narrow = label_basemap(wet_px={"major": 4.0, "medium": 3.0, "minor": 1.0})
    big = Label(
        name="Lyn",
        kind="river",
        why="",
        px=0.0,
        py=0.0,
        tier=TIER_RIVER,
        size=18.0,
        feature_px=feature_px(wide, "river", "major"),
    )
    small = Label(
        name="Lyn",
        kind="river",
        why="",
        px=0.0,
        py=0.0,
        tier=TIER_RIVER,
        size=18.0,
        feature_px=feature_px(narrow, "river", "major"),
    )
    assert lift_px(big) > lift_px(small)
    # The clearance starts where the painted ink stops: the whole painted
    # half-width, then `LIFT_CAPS` of the type size as paper.
    assert LIFT_FEATURE_FRAC == 1.0
    assert lift_px(big) - big.feature_px * 0.5 == pytest.approx(big.size * LIFT_CAPS)
