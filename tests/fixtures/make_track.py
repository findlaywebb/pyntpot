"""Build a fixture's synthetic track from public OpenStreetMap ways chosen by id.

Run as `uv run python tests/fixtures/make_track.py --contact CONTACT ...`, in one of two
modes. `--list-ways S,W,N,E` prints every `highway` way in a box (id, name, `highway`,
`sac_scale`), so a person can choose; the box is a command-line argument only and is
never written to a file the coordinate gate scans. `--ways ID,ID,...` fetches those ways,
joins them in the order given, resamples the line every 20 m and writes a GPX file
with no time, elevation or activity type. An item is a way id, or `ID:FROM:TO`, the part
of that way between two of its node ids, walked from FROM to TO; the same way may appear
more than once.

`--ways` takes checks, and fails on any miss: `--start-node ID:M`, `--via-node ID:M`
(repeatable) and `--end-node ID:M` each require the track to pass within M metres of that
OpenStreetMap node, and `--length-km MIN MAX` bounds the length. Only distances and the
length are logged, never a coordinate.

Ways are fetched with a raw `httpx` POST to `MIRROR`, sending the shipped provider's
User-Agent with the contact, one request at a time, retrying a 504 up to three times.
The raw response is not kept; the way ids and their versions are logged for the fixture's
README. Ways are chained where an end of one lies within 5 m of the last end (a shared end node is 0 m), reversing
a way where needed; a bigger gap, or a way whose two ends both join, fails.

It does not read the environment, or record anything from a person's activity.
"""

import argparse
import json
import logging
import math
import time
from collections.abc import Sequence
from itertools import pairwise
from pathlib import Path
from typing import Any

import httpx

from pyntpot.maps import OverpassFeatures

log = logging.getLogger("make_track")

#: The Overpass mirror that answers from the sessions this fixture work runs in.
MIRROR = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"

#: Metres between the points of the written track.
STEP_M = 20.0

#: The widest gap, in metres, between the end of one way and the start of the next.
JOIN_GAP_M = 5.0

#: Tries per request when the mirror answers a 504.
TRIES = 3

#: Seconds waited before the nth retry, per attempt already made.
RETRY_WAIT_S = 20.0

#: Seconds the client waits for one reply.
TIMEOUT_S = 240.0

_EARTH_M = 6_371_000.0

Point = tuple[float, float]


class TrackError(RuntimeError):
    """Raised when the ways cannot be fetched, joined or checked."""


def _metres(a: Point, b: Point) -> float:
    """Return the distance in metres between two (lat, lon) points."""
    p, q = math.radians(a[0]), math.radians(b[0])
    dlat, dlon = q - p, math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(p) * math.cos(q) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_M * math.asin(math.sqrt(h))


def _post(client: httpx.Client, query: str, agent: str) -> dict[str, Any]:
    """Post one query to the mirror, retrying a 504 with a growing wait."""
    for attempt in range(1, TRIES + 1):
        response = client.post(
            MIRROR, data={"data": query}, headers={"User-Agent": agent}, timeout=TIMEOUT_S
        )
        if response.status_code != httpx.codes.GATEWAY_TIMEOUT or attempt == TRIES:
            response.raise_for_status()
            return response.json()
        log.info("the mirror answered 504, try %d of %d", attempt, TRIES)
        time.sleep(RETRY_WAIT_S * attempt)
    raise TrackError("unreachable")


def list_ways(contact: str, box: str) -> list[str]:
    """Return one line per `highway` way in a south,west,north,east box."""
    agent = OverpassFeatures(contact).user_agent
    query = f'[out:json][timeout:180];way["highway"]({box});out tags;'
    with httpx.Client() as client:
        elements = _post(client, query, agent)["elements"]
    lines = []
    for way in elements:
        tags = way.get("tags", {})
        lines.append(
            f"{way['id']}\t{tags.get('name', '-')}\t{tags.get('highway', '-')}"
            f"\t{tags.get('sac_scale', '-')}"
        )
    return lines


def fetch_ways(
    contact: str, way_ids: Sequence[int], node_ids: Sequence[int]
) -> tuple[dict[int, dict[str, Any]], dict[int, Point]]:
    """Return the ways by id, with geometry and version, and the checked nodes' points."""
    agent = OverpassFeatures(contact).user_agent
    ways = ",".join(str(i) for i in way_ids)
    parts = f"way(id:{ways});"
    if node_ids:
        parts += f"node(id:{','.join(str(i) for i in node_ids)});"
    query = f"[out:json][timeout:180];({parts});out meta geom;"
    with httpx.Client() as client:
        elements = _post(client, query, agent)["elements"]
    found = {e["id"]: e for e in elements if e["type"] == "way"}
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in elements if e["type"] == "node"}
    missing = [i for i in way_ids if i not in found] + [i for i in node_ids if i not in nodes]
    if missing:
        raise TrackError(f"not returned by the mirror: {missing}")
    return found, nodes


