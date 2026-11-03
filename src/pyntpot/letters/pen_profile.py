"""The broad nib's width along one stroke, from the angle between the stroke and the nib.

Key function: `pen_profile`, the width multiplier at evenly spaced points along
a stroke, which `letters.nib` hands to the ink pad with the glyph's marks.

A broad nib held at a fixed angle draws its full width across itself and almost
nothing along itself, so a glyph's width follows the angle between the stroke
and the nib: `1 - thin` along it, all of it across, the sine between. The
direction is the stroke's own, smoothed along it over the nib's width, so a
pixel staircase reads as one width and a corner turns the width through the
angles between.

It does not stroke, colour or place anything, and it reads no style: the nib's
angle, how much it thins and its width arrive as numbers. The nib's angle is
fixed to the page; no mark but a glyph's stroke has a profile.

Invariants: the width is in `[1 - thin, 1]`; a sample on a corner is never
thinner than both of the legs either side of it; a closed stroke (its last point its first) has no
ends, so its width runs on round the seam; a stroke of fewer than two points or
no length keeps its full width.
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
    its height, centred on each sample, so a corner turns the width through the
    angles between. The length-weighted tangent over a span is the chord
    between its ends, so each box of the tent is read from the stroke's own
    points. An open stroke's window is cut at its ends; a closed one's runs on
    round the ring.

    Averaged across a sharp corner, the tangent points along the corner's
    bisector, a direction neither leg has, and where the nib lies along it the
    width would fall to a hairline at the point. So the direction is also
    averaged over the half of the tent before each sample and the half after,
    each read as a width, and where the smaller of those two is wider than the
    whole window's width (the whole is pinched), it is a floor: a sample on a
    corner is never thinner than both its legs. The floor is carried half a
    window either side, to the samples beside the corner, whose halves straddle
    it; it is never carried where nothing is pinched, so a turn through the
    angles between (an L whose leg lies along the nib) climbs as it did. On a
    straight stroke the halves agree with the whole and the floor does not
    bind; where a curve turns through the nib's own direction within a window,
    its halves straddle the nib too, and its thinnest point is read no thinner
    than half a window either side of it.

    So the width moves continuously along the stroke and with its direction:
    turning a stroke by an angle moves no sample by more than `thin` times it.
    The samples are evenly spaced, none more than half a window from the next.

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
    centre = at[:, None] + taps[None, :]
    lo = centre - width * 0.5
    hi = centre + width * 0.5
    here = at[:, None]
    closed = bool(np.array_equal(pts[0], pts[-1]))

    def chords(start: np.ndarray, end: np.ndarray) -> np.ndarray:
        """The chord of each box from `start` to `end`, summed over a sample's boxes."""
        return (_point(pts, cum, end, closed=closed) - _point(pts, cum, start, closed=closed)).sum(
            axis=1
        )

    whole = _across(chords(lo, hi), angle)
    before = _leg(chords(np.minimum(lo, here), np.minimum(hi, here)), angle)
    after = _leg(chords(np.maximum(lo, here), np.maximum(hi, here)), angle)
    legs = np.minimum(before, after)
    # Half a window in samples; the samples are at most half a window apart.
    reach = max(1, int(0.5 * width * (len(at) - 1) / total))
    pinched = np.where(legs > whole, legs, 0.0)
    across = np.maximum(whole, _spread(pinched, reach, closed=closed))
    return ((1.0 - thin) + thin * across).astype(F32)


def _spread(floor: np.ndarray, reach: int, *, closed: bool) -> np.ndarray:
    """The largest of `floor` within `reach` samples of each, wrapped round a closed stroke.

    A closed stroke's first and last samples are the same point, so the
    distinct samples are all but the last, and the last copies the first.
    """
    ring = floor[:-1] if closed else floor
    out = ring.copy()
    for k in range(1, min(reach, len(ring) - 1) + 1):
        if closed:
            out = np.maximum(out, np.maximum(np.roll(ring, k), np.roll(ring, -k)))
        else:
            out[k:] = np.maximum(out[k:], ring[:-k])
            out[:-k] = np.maximum(out[:-k], ring[k:])
    return np.append(out, out[0]) if closed else out


def _point(pts: np.ndarray, cum: np.ndarray, s: np.ndarray, *, closed: bool) -> np.ndarray:
    """The stroke's point at each length in `s`, with `s`'s shape plus a last axis of two.

    An open stroke's length is clamped to its ends, so a span reaching past an
    end is cut there; a closed stroke's length is read round the ring, so a
    span reaching past the seam carries on from the start.
    """
    at = np.mod(s, cum[-1]) if closed else s
    return np.stack([np.interp(at, cum, pts[:, 0]), np.interp(at, cum, pts[:, 1])], axis=-1)


def _across(chord: np.ndarray, angle: float) -> np.ndarray:
    """How far across the nib each summed chord points, as `|sin|` of the angle between."""
    return np.abs(np.sin(np.arctan2(chord[:, 1], chord[:, 0]) - angle))


def _leg(chord: np.ndarray, angle: float) -> np.ndarray:
    """`_across` for one half of the window, where an empty half sets no floor.

    A half is empty at an open stroke's end, where there is no stroke before
    the first sample or after the last; it reads as full width, so the other
    half, which is then the whole window, decides.
    """
    full = np.hypot(chord[:, 0], chord[:, 1]) > _MIN_LENGTH_PX
    return np.where(full, _across(chord, angle), 1.0)
