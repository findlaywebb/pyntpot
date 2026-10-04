"""The land-cover phase: labels, the wet field and a wash for each class."""

import numpy as np

from pyntpot.ink.style import WashStyle
from pyntpot.maps.painter.cover import cover_order, paint_cover, wet_field
from pyntpot.maps.painter.job import PlateStack
from pyntpot.maps.painter.water import paint_water

from .jobs import square, tiny_job, tiny_style

#: A meadow, a wood beside it, and a lake over the meadow's corner.
COVER = {
    "meadow": (square(20.0, 20.0, 150.0, 200.0),),
    "wood": (square(160.0, 20.0, 300.0, 200.0),),
}


def _painted(tmp_path, **over):
    """A job and the stack after the water and cover phases, over `COVER` and a lake."""
    job = tiny_job(
        tmp_path,
        over.pop("style", None),
        cover=COVER,
        cover_order=("meadow", "wood", "heath"),
        lakes=(square(100.0, 100.0, 150.0, 150.0),),
        **over,
    )
    stack = PlateStack.blank(job.shape)
    paint_water(job, stack)
    paint_cover(job, stack)
    return job, stack


class TestWetField:
    """The one wet map over the union of the cover."""

    def test_closing_the_cover_puts_the_class_seams_under_water(self):
        """The wet map's whole point: two washes that meet, meet wet.

        The classes do not abut, they meet along hairlines of unmapped ground, so
        the union taken as it stands leaves every seam dry however wide the bleed
        is set. Closing over the gap is what reaches them, and the land's outer
        silhouette is the one edge that has to survive it.
        """
        label = np.zeros((120, 200), np.uint8)
        label[20:100, 20:108] = 1
        label[20:100, 110:180] = 2  # a two pixel hairline between the two classes
        seam = np.zeros(label.shape, bool)
        seam[20:100, 106:112] = True
        raw = wet_field(label, WashStyle(wet_bleed=True, wet_close_px=0.0), 5.0)
        closed = wet_field(label, WashStyle(wet_bleed=True, wet_close_px=5.0), 5.0)
        assert raw is not None and closed is not None
        assert float(raw[seam].mean()) < 0.05
        assert float(closed[seam].mean()) > 0.5

    def test_no_wet_field_without_bleeding_or_land(self):
        """Bleeding off, or nothing labelled, gives no field."""
        label = np.ones((8, 8), np.uint8)
        assert wet_field(label, WashStyle(wet_bleed=False), 5.0) is None
        assert wet_field(np.zeros((8, 8), np.uint8), WashStyle(wet_bleed=True), 5.0) is None


class TestPaintCover:
    """What the phase writes into the stack."""

    def test_each_class_is_labelled_where_its_rings_are_and_water_is_cut_out(self, tmp_path):
        """Classes take their order's indices, the lake takes none, and a missing class is skipped."""
        job, stack = _painted(tmp_path)
        assert cover_order(job) == ["meadow", "wood"]
        assert stack.label[30, 20] == 1 and stack.label[30, 120] == 2
        assert stack.label[60, 60] == 0  # the lake's pixel, cut out of the meadow
        assert stack.label[1, 1] == 0

    def test_the_wood_is_found_and_washed(self, tmp_path):
        """The wood mask is the wood's label, and every class lays at least one layer."""
        _, stack = _painted(tmp_path)
        assert stack.wood_mask[30, 120] and not stack.wood_mask[30, 20]
        assert len(stack.trimmed) >= 2

    def test_no_wood_class_leaves_no_wood_mask(self, tmp_path):
        """Without the wood in the cover the mask stays empty."""
        job = tiny_job(
            tmp_path,
            cover={"meadow": COVER["meadow"]},
            cover_order=("meadow",),
        )
        stack = PlateStack.blank(job.shape)
        paint_cover(job, stack)
        assert not stack.wood_mask.any()
        assert stack.label.any()

    def test_cover_off_lays_the_one_pale_wash_and_labels_nothing(self, tmp_path):
        """The pale wash replaces the classes, and nothing is labelled."""
        style = tiny_style(cover={"land_cover": False})
        _, stack = _painted(tmp_path, style=style)
        assert len(stack.trimmed) == 1
        assert not stack.label.any() and not stack.wood_mask.any()
