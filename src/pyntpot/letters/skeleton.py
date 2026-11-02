"""A glyph's ink filled on a small grid, thinned and walked into chains.

`fill` rasterises a glyph's contours with an even-odd scanline fill, `thin`
takes the bitmap to a one pixel Zhang-Suen skeleton, and `skeleton_chains` walks that
skeleton into runs split at every junction, which `prune` clears of the short
spurs thinning grows. `components` finds the separate blobs of ink. All of it
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


#: Raster pixels an em, the scale a glyph is rasterised at before it is
#: thinned. Big enough that a thin stroke is several pixels across, small
#: enough that the walk stays milliseconds a glyph, and every glyph is cached
#: anyway.
RASTER_EM = 128

#: Zhang-Suen deletes a pixel only while it has between this many and
#: `MAX_NEIGHBOURS` ink neighbours: fewer is an end, more is interior.
MIN_NEIGHBOURS = 2
MAX_NEIGHBOURS = 6

#: Two branches leaving a junction whose directions are at least this opposed
#: are one stroke passing through it rather than two meeting in it.
THROUGH_DOT = -0.72

#: A pixel with this many strokes meeting at it is a stroke passing through,
#: not a junction and not an end.
PASSING = 2

#: A walk that is back beside the node it set out from has gone round a loop,
#: rather than stepped along beside it, once it is this many pixels long.
MIN_LOOP = 3

#: A leftover loop of this many distinct pixels or fewer is staircase speckle.
SPECKLE = 2


def fill(contours: list[list[Pt]], upem: int, pad: int = 3) -> tuple[np.ndarray, float, float]:
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

    Source: `zhang-suen` in docs/explanation/references.md.

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


def crossings(p: tuple[int, int], on: set[tuple[int, int]]) -> int:
    """How many strokes meet at a pixel, by transitions round its own ring.

    Counting neighbours instead is the mistake that fragments a skeleton: a
    diagonal staircase gives a pixel three neighbours and no junction, and
    every one of them then reads as a fork. Transitions round the ring do not
    care about the staircase, which is the whole reason they are the standard.
    """
    ring = [1 if q in on else 0 for q in _ring(p)]
    return sum(1 for i in range(8) if ring[i] == 0 and ring[(i + 1) % 8] == 1)


def _step(
    nbrs: dict[tuple[int, int], list[tuple[int, int]]],
    taken: set[tuple[int, int]],
    cur: tuple[int, int],
) -> tuple[int, int] | None:
    """The next pixel along, the one that touches the walk least.

    The pixel to go to is the one that sits beside the pixel the walk is on and
    nothing else it has passed. The pixel on the inside of a staircase corner
    touches the one before as well, and stepping onto it leaves the walk in a
    dead end that doubles back over itself.
    """
    ahead = [q for q in nbrs[cur] if q not in taken]
    if not ahead:
        return None
    return min(ahead, key=lambda q: sum(1 for r in nbrs[q] if r in taken and r != cur))


def _walk(
    nbrs: dict[tuple[int, int], list[tuple[int, int]]],
    nodes: set[tuple[int, int]],
    start: tuple[int, int],
    first: tuple[int, int],
) -> list[tuple[int, int]]:
    """Follow a chain from a node to the next node.

    A node beside the pixel the walk is on ends the walk there, even when the
    staircase puts that node next to the pixel before as well: stepping over
    it is how a chain came to run clean through a junction and be walked a
    second time from the far side. The node it set out from ends it too, once
    it has gone round: a bowl on a stem is a loop at the junction, and a walk
    that carried on past it would draw the stem again.
    """
    chain = [start, first]
    taken = {start, first}
    prev, cur = start, first
    while cur not in nodes:
        near = [
            q
            for q in nbrs[cur]
            if q in nodes
            and q != prev
            and (q not in chain or (q == start and len(chain) > MIN_LOOP))
        ]
        nxt = near[0] if near else _step(nbrs, taken, cur)
        if nxt is None:
            break
        prev, cur = cur, nxt
        taken.add(cur)
        chain.append(cur)
    return chain


def _again(
    chain: list[tuple[int, int]],
    seen: set[tuple[int, int]],
    ends: set[frozenset[tuple[int, int]]],
) -> bool:
    """Whether a walk has gone over a stroke an earlier walk already drew.

    A junction's pixel has a neighbour for every pixel of staircase leaving it,
    so one stroke can be set off along from two of them, and every stroke is
    walked once from each end. What the repeat has in common with the first
    walk is the run beyond its first step: the first pixel of a branch may sit
    beside another branch's, which is why a branch is only a repeat when the
    rest of it is already drawn, or, with nothing else of it to tell, when it
    joins the same two nodes as one already drawn.
    """
    inner = chain[1:-1]
    if len(inner) > 1:
        return _covered(inner[1:], seen) or _covered(inner[:-1], seen)
    return frozenset((chain[0], chain[-1])) in ends


def _covered(run: list[tuple[int, int]], seen: set[tuple[int, int]]) -> bool:
    """Whether every pixel of a run is a drawn pixel or touches one.

    Touching is enough because a walk back along a stroke takes the other
    pixel at each corner of the staircase.
    """
    return all(p in seen or any(q in seen for q in _ring(p)) for p in run)


def _loops(
    nbrs: dict[tuple[int, int], list[tuple[int, int]]],
    left: set[tuple[int, int]],
    done: set[tuple[int, int]],
) -> list[list[tuple[int, int]]]:
    """Closed loops with no junction at all, an `o` or an `0`, walked from what is left.

    `done` is every pixel already in a chain. A leftover that lies wholly
    beside them is the inner corners of a staircase and is not a loop.
    """
    out: list[list[tuple[int, int]]] = []
    while left:
        inside = {p: [q for q in nbrs[p] if q in left] for p in left}
        start = min(left)
        cur = next(iter(inside[start]), None)
        chain, taken = [start], {start}
        while cur is not None:
            chain.append(cur)
            taken.add(cur)
            if len(chain) > MIN_LOOP and start in inside[cur]:
                break
            cur = _step(inside, taken, cur)
        chain.append(start)
        # A walk steps over the inner pixel of every staircase corner, so what
        # is left after a loop has been traced is a scatter of single pixels
        # already covered by the line beside them. Emitted, each one is a
        # zero-length stroke, and the nib leaves a blot: that is where the
        # speckle round every curved letter came from. A leftover of `SPECKLE`
        # pixels or fewer is dropped; a real component is kept.
        if len(set(chain)) > SPECKLE and not all(any(q in done for q in nbrs[p]) for p in chain):
            out.append(chain)
            done.update(chain)
        left -= set(chain)
    return out


def skeleton_chains(skel: np.ndarray) -> list[list[tuple[int, int]]]:
    """The skeleton walked into chains, split at every junction.

    Args:
        skel: The one pixel skeleton.

    Returns:
        Chains of `(row, col)`, each running endpoint or junction to the next,
        then every closed loop that has no junction.
    """
    on = {(int(r), int(c)) for r, c in zip(*np.nonzero(skel), strict=True)}
    nbrs = {p: [q for q in _ring(p) if q in on] for p in on}
    cross = {p: crossings(p, on) for p in on}
    nodes = {p for p in on if cross[p] != PASSING}
    seen: set[tuple[int, int]] = set()
    ends: set[frozenset[tuple[int, int]]] = set()
    out: list[list[tuple[int, int]]] = []
    for node in sorted(nodes):
        for nb in nbrs[node]:
            chain = _walk(nbrs, nodes, node, nb)
            if _again(chain, seen, ends):
                continue
            seen.update(chain[1:-1])
            ends.add(frozenset((chain[0], chain[-1])))
            out.append(chain)
    left = on - {p for chain in out for p in chain}
    out.extend(_loops(nbrs, left, {p for chain in out for p in chain}))
    return out


def _leaves(chain: list[tuple[int, int]], node: tuple[int, int]) -> tuple[float, float]:
    """The unit direction a chain sets off in from one of its own ends."""
    run = chain if chain[0] == node else chain[::-1]
    (r0, c0), (r1, c1) = run[0], run[min(3, len(run) - 1)]
    d = math.hypot(r1 - r0, c1 - c0) or 1.0
    return ((r1 - r0) / d, (c1 - c0) / d)


def prune(chains: list[list[tuple[int, int]]], limit: float) -> list[list[tuple[int, int]]]:
    """Drop the short branches thinning grows at joins and at terminals.

    A short branch that carries straight on from another branch at its junction
    is not one of those: it is the end of a stem that runs on past where
    something joins it, the top of an `n` or the foot of a `d`, and it stays.
    """
    ends: dict[tuple[int, int], int] = {}
    for chain in chains:
        for p in (chain[0], chain[-1]):
            ends[p] = ends.get(p, 0) + 1
    keep = []
    for chain in chains:
        spur = ends.get(chain[0], 0) == 1 or ends.get(chain[-1], 0) == 1
        if spur and len(chain) < limit and len(chains) > 1 and not _carries_on(chain, chains, ends):
            continue
        keep.append(chain)
    return keep or chains


def _carries_on(
    chain: list[tuple[int, int]],
    chains: list[list[tuple[int, int]]],
    ends: dict[tuple[int, int], int],
) -> bool:
    """Whether a spur runs straight on from another branch at its junction."""
    node = chain[-1] if ends.get(chain[0], 0) == 1 else chain[0]
    if ends.get(node, 0) < PASSING + 1:
        return False
    mine = _leaves(chain, node)
    for other in chains:
        if other is chain or node not in (other[0], other[-1]):
            continue
        theirs = _leaves(other, node)
        if mine[0] * theirs[0] + mine[1] * theirs[1] <= THROUGH_DOT:
            return True
    return False


def components(img: np.ndarray) -> list[list[tuple[int, int]]]:
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
