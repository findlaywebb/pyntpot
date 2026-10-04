"""Drawable paths from a real typeface, so the map is lettered in a designed hand.

A stroke font gives a skeleton and nothing else: the proportions are the
plotter's, not a designer's. A handwriting face has proportions somebody drew,
and this module takes them off the glyph outlines and hands back polylines a
pen can be run along. Two routes, and they look different enough to be two
answers rather than one answer and its fallback.

**Centreline.** The glyph is filled on a small grid, thinned to a one pixel
skeleton, traced into chains, its spurs pruned and its ends pushed back out to
where the ink actually stopped. Draw that with a nib and the letter is written.
Thinning is the risk in the whole module: a medial axis forks at every join and
every terminal, and no amount of pruning makes a fork that should not be there
into one that should.

**Outline contour.** The glyph's own contours, flattened, drawn as closed
strokes with a fine pen. Nothing is derived and nothing can go wrong with it;
the letter reads as drawn round rather than written, which is a different and
perfectly good thing for a map to do.

The face is vendored under `fonts/` with its licence beside it. It is Patrick
Hand, SIL Open Font License 1.1: an upright, unjoined print hand with even
proportions and a large x-height. A looping connected script is too scripty
and ornate for a map, however well it is drawn. Patrick Hand is the opposite
end of the same shelf.
"""

from __future__ import annotations

import functools
import math
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import numpy as np

from pyntpot.ink.polyline import normals

Pt = tuple[float, float]

#: The vendored face and its licence.
DEFAULT_FONT = Path(str(resources.files("pyntpot._port") / "fonts" / "PatrickHand-Regular.ttf"))

#: How the glyph is turned into something a pen can follow.
CENTRELINE = "centreline"
OUTLINE = "outline"

#: Em units the glyph is rasterised at before it is thinned. Big enough that a
#: thin stroke is several pixels across, small enough that the walk stays
#: milliseconds a glyph, and every glyph is cached anyway.
RASTER_EM = 128

#: A curve is flattened to this many straight pieces. A letter is read at about
#: 14 pixels and never measured, so the tolerance that matters is the eye's.
CURVE_STEPS = 8

#: A branch shorter than this share of an em, hanging off a junction, is a
#: thinning artefact rather than a stroke. Pruned.
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


# --------------------------------------------------------------------------- outlines


