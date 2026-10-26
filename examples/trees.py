"""Painting with Python: a recursive tree, the trunk brushed and the twigs penned, and a family of nine.

A tree is one rule applied to itself. A limb grows a length along a heading, bending a
little as it goes, and at its tip it splits into two limbs (now and then three), each
shorter than the one before by `ratio`, each turned away from its parent by `spread`
degrees, a little more to one side than the other. `grow` follows that rule to `DEPTH`
splits and returns every limb as a path of points with the width it starts at and the
width it ends at. The straightest child carries on its parent's stroke and starts exactly as
wide as its parent ends, so the widths taper by depth with no step at a joint.

The painting goes the way the layers are listed in `LAYERS`. First a dry stroke of ground
under the foot, then the limbs in `burnt_sienna`. The trunk and the first limbs are brushed
(the brush sheet's row 2) and `stamp`'s `wprof` makes each stroke taper from its start width
to its end width; the trunk carries a narrower stroke of `perylene_maroon` on its shaded
side. Where a limb is thinner than a brush can draw, the hand changes to a pen (row 6) and
the twigs are penned in `perylene_maroon`. Over the limbs goes the canopy: a `wash` of
`sap_green` over the tips of the last limbs, a second, smaller wash in the same green on
some of them for depth, and a wash of `yellow_ochre` on a few, all glazed by Kubelka-Munk
so a warm leaf is still a leaf. Last, a few hundred short dabs of a wet brush (row 1) in
`sap_green` and `indigo` are laid over the canopy's edge, the leaves.

`figure="tree"` paints one tree, `figure="family"` paints nine in a grid three trees across.
A family is the same rule run with nine seeds: each seed moves `spread`, `ratio`, `droop`
and `lean` by a few per cent (`perturbed`) and draws the limbs' own wander from a generator
of its own, so the nine are one species and no two are alike. Every tree is painted in its
own cell at the cell's size, never at the grid's size and downsized, and the paper is laid once, under all nine.

It does not draw leaves one by one, model light or grow roots: the canopy is washes and dabs
laid over the limbs' tips.

Public names it uses, all from `pyntpot.ink`: `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`,
`wash`, `PAINTERS_PIGMENTS`, `PAINTERS_TRANSPARENCY`, `rgb`, `PigmentLayer`, `composite`,
`brush_from_id`, `BrushStyle`, `stamp`, `ink_density` and `save_image`.

Run it with `uv run python examples/trees.py out/ --figure family`; it writes
`out/trees-family.png`. It takes `figure` (`tree` or `family`), `size`, the image's width in
pixels (a tree is four thirds as high as it is wide; a family is three cells across and three
down, each cell four thirds as high as it is wide, so the grid has the same ratio), and `seed`.
"""

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pyntpot.ink import (
    PAINTERS_PIGMENTS,
    PAINTERS_TRANSPARENCY,
    BrushStyle,
    Canvas,
    PaperStyle,
    PigmentLayer,
    Sheet,
    brush_from_id,
    composite,
    ink_density,
    paper_plate,
    rgb,
    save_image,
    stamp,
    wash,
)

logger = logging.getLogger(__name__)

#: The default width of each figure's image in pixels, and the default seed.
SIZES = {"tree": 600, "family": 720}
SEED = 4
#: The width the paper's grain is sized against, in pixels, and the grain's size there.
REFERENCE = 600
GRAN_PX = 8.0
#: How many splits deep a tree grows, how many points make one limb's path, and the last
#: depth drawn with a brush; the limbs beyond are penned.
DEPTH = 6
POINTS = 14
LAST_BRUSHED = 3
#: The odds that a limb splits in three, that a dab is the dark one, and the share of the
#: tips the canopy's second, deeper wash covers.
THREE_ODDS, DARK_ODDS, DEEP_SHARE = 0.18, 0.08, 0.45
#: How hard young limbs are drawn toward the light, in radians over their length.
TROPISM = 0.45
#: The widest a tree's limbs stand, as a share of its cell's width, and the tallest, of its height,
#: and how far down the cell the trunk's foot is. The rest is margin for the crown, which reaches past the limbs.
FIT_WIDTH, FIT_HEIGHT, FOOT = 0.66, 0.74, 0.91
#: A family is this many trees across and this many down.
ACROSS, DOWN = 3, 3
#: Brushes follow the stroke smoothly and drift as a hand does.
STYLE = BrushStyle(brush_organic=True, stroke_smooth=True)
#: Each layer, bottom first, with its painter's pigment.
LAYERS = (
    ("ground", "raw_sienna"),
    ("limbs", "burnt_sienna"),
    ("shade", "perylene_maroon"),
    ("twigs", "perylene_maroon"),
    ("canopy", "sap_green"),
    ("canopy2", "sap_green"),
    ("warm", "yellow_ochre"),
    ("leaves", "sap_green"),
    ("leaves2", "indigo"),
)


