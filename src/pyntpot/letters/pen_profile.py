"""The broad nib's width along one stroke, from the angle between the stroke and the nib.

Key function: `pen_profile`, the width multiplier at evenly spaced points along
a stroke, which `letters.nib` hands to the ink pad with the glyph's marks.

A broad nib held at a fixed angle draws its full width across itself and almost
nothing along itself, so a glyph's width follows the angle between the stroke
and the nib: `1 - thin` along it, all of it across, the sine between. The
direction is the stroke's own, smoothed along it over the nib's width, so a
pixel staircase reads as one width and a gentle turn moves the width through
the angles between. Where the smoothed direction cuts across a sharp corner,
the corner is read from its legs instead (`pen_profile` says how).

It does not stroke, colour or place anything, and it reads no style: the nib's
angle, how much it thins and its width arrive as numbers. The nib's angle is
fixed to the page; no mark but a glyph's stroke has a profile.

Invariants, wherever the samples fall and however many there are:

- the width is in `[1 - thin, 1]`;
- turning the nib, or the stroke, by an angle moves no sample by more than
  `thin` times that angle;
- a stroke of two straight legs (a V or an L) is nowhere thinner than the
  narrower leg;
- a sample is lifted above its smoothed direction's width only by a vertex
  within its own smoothing window, and never above the narrower side of that
  window cut at the vertex;
- a closed stroke (its last point its first) has no ends, so its width runs on
  round the seam and does not depend on which vertex it starts at;
- a stroke of fewer than two points or no length keeps its full width.
"""

import math

import numpy as np

from pyntpot.ink.noise import F32

#: Points a stroke's width profile is sampled at.
PROFILE_SAMPLES = 24

#: How many boxes a stroke's direction is averaged through, spread over one
#: window, so the average is weighted as a tent rather than a box.
_TENT_TAPS = 8

#: The fewest points a stroke can be run along: it needs two ends.
_STROKE_ENDS = 2

#: A stroke shorter than this, in render pixels, has no direction to take a width from.
_MIN_LENGTH_PX = 1e-6


