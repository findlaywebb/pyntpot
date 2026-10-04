"""Climbs: the sustained rises in a track, and the distances they are measured in.

Key names: `rank_climbs`, the climbs of a track as candidates, in the order they
were ridden or run and ranked by metres gained; `cumulative`, `haversine`,
`bearing` and `compass`, the great-circle measures a climb and its grounding
are stated in.

Detection is an envelope: a rise of at least `MIN_GAIN_M` that never gives back
`MAX_DROP_M` on the way up. What is reported is the **felt** climb inside that
envelope, with any approach or run-out flatter than `FLAT_GRADE` trimmed off,
because the envelope's own start is wherever the ground first ticked upwards,
and that can be a kilometre of valley floor before the pitch. A trim that eats
the climb is a wrong trim, so the envelope is kept then.

It does not name a climb and does not ground one in roads or settlements; naming
is the caller's judgement and grounding is `places.ground_climbs`. A track with
no elevation has no climbs. Invariants: `rank` is the rank by metres gained, one
for the most; the list is in track order; `span` is the felt first and last
sample.
"""

import math
from collections.abc import Sequence
from typing import Any, NamedTuple

from pyntpot.maps.basemap import Line
from pyntpot.maps.candidates.candidate import Candidate
from pyntpot.maps.track import Track

#: Metres of gain a rise needs before it counts as a climb.
MIN_GAIN_M = 60.0

#: Metres of give-back that ends a rise.
MAX_DROP_M = 15.0

#: Gradient, as a fraction, below which ground at either end of a rise is
#: approach or run-out rather than climb.
FLAT_GRADE = 0.01

#: The window the steepest stretch of a climb is measured over.
STEEP_WINDOW_M = 500.0

#: A steepest window shorter than this share of the window is not measured.
WINDOW_SHARE = 0.9

#: The shortest track that can hold a climb, in samples.
MIN_SAMPLES = 3

EARTH_RADIUS_M = 6371000.0

#: The eight points a rider actually says out loud. Sixteen is a chart bearing,
#: not a description of which way a road went.
COMPASS = ("north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west")

_POINT_DEGREES = 45.0


