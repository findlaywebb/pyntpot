"""Raster generalisation: many detailed rings in, a few big soft shapes out.

Key names: `Generalisation`, the working grid and morphology of one pass;
`Finish`, the loose edge, second pass and tree seeds a wash wants on top;
`trace_mask`, a mask back into smooth rings; `generalise`, the whole
union-close-open-declutter-trace pass; `generalise_layer`, that pass plus the inner
ring set and the tree seeds, as a dict of `outer`, `inner` and `seeds`.

Everything that reaches the map has been through one grid, so a hundred stacked
outlines become a few shapes. It does not read map data or write path data.
Invariants: results are repeatable between builds, a mask's row 0 is its southern
edge, and an empty input gives an empty result and not a full-map blob.
"""

import math
from dataclasses import dataclass
from typing import Any

from pyntpot.ink.polyline import Pt, simplify, smooth
from pyntpot.maps.contours import _ring_is_wet, marching_squares
from pyntpot.maps.masks import _spread, declutter, rasterise
from pyntpot.maps.relief_strokes import _jitter
from pyntpot.maps.rings import orient, signed_area

#: The fewest points a traced loop needs to be a ring at all.
LOOP_MIN_POINTS = 4

#: The fewest points a simplified traced ring needs to be kept.
KEPT_MIN_POINTS = 4


@dataclass(frozen=True)
class Generalisation:
    """The working grid and the morphology of one generalisation pass.

    Attributes:
        cell: Metres per cell of the working grid.
        morph_cells: Radius of the close and the open, in cells.
        min_area_ha: Hectares below which a blob, or a hole, is dropped.
        passes: Chaikin passes on the traced outline.
    """

    cell: float
    morph_cells: int = 2
    min_area_ha: float = 4.0
    passes: int = 3


@dataclass(frozen=True)
class Finish:
    """What a wash wants on top of a generalised shape.

    Attributes:
        jitter_m: Metres of loose-edge wobble. Zero draws the measured edge.
        inset_cells: Cells to pull in for the second, darker pass of pigment.
        seed_spacing_m: Metres between tree seeds. Zero scatters none.
        seed: Shifts the wobble, so two layers do not move in step.
    """

    jitter_m: float = 0.0
    inset_cells: int = 2
    seed_spacing_m: float = 0.0
    seed: int = 0


DEFAULT_FINISH = Finish()


def trace_mask(
    mask: list[bytearray],
    clip: tuple[float, float, float, float],
    cell: float,
    eps: float = 18.0,
    passes: int = 3,
) -> list[list[Pt]]:
    """Trace a mask back into smooth rings.

    Args:
        mask: Rows of cells, row 0 southernmost.
        clip: (xmin, ymin, xmax, ymax) in metres.
        cell: Metres per cell.
        eps: Douglas-Peucker tolerance in metres, applied before the smoothing.
        passes: Chaikin passes. Two or three is the difference between a
            staircase and a brush stroke.

    Returns:
        Closed rings in metres, filled rings and holes both, wound so one
        `fill-rule="nonzero"` path fills the union once.
    """
    xmin, ymin, _, _ = clip
    padded = [[0.0] * (len(mask[0]) + 2)]
    padded += [[0.0] + [float(v) for v in row] + [0.0] for row in mask]
    padded += [[0.0] * (len(mask[0]) + 2)]
    out = []
    for ring in marching_squares(padded, 0.5):
        if len(ring) < LOOP_MIN_POINTS:
            continue
        wet = _ring_is_wet(ring, padded, 0.5)
        metres = [(xmin + (col - 1) * cell, ymin + (row - 1) * cell) for col, row in ring]
        metres = smooth(simplify(metres, eps), passes=passes, closed=True)
        metres = simplify(metres, eps * 0.3)
        if len(metres) >= KEPT_MIN_POINTS:
            out.append(orient(metres, counter_clockwise=wet))
    return out


def _closed_opened(mask: list[bytearray], grid: Generalisation) -> list[bytearray]:
    """The mask closed, then opened, then cleared of specks and pinholes."""
    morph = grid.morph_cells
    mask = _spread(_spread(mask, morph, grow=True), morph, grow=False)
    mask = _spread(_spread(mask, morph, grow=False), morph, grow=True)
    return declutter(mask, _min_cells(grid))


def _min_cells(grid: Generalisation) -> int:
    """The area below which a blob or a hole is dropped, in cells."""
    return max(1, int(grid.min_area_ha * 10000.0 / (grid.cell * grid.cell)))


def generalise(
    rings: list[list[Pt]],
    holes: list[list[Pt]],
    clip: tuple[float, float, float, float],
    grid: Generalisation,
) -> list[list[Pt]]:
    """Raster generalisation: union, close, open, declutter, trace, smooth.

    Everything that reaches the map has been through one grid, so what comes
    out is a few big shapes with soft edges rather than a hundred outlines
    stacked on each other.

    Args:
        rings: Filled rings in metres.
        holes: Rings that punch through them.
        clip: (xmin, ymin, xmax, ymax) in metres.
        grid: The working grid and the morphology.

    Returns:
        Rings ready to concatenate into one filled path.
    """
    if not rings:
        return []
    mask = _closed_opened(rasterise(rings, holes, clip, grid.cell), grid)
    return trace_mask(mask, clip, grid.cell, eps=grid.cell * 0.55, passes=grid.passes)


