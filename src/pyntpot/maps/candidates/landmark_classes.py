"""What a set of OSM tags means as a landmark: its class, its tier and its reach.

Key names: `classify`, the landmark class one tag set belongs to; `height_m`,
how tall OSM says a thing is; `LANDMARK_CLASSES`, whether the heuristic keeps a
class; `LANDMARK_REACH_M`, each class's tier and how far off the route it is
still worth naming; `OFFERED_CLASSES`, the classes a named area is offered for.

The tag lists `classify` reads for tourism, man-made, amenity and leisure
landmarks are the Overpass provider's own, so the vocabulary the box asks OSM
for and the vocabulary a thing is classed by cannot drift apart.

It does not rank, choose or project anything, and it reads no payload: the
landmark ranking is `landmarks`. Invariants: `classify` always returns a key of
`LANDMARK_REACH_M`, and `other` is the class of anything unrecognised.
"""

import re
from collections.abc import Mapping

from pyntpot.maps.providers.overpass import (
    AMENITY_LANDMARKS,
    LEISURE_LANDMARKS,
    MANMADE_LANDMARKS,
    TOURISM_LANDMARKS,
)

#: `historic` values that are a monument someone put there on purpose. The rest
#: of the tag's range is a site rather than a marker: a colliery, a station and
#: an earthwork are all history, but none of them is a thing to run past and see.
MONUMENT_HISTORIC = (
    "monument",
    "memorial",
    "castle",
    "wayside_cross",
    "cross",
    "tower",
    "cannon",
    "milestone",
    "boundary_stone",
)

#: `memorial` values that mark a wall, not a thing in the landscape. OSM tags a
#: blue plaque `historic=memorial` with the name of the building it is screwed
#: to, so a theatre, a hotel and a war name all arrive as monuments near the
#: route and one of them can end up naming a climb. A
#: plaque is a real record and a bad landmark; it is classed apart, not dropped.
PLAQUE_MEMORIAL = ("plaque", "blue_plaque")

#: What a landmark tag means, and whether the heuristic keeps it. A village is
#: classed and offered but never kept: a place name is not a landmark, it is a
#: label, and a map crowded with them reads worse.
LANDMARK_CLASSES: dict[str, bool] = {
    "sculpture": True,
    "monument": True,
    "viewpoint": True,
    "summit": True,
    "building": True,
    "bridge": True,
    "tower": True,
    "worship": True,
    "attraction": True,
    "block": True,
    "sight": False,
    "ruin": False,
    "place": False,
    "plaque": False,
    "other": False,
}

#: How far off the route a class of thing is still worth naming, in metres, and
#: how notable it is against the other classes. A mountain or an unusually tall
#: building is notable from further off, and the corollary is that a fountain
#: eight metres away is not notable at all. One radius for everything made the
#: first half impossible and the second half inevitable.
#:
#: The tier is what a runner would pick out first, not what OSM thinks is
#: important: a hill, a tower, a spire, a named building and a bridge are the
#: things you navigate by, a monument or a statue is something you pass, and a
#: ruin or a plaque is something you would have to stop and read.
LANDMARK_REACH_M: dict[str, tuple[int, float]] = {
    "summit": (1, 6000.0),
    "tower": (1, 1200.0),
    "worship": (1, 700.0),
    "building": (1, 450.0),
    "viewpoint": (1, 450.0),
    "attraction": (1, 450.0),
    "bridge": (1, 250.0),
    "block": (2, 250.0),
    "monument": (2, 250.0),
    "sculpture": (2, 150.0),
    "sight": (2, 150.0),
    "ruin": (3, 200.0),
    "place": (3, 300.0),
    "plaque": (3, 30.0),
    "other": (3, 150.0),
}

#: The classes a named area is offered as a candidate for at all. A place name,
#: a plaque and anything unrecognised are drawn or dropped by other rules and
#: were never landmarks; everything else is offered and ranked.
OFFERED_CLASSES = frozenset(LANDMARK_REACH_M) - {"place", "plaque", "other"}

#: A building tag OSM puts on the fabric rather than on the institution: every
#: block of a campus and every wing of a hospital carries one, so "Ilam Hall"
#: and "Hartington Hall" arrive looking exactly like the cathedral next to them.
#: They are still worth offering, because one of them is sometimes the thing on
#: the corner; they are not worth ranking above a spire, a tower or a zoo.
FABRIC_BUILDINGS = ("university", "hospital", "museum")
#: What a landmark building is: something that has a name because of what it is.
NAMED_BUILDINGS = ("castle", "palace", "stadium", "train_station")
#: The `tourism` values that are a destination, and the ones that are a sign on
#: a railing. OSM tags every enclosure in a zoo `tourism=attraction`, which is
#: how an enclosure sign can outrank the zoo itself.
TOURISM_DESTINATIONS = ("zoo", "museum", "aquarium", "theme_park")

