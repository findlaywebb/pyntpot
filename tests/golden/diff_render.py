"""Draw the review images of a changed image: the diff image and the 1:1 crop image.

The drawing half of the golden diff tooling (`diff_images.py` is the command,
`diff_measure.py` measures). Both review images are a two-by-two grid of labelled cells
on a light background, so they read the same in GitHub's light and dark themes and fit a
phone-width PR body:

- `diff_image`: the earlier image, the later one, the heat map of the difference and a key
  (the colour scale and the measurement), each cell shrunk by one whole factor to fit
  `CELL` pixels.
- `crop_image`: the same three at 1:1 over the crop box, and a locator, the whole later
  image shrunk with the crop box outlined.

The heat map colours each pixel by its delta (`diff_measure.channel_delta`): blue at or
under the channel bound, then red through orange to yellow at `SCALE_TOP`, white at 255. An
unchanged pixel shows the later image dimmed to grey, so the change reads in place. Shrinking
the heat map keeps each block's largest delta, so a one-pixel change stays visible at any
scale; the earlier and later images shrink by box averaging.

It does not measure (the numbers come in a `Measurement`), read or write files.
"""

import math

import numpy as np
from golden.diff_measure import Box, Measurement
from golden.test_parity import MAX_CHANNEL_DELTA
from PIL import Image, ImageDraw, ImageFont

#: The side, in pixels, a shrunk diff image cell fits within.
CELL = 480

#: The delta the heat map's colour scale saturates to yellow at.
SCALE_TOP = 32

#: Pixels between cells and round the review image.
GUTTER = 8

#: The height of a cell's label strip.
LABEL_HEIGHT = 22

_BACKGROUND = (246, 246, 243)
_INK = (34, 34, 34)
_OUTLINE = (230, 0, 120)
_FONT = ImageFont.load_default(size=14)

# The heat map's colour stops, by delta: blue to the bound, then red, orange, yellow, white.
_STOP_DELTAS = (1, MAX_CHANNEL_DELTA, MAX_CHANNEL_DELTA + 1, 12, SCALE_TOP, 255)
_STOP_COLOURS = (
    (70, 110, 210),
    (70, 110, 210),
    (205, 30, 30),
    (240, 125, 0),
    (255, 230, 50),
    (255, 255, 255),
)


def heat_colours(delta: np.ndarray) -> np.ndarray:
    """Return the scale's colour for each delta, as an `(..., 3)` uint8 array; delta 0 is blue too."""
    channels = [
        np.interp(delta, _STOP_DELTAS, [colour[band] for colour in _STOP_COLOURS])
        for band in range(3)
    ]
    return np.stack(channels, axis=-1).round().astype(np.uint8)


def heat_map(delta: np.ndarray, later: Image.Image) -> Image.Image:
    """Return the heat map of `delta` over `later` dimmed to grey, both the same size."""
    grey = np.asarray(later.convert("L"), dtype=np.float32)
    dimmed = (40 + grey * 0.3).astype(np.uint8)
    rgb = np.repeat(dimmed[..., None], 3, axis=-1)
    changed = delta > 0
    rgb[changed] = heat_colours(delta[changed])
    return Image.fromarray(rgb, "RGB")


def shrink_factor(width: int, height: int, cell: int = CELL) -> int:
    """Return the smallest whole factor that shrinks a `width` by `height` image to fit `cell`."""
    return max(1, math.ceil(max(width, height) / cell))


def block_max(delta: np.ndarray, factor: int) -> np.ndarray:
    """Shrink `delta` by `factor`, keeping each block's largest value; partial edge blocks count."""
    if factor == 1:
        return delta
    height, width = delta.shape
    rows, cols = math.ceil(height / factor), math.ceil(width / factor)
    padded = np.zeros((rows * factor, cols * factor), dtype=delta.dtype)
    padded[:height, :width] = delta
    return padded.reshape(rows, factor, cols, factor).max(axis=(1, 3))


def viewable(pixels: np.ndarray) -> Image.Image:
    """Return decoded pixels as an RGB image, any alpha laid over white."""
    if pixels.shape[-1] == 3:
        return Image.fromarray(pixels, "RGB")
    white = Image.new("RGB", (pixels.shape[1], pixels.shape[0]), (255, 255, 255))
    white.paste(Image.fromarray(pixels, "RGBA"), mask=Image.fromarray(pixels[..., 3], "L"))
    return white


def _shrunk(img: Image.Image, factor: int) -> Image.Image:
    """Return `img` shrunk by `factor` by box averaging, its size rounded up like `block_max`."""
    return img if factor == 1 else img.reduce(factor)


