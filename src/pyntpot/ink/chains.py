"""Chaining polylines: join pieces whose ends meet into as few lines as possible.

Key functions: `join_chains`, pieces sharing an endpoint chained greedily in
pool order until each closes or nothing meets it; `join_strokes`, open pieces
chained head to tail through a grid of their ends; `chain_lines`, ends matched
per axis on arrays of points; `joined`, `chain_lines` over point lists.

The three joiners are different algorithms with different tolerance handling,
not one algorithm three times: each keeps the order and tie-breaking its
callers were measured with. None of them simplifies, smooths or reorders the
points within a piece, and none of them drops a chain for being short: a
caller that wants only rings filters the chains itself.

Invariants: a piece is used at most once; every input piece with two or more
points ends up in exactly one output chain.
"""

import math
from collections.abc import Callable

import numpy as np

from pyntpot.ink.polyline import Pt

#: The fewest lines there must be for any two of them to chain.
_FEWEST_TO_CHAIN = 2


def join_strokes(lines: list[list[Pt]], tol: float = 1.0) -> list[list[Pt]]:
    """Chain open polylines head to tail wherever their ends meet.

    OSM cuts a road at every junction, every bridge and every change of tag, so
    what a person calls one street arrives as dozens of ways. The lettering
    already gathers them (`labels.pick_roads`, "a numbered road is one road");
    the painting did not, and painting them apart is what made the map look
    broken. Each piece was a stroke of its own: a nib set down with a blot,
    tapered to a point at both ends, and lifted again. A median piece of 2.5
    display pixels against a 30 px lift is all taper and blot and never a line,
    and thousands of such pieces can stand in for a few hundred roads.

    Unlike `join_chains` it looks for meeting ends through a grid of cells
    rather than in pool order, and grows the whole tail and then the whole head
    without stopping when the chain closes on itself.

    Args:
        lines: Polylines in metres. Only ones that belong together should be
            passed in one call, because anything whose ends meet will join.
        tol: Metres within which two endpoints are the same node.

    Returns:
        The chains, each as one polyline.
    """
    cell = max(tol, 1e-6)

    def near(p: Pt) -> list[int]:
        """Every piece with an end in this point's cell or the eight round it."""
        cx, cy = int(p[0] // cell), int(p[1] // cell)
        out: list[int] = []
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                out += at.get((gx, gy), ())
        return out

    live = {i: list(line) for i, line in enumerate(lines) if len(line) > 1}
    at: dict[tuple[int, int], list[int]] = {}
    for i, line in live.items():
        for p in (line[0], line[-1]):
            at.setdefault((int(p[0] // cell), int(p[1] // cell)), []).append(i)
    out: list[list[Pt]] = []
    while live:
        start, chain = live.popitem()
        # The tail first, then the head, so a piece taken from the middle of a
        # street still grows out to both of its ends.
        for head in (False, True):
            chain = _grow_end(chain, start, live, near, tol, head=head)
        out.append(chain)
    return out


def _grow_end(
    chain: list[Pt],
    start: int,
    live: dict[int, list[Pt]],
    near: Callable[[Pt], list[int]],
    tol: float,
    *,
    head: bool,
) -> list[Pt]:
    """Grow one end of a chain from the live pieces until nothing more meets it.

    A piece that joins is taken out of `live`.
    """
    grow = True
    while grow:
        grow = False
        tip = chain[0] if head else chain[-1]
        for j in near(tip):
            if j == start or j not in live:
                continue
            got = _attach(chain, tip, live[j], tol, head=head)
            if got is None:
                continue
            chain = got
            del live[j]
            grow = True
            break
    return chain


def _attach(chain: list[Pt], tip: Pt, cand: list[Pt], tol: float, *, head: bool) -> list[Pt] | None:
    """The chain with a piece joined at its head or tail, or None when it does not meet."""
    if head and math.dist(tip, cand[-1]) <= tol:
        return cand[:-1] + chain
    if head and math.dist(tip, cand[0]) <= tol:
        return list(reversed(cand))[:-1] + chain
    if not head and math.dist(tip, cand[0]) <= tol:
        return chain + cand[1:]
    if not head and math.dist(tip, cand[-1]) <= tol:
        return chain + list(reversed(cand))[1:]
    return None


def join_chains(lines: list[list[Pt]], tol: float) -> list[list[Pt]]:
    """Chain polylines that share an endpoint into as few pieces as possible.

    Greedy: the last piece is taken from the pool and grown, at either end, by
    the first piece in pool order whose end meets it, until nothing meets it or
    it has closed on itself. A chain that closes is a ring; one that does not
    stays open. Unlike `join_strokes` it stops growing a chain once it closes
    and searches the pool in order rather than through a grid of ends.

    Two callers depend on it. Overpass hands a multipolygon relation back as
    loose member ways, and treating each one as its own ring is what left a
    large wood unshaded: the outer boundary is split across dozens of ways and
    not one of them closes. And a saddle cell hands marching squares two
    segments through one vertex, so a ring that crosses one comes back as two
    open chains; closing each of those with a straight line draws a chord
    across the map that can leave a wedge of land lying over the sea.

    Args:
        lines: Polylines, in whatever space they were traced. They are copied,
            never changed.
        tol: Distance within which two endpoints are the same point.

    Returns:
        The joined polylines, closed rings and open chains alike.
    """
    pool = [list(line) for line in lines if len(line) > 1]
    out: list[list[Pt]] = []
    while pool:
        chain = pool.pop()
        joined = True
        while joined and math.dist(chain[0], chain[-1]) > tol:
            joined = False
            for i, cand in enumerate(pool):
                if math.dist(chain[-1], cand[0]) <= tol:
                    chain = chain + cand[1:]
                elif math.dist(chain[-1], cand[-1]) <= tol:
                    chain = chain + list(reversed(cand))[1:]
                elif math.dist(chain[0], cand[-1]) <= tol:
                    chain = cand[:-1] + chain
                elif math.dist(chain[0], cand[0]) <= tol:
                    chain = list(reversed(cand))[:-1] + chain
                else:
                    continue
                pool.pop(i)
                joined = True
                break
        out.append(chain)
    return out


def joined(parts: list[list[Pt]], tol: float = 8.0) -> list[list[Pt]]:
    """One road's pieces chained end to end, so a name has a road to sit on.

    OSM cuts a road at every junction and every change of surface, so a street
    arrives as fifteen fragments none of which is longer than the name written
    on it. The painter already chains ways for the brush; the same thing has to
    happen before a road is judged too short to letter.

    Unlike `join_chains` and `join_strokes` it is `chain_lines` underneath: ends
    meet within the tolerance on each axis, and a shared end is kept twice.
    """
    chained = chain_lines([np.asarray(part, float) for part in parts], tol)
    return [[(float(x), float(y)) for x, y in c] for c in chained] or parts


def chain_lines(lines: list[np.ndarray], tol: float) -> list[np.ndarray]:
    """Join polylines that meet end to end, so one road is one mark.

    OSM splits a road wherever a tag changes, so what arrives is a heap of
    short ways rather than a line: a woodland plate's A road is 43 of them, 25
    under 60 render pixels. Stamped separately each one takes a fresh tip
    pattern, a fresh set-down blob and a lift taper at both ends, and the road
    comes out as a chain of tapered lozenges with a bead at every join. Joined
    first, it is one stroke, which is also what a painter would have drawn.

    Greedy and deterministic: the ways are walked in the order they arrive,
    each is extended from its tail and then from its head, and a way is used
    once. A junction where three ways meet takes whichever arrived first, which
    is the honest answer with no more information than an endpoint.

    Unlike `join_chains` and `join_strokes` it takes two ends to meet when they
    are within the tolerance on each axis rather than by distance, and it
    concatenates the arrays whole, so a shared end appears twice.

    Args:
        lines: The polylines, in render pixels.
        tol: How close two ends have to be to be the same mark, in pixels.

    Returns:
        The chains, each a single polyline.
    """
    if len(lines) < _FEWEST_TO_CHAIN or tol <= 0:
        return list(lines)
    q = max(tol, 0.1)
    ends: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for i, ln in enumerate(lines):
        for e, p in ((0, ln[0]), (1, ln[-1])):
            ends.setdefault((round(p[0] / q), round(p[1] / q)), []).append((i, e))
    used = [False] * len(lines)

    def hook(p: np.ndarray) -> tuple[int, int] | None:
        """An unused end within the tolerance of this point."""
        return _free_end(p, lines, ends, used, q)

    out: list[np.ndarray] = []
    for i0 in range(len(lines)):
        if used[i0]:
            continue
        used[i0] = True
        chain = [lines[i0]]
        while (hit := hook(chain[-1][-1])) is not None:
            i, e = hit
            used[i] = True
            chain.append(lines[i] if e == 0 else lines[i][::-1])
        while (hit := hook(chain[0][0])) is not None:
            i, e = hit
            used[i] = True
            chain.insert(0, lines[i][::-1] if e == 0 else lines[i])
        out.append(np.concatenate(chain) if len(chain) > 1 else chain[0])
    return out


def _free_end(
    p: np.ndarray,
    lines: list[np.ndarray],
    ends: dict[tuple[int, int], list[tuple[int, int]]],
    used: list[bool],
    q: float,
) -> tuple[int, int] | None:
    """An unused end within the tolerance of this point."""
    kx, ky = round(p[0] / q), round(p[1] / q)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for i, e in ends.get((kx + dx, ky + dy), ()):
                if used[i]:
                    continue
                o = lines[i][0] if e == 0 else lines[i][-1]
                if abs(o[0] - p[0]) <= q and abs(o[1] - p[1]) <= q:
                    return i, e
    return None