class _Flatten:
    """A pen that records one glyph's contours as flattened polylines."""

    def __init__(self) -> None:
        """Start with nothing recorded."""
        self.contours: list[list[Pt]] = []
        self._cur: list[Pt] = []
        self._start: Pt = (0.0, 0.0)

    def moveTo(self, pt: Pt) -> None:  # noqa: N802 (the pen protocol's name)
        """Start a contour."""
        self._flush()
        self._cur = [(float(pt[0]), float(pt[1]))]
        self._start = self._cur[0]

    def lineTo(self, pt: Pt) -> None:  # noqa: N802
        """A straight piece."""
        if not self._cur:
            return
        self._cur.append((float(pt[0]), float(pt[1])))

    def curveTo(self, *pts: Pt) -> None:  # noqa: N802
        """A cubic, or the higher-order form fontTools hands a pen."""
        if len(pts) == 2:
            self.qCurveTo(*pts)
            return
        if not self._cur:
            return
        a = self._cur[-1]
        for i in range(0, len(pts) - 1, 2):
            b, c = pts[i], pts[i + 1]
            d = pts[i + 2] if i + 2 < len(pts) else pts[-1]
            self._cubic(a, b, c, d)
            a = self._cur[-1]

    def qCurveTo(self, *pts: Pt) -> None:  # noqa: N802
        """A quadratic run, with TrueType's implied on-curve points.

        A contour with no on-curve point at all is written as a run ending in
        None, and it arrives without a `moveTo` of its own, so it starts at the
        midpoint between its last control point and its first.
        """
        if pts and pts[-1] is None:
            self._all_off([(float(p[0]), float(p[1])) for p in pts[:-1]])
            return
        if not self._cur:
            return
        a = self._cur[-1]
        pts = tuple((float(p[0]), float(p[1])) for p in pts if p is not None) or (a,)
        for i in range(len(pts) - 1):
            ctrl = pts[i]
            nxt = pts[i + 1]
            end = nxt if i == len(pts) - 2 else ((ctrl[0] + nxt[0]) / 2, (ctrl[1] + nxt[1]) / 2)
            self._quad(a, ctrl, end)
            a = end

    def closePath(self) -> None:  # noqa: N802
        """Close the contour back onto its own first point."""
        if self._cur and self._cur[-1] != self._start:
            self._cur.append(self._start)
        self._flush()

    def endPath(self) -> None:  # noqa: N802
        """An open contour, which a glyph should not have but might."""
        self._flush()

    def addComponent(self, name: str, transform: Any) -> None:  # noqa: N802
        """Components are decomposed before the pen sees them."""

    def _all_off(self, ctrls: list[Pt]) -> None:
        """A closed contour made only of control points."""
        if len(ctrls) < 2:
            return
        self._flush()
        start = ((ctrls[-1][0] + ctrls[0][0]) / 2, (ctrls[-1][1] + ctrls[0][1]) / 2)
        self._cur = [start]
        self._start = start
        a = start
        for i, ctrl in enumerate(ctrls):
            nxt = ctrls[(i + 1) % len(ctrls)]
            end = start if i == len(ctrls) - 1 else ((ctrl[0] + nxt[0]) / 2, (ctrl[1] + nxt[1]) / 2)
            self._quad(a, ctrl, end)
            a = end
        self.closePath()

    def _quad(self, a: Pt, b: Pt, c: Pt) -> None:
        """One quadratic, flattened."""
        for i in range(1, CURVE_STEPS + 1):
            t = i / CURVE_STEPS
            u = 1.0 - t
            self._cur.append(
                (
                    u * u * a[0] + 2 * u * t * b[0] + t * t * c[0],
                    u * u * a[1] + 2 * u * t * b[1] + t * t * c[1],
                )
            )

    def _cubic(self, a: Pt, b: Pt, c: Pt, d: Pt) -> None:
        """One cubic, flattened."""
        for i in range(1, CURVE_STEPS + 1):
            t = i / CURVE_STEPS
            u = 1.0 - t
            self._cur.append(
                (
                    u**3 * a[0] + 3 * u * u * t * b[0] + 3 * u * t * t * c[0] + t**3 * d[0],
                    u**3 * a[1] + 3 * u * u * t * b[1] + 3 * u * t * t * c[1] + t**3 * d[1],
                )
            )

    def _flush(self) -> None:
        """Keep whatever contour is open."""
        if len(self._cur) > 2:
            self.contours.append(self._cur)
        self._cur = []


@dataclass
class Glyph:
    """One character, ready to be drawn.

    `paths` are in em units with the baseline at y zero and the pen starting at
    x zero, y up. `advance` is in the same units, so a caller multiplies both
    by the type size and never thinks about the font again.
    """

    ch: str
    advance: float
    paths: list[list[Pt]]

    @property
    def ink(self) -> bool:
        """Whether this glyph puts anything on the paper."""
        return bool(self.paths)


