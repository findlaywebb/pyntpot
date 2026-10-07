"""A grid index over the track, for asking how near a feature ran to it.

Key names: `TrackIndex`, which answers the distance from a point to the track and
whether a line ran alongside the track or crossed it; `_densify`, a polyline
resampled to a maximum point spacing.

A road is on the map because the track met it, not because it exists, so the minor
roads and the streams are each asked whether the track ran alongside them or crossed
them. It does not decide which
features to ask about and it does not draw anything. Invariants: a distance is
never more than the cap it was given, and an empty neighbourhood answers the cap.
"""

import math
from itertools import pairwise

from pyntpot.ink.polyline import Pt, segments_cross


class TrackIndex:
    """A grid index over the track, for asking how near a feature ran to it.

    A road is on the map because the track met it, not because it exists, so
    the minor roads and the streams are each asked this question.
    """

    def __init__(self, points: list[Pt], cell_m: float = 120.0) -> None:
        """Index the track.

        Args:
            points: The track in metres.
            cell_m: Bucket size in metres; a distance query scans every bucket
                within its cap of the point.
        """
        self.cell = cell_m
        self.points = points
        self.buckets: dict[tuple[int, int], list[Pt]] = {}
        for p in points:
            self.buckets.setdefault((int(p[0] // cell_m), int(p[1] // cell_m)), []).append(p)

    def distance(self, x: float, y: float, cap_m: float = 400.0) -> float:
        """Metres to the nearest track point, or `cap_m` when nothing is near.

        Args:
            x: Easting in metres.
            y: Northing in metres.
            cap_m: The answer given when no track point is within the scan.

        Returns:
            The distance, never more than `cap_m`.
        """
        rings = max(1, int(cap_m // self.cell) + 1)
        cx, cy = int(x // self.cell), int(y // self.cell)
        best = cap_m
        for i in range(-rings, rings + 1):
            for j in range(-rings, rings + 1):
                for px, py in self.buckets.get((cx + i, cy + j), ()):
                    d = math.hypot(px - x, py - y)
                    best = min(best, d)
        return best

    def interacts(self, line: list[Pt], within_m: float, run_m: float) -> bool:
        """True when the track ran alongside this line, or crossed it.

        Args:
            line: The feature in metres.
            within_m: How close counts as alongside.
            run_m: How many metres of unbroken contact are needed. A crossing
                needs none.

        Returns:
            Whether the track ran alongside the feature or crossed it.
        """
        dense = _densify(line, step_m=20.0)
        near = [self.distance(x, y, cap_m=within_m + 1) <= within_m for x, y in dense]
        if not any(near):
            return False
        run = 0.0
        for i in range(1, len(dense)):
            if near[i] and near[i - 1]:
                run += math.dist(dense[i - 1], dense[i])
                if run >= run_m:
                    return True
            else:
                run = 0.0
        return self._crosses(line)

    def _crosses(self, line: list[Pt]) -> bool:
        """True when a feature segment intersects a track segment."""
        for a, b in pairwise(line):
            for c, d in pairwise(self.points):
                if max(c[0], d[0]) < min(a[0], b[0]) or min(c[0], d[0]) > max(a[0], b[0]):
                    continue
                if max(c[1], d[1]) < min(a[1], b[1]) or min(c[1], d[1]) > max(a[1], b[1]):
                    continue
                if segments_cross(a, b, c, d):
                    return True
        return False


def _densify(line: list[Pt], step_m: float) -> list[Pt]:
    """A polyline resampled so no two points are more than `step_m` apart."""
    out: list[Pt] = []
    for a, b in pairwise(line):
        steps = max(1, int(math.dist(a, b) // step_m))
        for k in range(steps):
            t = k / steps
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    out.append(line[-1])
    return out
