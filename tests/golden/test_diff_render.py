"""Tests for the golden review images: the heat map's colours, shrinking, and the review images' sizes."""

import numpy as np
from golden.diff_measure import measure
from golden.diff_render import (
    CELL,
    GUTTER,
    LABEL_HEIGHT,
    SCALE_TOP,
    block_max,
    crop_image,
    diff_image,
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

    def test_the_crop_image_shows_the_box_at_one_to_one(self) -> None:
        """The crop cells hold the box's pixels unshrunk: the after cell is the after crop."""
        before, after = _pair(64, 48)
        drawn = np.asarray(
            crop_image(before, after, channel_delta(before, after), (30, 22, 34, 26))
        )
        # Cells are as wide as the widest, the unshrunk 64-pixel locator; "after" is the second.
        left, top = GUTTER + 64 + GUTTER, GUTTER + LABEL_HEIGHT
        assert np.array_equal(drawn[top : top + 4, left : left + 4], after[22:26, 30:34])
