"""Make the preview fixture: a synthetic route and the three payloads that hold every feature a theme can get wrong.

Run as `PYTHONPATH=tests uv run python -m fixtures.make_preview OUT_DIR`; it writes `track.gpx`,
`overpass-<key>.json`, `landcover-<key>.json`, `elevation-<key>.json` and `README.md` into
`OUT_DIR`, and nothing else. `tests/fixtures/preview/` is its committed output; the fixture
test runs it into a temporary directory and compares bytes.

The layout is in metres, x east and y north from the centre of the track's box (a rectangle
1.5 km east to west by 1.6 km north to south). The route, the coast, the offshore island,
the lake and its island, the river that parts round a gravel bar, the stream that joins it,
a major and a minor road, the cover patches (some under `min_patch_px`), the places and the
hill are laid so that they meet each other. `preview_payloads` turns the layout into bytes,
through one `Projection`, and the cache key comes from the track as read back from the
written GPX.

It makes up its data: nothing here is recorded from OpenStreetMap, and the names are real
names of the Lynmouth area standing at made-up places. It fetches nothing and reads no
environment. Invariants: running it twice gives identical bytes; every element lies inside
the features fetch box of the default `FetchMargins`, rounded inward by a metre, and the
land cover is written only inside that box too.
"""

import argparse
import logging
import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from fixtures.preview_payloads import (
    PROJECTION,
    Elements,
    Point,
    elevation_text,
    gpx_text,
    payload_text,
    readme_text,
)

from pyntpot.ink.polyline import foot_on
from pyntpot.maps import Cache, OpenTopoData, OverpassFeatures, Track
from pyntpot.maps.cache import MARGIN_M

log = logging.getLogger("make_preview")

#: How the providers name the caller in the key; never sent.
CONTACT = "pyntpot-tests@example.invalid"

#: Metres between the points of the written track.
STEP_M = 20.0

#: The features fetch box's half sides in metres, rounded inward by a metre: the track's
#: half sides (750, 800) plus the default margin (1500) less one.
EDGE_X = 2249.0
EDGE_Y = 2299.0

#: Where the coast runs, east to west, so land lies on its left (south); the sea is north.
COAST = [(EDGE_X, 450.0), (900.0, 450.0), (600.0, 700.0), (300.0, 1150.0), (-EDGE_X, 1150.0)]

#: The offshore island's centre and radius, and its ring's vertex count.
ISLAND = (950.0, 900.0)
ISLAND_R = 110.0
ISLAND_N = 24

#: The lake's centre, semi-axes and vertex count, and its island's radius and vertex count.
LAKE = (700.0, 0.0)
LAKE_RX = 200.0
LAKE_RY = 160.0
LAKE_N = 32
LAKE_ISLAND_R = 50.0
LAKE_ISLAND_N = 16

#: The East Lyn River, south to north, and its second channel round the gravel bar.
RIVER = [
    (250.0, -EDGE_Y),
    (290.0, -1700.0),
    (270.0, -1200.0),
    (300.0, -900.0),
    (320.0, -720.0),
    (290.0, -500.0),
    (330.0, -300.0),
    (335.0, -200.0),
    (330.0, -100.0),
    (375.0, -40.0),
    (400.0, 60.0),
    (375.0, 150.0),
    (335.0, 230.0),
    (360.0, 400.0),
    (420.0, 650.0),
    (450.0, 925.0),
]
SIDE_CHANNEL = [
    (330.0, -100.0),
    (292.0, -45.0),
    (275.0, 60.0),
    (295.0, 150.0),
    (335.0, 230.0),
]

#: The gravel bar between the two channels.
BAR = [
    (330.0, -70.0),
    (355.0, -20.0),
    (372.0, 60.0),
    (352.0, 130.0),
    (332.0, 195.0),
    (312.0, 130.0),
    (297.0, 60.0),
    (310.0, -20.0),
]

#: The West Lyn River, from the fetch box's west edge to its meeting with the East Lyn.
STREAM = [
    (-EDGE_X, -1300.0),
    (-1900.0, -1250.0),
    (-1300.0, -1180.0),
    (-700.0, -1060.0),
    (-450.0, -900.0),
    (-300.0, -740.0),
    (-100.0, -700.0),
    (100.0, -690.0),
    (320.0, -720.0),
]

#: The major road crosses the minor road, the river and the stream; the minor road crosses the river.
MAJOR = [
    (-EDGE_X, 450.0),
    (-1300.0, 330.0),
    (-720.0, 110.0),
    (-250.0, -480.0),
    (-100.0, -880.0),
    (250.0, -1180.0),
    (900.0, -1250.0),
    (EDGE_X, -1400.0),
]
MINOR = [
    (-EDGE_X, -300.0),
    (-1500.0, -290.0),
    (-1000.0, -250.0),
    (-600.0, -200.0),
    (-100.0, -195.0),
    (200.0, -260.0),
    (330.0, -297.0),
    (500.0, -340.0),
    (900.0, -390.0),
    (1600.0, -420.0),
    (EDGE_X, -400.0),
]

