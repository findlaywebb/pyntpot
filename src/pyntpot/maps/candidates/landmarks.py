"""Landmarks: the named things near a track, most notable first.

Key names: `rank_landmarks`, every named thing the box offered as candidates,
with its position both ways and how far off the route it sits; `pick_landmarks`,
the heuristic that chooses which of them the map labels; `landmark_reach` and
`landmark_rank`, how far off a thing is worth naming and the order things are
offered in.

**The order is notability, not distance.** Nearest-first is a list of plaques in
a city: the eighty nearest things can fail to reach out of one district, so a
zoo is not offered and a drinking fountain is. `landmark_rank` puts the things a
runner navigates by first and, inside a tier, the ones sitting most comfortably
inside their own reach. **The reach is the thing's own**, read off its class and
off whatever height OSM states, so a statue is worth naming from a hundred
metres and a hill from six kilometres.

It reads the landmark rows the feature layers collected, so it can run before the
basemap exists, and it does not classify tags (`landmark_classes`) or fetch
anything. Invariants: a row without a name or a position is never a candidate;
`pick_landmarks` returns most notable first.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from pyntpot.maps.candidates.candidate import Candidate
from pyntpot.maps.candidates.landmark_classes import (
    LANDMARK_CAP,
    LANDMARK_CLASSES,
    LANDMARK_RADIUS_M,
    LANDMARK_REACH_M,
    REACH_CAP_M,
    VISIBLE_PER_M,
    height_m,
)
from pyntpot.maps.projection import Projection

#: The distance a row with no distance is ranked at: further than anything.
UNKNOWN_DISTANCE_M = 9e9

#: Decimal places of a latitude or longitude in a candidate row.
COORDINATE_PLACES = 6


def landmark_reach(entry: Mapping[str, Any], scale: float = 1.0) -> float:
    """How far off the route this one thing is still worth naming, in metres.

    Its class says what it is; its own height says whether it stands above what
    is around it. The taller of the two answers wins, because a church tagged
    only as a church takes the class reach and one that states a 60 m spire
    takes the spire's.
    """
    cls = entry.get("cls") or entry.get("class") or "other"
    _tier, base = LANDMARK_REACH_M.get(cls, LANDMARK_REACH_M["other"])
    tall = height_m(entry.get("tags") or {}) * VISIBLE_PER_M
    return min(max(base, tall), REACH_CAP_M) * scale


def landmark_rank(entry: Mapping[str, Any], scale: float = 1.0) -> tuple[int, float]:
    """What order the candidates are offered in: notability, then comfort.

    The first term is the tier, so the things a runner navigates by come before
    the things they pass; the second is how comfortably the thing sits inside its
    own reach, so within a tier the nearer and the taller both rise.
    """
    cls = entry.get("cls") or entry.get("class") or "other"
    tier, _base = LANDMARK_REACH_M.get(cls, LANDMARK_REACH_M["other"])
    d = entry.get("d")
    d = entry.get("distance_m") if d is None else d
    far = UNKNOWN_DISTANCE_M if d is None else float(d)
    return (tier, far / max(landmark_reach(entry, scale), 1.0))


def _named_by(
    candidates: list[dict[str, Any]], picks: tuple[str, ...], scale: float
) -> list[dict[str, Any]]:
    """The candidates a payload named, then a marked row for each name the box lacks."""
    wanted = set(picks)
    chosen = [c for c in candidates if c["n"] in wanted]
    missing = sorted(wanted - {c["n"] for c in candidates if c["n"]})
    for entry in chosen:
        entry["picked"] = True
    return sorted(chosen, key=lambda c: landmark_rank(c, scale)) + [
        {"n": name, "cls": "missing", "d": 0.0, "x": None, "y": None, "missing": True}
        for name in missing
    ]


def pick_landmarks(
    candidates: list[dict[str, Any]],
    mode: str = "heuristic",
    radius_m: float = LANDMARK_RADIUS_M,
    cap: int = 8,
    picks: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """Choose which candidates the map labels.

    The default is a heuristic, not a decision: everything whose class earns a
    place on a map and that sits inside its own reach of the track, most
    notable first, at most `cap` of them. A payload that names landmarks
    replaces it outright, which is how the coach agent overrides a rule it can
    see. `radius_m` is the scale the class reaches are stated at rather than the
    limit itself, so a card drawn over four times the ground still stretches
    them all together.

    Args:
        candidates: Everything the box offered, each with `n`, `cls` and `d`.
            Rows a payload picked are marked `picked` in place.
        mode: `heuristic` or `all`.
        radius_m: The scale the class reaches are read at, against
            `LANDMARK_RADIUS_M`.
        cap: How many the heuristic keeps.
        picks: Names the payload chose.

    Returns:
        The chosen candidates, most notable first; a pick the box does not hold
        comes back as a row with `missing` set.
    """
    scale = radius_m / LANDMARK_RADIUS_M
    if picks:
        return _named_by(candidates, picks, scale)
    if mode == "all":
        return sorted((c for c in candidates if c["n"]), key=lambda c: landmark_rank(c, scale))
    keep = [
        c
        for c in candidates
        if c["n"] and LANDMARK_CLASSES.get(c["cls"], False) and c["d"] <= landmark_reach(c, scale)
    ]
    keep.sort(key=lambda c: landmark_rank(c, scale))
    return keep[:cap]


def _row(entry: Mapping[str, Any], projection: Projection) -> dict[str, Any]:
    """One landmark row: its position both ways, its distance off and its reach."""
    lat, lng = projection.inverse(entry["x"], entry["y"])
    reach = landmark_reach(entry)
    d = entry.get("d")
    return {
        "name": entry["n"],
        "class": entry.get("cls", ""),
        "lat": round(lat, COORDINATE_PLACES),
        "lng": round(lng, COORDINATE_PLACES),
        "x": entry["x"],
        "y": entry["y"],
        "distance_m": d,
        # How far off the route this thing is still worth naming, and whether it
        # is inside that. A tall thing well off the route reads `notable: true`
        # and a fountain at ten metres reads it too; a plaque at forty does not.
        "reach_m": round(reach),
        "notable": d is not None and d <= reach,
        "tags": entry.get("tags", {}),
    }


def rank_landmarks(
    entries: Sequence[Mapping[str, Any]], projection: Projection, cap: int = LANDMARK_CAP
) -> list[Candidate]:
    """Every named thing near the track, with its position both ways.

    Args:
        entries: The box's landmark rows, each with `n`, `cls`, `x`, `y`, `d` and
            `tags`, as the feature layers collect them.
        projection: The track's projection, to put each thing's latitude and
            longitude beside its metres.
        cap: How many to keep.

    Returns:
        At most `cap` candidates, most notable first. `where` is the thing in
        card metres and `at_m` and `span` are `None`. `detail` is `{"name",
        "class", "lat", "lng", "x", "y", "distance_m", "reach_m", "notable",
        "tags"}`, the row the label step reads.
    """
    rows = [_row(e, projection) for e in entries if e.get("n") and e.get("x") is not None]
    rows.sort(key=landmark_rank)
    return [
        Candidate("landmark", row["name"], rank, None, (row["x"], row["y"]), None, row)
        for rank, row in enumerate(rows[:cap], start=1)
    ]