#: The radius every reach above is stated against. A larger radius handed to
#: `pick_landmarks`, as a card over more ground has, scales them all together.
LANDMARK_RADIUS_M = 300.0

#: How far something is notable from, per metre of its own height. A thing that
#: stands above what is around it is seen from further away than its footprint
#: says, which is the whole point of a cathedral or a radio mast. Sixty metres
#: of reach a metre of height puts a thirty-metre spire at 1.8 km and a 108 m
#: dome at about 6.5 km, and the card's own box
#: cuts anything the reader could not see on the map anyway.
VISIBLE_PER_M = 60.0
#: Past this, height stops buying reach. Nothing on a session's card is further
#: off than this and still the thing a person would name.
REACH_CAP_M = 8000.0

#: How many named things the box offers as landmark candidates.
LANDMARK_CAP = 80

#: Metres in a foot, and the storey height `building:levels` is read at.
FOOT_M = 0.3048
LEVEL_M = 3.2

#: A rule's values: the tag values it accepts, or `ANY` for any non-empty value.
ANY = None

#: The classes in the order they are tried: a tag set takes the earliest class
#: for which it passes one of the tests. Each test is a tag key and the values it accepts.
_RULES: tuple[tuple[str, tuple[tuple[str, tuple[str, ...] | None], ...]], ...] = (
    ("sculpture", (("tourism", ("artwork",)), ("artwork_type", ANY))),
    ("summit", (("natural", ("peak",)),)),
    ("viewpoint", (("tourism", ("viewpoint",)),)),
    (
        "tower",
        (("man_made", ("tower", "water_tower", "chimney", "mast")), ("building", ("tower",))),
    ),
    (
        "monument",
        (("historic", MONUMENT_HISTORIC), ("man_made", ("obelisk", "monument", "lighthouse"))),
    ),
    (
        "worship",
        (
            ("amenity", ("place_of_worship",)),
            (
                "building",
                ("cathedral", "church", "chapel", "mosque", "synagogue", "temple"),
            ),
        ),
    ),
    ("bridge", (("man_made", ("bridge",)), ("bridge", ANY))),
    ("attraction", (("tourism", TOURISM_DESTINATIONS),)),
    (
        "building",
        (
            ("building", NAMED_BUILDINGS),
            ("amenity", AMENITY_LANDMARKS),
            ("leisure", LEISURE_LANDMARKS),
            ("man_made", MANMADE_LANDMARKS),
        ),
    ),
    ("sight", (("tourism", TOURISM_LANDMARKS),)),
    ("block", (("building", FABRIC_BUILDINGS),)),
    ("ruin", (("historic", ANY),)),
    ("place", (("place", ANY),)),
)


def _passes(tags: Mapping[str, str], key: str, values: tuple[str, ...] | None) -> bool:
    """Whether one tag is among the accepted values, or is set at all for `ANY`."""
    value = tags.get(key)
    return bool(value) if values is None else value in values


def classify(tags: Mapping[str, str]) -> str:
    """The landmark class one OSM tag set belongs to.

    A blue plaque is classed first and apart: OSM tags it `historic=memorial`
    with the name of the building it is screwed to, so it would otherwise arrive
    as a monument. After that the first matching class wins, from `sculpture`
    down to `place`, and a tag set that matches none is `other`.
    """
    if tags.get("historic") == "memorial" and tags.get("memorial") in PLAQUE_MEMORIAL:
        return "plaque"
    for cls, tests in _RULES:
        if any(_passes(tags, key, values) for key, values in tests):
            return cls
    return "other"


def _stated_height(raw: str) -> float:
    """The metres a `height` tag states, or zero when it states none."""
    number = re.match(r"([\d.]+)", raw)
    if not number:
        return 0.0
    try:
        value = float(number.group(1))
    except ValueError:
        return 0.0
    if "'" in raw or "ft" in raw:
        value *= FOOT_M
    return value


def height_m(tags: Mapping[str, str]) -> float:
    """How tall OSM says this thing is, in metres, or zero when it does not say.

    `height` is metres unless it names another unit, and `building:levels` is
    the only other statement of height that is common enough to be worth
    reading. Anything unparseable is no statement rather than a guess.
    """
    stated = _stated_height(str(tags.get("height", "")).strip().lower())
    if stated > 0:
        return stated
    levels = str(tags.get("building:levels", "")).strip()
    try:
        return float(levels) * LEVEL_M if levels else 0.0
    except ValueError:
        return 0.0
