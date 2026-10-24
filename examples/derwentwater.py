"""Painting with Python: Derwentwater, five hill washes, a lake and a name written by hand.

The picture is built the way a painter builds a view, far to near. Each ridge is a line
drawn in numpy from a few seeded sines; the ground below it, down to the shore, is a
coverage mask, and `wash` turns the mask into pigment density. The far fells are one pale
blue-grey wash; each nearer ridge is another wash laid over the last, so the multiply
compositing darkens the ground the more washes it sits under, and the colour warms from
`wetland` through `rock` and `relief` to `wood`. The density of each hill is faded toward
its foot, where mist lies, and the nearest hills granulate: their density follows the
paper's own `Sheet.gran` field.

The lake is the `water` pigment under a streaked, pale density. Its reflection is not a
second picture: it is the hills' own density turned over about the shore, shifted a few
pixels sideways row by row so it ripples, softened and laid at a fraction of the strength.
A wooded island and two tree-lined banks are washes of `wood`.

The hand then writes "Derwentwater" across the bottom with the nib, as the lettering rung
did, and the nib plate is laid over the painting by its alpha. Every wash stops short of
the edge, so the sheet keeps a margin of bare paper.

Public names: nothing new. From `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`,
`paper_plate`, `wash`, `PIGMENTS`, `rgb`, `composite`, `BrushStyle` and `save_image`;
from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`, `Setting`, `Mark`,
`NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`.

It writes two files into the directory it is given: the nib plate,
`derwentwater-plate.webp`, and the finished image, `derwentwater.png`. Every seed is
fixed, so one run writes the same files. `size` is the picture's width in pixels; its
height is two thirds of that.

Run it with:

    uv run python examples/derwentwater.py out/
"""

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot.ink import (
    PIGMENTS,
    BrushStyle,
    Canvas,
    PaperStyle,
    PigmentLayer,
    Sheet,
    composite,
    paper_plate,
    rgb,
    save_image,
    wash,
)
from pyntpot.letters import (
    FaceStyle,
    Hand,
    HandStyle,
    Mark,
    NibGroups,
    NibStyle,
    NibSurface,
    Setting,
    nib_plate,
)

logger = logging.getLogger(__name__)

#: The seed of the paper, the ridges, the ripples and the nib.
SEED = 21
STEM = "derwentwater"
NAME = "Derwentwater"
#: Each hill, far to near: the pigment, where its ridge runs (as a share of the height),
#: how far the ridge swings, the density at its crest and how granulating it is.
HILLS: tuple[tuple[str, float, float, float, float], ...] = (
    ("wetland", 0.30, 0.075, 0.80, 0.0),
    ("rock", 0.38, 0.065, 0.80, 0.3),
    ("relief", 0.45, 0.050, 0.85, 0.7),
)
#: The two banks that frame the lake: the pigment, which side, how far it reaches across the
#: picture and how high it stands above the shore (shares of the width and the height).
BANKS: tuple[tuple[str, bool, float, float], ...] = (
    ("scrub", True, 0.62, 0.26),
    ("heath", False, 0.40, 0.17),
)
#: Where the lake's shore runs and where its water ends, as shares of the height.
SHORE, LAKE_END = 0.60, 0.835
#: The margin of bare paper, as a share of the width.
MARGIN = 0.055


def _ridge(rng: np.random.Generator, width: int, centre: float, swing: float) -> np.ndarray:
    """Return a ridge line, in shares of the height, per column: broad fells and fine crags."""
    x = np.linspace(0.0, 1.0, width)
    y = np.zeros(width)
    for k in range(1, 7):
        y += rng.uniform(0.5, 1.0) / k**0.8 * np.sin(2 * np.pi * (k * 0.6 * x + rng.random()))
    crags = np.zeros(width)
    for k in range(9, 24):
        crags += rng.uniform(0.3, 1.0) / k * np.sin(2 * np.pi * (k * x + rng.random()))
    return centre + swing * (y / 1.8 + 0.35 * crags)


def _bank(width: int, h: int, *, left: bool, reach: float, rise: float) -> np.ndarray:
    """Return a ridge, in pixels, that falls from `rise` of the height above the shore to the shore."""
    x = np.linspace(0.0, 1.0, width)
    t = np.clip(1.0 - (x if left else 1.0 - x) / reach, 0.0, 1.0)
    return (SHORE - rise * t**1.6) * h


def _soften(a: np.ndarray, width: int) -> np.ndarray:
    """Return `a` smoothed along its columns by a box of `width` pixels."""
    kernel = np.ones(width, np.float32) / width
    return np.apply_along_axis(lambda col: np.convolve(col, kernel, mode="same"), 0, a)