#: Where the places and landmarks stand.
LYNMOUTH = (440.0, 880.0)
LYNTON = (-20.0, 950.0)
COUNTISBURY = (1000.0, -150.0)
FORELAND_POINT = (1050.0, 450.0)
WATERSMEET = (330.0, -735.0)

#: The hill: its centre, height above the floor, sigma, and the floor, all in metres.
HILL = (-700.0, 600.0)
HILL_HEIGHT = 300.0
HILL_SIGMA = 500.0
FLOOR_M = 20.0

#: Cover patches as west, south, east, north metres, by tag. The small ones are 50 m square.
LARGE_COVER: list[tuple[dict[str, str], tuple[float, float, float, float]]] = [
    ({"landuse": "meadow"}, (400.0, -900.0, 1200.0, -480.0)),
    ({"natural": "heath"}, (-1250.0, 150.0, -300.0, 1000.0)),
    ({"landuse": "residential"}, (-250.0, 820.0, 200.0, 1080.0)),
    ({"natural": "bare_rock"}, (-900.0, 400.0, -500.0, 800.0)),
]
SMALL_COVER: list[tuple[dict[str, str], tuple[float, float, float, float]]] = [
    ({"landuse": "meadow"}, (-560.0, 100.0, -510.0, 150.0)),
    ({"natural": "heath"}, (700.0, -480.0, 750.0, -430.0)),
]
LARGE_WOOD = (480.0, 240.0, 950.0, 420.0)
SMALL_WOOD = (350.0, -640.0, 400.0, -590.0)

#: A track point this far in from the coast and no nearer, in metres.
COAST_CLEARANCE_M = 300.0


def _box_ring(box: tuple[float, float, float, float]) -> list[Point]:
    """Return a rectangle's anticlockwise ring, closed."""
    x0, y0, x1, y1 = box
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def _ellipse(centre: Point, rx: float, ry: float, count: int, *, anticlockwise: bool) -> list[Point]:
    """Return a closed ring of `count` vertices round a centre, wound as asked."""
    sign = 1 if anticlockwise else -1
    angles = [sign * 2 * math.pi * k / count for k in range(count)]
    ring = [(centre[0] + rx * math.cos(a), centre[1] + ry * math.sin(a)) for a in angles]
    return [*ring, ring[0]]


def _road_y(road: Sequence[Point], x: float) -> float:
    """Return a road's northing at an easting, along its segments."""
    for (xa, ya), (xb, yb) in pairwise(road):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    raise ValueError(f"the road does not reach x = {x}")


def _along(road: Sequence[Point], x0: float, x1: float, dy: float) -> list[Point]:
    """Return the road's points between two eastings, moved `dy` north, in the order x0 to x1."""
    lo, hi = sorted((x0, x1))
    inner = [(x, y) for x, y in road if lo < x < hi]
    points = [(lo, _road_y(road, lo)), *inner, (hi, _road_y(road, hi))]
    points = [(x, y + dy) for x, y in points]
    return points if x0 <= x1 else points[::-1]


def _sample(corners: Sequence[Point]) -> list[Point]:
    """Return corners joined by points no more than `STEP_M` apart, the corners themselves kept."""
    out = [corners[0]]
    for (xa, ya), (xb, yb) in pairwise(corners):
        steps = max(1, math.ceil(math.dist((xa, ya), (xb, yb)) / STEP_M))
        out += [(xa + (xb - xa) * k / steps, ya + (yb - ya) * k / steps) for k in range(1, steps + 1)]
    return out


@dataclass(frozen=True)
class Route:
    """The route in metres: its points every `STEP_M` and the span of its riverside walk.

    Attributes:
        points: The route's points, in order.
        river_first: Index of the first point of the walk up the East Lyn River's bank.
        river_last: Index of the last point of the walk back down it.
    """

    points: list[Point]
    river_first: int
    river_last: int


def route() -> Route:
    """Lay the route: down from Lynton, along the road, up the river bank and back, out along the road and back, to the stream."""
    start = [
        (-300.0, 800.0),
        (-520.0, 640.0),
        (-700.0, 430.0),
        (-750.0, 300.0),
        (-735.0, 100.0),
        (-660.0, -100.0),
    ]
    river_out = [
        (358.0, -300.0),
        (354.0, -200.0),
        (356.0, -110.0),
        (397.0, -45.0),
        (422.0, 60.0),
        (397.0, 155.0),
        (372.0, 235.0),
        (380.0, 320.0),
    ]
    river_back = [(x + 12.0, y) for x, y in reversed(river_out)]
    finish = [
        (-115.0, -420.0),
        (-135.0, -560.0),
        (-150.0, -650.0),
        (-210.0, -760.0),
        (-260.0, -800.0),
    ]
    before = _sample([*start, *_along(MINOR, -600.0, 350.0, 6.0)])
    walk = _sample([before[-1], *river_out, *river_back])
    after = _sample([walk[-1], *_along(MINOR, 380.0, 750.0, 6.0), *_along(MINOR, 750.0, -100.0, -6.0), *finish])
    return Route([*before, *walk[1:], *after[1:]], len(before), len(before) + len(walk) - 2)