class _Rise(NamedTuple):
    """A detected rise: its felt span and the envelope it was found in."""

    a: int
    b: int
    start: int
    peak: int


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two coordinates."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Initial compass bearing in degrees from one coordinate to another."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lng2 - lng1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def compass(bearing_deg: float) -> str:
    """The eight-point compass word for a bearing."""
    return COMPASS[int((bearing_deg + _POINT_DEGREES / 2) // _POINT_DEGREES) % len(COMPASS)]


def cumulative(lat: Sequence[float], lng: Sequence[float]) -> list[float]:
    """Metres travelled at each track point, starting at zero."""
    out: list[float] = [0.0]
    for i in range(1, min(len(lat), len(lng))):
        out.append(out[-1] + haversine(lat[i - 1], lng[i - 1], lat[i], lng[i]))
    return out


def _felt_span(
    dist: Sequence[float], ele: Sequence[float], a: int, b: int, flat_grade: float
) -> tuple[int, int]:
    """Trim ground flatter than `flat_grade` off both ends of a rise.

    The sub-span kept is the one that maximises `gain - flat_grade * length`,
    which is the same as saying: ground flatter than `flat_grade` at either end
    is approach or run-out, not climb.

    Args:
        dist: Cumulative metres at each sample.
        ele: Elevation at each sample.
        a: First sample of the detected rise.
        b: Its summit sample.
        flat_grade: The gradient below which ground stops counting, as a fraction.

    Returns:
        The first and last sample of the felt climb.
    """
    best_start, best_value = a, flat_grade * dist[a] - ele[a]
    span, score = (a, b), -math.inf
    for e in range(a + 1, b + 1):
        gain = (ele[e] - ele[best_start]) - flat_grade * (dist[e] - dist[best_start])
        if gain > score:
            span, score = (best_start, e), gain
        value = flat_grade * dist[e] - ele[e]
        if value > best_value:
            best_value, best_start = value, e
    return span


def _steepest(
    dist: Sequence[float], ele: Sequence[float], a: int, b: int, window_m: float
) -> tuple[float, float]:
    """The steepest continuous `window_m` inside a span: its gradient and where.

    Returns:
        Percent gradient and the kilometre it starts at, or (0.0, 0.0) when the
        span is shorter than the window.
    """
    best, at, e = 0.0, 0.0, a
    for s in range(a, b):
        while e < b and dist[e] - dist[s] < window_m:
            e += 1
        run = dist[e] - dist[s]
        if run < window_m * WINDOW_SHARE:
            break
        grade = (ele[e] - ele[s]) / run
        if grade > best:
            best, at = grade, dist[s]
    return round(best * 100, 1), round(at / 1000, 2)


def _envelope(ele: Sequence[float], start: int) -> tuple[float, int]:
    """The summit elevation and sample of the rise that begins at `start`."""
    peak_ele, peak = ele[start], start
    for j in range(start + 1, len(ele)):
        if ele[j] > peak_ele:
            peak_ele, peak = ele[j], j
        elif peak_ele - ele[j] >= MAX_DROP_M:
            break
    return peak_ele, peak


def _rises(dist: Sequence[float], ele: Sequence[float]) -> list[_Rise]:
    """Every rise of at least `MIN_GAIN_M`, felt span and envelope, in track order."""
    rises: list[_Rise] = []
    i = 0
    while i < len(ele) - 1:
        if ele[i + 1] <= ele[i]:
            i += 1
            continue
        peak_ele, peak = _envelope(ele, i)
        if peak_ele - ele[i] < MIN_GAIN_M:
            i += 1
            continue
        a, b = _felt_span(dist, ele, i, peak, FLAT_GRADE)
        # A trim that eats the climb is a wrong trim: keep the envelope.
        if ele[b] - ele[a] < MIN_GAIN_M:
            a, b = i, peak
        rises.append(_Rise(a, b, i, peak))
        i = peak + 1
    return rises


def _row(
    track: Track, dist: Sequence[float], ele: Sequence[float], rise: _Rise, total: float
) -> dict[str, Any]:
    """One climb's row: its felt span, gradient shape and position."""
    a, b = rise.a, rise.b
    lat, lng = track.lat, track.lng
    gain = ele[b] - ele[a]
    length = max(dist[b] - dist[a], 1.0)
    steep_pct, steep_km = _steepest(dist, ele, a, b, STEEP_WINDOW_M)
    heading = bearing(lat[a], lng[a], lat[b], lng[b])
    return {
        "start_km": round(dist[a] / 1000, 2),
        "end_km": round(dist[b] / 1000, 2),
        "gain_m": round(gain),
        "length_km": round(length / 1000, 2),
        "avg_grade_pct": round(gain / length * 100, 1),
        "steepest_500m_pct": steep_pct,
        "steepest_500m_km": steep_km,
        "bottom_ele_m": round(ele[a]),
        "top_ele_m": round(ele[b]),
        "approach_trimmed_km": round((dist[a] - dist[rise.start]) / 1000, 2),
        "runout_trimmed_km": round((dist[rise.peak] - dist[b]) / 1000, 2),
        "share_of_climbing_pct": round(gain / total * 100),
        "position_pct": round(dist[a] / max(dist[-1], 1.0) * 100),
        "heading": compass(heading),
        "bearing_deg": round(heading),
        "start_lat": round(lat[a], 6),
        "start_lng": round(lng[a], 6),
        "end_lat": round(lat[b], 6),
        "end_lng": round(lng[b], 6),
    }


def rank_climbs(track: Track, line: Line) -> list[Candidate]:
    """Sustained rises in a track: where it climbed, how far, and how steeply.

    Args:
        track: The track; without elevation it has no climbs.
        line: The track in card metres, one point per track sample.

    Returns:
        One candidate per climb, in the order they were ridden or run, each
        ranked by metres gained. `name` is empty, since naming a climb is the
        caller's judgement; `at_m` is where the felt climb starts and `where`
        the point on `line` it starts at. `detail` carries the felt span, its
        gradient shape and the three ranks `rank_by_gain`, `rank_by_steepness`
        and `of_climbs`.
    """
    ele = track.ele
    if ele is None or len(ele) < MIN_SAMPLES:
        return []
    dist = cumulative(track.lat, track.lng)
    rises = _rises(dist, ele)
    total = sum(ele[r.b] - ele[r.a] for r in rises) or 1.0
    rows = [_row(track, dist, ele, rise, total) for rise in rises]
    by_gain = sorted(range(len(rows)), key=lambda k: -rows[k]["gain_m"])
    by_grade = sorted(range(len(rows)), key=lambda k: -rows[k]["avg_grade_pct"])
    out = []
    for k, (rise, row) in enumerate(zip(rises, rows, strict=True)):
        rank = by_gain.index(k) + 1
        detail = {
            **row,
            "rank_by_gain": rank,
            "rank_by_steepness": by_grade.index(k) + 1,
            "of_climbs": len(rows),
        }
        out.append(
            Candidate(
                kind="climb",
                name="",
                rank=rank,
                at_m=dist[rise.a],
                where=line[rise.a],
                span=(rise.a, rise.b),
                detail=detail,
            )
        )
    return out
