"""Strokes from a glyph: the centreline route and the outline route.

`CENTRELINE` thins the glyph to a skeleton (`letters.skeleton`), traces it into
chains, prunes its spurs and pushes its ends back out to where the ink actually
stopped. Draw that with a nib and the letter is written. `OUTLINE` is the
glyph's own flattened contours, drawn as closed strokes with a fine pen: nothing
is derived and nothing can go wrong with it; the letter reads as drawn round
rather than written. The two are different enough to be two answers rather than
one answer and its fallback.

Where thinning merges two strokes into one mass, `_flanks` gives the arm back
off the width of the ink, and `_dots` draws a blob thinning ate whole as a small
ring. Paths come back in em units with y up. This module does not open fonts
and does not choose a route; `letters.font` does.
"""

from __future__ import annotations

import math

import numpy as np

from pyntpot.ink.noise import edt
from pyntpot.ink.polyline import Pt, normals
from pyntpot.letters.skeleton import (
    RASTER_EM,
    _chains,
    _components,
    _crossings,
    _fill,
    _prune,
    thin,
)

#: How the glyph is turned into something a pen can follow.
CENTRELINE = "centreline"
OUTLINE = "outline"

#: A branch shorter than this share of an em, hanging off a junction, is a
#: thinning artefact rather than a stroke, and is pruned.
SPUR_EM = 0.075

#: Two branches leaving a junction whose directions are at least this opposed
#: are one stroke passing through it rather than two meeting in it.
THROUGH_DOT = -0.72

#: A flank is only drawn where the ink on that side of a through-stroke stands
#: this much further out than the stroke's own half-width, in half-widths. Under
#: it the two strokes are the same line and drawing both says nothing.
FLANK_MIN = 0.40

#: How far out a flank is allowed to be pushed, in half-widths, so a ray that
#: runs the length of a stem rather than across a stroke cannot throw one out
#: of the letter.
FLANK_CAP = 2.2

#: A component of ink whose skeleton comes back empty is a dot. It is drawn as
#: a small ring of this share of its own inscribed radius, because a nib run
#: round a tiny circle leaves a dot and a nib asked to draw a single point
#: leaves nothing at all.
DOT_FRAC = 0.45

#: A run of fewer points than this is too short to have a side to flank.
MIN_RUN = 4

#: A flank must stand apart from its stroke for at least this many points.
MIN_APART = 3

#: A junction of at least this many arms can have a stroke passing through it.
JUNCTION_ARMS = 3

#: A chain of fewer points than this is not a stroke.
MIN_STROKE = 2

#: A run of fewer points than this has no direction to push an end along.
MIN_EXTENDABLE = 3


def _half_width(skel: np.ndarray, reach: np.ndarray) -> float:
    """The glyph's own stroke half-width, in raster pixels.

    The median over the skeleton rather than the mean: a junction and a
    terminal both sit in more ink than a stroke does, and there are enough of
    them in a letter to drag a mean but never a median.
    """
    vals = reach[skel > 0]
    return float(np.median(vals)) if vals.size else 1.0


def _radii(pts: list[Pt], reach: np.ndarray) -> list[float]:
    """The inscribed radius under each point of a run, in raster pixels."""
    h, w = reach.shape
    out = []
    for x, y in pts:
        r = min(max(int(y), 0), h - 1)
        c = min(max(int(x), 0), w - 1)
        out.append(float(reach[r, c]))
    return out


def _edge(img: np.ndarray, at: Pt, along: Pt, cap: float) -> float:
    """How far the ink reaches from a point in one direction, up to `cap`."""
    h, w = img.shape
    step = 0.5
    d = 0.0
    while d < cap:
        x = at[0] + along[0] * (d + step)
        y = at[1] + along[1] * (d + step)
        r, c = int(y), int(x)
        if not (0 <= r < h and 0 <= c < w) or not img[r, c]:
            break
        d += step
    return d


