"""Tests for the golden diff measurement: tiny literal images in, fractions, deltas and boxes out."""

import io

import numpy as np
import pytest
from golden.diff_measure import (
    bounding_box,
    changed_mask,
    channel_delta,
    crop_box,
    decode,
    densest_window,
    extent,
    measure,
    padded,
)
from PIL import Image


def _flat(width: int, height: int, value: int = 100, bands: int = 3) -> np.ndarray:
    """Return a flat image of one grey value."""
    return np.full((height, width, bands), value, dtype=np.uint8)


def _encoded(pixels: np.ndarray, fmt: str = "PNG", **options: object) -> bytes:
    """Return pixels encoded in an image format."""
    buffer = io.BytesIO()
    mode = "RGBA" if pixels.shape[-1] == 4 else "RGB"
    Image.fromarray(pixels, mode).save(buffer, fmt, **options)
    return buffer.getvalue()


class TestMeasure:
    """`measure` counts the pixels past the channel bound and boxes the change."""

    def test_equal_pixels_have_no_measurement(self) -> None:
        """Two pixel-identical images are not a change."""
        assert measure(_flat(8, 6), _flat(8, 6)) is None

    def test_a_local_change_is_boxed_and_counted(self) -> None:
        """A 2 by 3 patch raised by 40 is 6 of 100 pixels, boxed exactly, and local."""
        after = _flat(10, 10)
        after[4:7, 2:4] += 40
        found = measure(_flat(10, 10), after)
        assert found is not None
        assert found.changed_fraction == 0.06
        assert found.max_delta == 40
        assert found.box == (2, 4, 4, 7)
        assert found.extent == "local"
        assert not found.shape_differs

    def test_changes_within_the_bound_are_not_counted_but_are_boxed(self) -> None:
        """Deltas of 2 count nothing past the bound; the box then spans every changed pixel."""
        after = _flat(10, 10)
        after[0, 0] += 2
        after[9, 9] += 1
        found = measure(_flat(10, 10), after)
        assert found is not None
        assert found.changed_fraction == 0.0
        assert found.max_delta == 2
        assert found.box == (0, 0, 10, 10)
        assert found.extent == "widespread"

    def test_the_box_follows_pixels_past_the_bound_when_there_are_any(self) -> None:
        """Sub-bound noise elsewhere does not widen the box round a real change."""
        after = _flat(20, 20)
        after[0, 0] += 1
        after[10, 12] += 30
        found = measure(_flat(20, 20), after)
        assert found is not None
        assert found.box == (12, 10, 13, 11)

    def test_images_of_different_shapes_differ_everywhere(self) -> None:
        """A resized image, or one that gained alpha, is fully changed, with no box or delta."""
        for after in (_flat(9, 6), _flat(8, 6, bands=4)):
            found = measure(_flat(8, 6), after)
            assert found is not None
            assert found.changed_fraction == 1.0
            assert found.max_delta is None
            assert found.box is None
            assert found.shape_differs

    def test_alpha_counts_as_a_channel(self) -> None:
        """A change to alpha alone is a change, as the parity gate counts it."""
        after = _flat(4, 4, bands=4)
        after[1, 1, 3] = 0
        found = measure(_flat(4, 4, bands=4), after)
        assert found is not None
        assert found.max_delta == 100


class TestBoxes:
    """The box helpers: bounding, padding, extent and the densest window."""

    def test_an_empty_mask_has_no_box(self) -> None:
        """No set pixel, no box."""
        assert bounding_box(np.zeros((5, 5), dtype=bool)) is None

    def test_padding_is_clipped_to_the_image(self) -> None:
        """A box near the corner grows by the pad but never past an edge."""
        assert padded((1, 2, 4, 5), 3, width=6, height=7) == (0, 0, 6, 7)
        assert padded((10, 10, 12, 12), 3, width=40, height=40) == (7, 7, 15, 15)

    @pytest.mark.parametrize(
        ("box", "want"),
        [((0, 0, 5, 5), "local"), ((0, 0, 5, 6), "widespread")],
        ids=["quarter", "over-a-quarter"],
    )
    def test_local_means_at_most_a_quarter_of_the_area(self, box, want) -> None:
        """A box of a quarter of a 10 by 10 image is local; one pixel row more is not."""
        assert extent(box, 10, 10) == want

    def test_the_densest_window_holds_the_most_set_pixels(self) -> None:
        """Of a lone pixel and a cluster, a small window lands on the cluster."""
        mask = np.zeros((30, 40), dtype=bool)
        mask[0, 0] = True
        mask[20:23, 30:34] = True
        assert densest_window(mask, 4, 3) == (30, 20, 34, 23)

    def test_the_densest_window_is_clipped_to_the_mask(self) -> None:
        """A window larger than the mask is the whole mask."""
        mask = np.ones((3, 5), dtype=bool)
        assert densest_window(mask, 50, 50) == (0, 0, 5, 3)

    def test_a_small_change_is_cropped_with_its_pad(self) -> None:
        """A change smaller than the limit crops to its box and the pad round it."""
        mask = np.zeros((100, 100), dtype=bool)
        mask[40:42, 50:55] = True
        assert crop_box(mask, pad=4, limit=60) == (46, 36, 59, 46)

    def test_a_large_change_is_cropped_to_its_densest_part(self) -> None:
        """A change wider than the limit crops to the limit, on its densest stretch."""
        mask = np.zeros((50, 200), dtype=bool)
        mask[10, 5:195] = True
        mask[12:20, 150:170] = True
        left, top, right, bottom = crop_box(mask, pad=2, limit=30) or (0, 0, 0, 0)
        assert (right - left, bottom - top) == (30, 14)
        assert left <= 150
        assert right >= 170

    def test_nothing_changed_has_no_crop(self) -> None:
        """An empty mask crops nothing."""
        assert crop_box(np.zeros((4, 4), dtype=bool)) is None

    def test_the_changed_mask_falls_back_to_any_change(self) -> None:
        """With no pixel past the bound, the mask is every changed pixel."""
        delta = np.array([[0, 1], [2, 0]], dtype=np.uint8)
        assert changed_mask(delta).tolist() == [[False, True], [True, False]]
        delta[0, 0] = 9
        assert changed_mask(delta).tolist() == [[True, False], [False, False]]


class TestDecode:
    """`decode` and `channel_delta` read encoded images as the parity gate does."""

    def test_alpha_is_kept_only_when_present(self) -> None:
        """An RGBA PNG decodes to four bands and an RGB one to three."""
        assert decode(_encoded(_flat(3, 2, bands=4))).shape == (2, 3, 4)
        assert decode(_encoded(_flat(3, 2))).shape == (2, 3, 3)

    def test_a_reencoded_image_decodes_to_equal_pixels(self) -> None:
        """Lossless WebP and PNG at another compression hold the same pixels, so no change."""
        pixels = _flat(6, 6)
        pixels[2, 3] = (10, 200, 30)
        webp = decode(_encoded(pixels, "WEBP", lossless=True))
        png = decode(_encoded(pixels, "PNG", compress_level=1))
        assert measure(webp, png) is None

    def test_the_delta_is_the_largest_channel_difference(self) -> None:
        """A pixel changed by 5 in red and 30 in blue, both ways, has delta 30."""
        before = _flat(2, 1)
        after = before.copy()
        after[0, 0] = (105, 100, 70)
        after[0, 1] = (95, 100, 130)
        assert channel_delta(before, after).tolist() == [[30, 30]]