def coast_side(point: Point) -> float:
    """Return how far north of the coast a point lies, in metres; positive is sea."""
    x, y = min(max(point[0], -EDGE_X), EDGE_X), point[1]
    for (xa, ya), (xb, yb) in pairwise(COAST[::-1]):
        if xa <= x <= xb:
            return y - (ya + (yb - ya) * (x - xa) / (xb - xa))
    raise ValueError(f"the coast does not reach x = {x}")


def elevation(point: Point) -> float:
    """Return the ground's height at a point in metres: sea 0, land a floor and a hill."""
    in_island = math.dist(point, ISLAND) <= ISLAND_R
    if coast_side(point) > 0 and not in_island:
        return 0.0
    hill = HILL_HEIGHT * math.exp(-(math.dist(point, HILL) ** 2) / (2 * HILL_SIGMA**2))
    return FLOOR_M + hill


def coast_gap(point: Point) -> float:
    """Return how far a point is from the coast's line, in metres."""
    return foot_on(point, COAST)[0]


def _features(ids: Elements) -> list[dict[str, object]]:
    """Make the feature payload's elements: coast, water, roads, woods, then places and landmarks."""
    lake_ring = _ellipse(LAKE, LAKE_RX, LAKE_RY, LAKE_N, anticlockwise=True)
    lake_island = _ellipse(LAKE, LAKE_ISLAND_R, LAKE_ISLAND_R, LAKE_ISLAND_N, anticlockwise=False)
    river = {"waterway": "river", "name": "East Lyn River"}
    return [
        ids.way({"natural": "coastline"}, COAST),
        ids.way(
            {"natural": "coastline"},
            _ellipse(ISLAND, ISLAND_R, ISLAND_R, ISLAND_N, anticlockwise=True),
        ),
        ids.relation(
            {"type": "multipolygon", "natural": "water"},
            [("outer", lake_ring), ("inner", lake_island)],
        ),
        ids.way(river, RIVER),
        ids.way(river, SIDE_CHANNEL),
        ids.way({"waterway": "stream", "name": "West Lyn River"}, STREAM),
        ids.way({"highway": "primary"}, MAJOR),
        ids.way({"highway": "unclassified"}, MINOR),
        ids.way({"natural": "wood"}, _box_ring(LARGE_WOOD)),
        ids.way({"natural": "wood"}, _box_ring(SMALL_WOOD)),
        ids.node({"place": "village", "name": "Lynmouth"}, LYNMOUTH),
        ids.node({"place": "town", "name": "Lynton"}, LYNTON),
        ids.node({"place": "hamlet", "name": "Countisbury"}, COUNTISBURY),
        ids.node({"man_made": "lighthouse", "name": "Foreland Point"}, FORELAND_POINT),
        ids.node({"tourism": "attraction", "name": "Watersmeet"}, WATERSMEET),
    ]


def _landcover(ids: Elements) -> list[dict[str, object]]:
    """Make the land cover payload's elements: the gravel bar, the large patches, the small ones."""
    bar = [*BAR, BAR[0]]
    made = [ids.way({"natural": "shingle"}, bar)]
    for tags, box in [*LARGE_COVER, *SMALL_COVER]:
        made.append(ids.way(tags, _box_ring(box)))
    return made


def _fetch_box_edges(track: Track) -> tuple[float, float]:
    """Return the features fetch box's half sides in metres, which the layout must stay inside."""
    south, west, north, east = track.bounding_box(MARGIN_M)
    (x0, y0), (x1, y1) = PROJECTION(south, west), PROJECTION(north, east)
    return min(-x0, x1), min(-y0, y1)


def make(out_dir: Path) -> str:
    """Write the preview fixture into a directory and return its cache key.

    Args:
        out_dir: Where the five files go; created when missing.

    Returns:
        The key the payloads are named by, from the track as read back from its GPX.

    Raises:
        ValueError: When the layout reaches past the features fetch box.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    walk = route()
    gpx = out_dir / "track.gpx"
    gpx.write_bytes(gpx_text("Lynmouth preview route (synthetic)", walk.points).encode())
    track = Track.from_gpx(gpx)
    key = Cache(out_dir).key(track, OverpassFeatures(CONTACT), OpenTopoData(CONTACT))
    half_x, half_y = _fetch_box_edges(track)
    if EDGE_X > half_x or EDGE_Y > half_y:
        raise ValueError(f"the layout reaches past the fetch box ({half_x:.1f}, {half_y:.1f})")
    ids = Elements()
    texts = {
        f"overpass-{key}.json": payload_text(_features(ids)),
        f"landcover-{key}.json": payload_text(_landcover(ids)),
        f"elevation-{key}.json": elevation_text(track.bounding_box(MARGIN_M), elevation),
        "README.md": readme_text(key, len(walk.points), walk.river_first, walk.river_last),
    }
    for name, text in texts.items():
        (out_dir / name).write_bytes(text.encode())
    return key


def main() -> None:
    """Write the fixture into the directory named on the command line."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Make the preview fixture.")
    parser.add_argument("out_dir", type=Path)
    log.info("key %s", make(parser.parse_args().out_dir))


if __name__ == "__main__":
    main()