# --------------------------------------------------------------------------- thinning


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
    w = int(math.ceil((max(xs) - x0) * k)) + 2 * pad + 1
    h = int(math.ceil((max(ys) - y0) * k)) + 2 * pad + 1
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
            lo = int(math.ceil(cuts[i] - 0.5))
            hi = int(math.floor(cuts[i + 1] - 0.5))
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
            kill = (out == 1) & (count >= 2) & (count <= 6) & (turns == 1) & (c1 == 0) & (c2 == 0)
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
    nodes = {p for p in on if cross[p] != 2}
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    out: list[list[tuple[int, int]]] = []

    def step(prev: tuple[int, int], cur: tuple[int, int]) -> tuple[int, int] | None:
        """The next pixel along, ignoring the one the staircase came from."""
        back = set(nbrs[prev]) | {prev}
        ahead = [q for q in nbrs[cur] if q not in back]
        return ahead[0] if ahead else next((q for q in nbrs[cur] if q != prev), None)

    def walk(start: tuple[int, int], first: tuple[int, int]) -> list[tuple[int, int]]:
        """Follow a chain from a node to the next node."""
        chain = [start, first]
        prev, cur = start, first
        while cur not in nodes:
            nxt = step(prev, cur)
            if nxt is None or nxt in chain[:-1]:
                break
            prev, cur = cur, nxt
            chain.append(cur)
        return chain

    for node in sorted(nodes):
        for nb in nbrs[node]:
            if (node, nb) in seen:
                continue
            chain = walk(node, nb)
            seen.add((node, nb))
            if len(chain) > 1:
                seen.add((chain[-1], chain[-2]))
            out.append(chain)
    # Anything left is a closed loop with no junction at all, an `o` or an `0`.
    left = on - {p for chain in out for p in chain}
    while left:
        start = min(left)
        cur = next((q for q in nbrs[start] if q in left), None)
        chain, prev = [start], start
        while cur is not None and cur != start:
            chain.append(cur)
            nxt = step(prev, cur)
            prev, cur = cur, (nxt if nxt in left or nxt == start else None)
        chain.append(start)
        # A walk steps over the inner pixel of every staircase corner, so what
        # is left after a loop has been traced is a scatter of single pixels
        # already covered by the line beside them. Emitted, each one is a
        # zero-length stroke, and the nib leaves a blot: that is where the
        # speckle round every curved letter came from. A leftover of one or
        # two pixels is dropped; a real component is kept.
        if len(set(chain)) > 2:
            out.append(chain)
        left -= set(chain)
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

    This is the fault that drew an M as an H. Where two strokes of a
    letter run together along their length rather than crossing, the ink is one
    mass and its medial axis is one line up the middle, so the thinner hands
    back one stroke where the designer drew two. In Patrick Hand's capital M
    the bowl's arms merge into the stems from the cap line down to about half
    the height; what survived was two full stems joined by a shallow curve
    sitting exactly where an H's crossbar sits, which is why a word starting
    with M read as starting with H.

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
    if len(pts) < 4:
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
    if last < 3:
        return None
    return [
        (x + nx * side * lift[i], y + ny * side * lift[i])
        for i, ((x, y), (nx, ny)) in enumerate(zip(pts[: last + 1], norms[: last + 1], strict=True))
    ]


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
    ends: dict[tuple[int, int], list[list[Pt]]] = {}
    for chain, run in kept:
        if chain[0] == chain[-1] or len(run) < 4:
            continue
        for node, out_run in ((chain[0], run), (chain[-1], run[::-1])):
            ends.setdefault(node, []).append(_from(node, out_run))
    out: list[list[Pt]] = []
    for arms in ends.values():
        if len(arms) < 3:
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