def _points(way: dict[str, Any]) -> list[Point]:
    """Return a way's geometry as (lat, lon) points."""
    return [(g["lat"], g["lon"]) for g in way["geometry"]]


def _orient(way: dict[str, Any], joined: list[Point], last_node: int | None) -> list[Point]:
    """Return a way's points oriented to continue from the end of `joined`.

    A shared end node decides; failing that, the end within `JOIN_GAP_M` metres does.
    """
    points, ids = _points(way), way["nodes"]
    if last_node is not None and (last_node in (ids[0], ids[-1])) and ids[0] != ids[-1]:
        return points if ids[0] == last_node else points[::-1]
    ahead, behind = _metres(joined[-1], points[0]), _metres(joined[-1], points[-1])
    if ahead <= JOIN_GAP_M and behind <= JOIN_GAP_M:
        raise TrackError(f"way {way['id']} joins at both ends: ambiguous")
    if min(ahead, behind) > JOIN_GAP_M:
        raise TrackError(f"way {way['id']} starts {min(ahead, behind):.1f} m from the last way")
    return points if ahead <= behind else points[::-1]


def _first_orientation(first: dict[str, Any], second: dict[str, Any]) -> list[Point]:
    """Return the first way's points oriented so its end meets the second way."""
    points, ids = _points(first), first["nodes"]
    other, other_ids = _points(second), second["nodes"]
    if ids[0] != ids[-1]:
        meets = [ids[-1] in (other_ids[0], other_ids[-1]), ids[0] in (other_ids[0], other_ids[-1])]
        if meets[0] != meets[1]:
            return points if meets[0] else points[::-1]
    ends = (other[0], other[-1])
    gaps = [min(_metres(p, e) for e in ends) for p in (points[-1], points[0])]
    if gaps[0] <= JOIN_GAP_M and gaps[1] <= JOIN_GAP_M:
        raise TrackError(f"way {first['id']} joins at both ends: ambiguous")
    if min(gaps) > JOIN_GAP_M:
        raise TrackError(f"way {first['id']} is {min(gaps):.1f} m from the next way")
    return points if gaps[0] <= gaps[1] else points[::-1]


def chain(ways: Sequence[dict[str, Any]]) -> list[Point]:
    """Join ways in order into one run of points, reversing a way where needed."""
    if len(ways) == 1:
        return _points(ways[0])
    joined = _first_orientation(ways[0], ways[1])
    last = ways[0]["nodes"][-1] if joined == _points(ways[0]) else ways[0]["nodes"][0]
    for way in ways[1:]:
        points = _orient(way, joined, last)
        forward = points == _points(way)
        last = way["nodes"][-1] if forward else way["nodes"][0]
        joined.extend(points[1:])
    return joined


def part(way: dict[str, Any], start: int | None, stop: int | None) -> dict[str, Any]:
    """Return a copy of a way cut to the stretch from node `start` to node `stop`.

    The stretch runs in the order of `start` then `stop`, so it may run against the way.
    With neither node the way is returned whole.
    """
    if start is None or stop is None:
        return way
    ids = way["nodes"]
    if start not in ids or stop not in ids:
        raise TrackError(f"way {way['id']} lacks node {start} or {stop}")
    a, b = ids.index(start), ids.index(stop)
    if a == b:
        raise TrackError(f"way {way['id']} cut from node {start} to itself")
    lo, hi = min(a, b), max(a, b) + 1
    geometry, nodes = way["geometry"][lo:hi], ids[lo:hi]
    if a > b:
        geometry, nodes = geometry[::-1], nodes[::-1]
    return {**way, "geometry": geometry, "nodes": nodes}


def parse_items(text: str) -> list[tuple[int, int | None, int | None]]:
    """Parse `ID,ID:FROM:TO,...` into (way id, from node, to node) triples."""
    items: list[tuple[int, int | None, int | None]] = []
    for item in text.split(","):
        way, *nodes = item.split(":")
        if len(nodes) not in (0, 2):
            raise TrackError(f"bad way item {item!r}: use ID or ID:FROM:TO")
        if nodes:
            items.append((int(way), int(nodes[0]), int(nodes[1])))
        else:
            items.append((int(way), None, None))
    return items


def resample(points: Sequence[Point], step_m: float = STEP_M) -> list[Point]:
    """Return points every `step_m` along the line, ending on its last point."""
    out = [points[0]]
    carried = 0.0
    for a, b in pairwise(points):
        length = _metres(a, b)
        at = step_m - carried
        while at <= length:
            t = at / length
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            at += step_m
        carried = length - (at - step_m)
    if _metres(out[-1], points[-1]) > 0.0:
        out.append(points[-1])
    return out