def jitter_ring(ring: list[Pt], amplitude: float, seed: int = 0) -> list[Pt]:
    """Push a ring's outline in and out along its own normals.

    A generalised mask traces as a smooth but obviously computed curve. A
    hand-drawn map does not have accurate edges, it has loose ones, so every
    vertex is moved along its outward normal by a low-frequency wave: the shape
    stays the shape and the edge stops looking measured.

    Args:
        ring: A closed ring in metres.
        amplitude: Metres of movement at the peak of the wave.
        seed: Shifts the wave, so two layers do not wobble in step.

    Returns:
        The moved ring, with as many points; the ring itself when it has fewer
        than `LOOP_MIN_POINTS` points or `amplitude` is not positive.
    """
    n = len(ring)
    if n < LOOP_MIN_POINTS or amplitude <= 0:
        return ring
    outward = 1.0 if signed_area(ring) > 0 else -1.0
    phase = (seed % 17) * 0.37
    out = []
    for i, (x, y) in enumerate(ring):
        ax, ay = ring[i - 1]
        bx, by = ring[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = dy / norm * outward, -dx / norm * outward
        t = i / n * math.tau
        wave = 0.62 * math.sin(3 * t + phase) + 0.38 * math.sin(7 * t + phase * 2.3)
        out.append((x + nx * amplitude * wave, y + ny * amplitude * wave))
    return out


def scatter(
    mask: list[bytearray],
    clip: tuple[float, float, float, float],
    cell: float,
    spacing_m: float,
    salt: int = 3,
) -> list[Pt]:
    """Points on a jittered grid that fall well inside a mask.

    For the tree glyphs: a wood is a wash, and a handful of little conifers in
    it is what says the wash is a wood rather than a field.

    Args:
        mask: Rows of cells, row 0 southernmost.
        clip: (xmin, ymin, xmax, ymax) in metres.
        cell: Metres per cell of the mask.
        spacing_m: Metres between seeds. Zero scatters nothing.
        salt: Shifts the jitter.

    Returns:
        Points in metres, repeatable between builds.
    """
    if spacing_m <= 0:
        return []
    inner = _spread(mask, 1, grow=False)
    xmin, ymin, xmax, ymax = clip
    out: list[Pt] = []
    cols = int((xmax - xmin) / spacing_m) + 1
    rows = int((ymax - ymin) / spacing_m) + 1
    for j in range(rows):
        for i in range(cols):
            jx, jy = _jitter(i, j, salt)
            x = xmin + (i + 0.5 + jx * 0.9) * spacing_m
            y = ymin + (j + 0.5 + jy * 0.9) * spacing_m
            c, r = int((x - xmin) / cell), int((y - ymin) / cell)
            if 0 <= r < len(inner) and 0 <= c < len(inner[0]) and inner[r][c]:
                out.append((round(x, 1), round(y, 1)))
    return out


def generalise_layer(
    rings: list[list[Pt]],
    holes: list[list[Pt]],
    clip: tuple[float, float, float, float],
    grid: Generalisation,
    finish: Finish = DEFAULT_FINISH,
) -> dict[str, Any]:
    """The generalisation stage, and the two extra passes a wash wants.

    Args:
        rings: Filled rings in metres.
        holes: Rings that punch through them.
        clip: (xmin, ymin, xmax, ymax) in metres.
        grid: The working grid and the morphology.
        finish: The loose edge, the second pass and the tree seeds.

    Returns:
        `outer` rings, the `inner` second-pass rings (none when
        `finish.inset_cells` is 0), and the tree `seeds`.
    """
    empty: dict[str, Any] = {"outer": [], "inner": [], "seeds": []}
    if not rings:
        return empty
    cell = grid.cell
    mask = _closed_opened(rasterise(rings, holes, clip, cell), grid)
    eps = cell * 0.55

    def traced(source: list[bytearray], salt: int) -> list[list[Pt]]:
        """Trace a mask into rings, each given a loose edge when the finish asks for one."""
        out = []
        for ring in trace_mask(source, clip, cell, eps=eps, passes=grid.passes):
            out.append(jitter_ring(ring, finish.jitter_m, salt) if finish.jitter_m else ring)
        return out

    inset = max(1, finish.inset_cells)
    inner_mask = declutter(_spread(mask, inset, grow=False), _min_cells(grid))
    return {
        "outer": traced(mask, finish.seed),
        "inner": traced(inner_mask, finish.seed + 5) if finish.inset_cells > 0 else [],
        "seeds": scatter(mask, clip, cell, finish.seed_spacing_m),
    }
