"""The painting job and the plate stack: what they hold, derive and share."""

import numpy as np

from pyntpot.maps.painter.job import PlateStack, drawable

from .jobs import CARD, tiny_job, tiny_style


class TestDrawable:
    """Which lines the painter draws."""

    def test_a_single_point_is_not_a_line(self):
        """A line of one point is dropped; a line of two is kept as a point list."""
        kept = drawable((((1.0, 2.0),), ((0.0, 0.0), (1.0, 1.0))))
        assert kept == [[(0.0, 0.0), (1.0, 1.0)]]


class TestBegin:
    """What a job derives from the card and the style."""

    def test_the_plate_has_the_cards_render_shape_and_scale(self, tmp_path):
        """The canvas, the sheet and the derived sizes follow the card."""
        job = tiny_job(tmp_path)
        assert job.shape == (120, 160)
        assert (job.canvas.h, job.canvas.w) == (120, 160)
        assert job.scale == 2.0
        assert job.mpp == CARD.mpp
        assert job.rim_cov == 45.0

    def test_the_same_inputs_seed_the_same_generators(self, tmp_path):
        """Two jobs over one style draw the same first numbers from each shared generator."""
        style = tiny_style(wash={"blooms": True})
        one, two = tiny_job(tmp_path, style), tiny_job(tmp_path, style)
        assert one.bloom_rng is not None and two.bloom_rng is not None
        assert one.bloom_rng.random() == two.bloom_rng.random()
        assert one.dither_rng.random() == two.dither_rng.random()
        assert one.ink_rng.random() == two.ink_rng.random()
        assert one.pen_rng.random() != one.ink_rng.random()

    def test_blooms_off_leaves_no_bloom_generator(self, tmp_path):
        """A style with blooms off has no generator and no bloom argument."""
        job = tiny_job(tmp_path, tiny_style(wash={"blooms": False}))
        assert job.bloom_rng is None
        assert job.bloom(np.ones((4, 4), np.float32)) is None


class TestBloom:
    """The bloom argument of one wash."""

    def test_a_large_wash_gets_blooms_and_an_empty_one_none(self, tmp_path):
        """The count follows the wash's area, and a wash with no area has none."""
        job = tiny_job(tmp_path, tiny_style(wash={"blooms": True, "bloom_density": 1.0}))
        big = job.bloom(np.ones((120, 160), np.float32))
        assert big is not None
        assert big[0] is job.bloom_rng
        assert big[1] >= 1
        assert job.bloom(np.zeros((120, 160), np.float32)) is None


class TestTransparency:
    """What a pigment shows over black."""

    def test_a_pigment_without_its_own_takes_the_km_default(self, tmp_path):
        """A key the style does not list falls back to `km_transparency`."""
        job = tiny_job(tmp_path)
        assert job.transp("no such pigment") == job.style.paper.km_transparency


class TestPlateStack:
    """The accumulator of the arrays the phases share."""

    def test_blank_is_empty_and_of_the_plates_shape(self):
        """A blank stack has masks of the shape given, nothing set, and no files."""
        stack = PlateStack.blank((6, 9))
        assert stack.sea_cov.shape == stack.label.shape == stack.wood_mask.shape == (6, 9)
        assert not (stack.water.any() or stack.wood_mask.any() or stack.label.any())
        assert stack.trimmed == [] and stack.files == {} and stack.sizes == {}