def pen_profile(
    pts: np.ndarray,
    angle: float,
    thin: float,
    window: float,
    samples: int = PROFILE_SAMPLES,
) -> np.ndarray:
    """A width along one stroke, from the angle between it and the nib.

    A broad nib held at a fixed angle draws its full width across itself and
    almost nothing along itself. That single fact is most of what separates a
    written letter from a plotted one, and it is why the same skeleton stamped
    at one width reads as a machine.

    The direction is the stroke's own, smoothed along it: a glyph's stroke
    comes off a thinned skeleton and turns a pixel at a time, a staircase of
    flats and diagonals, and read segment by segment a stroke near the nib's
    angle swings between full width and a hairline stamp by stamp. The unit
    tangent is averaged, weighted by length under a tent `window` wide at half
    its height, centred on each sample, so a gentle turn moves the width
    through the angles between. The length-weighted tangent over a span is the
    chord between its ends, so each box of the tent is read from the stroke's
    own points. An open stroke's tent is cut at its ends; a closed one's runs on
    round the ring.

    Averaged across a sharp corner, the tangent points along the corner's
    bisector, a direction neither leg has, and where the nib lies along it the
    width would fall to a hairline that neither leg has. So each sample's tent
    is also cut in two at every vertex of the stroke it reaches, and each side
    read as a width on its own (an empty side, past an open stroke's end, reads
    full, so the other side decides). The narrower side of each cut is a floor,
    and the sample's width is the widest of those floors and the whole tent's.
    Cut at a corner, each side is one leg, so a stroke of two straight legs is
    nowhere thinner than the narrower leg. Where both sides of a cut lie on
    one side of the nib's direction (a straight run, or an L whose leg lies
    along the nib), the whole lies between them and is no narrower than the
    narrower side, so the floor does not bind and the L climbs through the
    angles between. A floor binds only where the two sides lie either side of
    the nib's direction, and never above the narrower of them: a hairline
    running straight along the nib is lifted only where its tent reaches a
    vertex past a turn's first, and never above the side of that cut that
    holds the hairline.

    Every width here is the sine between a direction the stroke alone fixes
    and the nib (or full, for an empty side), and the floor is a widest of
    narrowest of them, so turning the nib, or the stroke, by an angle moves no
    sample by more than `thin` times it. The samples
    are evenly spaced, none more than half a window from the next, and the
    floor holds at each of them however they fall, since it is read from the
    stroke's vertices, not from the samples.

    Args:
        pts: The stroke in render pixels; closed when its last point is its first.
        angle: The nib's angle in radians from the page's horizontal, in
            render pixels with y down.
        thin: How much of the width a stroke drawn straight along the nib loses.
        window: How much of the stroke, in render pixels, its direction is
            averaged over; the nib's own width.
        samples: The fewest points the profile is sampled at.

    Returns:
        The multiplier at evenly spaced points from the stroke's start to end.
    """
    if len(pts) < _STROKE_ENDS:
        return np.ones(_STROKE_ENDS, F32)
    d = np.diff(pts, axis=0)
    cum = np.concatenate([[0.0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])
    total = float(cum[-1])
    if total <= _MIN_LENGTH_PX:
        return np.ones(_STROKE_ENDS, F32)
    width = max(window, _MIN_LENGTH_PX)
    at = np.linspace(0.0, total, max(samples, math.ceil(2.0 * total / width) + 1))
    # A tent is a box of boxes: one box a window wide at each of `_TENT_TAPS`
    # points spread over a window round the sample.
    taps = ((np.arange(_TENT_TAPS) + 0.5) / _TENT_TAPS - 0.5) * width
    lo = at[:, None] + taps[None, :] - width * 0.5
    hi = at[:, None] + taps[None, :] + width * 0.5
    closed = bool(np.array_equal(pts[0], pts[-1]))
    at_lo = _point(pts, cum, lo, closed=closed)
    at_hi = _point(pts, cum, hi, closed=closed)
    whole = (at_hi - at_lo).sum(axis=1)
    cut, cut_at, real = _cuts(pts, cum, lo[:, 0], hi[:, -1], closed=closed)
    before = _reached(hi, at_hi, cut, cut_at) - _reached(lo, at_lo, cut, cut_at)
    after = whole[:, None, :] - before
    floors = np.where(real, np.minimum(_side(before, angle), _side(after, angle)), 0.0)
    across = np.maximum(_across(whole, angle), floors.max(axis=1))
    return ((1.0 - thin) + thin * across).astype(F32)


def _cuts(
    pts: np.ndarray, cum: np.ndarray, start: np.ndarray, end: np.ndarray, *, closed: bool
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The stroke's vertices from `start` to `end` along it, one row per sample.

    Returns each row's vertices' lengths along the stroke and points, padded to
    the longest row, with a mask of which are real. A closed stroke's vertices
    are repeated a ring's length either side, often enough to cover a window
    reaching past the seam, so a row can hold a vertex at its unwrapped length;
    its seam is one vertex, not two.
    """
    if closed:
        laps = math.ceil((end[-1] - start[0]) / cum[-1])
        lap = np.arange(-laps, laps + 1)[:, None] * cum[-1]
        length = (cum[:-1][None, :] + lap).ravel()
        which = np.tile(np.arange(len(pts) - 1), len(lap))
    else:
        length, which = cum, np.arange(len(pts))
    first = np.searchsorted(length, start, side="left")
    count = np.searchsorted(length, end, side="right") - first
    slot = np.arange(count.max())[None, :]
    index = np.minimum(first[:, None] + slot, len(length) - 1)
    return length[index], pts[which[index]], slot < count[:, None]


def _reached(ends: np.ndarray, at: np.ndarray, cut: np.ndarray, cut_at: np.ndarray) -> np.ndarray:
    """The sum over a sample's boxes of the point at each box end, or at the cut if that comes first.

    `ends` is each sample's box ends along the stroke, in order, and `at`
    their points; `cut` and `cut_at` are each sample's vertices and their
    points. The ends at or before a cut are summed as they are (a running sum,
    since they are in order) and each end past it adds the vertex instead.
    Returned per sample and vertex, with a last axis of two; the box ends'
    sum less the box starts' sum is the chord of the tent before the cut.
    """
    taken = (ends[:, None, :] <= cut[:, :, None]).sum(axis=2)
    run = np.concatenate([np.zeros_like(at[:, :1]), np.cumsum(at, axis=1)], axis=1)
    past = ends.shape[1] - taken
    return np.take_along_axis(run, taken[:, :, None], axis=1) + past[:, :, None] * cut_at


def _point(pts: np.ndarray, cum: np.ndarray, s: np.ndarray, *, closed: bool) -> np.ndarray:
    """The stroke's point at each length in `s`, with `s`'s shape plus a last axis of two.

    An open stroke's length is clamped to its ends, so a span reaching past an
    end is cut there; a closed stroke's length is read round the ring, so a
    span reaching past the seam carries on from the start.
    """
    at = np.mod(s, cum[-1]) if closed else s
    return np.stack([np.interp(at, cum, pts[:, 0]), np.interp(at, cum, pts[:, 1])], axis=-1)


def _across(chord: np.ndarray, angle: float) -> np.ndarray:
    """How far across the nib each chord points, as `|sin|` of the angle between."""
    return np.abs(np.sin(np.arctan2(chord[..., 1], chord[..., 0]) - angle))


def _side(chord: np.ndarray, angle: float) -> np.ndarray:
    """`_across` for one side of a cut tent, where an empty side sets no floor.

    A side is empty past an open stroke's end, where there is no stroke before
    the first vertex or after the last; it reads as full width, so the other
    side, which is then the whole tent, decides.
    """
    full = np.hypot(chord[..., 0], chord[..., 1]) > _MIN_LENGTH_PX
    return np.where(full, _across(chord, angle), 1.0)