def _grid(cells: list[tuple[str, Image.Image]]) -> Image.Image:
    """Lay labelled cells out two to a row on the background, each cell as large as the largest."""
    cell_w = max(img.width for _, img in cells)
    cell_h = max(img.height for _, img in cells) + LABEL_HEIGHT
    rows = math.ceil(len(cells) / 2)
    grid = Image.new(
        "RGB", (GUTTER + 2 * (cell_w + GUTTER), GUTTER + rows * (cell_h + GUTTER)), _BACKGROUND
    )
    draw = ImageDraw.Draw(grid)
    for index, (label, img) in enumerate(cells):
        x = GUTTER + (index % 2) * (cell_w + GUTTER)
        y = GUTTER + (index // 2) * (cell_h + GUTTER)
        draw.text((x, y + 3), label, fill=_INK, font=_FONT)
        grid.paste(img, (x, y + LABEL_HEIGHT))
    return grid


def _scale_bar(width: int) -> Image.Image:
    """Return the heat map's colour scale from delta 1 to `SCALE_TOP`, labelled under its ends."""
    bar = Image.new("RGB", (width, 40), _BACKGROUND)
    deltas = np.linspace(1, SCALE_TOP, width)
    strip = np.repeat(heat_colours(deltas)[None, ...], 14, axis=0)
    bar.paste(Image.fromarray(strip, "RGB"), (0, 0))
    draw = ImageDraw.Draw(bar)
    bound_x = round((MAX_CHANNEL_DELTA - 1) / (SCALE_TOP - 1) * (width - 1))
    draw.line([(bound_x, 0), (bound_x, 18)], fill=_INK)
    draw.text((0, 20), "1", fill=_INK, font=_FONT)
    draw.text((max(bound_x - 4, 16), 20), f"{MAX_CHANNEL_DELTA} bound", fill=_INK, font=_FONT)
    draw.text((width - 34, 20), f"{SCALE_TOP}+", fill=_INK, font=_FONT)
    return bar


def key_panel(lines: list[str], width: int, height: int) -> Image.Image:
    """Return the key: the colour scale, a note on grey, then `lines`, on a `width` by `height` panel."""
    panel = Image.new("RGB", (width, height), _BACKGROUND)
    panel.paste(_scale_bar(min(width - 8, 300)), (4, 4))
    draw = ImageDraw.Draw(panel)
    text = [
        "colour: delta, the largest channel difference",
        "grey: unchanged, the after image dimmed",
        "",
        *lines,
    ]
    for row, line in enumerate(text):
        draw.text((4, 50 + row * 18), line, fill=_INK, font=_FONT)
    return panel


def measurement_lines(measurement: Measurement, factor: int) -> list[str]:
    """Return the key's lines for a measurement shown shrunk by `factor`."""
    if measurement.shape_differs:
        return ["the sizes or bands differ:", "no pixel compares"]
    left, top, right, bottom = measurement.box or (0, 0, 0, 0)
    return [
        f"changed (delta>{MAX_CHANNEL_DELTA}): {measurement.changed_fraction:.6f}",
        f"max delta: {measurement.max_delta}",
        f"box: {left},{top} to {right},{bottom}",
        f"extent: {measurement.extent}",
        f"shown at 1:{factor}",
    ]


def diff_image(
    before: np.ndarray, after: np.ndarray, measurement: Measurement, delta: np.ndarray | None
) -> Image.Image:
    """Return the diff image: before, after, the heat map and the key, shrunk to fit `CELL`.

    Args:
        before: The earlier image's decoded pixels.
        after: The later image's decoded pixels.
        measurement: How they differ.
        delta: The per-pixel delta, or `None` when the shapes differ (the heat map cell then
            says so).

    Returns:
        The review image, an RGB image.
    """
    factor = shrink_factor(*after.shape[1::-1])
    later = _shrunk(viewable(after), factor)
    earlier = _shrunk(viewable(before), shrink_factor(*before.shape[1::-1]))
    if delta is None:
        heat = Image.new("RGB", later.size, (60, 60, 60))
    else:
        heat = heat_map(block_max(delta, factor), later)
    key = key_panel(
        measurement_lines(measurement, factor), max(later.width, 320), max(later.height, 220)
    )
    return _grid([("before", earlier), ("after", later), ("difference", heat), ("key", key)])


def crop_image(before: np.ndarray, after: np.ndarray, delta: np.ndarray, box: Box) -> Image.Image:
    """Return the crop image: before, after and the heat map at 1:1 over `box`, and a locator."""
    later = viewable(after)
    crop_heat = heat_map(delta[box[1] : box[3], box[0] : box[2]], later.crop(box))
    factor = shrink_factor(later.width, later.height, CELL // 2)
    locator = _shrunk(later, factor).copy()  # drawn on, so never `later` itself
    draw = ImageDraw.Draw(locator)
    shrunk_box = [
        box[0] // factor,
        box[1] // factor,
        (box[2] - 1) // factor,
        (box[3] - 1) // factor,
    ]
    draw.rectangle(shrunk_box, outline=_OUTLINE, width=2)
    left, top, right, bottom = box
    return _grid(
        [
            ("before, 1:1", viewable(before).crop(box)),
            ("after, 1:1", later.crop(box)),
            ("difference, 1:1", crop_heat),
            (f"where: {left},{top} to {right},{bottom}", locator),
        ]
    )
