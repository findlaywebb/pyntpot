"""Measure how two images differ: how much, how far, and where.

The measuring half of the golden diff tooling (`diff_images.py` is the command). Key
types: `Box`, a pixel rectangle `(left, top, right, bottom)` with exclusive right and
bottom edges, as Pillow's `crop` takes it; `Measurement`, one changed image's numbers.

A pixel's delta is its largest absolute channel difference, over RGB, or RGBA when the image
has alpha, as the parity gate measures it (`support.golden.differing_fraction`). The changed
fraction counts the pixels whose delta exceeds the channel bound (`MAX_CHANNEL_DELTA`, 2),
so it is the number `test_parity.py` holds to `MAX_DIFFERING_FRACTION`. The box spans the
pixels past the channel bound, or every changed pixel when none is past it. An image is
`local` when its box covers at most `LOCAL_BOX_AREA` of the image, else `widespread`; one
stray pixel far from the rest makes an image widespread, which is what a reviewer should see.

Invariants: two decoded images that are pixel-identical have no measurement (`measure`
returns `None`), whatever their bytes; two of different shapes or band counts differ
everywhere, as in the parity gate. It does not draw anything (`diff_render.py` does) and does
not decide pass or fail: the gate is `test_parity.py`.
"""

import io
from dataclasses import dataclass
from typing import Literal

import numpy as np
from golden.test_parity import MAX_CHANNEL_DELTA
from PIL import Image

#: A pixel rectangle: left, top, right and bottom, the right and bottom edges exclusive.
Box = tuple[int, int, int, int]

#: Where a change lies: within a small box, or across the image.
Extent = Literal["local", "widespread"]

#: The largest share of the image area a `local` change's box may cover.
LOCAL_BOX_AREA = 0.25

#: The margin, in pixels, kept round the changed pixels in a crop.
CROP_PAD = 16

#: The largest side, in pixels, of a 1:1 crop; a larger change is cropped to its densest part.
CROP_LIMIT = 360


@dataclass(frozen=True)
class Measurement:
    """How one image differs from its earlier version.

    Attributes:
        width: The later image's width in pixels.
        height: The later image's height in pixels.
        changed_fraction: The share of pixels whose delta exceeds the channel bound; 1.0
            when the shapes differ.
        max_delta: The largest channel difference, 0 to 255; `None` when the shapes differ.
        box: The changed pixels' bounding box; `None` when the shapes differ.
        extent: `local` when `box` covers at most `LOCAL_BOX_AREA` of the image.
    """

    width: int
    height: int
    changed_fraction: float
    max_delta: int | None
    box: Box | None
    extent: Extent

    @property
    def shape_differs(self) -> bool:
        """Whether the two images differ in size or band count, so no pixel compares."""
        return self.max_delta is None


def decode(data: bytes) -> np.ndarray:
    """Decode an encoded image to an `(height, width, bands)` array, keeping alpha when it has any."""
    with Image.open(io.BytesIO(data)) as img:
        return np.asarray(img.convert("RGBA" if "A" in img.getbands() else "RGB"))


def channel_delta(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    """Return each pixel's largest absolute channel difference, as an `(height, width)` uint8 array."""
    wide = np.abs(before.astype(np.int16) - after.astype(np.int16))
    return wide.max(axis=-1).astype(np.uint8)


def bounding_box(mask: np.ndarray) -> Box | None:
    """Return the box round a mask's set pixels, or `None` when none is set."""
    rows = np.flatnonzero(mask.any(axis=1))
    cols = np.flatnonzero(mask.any(axis=0))
    if rows.size == 0:
        return None
    return int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1


def padded(box: Box, pad: int, width: int, height: int) -> Box:
    """Return `box` grown by `pad` pixels on every side, clipped to a `width` by `height` image."""
    left, top, right, bottom = box
    return max(0, left - pad), max(0, top - pad), min(width, right + pad), min(height, bottom + pad)


def densest_window(mask: np.ndarray, window_width: int, window_height: int) -> Box:
    """Return the `window_width` by `window_height` box holding the most set pixels of `mask`.

    The window is clipped to the mask's size. Of equally dense windows, the topmost, then the
    leftmost, wins. It reads a summed-area table, so it costs one pass over the mask.
    """
    height, width = int(mask.shape[0]), int(mask.shape[1])
    w, h = min(window_width, width), min(window_height, height)
    table = np.zeros((height + 1, width + 1), dtype=np.int64)
    table[1:, 1:] = mask.astype(np.int64).cumsum(axis=0).cumsum(axis=1)
    sums = table[h:, w:] - table[:-h, w:] - table[h:, :-w] + table[:-h, :-w]
    top, left = np.unravel_index(int(np.argmax(sums)), sums.shape)
    return int(left), int(top), int(left) + w, int(top) + h


def crop_box(mask: np.ndarray, pad: int = CROP_PAD, limit: int = CROP_LIMIT) -> Box | None:
    """Return the box a 1:1 crop of the most-changed region shows, or `None` when nothing changed.

    The crop is the changed pixels' box grown by `pad`. Where that is longer than `limit` on
    a side, the crop is the `limit`-long window, on that side, holding the most changed pixels.
    """
    box = bounding_box(mask)
    if box is None:
        return None
    height, width = mask.shape
    left, top, right, bottom = padded(box, pad, width, height)
    if right - left <= limit and bottom - top <= limit:
        return left, top, right, bottom
    return densest_window(mask, min(right - left, limit), min(bottom - top, limit))


def changed_mask(delta: np.ndarray, channel_bound: int = MAX_CHANNEL_DELTA) -> np.ndarray:
    """Return the pixels the box and the crop follow: past `channel_bound`, else any change."""
    past = delta > channel_bound
    return past if past.any() else delta > 0


def extent(box: Box, width: int, height: int) -> Extent:
    """Return `local` when `box` covers at most `LOCAL_BOX_AREA` of a `width` by `height` image."""
    left, top, right, bottom = box
    share = (right - left) * (bottom - top) / (width * height)
    return "local" if share <= LOCAL_BOX_AREA else "widespread"


def measure(
    before: np.ndarray, after: np.ndarray, channel_bound: int = MAX_CHANNEL_DELTA
) -> Measurement | None:
    """Measure how `after` differs from `before`; `None` when they are pixel-identical.

    Args:
        before: The earlier image, as `decode` returns it.
        after: The later image, as `decode` returns it.
        channel_bound: The channel difference a pixel must exceed to count as changed.

    Returns:
        The measurement, or `None` when every pixel is equal.
    """
    height, width = after.shape[:2]
    if before.shape != after.shape:
        return Measurement(width, height, 1.0, None, None, "widespread")
    delta = channel_delta(before, after)
    max_delta = int(delta.max())
    if max_delta == 0:
        return None
    # Some pixel changed, so the mask is not empty and the box is set.
    left, top, right, bottom = bounding_box(changed_mask(delta, channel_bound)) or (0, 0, 0, 0)
    box = (left, top, right, bottom)
    return Measurement(
        width=width,
        height=height,
        changed_fraction=float((delta > channel_bound).mean()),
        max_delta=max_delta,
        box=box,
        extent=extent(box, width, height),
    )