@dataclass(frozen=True)
class Shape:
    """The few numbers that make one species of tree, before a seed's own wander."""

    #: How far a child turns from its parent, in degrees.
    spread: float = 31.0
    #: A child's length as a share of its parent's.
    ratio: float = 0.8
    #: How much an old limb sags toward the ground, in radians over its length.
    droop: float = 0.3
    #: How far the whole tree leans, in degrees: the wind.
    lean: float = 0.0


@dataclass(frozen=True)
class Limb:
    """One limb: its path, its splits from the trunk, its widths and the stroke it belongs to."""

    path: np.ndarray
    depth: int
    w_start: float
    w_end: float
    stroke: int


def perturbed(shape: Shape, rng: np.random.Generator) -> Shape:
    """Return `shape` with each number moved by a few per cent, so a seed grows a new tree of one species."""
    return Shape(
        spread=shape.spread * rng.uniform(0.85, 1.2),
        ratio=shape.ratio * rng.uniform(0.95, 1.04),
        droop=shape.droop * rng.uniform(0.5, 1.6),
        lean=shape.lean + rng.normal(0.0, 4.0),
    )


def _path(
    start: np.ndarray,
    heading: float,
    length: float,
    depth: int,
    shape: Shape,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return a limb's path from `start`: `POINTS` points along `heading`, drawn up when young and sagging when old."""
    pts = [start]
    step = length / (POINTS - 1)
    h = heading
    young = 1.0 - depth / DEPTH
    for _ in range(POINTS - 1):
        pull = (shape.droop * (1.0 - young) - TROPISM * young) * np.sin(h)
        h += pull / (POINTS - 1) + rng.normal(0.0, 0.055)
        pts.append(pts[-1] + step * np.array([np.sin(h), -np.cos(h)]))
    return np.array(pts)


def grow(
    start: np.ndarray, length: float, width: float, shape: Shape, rng: np.random.Generator
) -> list[Limb]:
    """Grow a tree from `start`: the trunk, then every limb to `DEPTH` splits.

    Args:
        start: Where the trunk's foot is, in pixels.
        length: The trunk's length in pixels.
        width: The trunk's width at its foot in pixels.
        shape: The species' numbers.
        rng: The generator the wander, the splits and the lengths are drawn from.

    Returns:
        Every limb, the trunk first.
    """
    limbs: list[Limb] = []
    strokes = 1
    todo = [(start, np.radians(shape.lean), length, width, 0, 0)]
    while todo:
        foot, heading, ln, w, depth, stroke = todo.pop()
        path = _path(foot, heading, ln, depth, shape, rng)
        w_end = w * (0.62 if depth == 0 else 0.78 if depth < LAST_BRUSHED else 0.62)
        limbs.append(Limb(path, depth, w, w_end, stroke))
        if depth == DEPTH:
            continue
        turn = np.radians(shape.spread) * (0.45 if depth == 0 else 0.8 if depth == 1 else 1.0)
        three = rng.random() < THREE_ODDS and depth < DEPTH - 2
        offsets = [-1.3 * turn, 0.1 * turn, 1.2 * turn] if three else [-turn, turn]
        lead = int(np.argmin(np.abs(offsets)))
        dx, dy = path[-1] - path[-2]
        base = float(np.arctan2(dx, -dy))
        for i, off in enumerate(offsets):
            kid_len = ln * shape.ratio * rng.uniform(0.75, 1.15)
            heading_i = base + off * rng.uniform(0.7, 1.3)
            if i == lead:
                todo.append((path[-1], heading_i, kid_len, w_end, depth + 1, stroke))
            else:
                todo.append((path[-1], heading_i, kid_len, w_end * 0.88, depth + 1, strokes))
                strokes += 1
    return limbs


def fitted(limbs: list[Limb], cell: tuple[int, int]) -> list[Limb]:
    """Return `limbs` scaled and moved to stand centred in the `(height, width)` cell, foot low, in a margin of paper."""
    h, w = cell
    pts = np.vstack([limb.path for limb in limbs])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    k = min(FIT_WIDTH * w / (hi[0] - lo[0]), FIT_HEIGHT * h / (hi[1] - lo[1]))
    foot = np.array([w * 0.5, h * FOOT])
    origin = np.array([(lo[0] + hi[0]) / 2, hi[1]])
    return [
        Limb(
            foot + k * (limb.path - origin),
            limb.depth,
            limb.w_start * k,
            limb.w_end * k,
            limb.stroke,
        )
        for limb in limbs
    ]


def _strokes(limbs: list[Limb], *, penned: bool) -> list[tuple[np.ndarray, np.ndarray]]:
    """Join each stroke's limbs into one path and its widths: the brushed part of each, or the penned part."""
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for stroke in sorted({limb.stroke for limb in limbs}):
        mine = sorted((limb for limb in limbs if limb.stroke == stroke), key=lambda x: x.depth)
        chosen = [limb for limb in mine if (limb.depth > LAST_BRUSHED) == penned]
        if not chosen:
            continue
        before = [limb for limb in mine if limb.depth < chosen[0].depth]
        pts = [before[-1].path[-1:]] if before else []
        wid = [np.array([before[-1].w_end])] if before else []
        for limb in chosen:
            skip = 1 if pts else 0
            pts.append(limb.path[skip:])
            wid.append(np.linspace(limb.w_start, limb.w_end, len(limb.path))[skip:])
        out.append((np.vstack(pts), np.concatenate(wid)))
    return out


def _lay(
    acc: np.ndarray, strokes: list[tuple[np.ndarray, np.ndarray]], row: str, floor: float, seed: int
) -> None:
    """Stamp each `(path, widths)` into `acc` with a brush of `row` as wide as its stroke starts, tapering by `wprof`."""
    for i, (path, widths) in enumerate(strokes):
        width = max(float(widths.max()), floor)
        brush, _ = brush_from_id(row, width, 1.0, STYLE)
        along = np.r_[0.0, np.cumsum(np.hypot(*np.diff(path, axis=0).T))]
        at = np.linspace(0.0, along[-1], 48)
        wprof = np.maximum(np.interp(at, along, widths), floor) / width
        stamp(acc, path, brush, np.random.default_rng([seed, i]), wprof=wprof)


def _crown(
    tips: np.ndarray, radius: float, cell: tuple[int, int], rng: np.random.Generator
) -> np.ndarray:
    """Return a 0 to 1 mask of lumpy discs of about `radius` pixels centred on `tips`: each edge swells and dips twice or thrice."""
    h, w = cell
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    mask = np.zeros((h, w), bool)
    for x, y in tips:
        r = radius * rng.uniform(0.7, 1.3)
        a, b, p, q = rng.uniform(0.12, 0.3), rng.uniform(0.12, 0.3), *rng.uniform(0.0, 6.3, 2)
        theta = np.arctan2(yy - y, xx - x)
        mask |= np.hypot(xx - x, yy - y) <= r * (
            1 + a * np.sin(2 * theta + p) + b * np.sin(3 * theta + q)
        )
    return mask.astype(np.float32)


def _leaves(tips: np.ndarray, cell: tuple[int, int], sheet: Sheet, seed: int) -> list[np.ndarray]:
    """Dab a wet brush round the tips, short strokes leaning every way: the leaves, light and dark."""
    h, w = cell
    rng = np.random.default_rng(seed)
    brush, _ = brush_from_id("RIV1-a", max(w * 0.012, 1.0), 1.0, STYLE)
    acc = [np.zeros((h, w), np.float32), np.zeros((h, w), np.float32)]
    for i, (x, y) in enumerate(tips):
        dab_rng = np.random.default_rng([seed, i])
        for _ in range(2):
            ox, oy = rng.normal(0.0, w * 0.025, 2)
            lean = dab_rng.uniform(-np.pi, np.pi)
            a = np.array([x + ox, y + oy])
            tip = a + w * dab_rng.uniform(0.02, 0.04) * np.array([np.sin(lean), -np.cos(lean)])
            stamp(acc[int(rng.random() < DARK_ODDS)], np.array([a, tip]), brush, dab_rng)
    return [0.45 * ink_density(a, brush, sheet) for a in acc]


def paint_tree(
    cell: tuple[int, int], sheet: Sheet, shape: Shape, seed: int
) -> dict[str, np.ndarray]:
    """Paint one tree in a `(height, width)` cell and return its densities by layer name, `LAYERS`."""
    h, w = cell
    rng = np.random.default_rng(seed)
    limbs = fitted(grow(np.array([w * 0.5, h * FOOT]), h * 0.22, w * 0.07, shape, rng), cell)
    tips = np.array([(*limb.path[-1], limb.depth) for limb in limbs if limb.depth >= DEPTH - 2])
    warm = tips[rng.random(len(tips)) < rng.uniform(0.1, 0.4), :2]
    layers = {
        "canopy": wash(_crown(tips[:, :2], w * 0.075, cell, rng), sheet, 0.3, 0.15),
        "canopy2": wash(
            _crown(tips[rng.random(len(tips)) < DEEP_SHARE, :2], w * 0.05, cell, rng),
            sheet,
            0.3,
            0.15,
        ),
        "warm": wash(_crown(warm, w * 0.07, cell, rng), sheet, 0.4, 0.3),
    }
    ground = np.zeros((h, w), np.float32)
    dry, _ = brush_from_id("TRK4-d", w * 0.025, 1.0, STYLE)
    stamp(
        ground,
        np.array([(w * 0.34, h * (FOOT + 0.007)), (w * 0.66, h * (FOOT + 0.004))]),
        dry,
        rng,
        wprof=np.sin(np.linspace(0.05, np.pi - 0.05, 12)) ** 0.6,
    )
    layers["ground"] = 0.4 * ink_density(ground, dry, sheet)

    wet, _ = brush_from_id("RIV2-a", limbs[0].w_start, 1.0, STYLE)
    nib, _ = brush_from_id("MAJ6-e", 1.0, 1.0, STYLE)
    brushed, penned = np.zeros((h, w), np.float32), np.zeros((h, w), np.float32)
    _lay(brushed, _strokes(limbs, penned=False), "RIV2-a", 1.0, seed)
    _lay(penned, _strokes(limbs, penned=True), "MAJ6-e", 0.55, seed + 1)
    layers["limbs"] = ink_density(brushed, wet, sheet)
    layers["twigs"] = 0.7 * ink_density(penned, nib, sheet)
    shade = np.zeros((h, w), np.float32)
    swell = np.sin(np.linspace(0.05, np.pi - 0.05, 10)) ** 0.5
    trunk = [  # from a sixth to five sixths of the way up the trunk, swelling and thinning out
        (p[2:12] + np.column_stack([0.22 * wd[2:12], np.zeros(10)]), 0.3 * wd[2:12] * swell)
        for p, wd in _strokes(limbs[:1], penned=False)
    ]
    _lay(shade, trunk, "RIV2-a", 1.0, seed + 2)
    layers["shade"] = 0.45 * ink_density(shade, wet, sheet)
    layers["leaves"], layers["leaves2"] = _leaves(
        tips[tips[:, 2] >= DEPTH - 1][:, :2], cell, sheet, seed + 3
    )
    return layers


def _stack(layers: dict[str, np.ndarray]) -> list[PigmentLayer]:
    """Return the layers in painting order, each with its painter's pigment and transparency."""
    return [
        (layers[name], rgb(PAINTERS_PIGMENTS[key]), PAINTERS_TRANSPARENCY[key])
        for name, key in LAYERS
    ]


def main(out_dir: Path, figure: str = "tree", size: int | None = None, seed: int = SEED) -> Path:
    """Paint a tree or a family of nine and write `trees-<figure>.png` into `out_dir`.

    Args:
        out_dir: The directory the image is written into.
        figure: `tree` for one tree, `family` for nine in a grid.
        size: The image's width in pixels; its height is four thirds of that. A default for each figure.
        seed: The seed of the paper and of the trees.

    Returns:
        The path of the image.

    Raises:
        ValueError: When `figure` is not `tree` or `family`.
    """
    if figure not in SIZES:
        raise ValueError(f"figure must be one of {sorted(SIZES)}, not {figure!r}")
    out_dir.mkdir(parents=True, exist_ok=True)
    width = size or SIZES[figure]
    w, h = width, width * 4 // 3
    style = PaperStyle(km_glazing=True, paper_foxing=0.03)
    paper = paper_plate(
        Sheet(h, w, GRAN_PX * w / REFERENCE, seed), Canvas(0, 0, w, h, w, h), style, w
    )

    across, down = (1, 1) if figure == "tree" else (ACROSS, DOWN)
    cw, ch = w // across, h // down
    grid = {name: np.zeros((h, w), np.float32) for name, _ in LAYERS}
    for i in range(across * down):
        rng = np.random.default_rng([seed, i])
        shape = Shape() if figure == "tree" else perturbed(Shape(), rng)
        cell_sheet = Sheet(ch, cw, GRAN_PX * cw / REFERENCE, seed + i)
        row, col = divmod(i, across)
        window = (slice(row * ch, (row + 1) * ch), slice(col * cw, (col + 1) * cw))
        for name, density in paint_tree((ch, cw), cell_sheet, shape, seed + i).items():
            grid[name][window] = density
    out = composite(_stack(grid), paper, style)
    path = out_dir / f"trees-{figure}.png"
    save_image(out, path, seed=seed)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint a recursive tree or a family of nine.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=sorted(SIZES), default="tree", help="one tree or nine")
    parser.add_argument("--size", type=int, default=None, help="the image's width in pixels")
    parser.add_argument(
        "--seed", type=int, default=SEED, help="the seed of the paper and the trees"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure, args.size, args.seed)