def _streaks(rng: np.random.Generator, h: int, w: int, across: int) -> np.ndarray:
    """Return noise in 0 to 1 stretched along x: `across` cells wide, a cell per few rows."""
    cells = rng.random((h // 3 + 2, across)).astype(np.float32)
    img = Image.fromarray(cells, "F").resize((w, h), Image.Resampling.BICUBIC)
    return np.clip(np.asarray(img), 0.0, 1.0)


def _blobs(
    rng: np.random.Generator, grid: tuple[np.ndarray, np.ndarray], spec: tuple[float, ...]
) -> np.ndarray:
    """Return a row of tree crowns as a mask: `spec` is x0, x1, base y, radius, count (pixels)."""
    yy, xx = grid
    x0, x1, base, radius, count = spec
    mask = np.zeros(yy.shape, bool)
    for cx in np.linspace(x0, x1, int(count)):
        r = radius * rng.uniform(0.7, 1.25)
        cy = base - r * rng.uniform(0.5, 1.3)
        mask |= (xx - cx) ** 2 / 0.8 + (yy - cy) ** 2 <= r**2
    return mask


def _reflected(dens: np.ndarray, shore: int, rows: slice, ripple: np.ndarray) -> np.ndarray:
    """Return `dens` turned over about the shore, rippled sideways, softened, over `rows` only."""
    h, w = dens.shape
    y = np.arange(rows.start, rows.stop)
    src = np.clip(2 * shore - y, 0, h - 1)
    out = np.zeros_like(dens)
    cols = np.arange(w)
    shift = np.round(ripple[y - rows.start]).astype(int)
    out[rows] = dens[src[:, None], np.clip(cols[None, :] + shift[:, None], 0, w - 1)]
    return _soften(out, 5)


@dataclass(frozen=True)
class _Scene:
    """What every part of the picture is painted on: the sheet, the pixel grid and the geometry."""

    sheet: Sheet
    yy: np.ndarray
    xx: np.ndarray
    inside: np.ndarray
    shore: int
    lake_end: int

    @property
    def h(self) -> int:
        """Return the picture's height in pixels."""
        return int(self.yy.shape[0])

    @property
    def w(self) -> int:
        """Return the picture's width in pixels."""
        return int(self.yy.shape[1])


Layer = tuple[np.ndarray, np.ndarray]


def _hills(scene: _Scene, rng: np.random.Generator) -> tuple[list[Layer], np.ndarray]:
    """Return the hills' washes, far to near, and the farthest ridge, in pixels."""
    h, w, yy, shore = scene.h, scene.w, scene.yy, scene.shore
    ridges = [_ridge(rng, w, c, sw) * h for _, c, sw, _, _ in HILLS]
    ridges += [_bank(w, h, left=left, reach=reach, rise=rise) for _, left, reach, rise in BANKS]
    ridges[-2] += _ridge(rng, w, 0.0, 0.03) * h
    ridges[-1] += _ridge(rng, w, 0.0, 0.025) * h
    looks = [(k, c, g) for k, _, _, c, g in HILLS] + [(k, 0.95, 1.0) for k, *_ in BANKS]
    layers: list[Layer] = []
    for ridge, (key, crest, gran) in zip(ridges, looks, strict=True):
        cover = ((yy >= ridge[None, :]) & (yy < shore + 2) & scene.inside).astype(np.float32)
        dens = wash(cover, scene.sheet, crest, 0.25)
        mist = 0.62 + 0.38 * np.exp(-np.clip(yy - ridge[None, :], 0, None) / (0.14 * h))
        grain = np.clip((scene.sheet.gran - 0.5) * 2.4, -0.7, 1.0)
        dens = np.clip(dens * mist * (1.0 + gran * 0.5 * grain), 0, 1).astype(np.float32)
        layers.append((dens, rgb(PIGMENTS[key])))
    return layers, ridges[0]


def _sky(scene: _Scene, far: np.ndarray) -> Layer:
    """Return a pale sky wash over the farthest ridge, graded to nothing at the top."""
    top, yy = 0.07 * scene.h, scene.yy
    cover = ((yy < far[None, :] + 4) & (yy > top) & scene.inside).astype(np.float32)
    grade = np.clip((yy - top) / (far[None, :] - top + 1), 0, 1) ** 1.4
    return (wash(cover, scene.sheet, 0.5, 0.1) * grade).astype(np.float32), rgb(PIGMENTS["sand"])


def _trees(scene: _Scene, rng: np.random.Generator) -> Layer:
    """Return the wooded island and a bank of crowns at each side of the shore."""
    w, h, shore, margin = scene.w, scene.h, scene.shore, MARGIN * scene.w
    grid = (scene.yy, scene.xx)
    island = _blobs(rng, grid, (0.50 * w, 0.65 * w, shore + 0.075 * h, 0.032 * h, 10))
    left = _blobs(rng, grid, (margin, 0.30 * w, shore + 0.02 * h, 0.03 * h, 11))
    right = _blobs(rng, grid, (0.78 * w, w - margin, shore + 0.02 * h, 0.03 * h, 9))
    cover = ((island | left | right) & scene.inside).astype(np.float32)
    dens = wash(cover, scene.sheet, 0.95, 0.35)
    dens = dens * (1.0 + 0.6 * np.clip((scene.sheet.gran - 0.5) * 2.4, -0.7, 1.0))
    return np.clip(dens, 0, 1).astype(np.float32), rgb(PIGMENTS["wood"])


def _lake(scene: _Scene, rng: np.random.Generator, sources: list[Layer]) -> list[Layer]:
    """Return the water's wash and, over it, the reflection of each of `sources`."""
    h, w, yy, shore, lake_end = scene.h, scene.w, scene.yy, scene.shore, scene.lake_end
    wobble = 0.006 * h * np.sin(np.linspace(0, 9, w))
    lake = ((yy >= shore) & (yy < lake_end + wobble[None, :]) & scene.inside).astype(np.float32)
    streak = _streaks(rng, h, w, max(w // 90, 3))
    depth = np.clip((yy - shore) / (lake_end - shore), 0, 1)
    water = wash(lake, scene.sheet, 0.66, 0.20) * (0.8 + 0.4 * streak) * (1.0 - 0.4 * depth**2)
    layers: list[Layer] = [(np.clip(water, 0, 1).astype(np.float32), rgb(PIGMENTS["water"]))]

    ripple = 2.2 * (w / 720) * np.sin(np.arange(h) * 0.9) + rng.normal(0, 0.6, h)
    fade = (1.0 - depth) ** 0.7 * lake * (0.5 + 0.8 * (1.0 - streak))
    for dens, pigment in sources:
        mirror = _reflected(dens, shore, slice(shore, lake_end), ripple) * fade * 0.85
        layers.append((np.clip(mirror, 0, 1).astype(np.float32), pigment))
    return layers


def _name(canvas: Canvas, gran_px: float, plate: Path) -> np.ndarray:
    """Write the name across the bottom with the nib and return the plate as RGBA floats.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    w, h = canvas.w, canvas.h
    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    setting = Setting(NAME, 0.072 * w, anchor=(w / 2, 0.935 * h), align="middle", ink="#4a4a58")
    marks: list[Mark] = hand.write(setting, hand.generator(SEED))
    surface = NibSurface(canvas, 1.0, np.zeros((h, w), np.float32), gran_px)
    groups = NibGroups(NibStyle(), face, hand_style, BrushStyle(), PaperStyle())
    plate_path = nib_plate(marks, surface, groups, plate)
    if plate_path is None:
        raise RuntimeError("the hand wrote no marks")
    return np.asarray(Image.open(plate_path).convert("RGBA"), np.float32) / 255


def main(out_dir: Path, size: int = 720) -> Path:
    """Paint Derwentwater, write `derwentwater.png` and its nib plate into `out_dir`.

    Args:
        out_dir: The directory the nib plate and the finished image are written into.
        size: The picture's width in pixels; its height is two thirds of that.

    Returns:
        The path of the finished image, `derwentwater.png`.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = size, size * 2 // 3
    gran_px = max(size / 120, 2.0)
    rng = np.random.default_rng(SEED)
    sheet = Sheet(h, w, gran_px, SEED)
    canvas = Canvas(0, 0, w, h, w, h)
    paper = paper_plate(sheet, canvas, PaperStyle(), w)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    inside = (xx > MARGIN * w) & (xx < w - MARGIN * w)
    scene = _Scene(sheet, yy, xx, inside, int(SHORE * h), int(LAKE_END * h))

    hills, far = _hills(scene, rng)
    trees = _trees(scene, rng)
    layers: list[PigmentLayer] = [
        *hills,
        _sky(scene, far),
        trees,
        *_lake(scene, rng, [*hills, trees]),
    ]
    painted = composite(layers, paper, PaperStyle())

    rgba = _name(canvas, gran_px, out_dir / f"{STEM}-plate.webp")
    alpha = rgba[..., 3:]
    out = painted * (1 - alpha) + rgba[..., :3] * alpha

    path = out_dir / f"{STEM}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=Path, help="the directory to write the images into")
    parser.add_argument("--size", type=int, default=720, help="the picture's width in pixels")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.size)