def length_km(points: Sequence[Point]) -> float:
    """Return the length of the line in kilometres."""
    return sum(_metres(a, b) for a, b in pairwise(points)) / 1000.0


def distance_to_line(node: Point, points: Sequence[Point]) -> float:
    """Return the shortest distance in metres from a node to the line."""
    scale = math.cos(math.radians(node[0]))

    def local(p: Point) -> Point:
        return (
            math.radians(p[1] - node[1]) * scale * _EARTH_M,
            math.radians(p[0] - node[0]) * _EARTH_M,
        )

    best = math.inf
    for a, b in pairwise(points):
        (ax, ay), (bx, by) = local(a), local(b)
        dx, dy = bx - ax, by - ay
        span = dx * dx + dy * dy
        t = 0.0 if span == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / span))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def write_gpx(path: Path, points: Sequence[Point], name: str) -> None:
    """Write the points as a GPX track with no time, elevation or activity type."""
    rows = "".join(f'      <trkpt lat="{lat:.6f}" lon="{lon:.6f}"/>\n' for lat, lon in points)
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" creator="pyntpot-fixture" xmlns="http://www.topografix.com/GPX/1/1">\n'
        f"  <trk>\n    <name>{name}</name>\n    <trkseg>\n{rows}    </trkseg>\n  </trk>\n</gpx>\n",
        encoding="utf-8",
    )


def _node_check(text: str) -> tuple[int, float]:
    """Parse `ID:M` into a node id and a distance in metres."""
    node, _, metres = text.partition(":")
    return int(node), float(metres)


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Build a fixture track from OSM ways.")
    parser.add_argument("--contact", required=True, help="how the mirror's operator reaches you")
    parser.add_argument("--list-ways", metavar="S,W,N,E", help="list the highway ways in a box")
    parser.add_argument("--ways", metavar="ID[:FROM:TO],...", help="ways to join, in order")
    parser.add_argument("--out", type=Path, help="the GPX file to write")
    parser.add_argument("--name", default="Fixture track (synthetic)", help="the GPX track name")
    parser.add_argument("--start-node", metavar="ID:M")
    parser.add_argument("--via-node", metavar="ID:M", action="append", default=[])
    parser.add_argument("--end-node", metavar="ID:M")
    parser.add_argument("--length-km", nargs=2, type=float, metavar=("MIN", "MAX"))
    return parser.parse_args(argv)


def _checks(args: argparse.Namespace) -> list[tuple[str, int, float]]:
    """Return the node checks as (label, node id, metres)."""
    checks = []
    if args.start_node:
        checks.append(("start", *_node_check(args.start_node)))
    checks += [("via", *_node_check(text)) for text in args.via_node]
    if args.end_node:
        checks.append(("end", *_node_check(args.end_node)))
    return checks


def build(args: argparse.Namespace) -> int:
    """Fetch, join, check, resample and write; return 1 when a check misses."""
    items = parse_items(args.ways)
    way_ids = list(dict.fromkeys(way for way, _, _ in items))
    checks = _checks(args)
    found, nodes = fetch_ways(args.contact, way_ids, [node for _, node, _ in checks])
    for way_id in way_ids:
        tags = found[way_id].get("tags", {})
        log.info(
            "way %d version %d %s %s",
            way_id,
            found[way_id]["version"],
            tags.get("highway", "-"),
            tags.get("name", "-"),
        )
    for node_id in nodes:
        log.info("node %d found", node_id)
    points = resample(chain([part(found[way], a, b) for way, a, b in items]))
    failed = False
    for label, node_id, limit in checks:
        gap = distance_to_line(nodes[node_id], points)
        failed |= gap > limit
        log.info("%s node %d: %.0f m from the track (limit %.0f m)", label, node_id, gap, limit)
    length = length_km(points)
    log.info("length %.2f km, %d points", length, len(points))
    if args.length_km and not args.length_km[0] <= length <= args.length_km[1]:
        log.error("length outside %.1f to %.1f km", *args.length_km)
        failed = True
    if failed:
        return 1
    if args.out:
        write_gpx(args.out, points, args.name)
        log.info("wrote %s", args.out)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the chosen mode; return the exit status."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    args = _parse(argv)
    try:
        if args.list_ways:
            for line in list_ways(args.contact, args.list_ways):
                log.info("%s", line)
            return 0
        if args.ways:
            return build(args)
    except (TrackError, httpx.HTTPError, json.JSONDecodeError):
        log.exception("failed")
        return 1
    log.error("give --list-ways or --ways")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
