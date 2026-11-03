"""Tests for the golden review images: the heat map's colours, shrinking, and the review images' sizes."""

import numpy as np
import pytest
from golden.diff_measure import measure
from golden.diff_render import (
    CELL,
    CROP_MAX_FACTOR,
    CROP_TARGET,
    GUTTER,
    LABEL_HEIGHT,
    SCALE_TOP,
    block_max,
    crop_cells,
    crop_image,
    diff_image,
    enlarge,
    enlarge_factor,
    heat_colours,
    heat_map,
    shrink_factor,
    viewable,
)
from PIL import Image

from support.golden import channel_delta


def _pair(width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    """Return a flat image and a copy with one bright pixel near the middle."""
    before = np.full((height, width, 3), 120, dtype=np.uint8)
    after = before.copy()
    after[height // 2, width // 2] = 255
    return before, after


class TestHeatMap:
    """The heat map colours deltas on the dimmed later image."""

    def test_within_the_bound_is_blue_and_past_it_is_red(self) -> None:
        """Deltas 1 and 2 are the same blue; 3 turns red, and the scale top is yellow."""
        low, bound, past, top = heat_colours(np.array([1, 2, 3, SCALE_TOP]))
        assert low.tolist() == bound.tolist()
        assert bound[2] > bound[0]
        assert past[0] > 150 > past[2]
        assert top[0] == 255
        assert top[1] > 200

    def test_unchanged_pixels_show_the_later_image_dimmed(self) -> None:
        """Delta 0 shows grey from the later image, darker than it; a changed pixel is coloured."""
        later = Image.new("RGB", (2, 1), (200, 200, 200))
        delta = np.array([[0, 40]], dtype=np.uint8)
        pixels = np.asarray(heat_map(delta, later))
        grey, changed = pixels[0, 0], pixels[0, 1]
        assert len(set(grey.tolist())) == 1
        assert grey[0] < 200
        assert changed.tolist() == heat_colours(np.array([40]))[0].tolist()


class TestShrinking:
    """Shrinking keeps the review images small and a one-pixel change visible."""

    def test_the_factor_is_the_smallest_that_fits(self) -> None:
        """An image the cell holds is not shrunk; one a pixel over halves."""
        assert shrink_factor(CELL, 10) == 1
        assert shrink_factor(10, CELL + 1) == 2
        assert shrink_factor(3 * CELL, CELL) == 3

    def test_block_max_keeps_a_lone_pixel(self) -> None:
        """A single changed pixel survives a shrink by 4, at its block, with its full delta."""
        delta = np.zeros((9, 10), dtype=np.uint8)
        delta[5, 6] = 77
        shrunk = block_max(delta, 4)
        assert shrunk.shape == (3, 3)
        assert shrunk[1, 1] == 77
        assert int(shrunk.sum()) == 77

    def test_alpha_is_laid_over_white(self) -> None:
        """A transparent pixel views as white, an opaque one as itself."""
        pixels = np.array([[[10, 20, 30, 0], [10, 20, 30, 255]]], dtype=np.uint8)
        assert np.asarray(viewable(pixels)).tolist() == [[[255, 255, 255], [10, 20, 30]]]


class TestReviewImages:
    """The diff and crop images are two-by-two grids bounded for a PR body."""

    def test_a_large_images_diff_image_fits_two_cells_wide(self) -> None:
        """A 1500 by 1000 image's diff image is under three cells wide, its cells shrunk."""
        before, after = _pair(1500, 1000)
        found = measure(before, after)
        assert found is not None
        drawn = diff_image(before, after, found, channel_delta(before, after))
        assert drawn.width < 2 * CELL + 40
        assert drawn.height < 2 * CELL + 100

    def test_a_resized_image_gets_a_diff_image_without_a_heat_map(self) -> None:
        """Images of different sizes still get a diff image."""
        before, after = _pair(40, 30)[0], _pair(50, 30)[1]
        found = measure(before, after)
        assert found is not None
        assert diff_image(before, after, found, None).mode == "RGB"

    def test_the_crop_image_shows_the_box_enlarged(self) -> None:
        """The after cell holds the 4-pixel box enlarged 8 times, each pixel an 8-square block."""
        before, after = _pair(64, 48)
        drawn = np.asarray(
            crop_image(before, after, channel_delta(before, after), (30, 22, 34, 26))
        )
        # The first column is the 32-pixel enlarged crops; "after" heads the second column.
        left, top = GUTTER + 32 + GUTTER, GUTTER + LABEL_HEIGHT
        expected = after[22:26, 30:34].repeat(8, axis=0).repeat(8, axis=1)
        assert np.array_equal(drawn[top : top + 32, left : left + 32], expected)


class TestCropEnlarging:
    """A small crop is enlarged by a whole factor to read on a phone; a large one stays 1:1."""

    @pytest.mark.parametrize(
        ("size", "factor"),
        [
            ((50, 30), 8),
            ((4, 4), CROP_MAX_FACTOR),
            ((30, 120), 3),
            ((100, 60), 4),
            ((180, 90), 2),
            ((90, 40), 4),
            ((CROP_TARGET, 20), 1),
            ((CROP_TARGET, CROP_TARGET), 1),
            ((600, 1200), 1),
        ],
        ids=[
            "docs-master-crop",
            "tiny-capped",
            "tall",
            "rounds-up",
            "exact-half",
            "exact-quarter",
            "target-wide",
            "target-square",
            "large",
        ],
    )
    def test_the_factor_is_the_smallest_that_reaches_the_target(
        self, size: tuple[int, int], factor: int
    ) -> None:
        """The factor is the smallest whole one taking the longer side to the target, capped."""
        assert enlarge_factor(*size) == factor

    def test_enlarging_makes_each_pixel_a_square_block(self) -> None:
        """Nearest-neighbour by 5 turns every source pixel into an exact 5 by 5 block."""
        rng = np.random.default_rng(7)
        pixels = rng.integers(0, 256, size=(3, 4, 3), dtype=np.uint8)
        enlarged = np.asarray(enlarge(Image.fromarray(pixels, "RGB"), 5))
        assert enlarged.shape == (15, 20, 3)
        assert np.array_equal(enlarged, pixels.repeat(5, axis=0).repeat(5, axis=1))

    def test_a_small_crop_is_labelled_with_its_scale(self) -> None:
        """A 50 by 30 box of a 240-pixel image shows at 8:1, 400 by 240, the locator unscaled."""
        before, after = _pair(240, 180)
        cells = crop_cells(before, after, channel_delta(before, after), (100, 70, 150, 100))
        assert [label for label, _ in cells] == [
            "before, 8:1",
            "after, 8:1",
            "difference, 8:1",
            "where: 100,70 to 150,100",
        ]
        assert [img.size for _, img in cells] == [(400, 240)] * 3 + [(240, 180)]

    def test_a_large_crop_stays_at_one_to_one(self) -> None:
        """A target-sized box of an 1800-pixel image is not enlarged and says 1:1."""
        before, after = _pair(1800, 1200)
        box = (700, 400, 700 + CROP_TARGET, 400 + CROP_TARGET)
        cells = crop_cells(before, after, channel_delta(before, after), box)
        assert [label for label, _ in cells][:3] == ["before, 1:1", "after, 1:1", "difference, 1:1"]
        assert cells[1][1].size == (CROP_TARGET, CROP_TARGET)

    @pytest.mark.parametrize(
        "box",
        [(100, 70, 146, 116), (0, 0, 4, 4), (10, 5, 189, 100), (0, 0, 240, 180)],
        ids=["just-under-a-factor", "tiny", "just-under-half-target", "whole-image"],
    )
    def test_the_crop_image_stays_bounded(self, box: tuple[int, int, int, int]) -> None:
        """Every crop image is at most two enlarged crops wide and tall, with no slack round them."""
        before, after = _pair(240, 180)
        cells = crop_cells(before, after, channel_delta(before, after), box)
        drawn = crop_image(before, after, channel_delta(before, after), box)
        crop_w, crop_h = cells[0][1].size
        assert max(crop_w, crop_h) < 2 * CROP_TARGET
        assert drawn.width == 3 * GUTTER + crop_w + max(crop_w, 240)
        assert drawn.height == 3 * GUTTER + 2 * LABEL_HEIGHT + crop_h + max(crop_h, 180)