def _flank(pts: list[Pt], img: np.ndarray, half: float, side: float) -> list[Pt] | None:
    """The second stroke hiding on one side of a run, or None if there is none.

    Where two strokes of a letter run together along their length rather
    than crossing, the ink is one mass and its medial axis is one line up the
    middle, so the thinner hands back one stroke where the designer drew two.
    In Patrick Hand's capital M the bowl's arms merge into the stems from the
    cap line down to about half the height, and the skeleton alone is two full
    stems joined by a shallow curve sitting exactly where an H's crossbar
    sits, so the M reads as an H.

    The mass gives the arm back. Along the stem, the ink on the arm's side
    stands further out than the stem's own half-width, by exactly the sliver
    the arm is; a stroke laid half a width inside that edge is the arm, and it
    tapers to nothing where the two really are one line.

    Args:
        pts: The through-stroke, in raster pixels, running away from the
            junction the other branch met it at.
        img: The filled glyph.
        half: The glyph's own stroke half-width.
        side: +1 or -1, which side of the run the other branch came from.

    Returns:
        The flanking stroke, or None when the ink on that side is no wider
        than one stroke and there is nothing to recover.
    """
    if len(pts) < MIN_RUN:
        return None
    cap = half * FLANK_CAP
    norms = normals(pts)
    raw = []
    for (x, y), (nx, ny) in zip(pts, norms, strict=True):
        reach = _edge(img, (x, y), (nx * side, ny * side), cap)
        raw.append(max(reach - half, 0.0))
    n = len(raw)
    lift = [sum(raw[max(i - 2, 0) : i + 3]) / len(raw[max(i - 2, 0) : i + 3]) for i in range(n)]
    if max(lift) < half * FLANK_MIN:
        return None
    # Only the stretch where the two strokes are actually apart. Carried to the
    # far end of the through-stroke the flank would lie exactly on top of it,
    # which is a second helping of ink and nothing else: that is what thickened
    # the bowl of every b, q and 6 on the first attempt.
    floor = half * FLANK_MIN * 0.5
    last = max((i for i, v in enumerate(lift) if v > floor), default=0)
    if last < MIN_APART:
        return None
    return [
        (x + nx * side * lift[i], y + ny * side * lift[i])
        for i, ((x, y), (nx, ny)) in enumerate(zip(pts[: last + 1], norms[: last + 1], strict=True))
    ]


def _arms(
    kept: list[tuple[list[tuple[int, int]], list[Pt]]],
) -> dict[tuple[int, int], list[list[Pt]]]:
    """Every open run, oriented to leave each of its end nodes, grouped by node."""
    ends: dict[tuple[int, int], list[list[Pt]]] = {}
    for chain, run in kept:
        if chain[0] == chain[-1] or len(run) < MIN_RUN:
            continue
        for node, out_run in ((chain[0], run), (chain[-1], run[::-1])):
            ends.setdefault(node, []).append(_from(node, out_run))
    return ends


def _flanks(
    kept: list[tuple[list[tuple[int, int]], list[Pt]]], ink: np.ndarray, half: float
) -> list[list[Pt]]:
    """Every stroke that merged into another one, recovered at its junction.

    A junction where one branch runs into a stroke passing straight through is
    the shape a merge leaves behind: the through-stroke is the pair of branches
    leaving in nearly opposite directions, and the odd branch is the one whose
    far half has been swallowed. Each half of the through-stroke is asked for a
    flank on the odd branch's side, and answers None wherever the two really
    are one line.

    Args:
        kept: Each traced chain and the run of points it became.
        ink: The filled glyph as a boolean mask.
        half: The glyph's own stroke half-width.

    Returns:
        The recovered strokes, in raster pixels.
    """
    out: list[list[Pt]] = []
    for arms in _arms(kept).values():
        if len(arms) < JUNCTION_ARMS:
            continue
        dirs = [_leaving(a) for a in arms]
        pair = max(
            ((i, j) for i in range(len(arms)) for j in range(i + 1, len(arms))),
            key=lambda ij: -(dirs[ij[0]][0] * dirs[ij[1]][0] + dirs[ij[0]][1] * dirs[ij[1]][1]),
        )
        p, q = pair
        if dirs[p][0] * dirs[q][0] + dirs[p][1] * dirs[q][1] > THROUGH_DOT:
            continue
        for k in range(len(arms)):
            if k in (p, q):
                continue
            for t in (p, q):
                cross = dirs[t][0] * dirs[k][1] - dirs[t][1] * dirs[k][0]
                got = _flank(arms[t], ink, half, 1.0 if cross > 0 else -1.0)
                if got:
                    out.append(got)
    return out


def _from(node: tuple[int, int], run: list[Pt]) -> list[Pt]:
    """A run oriented to start at one of its own end nodes."""
    at = (node[1] + 0.5, node[0] + 0.5)
    if math.dist(run[0], at) <= math.dist(run[-1], at):
        return run
    return run[::-1]


