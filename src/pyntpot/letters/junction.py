"""Strokes joined where a pen would not lift: the arms that run straight on through a junction.

`join_through` takes the runs traced from a glyph's skeleton chains and makes one
stroke of any two that leave a junction in nearly opposite directions, so a stem
is written top to bottom in one go and a crossing is two strokes, not four.
`leaving` is the direction a run sets off in. Junction pixels a few pixels apart
are one junction, and so are two junctions joined by a run shorter than a stroke
is wide: thinning draws an `X` as two forks and a short bridge between them.
This module does not trace and does not draw.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING

from pyntpot.letters.skeleton import THROUGH_DOT

if TYPE_CHECKING:
    from pyntpot.ink.polyline import Point

#: A junction of at least this many arms can have a stroke passing through it.
JUNCTION_ARMS = 3

#: How many points along a run its direction is read at when two are to be joined,
#: far enough that the kink a junction pixel leaves does not turn it.
LOOK = 8

#: Junction pixels this close, in raster pixels, are one crossing.
JOIN_PX = 3

#: A junction with this many arms left can still have a stroke passing through it.
MIN_PAIR = 2


def leaving(run: list[Point], look: int = 3) -> Point:
    """The unit direction a run sets off in from its own first point."""
    a, b = run[0], run[min(look, len(run) - 1)]
    d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


@dataclass
class _Piece:
    """A run and the two junction pixels it runs between."""

    start: tuple[int, int]
    end: tuple[int, int]
    pts: list[Point]

    def reversed(self) -> _Piece:
        """The same run, walked the other way."""
        return _Piece(self.end, self.start, self.pts[::-1])


def _junctions(nodes: set[tuple[int, int]]) -> dict[tuple[int, int], tuple[int, int]]:
    """Each junction pixel mapped to the first of the pixels it is crowded with.

    A crossing of two strokes is rarely one pixel: the skeleton has two or three
    side by side, and a stroke ends at whichever it reached. Pixels within
    `JOIN_PX` of each other are one junction.
    """
    group: dict[tuple[int, int], tuple[int, int]] = {}
    for seed in sorted(nodes):
        if seed in group:
            continue
        stack = [seed]
        group[seed] = seed
        while stack:
            r, c = stack.pop()
            for q in nodes:
                if q not in group and max(abs(q[0] - r), abs(q[1] - c)) <= JOIN_PX:
                    group[q] = seed
                    stack.append(q)
    return group


def _bridged(
    pieces: dict[int, _Piece], group: dict[tuple[int, int], tuple[int, int]], bridge: float
) -> None:
    """Make one junction of two that a run shorter than `bridge` joins, and drop the run.

    Where two strokes cross at a shallow angle thinning does not meet them in
    one pixel: it forks twice and joins the forks with a short run, the bridge
    in the waist of an `8`. Drawn, the bridge is a stroke of its own across the
    crossing. Both ends must be junctions of `JUNCTION_ARMS` arms or more, so a
    short stroke that ends free is never taken for one. `pieces` and `group`
    are changed in place.
    """
    while True:
        arms: dict[tuple[int, int], int] = {}
        for piece in pieces.values():
            for at in (piece.start, piece.end):
                arms[group[at]] = arms.get(group[at], 0) + 1
        short = [
            i
            for i, piece in pieces.items()
            if group[piece.start] != group[piece.end]
            and arms[group[piece.start]] >= JUNCTION_ARMS
            and arms[group[piece.end]] >= JUNCTION_ARMS
            and sum(math.dist(a, b) for a, b in pairwise(piece.pts)) < bridge
        ]
        if not short:
            return
        piece = pieces.pop(short[0])
        keep, gone = group[piece.start], group[piece.end]
        for node, of in group.items():
            if of == gone:
                group[node] = keep


def join_through(
    kept: list[tuple[list[tuple[int, int]], list[Point]]], bridge: float
) -> list[list[Point]]:
    """The runs, with the two that run straight on through a junction made one.

    A pen writes a stem top to bottom in one go. Left as two strokes that meet
    at the junction, each tapers where it ends and the stem is thin at the
    very place it is joined: a letter with a waist, or a tick that has come
    away from its stem. At every junction the pair of arms leaving in nearly
    opposite directions is joined, and a crossing of two strokes, a `t` or an
    `f`, joins both of its pairs. A run that leaves a junction and comes back
    to it straight on, as the two strokes of an `8` do once joined through its
    waist, is closed into a ring.

    Args:
        kept: Each traced chain and the run of points it became.
        bridge: A run shorter than this, in raster pixels, between two
            junctions is a bridge across one crossing (`_bridged`): a stroke's
            width.

    Returns:
        The runs, fewer than there were wherever strokes were joined.
    """
    pieces: dict[int, _Piece] = {
        i: _Piece(chain[0], chain[-1], list(run)) for i, (chain, run) in enumerate(kept)
    }
    group = _junctions({n for chain, _run in kept for n in (chain[0], chain[-1])})
    # What runs from a junction pixel to its neighbour in the same crossing is
    # part of the crossing, not a stroke.
    for i in [
        i
        for i, piece in pieces.items()
        if group[piece.start] == group[piece.end] and len(piece.pts) <= JOIN_PX * 2
    ]:
        del pieces[i]
    _bridged(pieces, group, bridge)
    for node in sorted(set(group.values())):
        arms = [
            (i, end)
            for i, piece in pieces.items()
            for end, at in enumerate((piece.start, piece.end))
            if group[at] == node
        ]
        if len(arms) < JUNCTION_ARMS:
            continue
        while len(arms) >= MIN_PAIR:
            dirs = {
                arm: leaving(pieces[arm[0]].pts if arm[1] == 0 else pieces[arm[0]].pts[::-1], LOOK)
                for arm in arms
            }
            dots = [
                (dirs[a][0] * dirs[b][0] + dirs[a][1] * dirs[b][1], a, b)
                for a in arms
                for b in arms
                if a[0] < b[0]
            ]
            if not dots:
                break
            dot, a, b = min(dots)
            if dot > THROUGH_DOT:
                break
            into = pieces[a[0]] if a[1] == 1 else pieces[a[0]].reversed()
            onward = pieces[b[0]] if b[1] == 0 else pieces[b[0]].reversed()
            joined = _Piece(into.start, onward.end, [*into.pts, *onward.pts[1:]])
            pieces[a[0]] = _closed(joined, group, node)
            del pieces[b[0]]
            arms = [m for m in arms if m[0] not in (a[0], b[0])]
    return [piece.pts for piece in pieces.values()]


def _closed(
    piece: _Piece, group: dict[tuple[int, int], tuple[int, int]], node: tuple[int, int]
) -> _Piece:
    """A joined run closed into a ring when both its ends are at `node` and meet straight on."""
    if group[piece.start] != node or group[piece.end] != node:
        return piece
    out = leaving(piece.pts, LOOK)
    back = leaving(piece.pts[::-1], LOOK)
    if out[0] * back[0] + out[1] * back[1] > THROUGH_DOT:
        return piece
    return _Piece(piece.start, piece.start, [*piece.pts, piece.pts[0]])
