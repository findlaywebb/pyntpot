"""The painting job and the plate stack: what they hold, derive and share."""

import numpy as np
import pytest

from pyntpot.ink.bloom import Blooms
from pyntpot.ink.washing import Flow
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
        """Two jobs over one style draw the same first numbers from the shared generator."""
        style = tiny_style(wash={"blooms": True})
        one, two = tiny_job(tmp_path, style), tiny_job(tmp_path, style)
        assert one.dither_rng.random() == two.dither_rng.random()
        assert one.pen_seed == style.brush.ink_seed + 1

    def test_blooms_off_leaves_no_bloom_argument(self, tmp_path):
        """A style with blooms off gives no wash a bloom argument."""
        job = tiny_job(tmp_path, tiny_style(wash={"blooms": False}))
        assert job.bloom(np.ones((4, 4), np.float32), "wood") is None


class TestFlow:
    """The flow-rim option every wash is laid with."""

    def test_the_flow_option_carries_the_wash_styles_rim_settings(self, tmp_path):
        """With the flow rim on, `flow` holds the style's three rim numbers; off, it is `None`."""
        rim = {"flow_rim_exp": 0.25, "flow_rim_ref_frac": 0.05, "flow_rim_frac": 0.5}
        on = tiny_job(tmp_path, tiny_style(wash={"flow_rim": True, **rim}))
        off = tiny_job(tmp_path, tiny_style(wash={"flow_rim": False, **rim}))
        assert on.flow == Flow(exp=0.25, ref_frac=0.05, frac=0.5)
        assert off.flow is None


class TestBloom:
    """The bloom argument of one wash."""

    def test_a_large_wash_gets_blooms_and_an_empty_one_none(self, tmp_path):
        """The count follows the wash's area, and a wash with no area has none."""
        job = tiny_job(tmp_path, tiny_style(wash={"blooms": True, "bloom_density": 1.0}))
        big = job.bloom(np.ones((120, 160), np.float32), "wood")
        assert big is not None
        assert big.count >= 1
        assert job.bloom(np.zeros((120, 160), np.float32), "wood") is None

    def test_each_wash_is_seeded_by_its_name_alone(self, tmp_path):
        """Two washes of one name share a seed on any job; two names never do."""
        style = tiny_style(wash={"blooms": True, "bloom_density": 1.0})
        cov = np.ones((120, 160), np.float32)
        one, two = tiny_job(tmp_path, style), tiny_job(tmp_path, style)
        wood, lake = one.bloom(cov, "wood"), one.bloom(cov, "lake")
        again = two.bloom(cov[:60], "wood")
        assert wood is not None and lake is not None and again is not None
        assert wood.seed == again.seed
        assert wood.seed != lake.seed

    def test_the_bloom_argument_carries_the_styles_settings_and_a_keyed_seed(self, tmp_path):
        """The record holds the pinned seed, the count for its area and the style's settings."""
        moved = {"bloom_strength": 0.5, "bloom_radius_frac": 0.2, "bloom_warp": 0.3}
        job = tiny_job(tmp_path, tiny_style(wash={"blooms": True, **moved}))
        got = job.bloom(np.ones((600, 600), np.float32), "wood")
        assert got == Blooms(
            seed=4362746225535461558, count=2, radius_frac=0.2, lift=0.225, warp=0.3
        )

    def test_another_bloom_seed_gives_another_wash_seed(self, tmp_path):
        """The wash's seed is keyed from the style's bloom seed as well as its name."""
        cov = np.ones((120, 160), np.float32)
        one = tiny_job(tmp_path, tiny_style(wash={"blooms": True, "bloom_seed": 57}))
        two = tiny_job(tmp_path, tiny_style(wash={"blooms": True, "bloom_seed": 58}))
        first, second = one.bloom(cov, "wood"), two.bloom(cov, "wood")
        assert first is not None and second is not None
        assert first.seed != second.seed

    @pytest.mark.parametrize(
        ("wash", "cov"),
        [
            ({"blooms": False}, np.ones((600, 600), np.float32)),
            ({"blooms": True, "bloom_density": 0.0}, np.ones((600, 600), np.float32)),
            ({"blooms": True}, np.full((600, 600), 0.5, np.float32)),
        ],
        ids=["blooms-off", "no-density", "cover-at-the-inside-line"],
    )
    def test_no_bloom_argument_when_off_or_nothing_inside(self, tmp_path, wash, cov):
        """Blooms off, a density of 0, or cover no higher than 0.5 gives no bloom argument."""
        assert tiny_job(tmp_path, tiny_style(wash=wash)).bloom(cov, "wood") is None

    @pytest.mark.parametrize(
        ("inside", "density", "count"),
        [(400, 1.0, None), (401, 1.0, 1), (360_000, 10.0, 5)],
        ids=["at-the-floor", "past-the-floor", "past-the-most"],
    )
    def test_the_count_is_floored_past_400_pixels_and_capped_at_the_most(
        self, tmp_path, inside, density, count
    ):
        """At 400 inside pixels a wash may round to none; past it, one; never past `bloom_max`."""
        cov = np.zeros(360_000, np.float32)
        cov[:inside] = 1.0
        job = tiny_job(tmp_path, tiny_style(wash={"blooms": True, "bloom_density": density}))
        got = job.bloom(cov.reshape(600, 600), "wood")
        assert (got.count if got is not None else None) == count


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