def _leaving(run: list[Pt]) -> Pt:
    """The unit direction a run sets off in from its own first point."""
    a, b = run[0], run[min(3, len(run) - 1)]
    d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def _dots(img: np.ndarray, reach: np.ndarray, drawn: set[tuple[int, int]]) -> list[list[Pt]]:
    """A ring for every blob of ink the thinning ate whole.

    Zhang-Suen deletes a small round component from both sides at once and
    leaves nothing behind, so without this the tittle of an `i` and a `j` and
    the whole of a full stop are missing from the sheet. A blob is drawn as a
    small ring rather than a point, because a nib asked to draw one point
    leaves no mark at all.
    """
    out: list[list[Pt]] = []
    for blob in _components(img):
        if any(p in drawn for p in blob):
            continue
        rows = [r for r, _c in blob]
        cols = [c for _r, c in blob]
        cx = (min(cols) + max(cols)) / 2.0 + 0.5
        cy = (min(rows) + max(rows)) / 2.0 + 0.5
        rad = max(float(max(reach[r, c] for r, c in blob)) * DOT_FRAC, 0.6)
        out.append(
            [
                (cx + rad * math.cos(t * math.tau / 12), cy + rad * math.sin(t * math.tau / 12))
                for t in range(13)
            ]
        )
    return out


def _centrelines(contours: list[list[Pt]], upem: int) -> list[list[Pt]]:
    """One glyph's skeleton, in em units with y up.

    The free ends are pushed back out along their own direction by the
    distance the thinning ate: a medial axis stops half a stroke width short of
    the ink, so an unextended skeleton draws an `l` shorter than the letter is.
    Runs that stand in more ink than one stroke is wide are split back into the
    two strokes that made them, and a blob the thinning ate whole comes back as
    a dot.
    """
    img, ox, oy = _fill(contours, upem)
    skel = thin(img)
    # Distance from an inked pixel to the nearest blank one, which at a
    # terminal is half the stroke's own width: exactly what thinning ate.
    reach = edt(img == 0)
    k = upem / RASTER_EM
    half = _half_width(skel, reach) if skel.any() else 1.0
    on = {(int(r), int(c)) for r, c in zip(*np.nonzero(skel), strict=True)}
    free = {p for p in on if _crossings(p, on) <= 1}
    runs: list[list[Pt]] = []
    drawn: set[tuple[int, int]] = set()
    kept: list[tuple[list[tuple[int, int]], list[Pt]]] = []
    for chain in _prune(_chains(skel), SPUR_EM * RASTER_EM):
        pts = [(c + 0.5, r + 0.5) for r, c in chain]
        if len(pts) < MIN_STROKE:
            continue
        drawn.update(chain)
        run = _extend(pts, chain, reach, free)
        runs.append(run)
        kept.append((chain, run))
    runs.extend(_flanks(kept, img > 0, half))
    runs.extend(_dots(img, reach, drawn))
    return [[((x * k + ox) / upem, (y * k + oy) / upem) for x, y in run] for run in runs]


def _extend(
    pts: list[Pt], chain: list[tuple[int, int]], inside: np.ndarray, free: set[tuple[int, int]]
) -> list[Pt]:
    """Push a free end out to where the ink stops, along the chain's own run.

    Only a free end. A chain that stops at a junction stops there because
    another stroke starts, and the inscribed disc at a junction is as wide as
    every stroke meeting in it, so pushing that end out by the disc would
    throw a long spike clean out of the letter, a star at the top of every M
    and W.
    """
    if chain[0] == chain[-1] or len(pts) < MIN_EXTENDABLE:
        return pts
    h, w = inside.shape
    out = list(pts)
    for at, look in ((0, 2), (-1, -3)):
        r, c = chain[at]
        if (r, c) not in free:
            continue
        if not (0 <= r < h and 0 <= c < w):
            continue
        reach = float(inside[r, c])
        if reach < 1.0:
            continue
        ax, ay = out[at]
        bx, by = out[look]
        run = math.hypot(ax - bx, ay - by) or 1.0
        step = ((ax - bx) / run * reach, (ay - by) / run * reach)
        end = (ax + step[0], ay + step[1])
        if at == 0:
            out.insert(0, end)
        else:
            out.append(end)
    return out
