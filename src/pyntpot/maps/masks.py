"""Binary masks of ring sets: rasterising, morphology and speck removal.

Key names: `rasterise`, rings and holes to a coarse mask with row 0 southernmost;
`declutter`, specks and pinholes below a cell count dropped.

A mask is a list of `bytearray` rows of 0 and 1. Rasterising is what turns a
hundred overlapping polygons into one shape, so every later step works on the
shape and not on the hundred. It does not trace a mask back into rings or choose
how coarse the grid is. Invariants: a ring is filled by scanline in place, a hole
erases what it covers, and every function returns a new mask unless it says it
fills in place.
"""

import math

from pyntpot.ink.polyline import Pt

#: The fewest points a ring needs to enclose anything.
MIN_RING_POINTS = 3


def _fill_ring(
    mask: list[bytearray], ring: list[Pt], x0: float, y0: float, cell: float, value: int
) -> None:
    """Scanline-fill one ring into a mask, in place.

    Testing every cell against every ring is the obvious way and far too slow on
    a ride's sheet; a scanline costs one pass over the ring's own points per row
    it covers.

    Args:
        mask: Rows of cells, row 0 southernmost.
        ring: Closed ring in metres.
        x0: Metres at the mask's western edge.
        y0: Metres at the mask's southern edge.
        cell: Metres per cell.
        value: 1 to paint, 0 to erase.
    """
    rows, cols = len(mask), len(mask[0])
    ys = [p[1] for p in ring]
    lo = max(0, int((min(ys) - y0) / cell))
    hi = min(rows - 1, int((max(ys) - y0) / cell) + 1)
    for r in range(lo, hi + 1):
        y = y0 + (r + 0.5) * cell
        crossings = []
        for i in range(len(ring)):
            (ax, ay), (bx, by) = ring[i], ring[(i + 1) % len(ring)]
            if (ay > y) == (by > y):
                continue
            crossings.append(ax + (y - ay) * (bx - ax) / (by - ay))
        crossings.sort()
        row = mask[r]
        for a, b in zip(crossings[0::2], crossings[1::2], strict=False):
            ca = max(0, math.ceil((a - x0) / cell - 0.5))
            cb = min(cols - 1, int((b - x0) / cell - 0.5))
            for c in range(ca, cb + 1):
                row[c] = value


def rasterise(
    rings: list[list[Pt]],
    holes: list[list[Pt]],
    clip: tuple[float, float, float, float],
    cell: float,
) -> list[bytearray]:
    """The union of a set of rings as a coarse binary mask.

    Rasterising is what turns "one hundred overlapping wood polygons" into one
    shape. Every later step, the smoothing and the speck removal, works on the
    shape rather than on the hundred.

    Args:
        rings: Filled rings in metres.
        holes: Rings that punch through them.
        clip: (xmin, ymin, xmax, ymax) in metres.
        cell: Metres per cell.

    Returns:
        Rows of cells, row 0 southernmost.
    """
    xmin, ymin, xmax, ymax = clip
    cols = max(1, int((xmax - xmin) / cell) + 1)
    rows = max(1, int((ymax - ymin) / cell) + 1)
    mask = [bytearray(cols) for _ in range(rows)]
    for ring in rings:
        if len(ring) >= MIN_RING_POINTS:
            _fill_ring(mask, ring, xmin, ymin, cell, 1)
    for ring in holes:
        if len(ring) >= MIN_RING_POINTS:
            _fill_ring(mask, ring, xmin, ymin, cell, 0)
    return mask


def _spread(mask: list[bytearray], radius: int, *, grow: bool) -> list[bytearray]:
    """Dilate or erode a mask by a square of `radius` cells, separably."""
    if radius <= 0:
        return [bytearray(row) for row in mask]
    rows, cols = len(mask), len(mask[0])
    hit = 1 if grow else 0
    out = [bytearray(row) for row in mask]
    for r in range(rows):
        src, dst = mask[r], out[r]
        for c in range(cols):
            lo, hi = max(0, c - radius), min(cols - 1, c + radius)
            dst[c] = hit if any(src[i] == hit for i in range(lo, hi + 1)) else src[c]
    final = [bytearray(row) for row in out]
    for c in range(cols):
        column = [out[r][c] for r in range(rows)]
        for r in range(rows):
            lo, hi = max(0, r - radius), min(rows - 1, r + radius)
            if any(column[i] == hit for i in range(lo, hi + 1)):
                final[r][c] = hit
    return final


def _components(mask: list[bytearray], value: int) -> list[list[tuple[int, int]]]:
    """Four-connected components of the cells equal to `value`."""
    rows, cols = len(mask), len(mask[0])
    seen = [bytearray(cols) for _ in range(rows)]
    out = []
    for r0 in range(rows):
        for c0 in range(cols):
            if seen[r0][c0] or mask[r0][c0] != value:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = 1
            blob = []
            while stack:
                r, c = stack.pop()
                blob.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and not seen[nr][nc]
                        and mask[nr][nc] == value
                    ):
                        seen[nr][nc] = 1
                        stack.append((nr, nc))
            out.append(blob)
    return out


def declutter(mask: list[bytearray], min_cells: int) -> list[bytearray]:
    """Drop specks and fill pinholes below `min_cells` in area.

    A wood the size of four cells is noise on a sheet this size, and so is a
    clearing the same size. Both go, which is what leaves few big shapes.
    """
    out = [bytearray(row) for row in mask]
    for blob in _components(out, 1):
        if len(blob) < min_cells:
            for r, c in blob:
                out[r][c] = 0
    rows, cols = len(out), len(out[0])
    for blob in _components(out, 0):
        touches_edge = any(r in (0, rows - 1) or c in (0, cols - 1) for r, c in blob)
        if not touches_edge and len(blob) < min_cells:
            for r, c in blob:
                out[r][c] = 1
    return out