def _dots(img: np.ndarray, reach: np.ndarray, drawn: set[tuple[int, int]]) -> list[list[Pt]]:
    """A ring for every blob of ink the thinning ate whole.

    Zhang-Suen deletes a small round component from both sides at once and
    leaves nothing behind, which is why the tittle of an `i` and a `j` and the
    whole of a full stop were missing from the sheet. A blob is drawn as a
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

    The ends are pushed back out along their own direction by the distance the
    thinning ate: a medial axis stops half a stroke width short of the ink, so
    an unextended skeleton draws an `l` shorter than the letter is. Runs that
    stand in more ink than one stroke is wide are split back into the two
    strokes that made them, and a blob the thinning ate whole comes back as a
    dot.
    """
    from pyntpot._port import paint

    img, ox, oy = _fill(contours, upem)
    skel = thin(img)
    # Distance from an inked pixel to the nearest blank one, which at a
    # terminal is half the stroke's own width: exactly what thinning ate.
    reach = paint.edt(img == 0)
    k = upem / RASTER_EM
    half = _half_width(skel, reach) if skel.any() else 1.0
    on = {(int(r), int(c)) for r, c in zip(*np.nonzero(skel), strict=True)}
    free = {p for p in on if _crossings(p, on) <= 1}
    runs: list[list[Pt]] = []
    drawn: set[tuple[int, int]] = set()
    kept: list[tuple[list[tuple[int, int]], list[Pt]]] = []
    for chain in _prune(_chains(skel), SPUR_EM * RASTER_EM):
        pts = [(c + 0.5, r + 0.5) for r, c in chain]
        if len(pts) < 2:
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
    every stroke meeting in it, so pushing that end out by the disc threw a
    long spike clean out of the letter. That is where the star at the top of
    every M and W came from.
    """
    if chain[0] == chain[-1] or len(pts) < 3:
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


# --------------------------------------------------------------------------- the face


class OutlineFont:
    """One typeface, as glyphs a pen can be run along.

    Args:
        path: The `.ttf` to read.
        route: `CENTRELINE` to thin the glyph to a written skeleton, `OUTLINE`
            to draw round its own contour.
    """

    def __init__(self, path: Path | str = DEFAULT_FONT, route: str = CENTRELINE) -> None:
        """Open the face and read its metrics."""
        from fontTools.pens.recordingPen import DecomposingRecordingPen
        from fontTools.ttLib import TTFont

        self.path = Path(path)
        self.route = route
        self._font = TTFont(str(self.path), lazy=True)
        self._pen_cls = DecomposingRecordingPen
        self._glyphs = self._font.getGlyphSet()
        self._cmap = self._font.getBestCmap()
        head = self._font["head"]
        hhea = self._font["hhea"]
        self.upem = int(head.unitsPerEm)
        self.ascender = float(hhea.ascent) / self.upem
        self.descender = float(hhea.descent) / self.upem
        self._cache: dict[str, Glyph] = {}

    @property
    def name(self) -> str:
        """The face's file name, for a note that says what lettered the map."""
        return self.path.stem

    def _name_of(self, ch: str) -> str | None:
        """The glyph name for one character, or None when the face has none."""
        return self._cmap.get(ord(ch))

    def glyph(self, ch: str) -> Glyph:
        """One character as paths in em units, cached.

        Args:
            ch: The character.

        Returns:
            The glyph. A character the face has not got comes back with the
            advance of a space and nothing to draw, which is what a missing
            glyph should look like on a map and not a box.
        """
        got = self._cache.get(ch)
        if got is not None:
            return got
        name = self._name_of(ch)
        if name is None:
            self._cache[ch] = Glyph(ch, 0.28, [])
            return self._cache[ch]
        advance = self._font["hmtx"][name][0] / self.upem
        rec = self._pen_cls(self._glyphs)
        self._glyphs[name].draw(rec)
        flat = _Flatten()
        rec.replay(flat)
        contours = flat.contours
        if not contours:
            self._cache[ch] = Glyph(ch, advance, [])
            return self._cache[ch]
        if self.route == CENTRELINE:
            paths = _centrelines(contours, self.upem)
        else:
            paths = [[(x / self.upem, y / self.upem) for x, y in c] for c in contours]
        self._cache[ch] = Glyph(ch, advance, paths)
        return self._cache[ch]

    def advance(self, ch: str) -> float:
        """One character's advance in em units."""
        return self.glyph(ch).advance

    def measure(self, text: str, size: float, tracking: float = 0.0) -> tuple[float, float]:
        """How wide and how tall one line is, in the caller's own pixels.

        This is the whole point of taking a real face: every box on the sheet
        was sized at a flat eight pixels a character, which is why the placer
        put names off the paper and why the standalone card had to shrink its
        type to fit boxes drawn for a different hand.

        Args:
            text: The line.
            size: The type size in display pixels.
            tracking: Extra letter spacing, in em units.

        Returns:
            `(width, height)` in display pixels.
        """
        s = str(text)
        if not s:
            return 0.0, size
        width = sum(self.advance(c) + tracking for c in s) - tracking
        return width * size, (self.ascender - self.descender) * size * 0.86

    def run(
        self, text: str, size: float, tracking: float = 0.0
    ) -> list[tuple[str, float, float, list[list[Pt]]]]:
        """Every glyph of a line, at its pen position, scaled to the type size.

        Args:
            text: The line.
            size: The type size in display pixels.
            tracking: Extra letter spacing, in em units.

        Returns:
            One `(character, pen x, advance, paths)` a character, paths in
            display pixels with the baseline at y zero and y up, relative to
            that character's own pen position.
        """
        out = []
        pen = 0.0
        for ch in str(text):
            g = self.glyph(ch)
            paths = [[(x * size, y * size) for x, y in p] for p in g.paths]
            out.append((ch, pen, g.advance * size, paths))
            pen += (g.advance + tracking) * size
        return out


@functools.lru_cache(maxsize=8)
def load(path: str | None = None, route: str = CENTRELINE) -> OutlineFont:
    """The vendored face, opened once a route and kept.

    Args:
        path: The font file, or None for the vendored one.
        route: `CENTRELINE` or `OUTLINE`.

    Returns:
        The face.
    """
    return OutlineFont(Path(path) if path else DEFAULT_FONT, route)
