"""A glyph's ink filled on a small grid, thinned and walked into chains.

`_fill` rasterises a glyph's contours with an even-odd scanline fill, `thin`
takes the bitmap to a one pixel Zhang-Suen skeleton, and `_chains` walks that
skeleton into runs split at every junction, which `_prune` clears of the short
spurs thinning grows. `_components` finds the separate blobs of ink. All of it
works in raster pixels as `(row, col)`.

Thinning is the risk: a medial axis forks at every join and every terminal, and
no amount of pruning makes a fork that should not be there into one that
should. What is done with the chains, pushing ends out and recovering merged
strokes, is `letters.trace`. This module does not read fonts and does not draw.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pyntpot.ink.polyline import Pt


#: Em units the glyph is rasterised at before it is thinned. Big enough that a
#: thin stroke is several pixels across, small enough that the walk stays
#: milliseconds a glyph, and every glyph is cached anyway.
RASTER_EM = 128

#: Zhang-Suen deletes a pixel only while it has between this many and
#: `MAX_NEIGHBOURS` ink neighbours: fewer is an end, more is interior.
MIN_NEIGHBOURS = 2
MAX_NEIGHBOURS = 6

#: A pixel with this many strokes meeting at it is a stroke passing through,
#: not a junction and not an end.
PASSING = 2

#: A leftover loop of this many distinct pixels or fewer is staircase speckle.
SPECKLE = 2


def _fill(contours: list[list[Pt]], upem: int, pad: int = 3) -> tuple[np.ndarray, float, float]:
    """A filled bitmap of one glyph, and where its bottom left corner sits.

    Even-odd scanline fill rather than a library rasteriser, because a glyph is
    a handful of closed contours and the fill has to agree exactly with the
    contours the outline route draws.

    Args:
        contours: The glyph's contours in font units.
        upem: Units per em, so the grid is `RASTER_EM` pixels an em.
        pad: Blank pixels round the glyph, so the skeleton never touches an edge.

    Returns:
        The bitmap, and the x and y of its origin in font units.
    """
    k = RASTER_EM / upem
    xs = [p[0] for c in contours for p in c]
    ys = [p[1] for c in contours for p in c]
    x0, y0 = min(xs), min(ys)
    w = math.ceil((max(xs) - x0) * k) + 2 * pad + 1
    h = math.ceil((max(ys) - y0) * k) + 2 * pad + 1
    img = np.zeros((h, w), np.uint8)
    edges = []
    for c in contours:
        for a, b in zip(c, c[1:] + c[:1], strict=True):
            ax, ay = (a[0] - x0) * k + pad, (a[1] - y0) * k + pad
            bx, by = (b[0] - x0) * k + pad, (b[1] - y0) * k + pad
            if ay != by:
                edges.append((ax, ay, bx, by))
    for row in range(h):
        yc = row + 0.5
        cuts = sorted(
            ax + (yc - ay) * (bx - ax) / (by - ay)
            for ax, ay, bx, by in edges
            if min(ay, by) <= yc < max(ay, by)
        )
        for i in range(0, len(cuts) - 1, 2):
            lo = math.ceil(cuts[i] - 0.5)
            hi = math.floor(cuts[i + 1] - 0.5)
            if hi >= lo:
                img[row, max(lo, 0) : hi + 1] = 1
    return img, x0 - pad / k, y0 - pad / k


def thin(img: np.ndarray) -> np.ndarray:
    """Zhang-Suen thinning: a filled shape down to a one pixel skeleton.

    Args:
        img: The filled bitmap, 1 where there is ink.

    Returns:
        The skeleton, the same shape.
    """
    out = (np.asarray(img) > 0).astype(np.uint8)
    for _ in range(200):
        changed = False
        for step in (0, 1):
            p = np.pad(out, 1)
            n2, n3 = p[0:-2, 1:-1], p[0:-2, 2:]
            n4, n5 = p[1:-1, 2:], p[2:, 2:]
            n6, n7 = p[2:, 1:-1], p[2:, 0:-2]
            n8, n9 = p[1:-1, 0:-2], p[0:-2, 0:-2]
            ring = [n2, n3, n4, n5, n6, n7, n8, n9, n2]
            count = n2 + n3 + n4 + n5 + n6 + n7 + n8 + n9
            turns = sum(((ring[i] == 0) & (ring[i + 1] == 1)).astype(np.uint8) for i in range(8))
            if step == 0:
                c1, c2 = n2 * n4 * n6, n4 * n6 * n8
            else:
                c1, c2 = n2 * n4 * n8, n2 * n6 * n8
            kill = (
                (out == 1)
                & (count >= MIN_NEIGHBOURS)
                & (count <= MAX_NEIGHBOURS)
                & (turns == 1)
                & (c1 == 0)
                & (c2 == 0)
            )
            if kill.any():
                out[kill] = 0
                changed = True
        if not changed:
            break
    return out


def _ring(p: tuple[int, int]) -> list[tuple[int, int]]:
    """The eight neighbours of a pixel, in order round it."""
    r, c = p
    return [
        (r - 1, c),
        (r - 1, c + 1),
        (r, c + 1),
        (r + 1, c + 1),
        (r + 1, c),
        (r + 1, c - 1),
        (r, c - 1),
        (r - 1, c - 1),
    ]


def _crossings(p: tuple[int, int], on: set[tuple[int, int]]) -> int:
    """How many strokes meet at a pixel, by transitions round its own ring.

    Counting neighbours instead is the mistake that fragments a skeleton: a
    diagonal staircase gives a pixel three neighbours and no junction, and
    every one of them then reads as a fork. Transitions round the ring do not
    care about the staircase, which is the whole reason they are the standard.
    """
    ring = [1 if q in on else 0 for q in _ring(p)]
    return sum(1 for i in range(8) if ring[i] == 0 and ring[(i + 1) % 8] == 1)


def _step(
    nbrs: dict[tuple[int, int], list[tuple[int, int]]], prev: tuple[int, int], cur: tuple[int, int]
) -> tuple[int, int] | None:
    """The next pixel along, ignoring the one the staircase came from."""
    back = set(nbrs[prev]) | {prev}
    ahead = [q for q in nbrs[cur] if q not in back]
    return ahead[0] if ahead else next((q for q in nbrs[cur] if q != prev), None)


def _walk(
    nbrs: dict[tuple[int, int], list[tuple[int, int]]],
    nodes: set[tuple[int, int]],
    start: tuple[int, int],
    first: tuple[int, int],
) -> list[tuple[int, int]]:
    """Follow a chain from a node to the next node."""
    chain = [start, first]
    prev, cur = start, first
    while cur not in nodes:
        nxt = _step(nbrs, prev, cur)
        if nxt is None or nxt in chain[:-1]:
            break
        prev, cur = cur, nxt
        chain.append(cur)
    return chain


def _loops(
    nbrs: dict[tuple[int, int], list[tuple[int, int]]], left: set[tuple[int, int]]
) -> list[list[tuple[int, int]]]:
    """Closed loops with no junction at all, an `o` or an `0`, walked from what is left."""
    out: list[list[tuple[int, int]]] = []
    while left:
        start = min(left)
        cur = next((q for q in nbrs[start] if q in left), None)
        chain, prev = [start], start
        while cur is not None and cur != start:
            chain.append(cur)
            nxt = _step(nbrs, prev, cur)
            prev, cur = cur, (nxt if nxt in left or nxt == start else None)
        chain.append(start)
        # A walk steps over the inner pixel of every staircase corner, so what
        # is left after a loop has been traced is a scatter of single pixels
        # already covered by the line beside them. Emitted, each one is a
        # zero-length stroke, and the nib leaves a blot: that is where the
        # speckle round every curved letter came from. A leftover of one or
        # two pixels is dropped; a real component is kept.
        if len(set(chain)) > SPECKLE:
            out.append(chain)
        left -= set(chain)
    return out


def _chains(skel: np.ndarray) -> list[list[tuple[int, int]]]:
    """The skeleton walked into chains, split at every junction.

    Args:
        skel: The one pixel skeleton.

    Returns:
        Chains of `(row, col)`, each running endpoint or junction to the next.
    """
    on = {(int(r), int(c)) for r, c in zip(*np.nonzero(skel), strict=True)}
    nbrs = {p: [q for q in _ring(p) if q in on] for p in on}
    cross = {p: _crossings(p, on) for p in on}
    nodes = {p for p in on if cross[p] != PASSING}
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    out: list[list[tuple[int, int]]] = []
    for node in sorted(nodes):
        for nb in nbrs[node]:
            if (node, nb) in seen:
                continue
            chain = _walk(nbrs, nodes, node, nb)
            seen.add((node, nb))
            if len(chain) > 1:
                seen.add((chain[-1], chain[-2]))
            out.append(chain)
    left = on - {p for chain in out for p in chain}
    out.extend(_loops(nbrs, left))
    return out


def _prune(chains: list[list[tuple[int, int]]], limit: float) -> list[list[tuple[int, int]]]:
    """Drop the short branches thinning grows at joins and at terminals."""
    ends: dict[tuple[int, int], int] = {}
    for chain in chains:
        for p in (chain[0], chain[-1]):
            ends[p] = ends.get(p, 0) + 1
    keep = []
    for chain in chains:
        spur = ends.get(chain[0], 0) == 1 or ends.get(chain[-1], 0) == 1
        if spur and len(chain) < limit and len(chains) > 1:
            continue
        keep.append(chain)
    return keep or chains


def _components(img: np.ndarray) -> list[list[tuple[int, int]]]:
    """The ink's connected components, eight-connected."""
    on = {(int(r), int(c)) for r, c in zip(*np.nonzero(img), strict=True)}
    out: list[list[tuple[int, int]]] = []
    while on:
        seed = next(iter(on))
        stack, blob = [seed], []
        on.discard(seed)
        while stack:
            p = stack.pop()
            blob.append(p)
            for q in _ring(p):
                if q in on:
                    on.discard(q)
                    stack.append(q)
        out.append(blob)
    return out
