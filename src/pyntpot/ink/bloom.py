"""Blooms: backruns laid into a wash's density in place, seated by keyed lots.

Key functions: `bloom`, the backruns of one wash; `bloom_radius`, a wash's base bloom
radius, held on quarter-octave steps; `highest`, the indices of the highest lots, as a
stable descending sort's head gives them. Key type: `Blooms`, what one wash's blooms are
laid by.

It lays blooms only: the wash they are laid in is `ink.wash`, which calls `bloom`. It reads
no style and writes no file.

Invariants: a bloom's seat, size and warp are pure functions of the wash's seed, the
density and the bloom's own position (`ink.keyed`), so an edge that moves elsewhere on the
plate moves no bloom unless it moves the area across a radius step; `highest` returns
exactly what a stable descending sort's first `k` would.
"""

import math

import numpy as np

from pyntpot.ink.keyed import keyed_rng, uniform_at
from pyntpot.ink.noise import F32, fbm
from pyntpot.ink.sheet import Sheet

#: Alpha above this counts as inside the wash, and above the second as thick enough to bloom.
_INSIDE = 0.5
_THICK = 0.6
#: A wash with fewer thick pixels than this carries no bloom.
_MIN_BLOOM_PIXELS = 64
#: A bloom's box must be at least this many pixels on a side.
_MIN_BOX = 5
#: A bloom's base radius is held on this many steps per doubling (`bloom_radius`).
_RADIUS_STEPS = 4

#: What blooms are laid by: the wash's own seed, how many, the radius as a share
#: of the root of the wash's area, how much pigment the front lifts out of the
#: centre and how far the fbm warps the front off a circle.
Blooms = tuple[int, int, float, float, float]


def bloom_radius(radius_frac: float, area: int) -> float:
    """A wash's base bloom radius, held on a step of a quarter of an octave.

    The radius follows the root of the wash's area, and an edge that moves a pixel
    anywhere changes the area. Held to the nearest of the steps `2 ** (k / 4)`, the
    radius moves only when the area crosses a step. Each step is a fifth of the radius,
    where a pixel is a fiftieth to a two-hundredth of one, so a one-pixel edge move
    resizes the blooms a fifth to a seventeenth as often as rounding to the pixel did.
    The step's error is at most a tenth of the radius, inside the 0.7 to 1.3 each bloom
    already draws its own size from, so it does not show.

    Args:
        radius_frac: The radius as a share of the root of the area.
        area: The wash's thick pixels.

    Returns:
        The base radius in pixels, before the plate's bounds; 0 for no area.
    """
    raw = radius_frac * math.sqrt(max(area, 0))
    if raw <= 0:
        return 0.0
    return float(2.0 ** (round(_RADIUS_STEPS * math.log2(raw)) / _RADIUS_STEPS))


def highest(lots: np.ndarray, k: int) -> np.ndarray:
    """The indices of the `k` highest lots, highest first, ties to the lower index.

    What a stable descending sort's first `k` are, without sorting the rest: a
    partition finds the `k`-th highest lot, every lot above it is kept, the lots equal
    to it are kept from the lowest index up until `k` are held, and only those are
    sorted. A partition alone may keep any of the tied lots and keeps them unordered.

    Args:
        lots: The lots, one dimension.
        k: How many to keep; at least the number of lots keeps them all.

    Returns:
        At most `k` indices into `lots`, `int64`.
    """
    n = lots.size
    if k <= 0 or not n:
        return np.zeros(0, np.int64)
    neg = -lots
    if k < n:
        cut = neg[np.argpartition(neg, k - 1)[k - 1]]
        above = np.flatnonzero(neg < cut)
        tied = np.flatnonzero(neg == cut)[: k - above.size]
        pick = np.concatenate([above, tied])
    else:
        pick = np.arange(n)
    return pick[np.lexsort((pick, neg[pick]))].astype(np.int64)


def bloom(dens: np.ndarray, a: np.ndarray, sheet: Sheet, blooms: Blooms) -> None:
    """Backruns, as a re-wet event with no solver. Modifies `dens` in place.

    A backrun is a second front of liquid pushing already-deposited pigment out
    ahead of it: the centre goes lighter than the wash around it and the front
    dries as a dark crenellated ridge. Seeded where the wash is thick, grown
    outward, and warped off a circle by fractal noise, which is what makes the
    ridge read as a cauliflower rather than a halo. Cropped to the bloom's own
    box, so the cost does not scale with the plate.

    Placement is local. Every thick pixel draws one lot from its own position
    (`ink.keyed.uniform_at`), raised to one over its density, and the `count`
    highest lots are the centres. Weighted by the density itself and no more
    steeply: the pooled rim is denser than any of the body, and a steeper weight
    lets it take every bloom, so they crowd the coast. Each bloom then draws its
    size and its warp from a generator keyed by its centre. So an edge that moves
    elsewhere on the plate moves no bloom, where drawing candidates by their rank
    among the thick pixels moved every one.

    Source: `backruns` in docs/explanation/references.md.

    Args:
        dens: The wash's density, changed in place.
        a: The wash's alpha, so a bloom stops at the wash's edge.
        sheet: The paper's noise fields.
        blooms: The settings, in `Blooms`' order: the wash's own seed, which the
            lots and each bloom's generator are keyed from; how many blooms to lay;
            the radius as a share of the root of the wash's area; how much pigment
            the front takes out of the centre; and how far the fbm pushes the front
            off a circle.
    """
    seed, count, radius_frac, lift, warp = blooms
    inside = np.flatnonzero((a > _THICK).ravel())
    if count < 1 or inside.size < _MIN_BLOOM_PIXELS:
        return
    h, w = dens.shape
    radius = float(np.clip(bloom_radius(radius_frac, inside.size), 5.0, 0.22 * min(h, w)))
    flat = dens.ravel()
    # Seeded toward the thick: a lot per pixel, weighted by its density, the
    # highest win (Efraimidis and Spirakis' weighted sampling).
    weight = np.maximum(flat[inside].astype(np.float64), 1e-6)
    lots = np.log(uniform_at(seed, inside)) / weight
    for at in inside[highest(lots, int(count))]:
        cy, cx = divmod(int(at), w)
        rng = keyed_rng(seed, cy, cx)
        r = radius * float(rng.uniform(0.7, 1.3))
        span = int(r * 1.9) + 3
        y0, y1 = max(cy - span, 0), min(cy + span + 1, h)
        x0, x1 = max(cx - span, 0), min(cx + span + 1, w)
        if y1 - y0 < _MIN_BOX or x1 - x0 < _MIN_BOX:
            continue
        bh, bw = y1 - y0, x1 - x0
        yy = (np.arange(y0, y1, dtype=F32) - cy)[:, None]
        xx = (np.arange(x0, x1, dtype=F32) - cx)[None, :]
        d = np.hypot(yy, xx) + warp * (fbm(bh, bw, r * 0.55, 3, rng) - 0.5) * r
        front = np.exp(-(((d - r) / F32(max(r * 0.09, 1.6))) ** 2))
        box_a = a[y0:y1, x0:x1]
        box = dens[y0:y1, x0:x1]
        core = (d < r) * box_a
        held = float(box[core > _INSIDE].mean()) if (core > _INSIDE).any() else 0.0
        box *= 1.0 - lift * core
        box += held * lift * 1.5 * front * box_a
        np.clip(box, 0.0, 1.0, out=box)
