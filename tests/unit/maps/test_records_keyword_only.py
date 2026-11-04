"""The records the pipeline hands back are built by keyword, and all but two are frozen.

Each record is built from a minimal keyword dict; the same values passed by position
raise `TypeError`. The fourteen frozen records refuse assignment; `Label` and `Span`
stay mutable because the placer fills them in.
"""

import dataclasses
from typing import Any

import pytest

from pyntpot.maps import (
    BoundingBox,
    Card,
    Credit,
    DarkGrid,
    ElevationGrid,
    ElevationPatch,
    HillshadeBand,
    HillshadeImage,
    Label,
    Layers,
    Manifest,
    Projection,
    River,
    Road,
    Span,
    VectorArea,
    VectorLine,
)

CARD: dict[str, Any] = {
    "box": (0.0, 0.0, 100.0, 80.0),
    "display": (100, 80),
    "render": (200, 160),
    "mpp": 0.5,
    "mpp_display": 1.0,
}

DARK: dict[str, Any] = {"w": 1, "h": 1, "values": ((0.0,),)}

LAYERS: dict[str, Any] = {
    "route": ((0.0, 0.0), (1.0, 1.0)),
    "cover": {},
    "cover_order": (),
    "lakes": (),
    "sea": (),
    "coastline": (),
    "roads": (),
    "rivers": (),
    "elevation": None,
    "ribbon_m": 420,
    "wet_px": {},
    "minor_roads": False,
    "blotch_m": 1.0,
    "dab_spacing_m": 1.0,
    "gran_m": 1.0,
}

MANIFEST: dict[str, Any] = {
    "hash": "0" * 16,
    "files": {},
    "sizes": {},
    "bytes": 0,
    "card": Card(**CARD),
    "ribbon_m": 420,
    "span_m": 4000,
    "wet_px": {},
    "gran_px": 1.0,
    "dark": DarkGrid(**DARK),
    "wood_px": 0,
    "water_px": 0,
}

#: Each frozen record with the fewest keywords that build it.
FROZEN: dict[type, dict[str, Any]] = {
    Card: CARD,
    Credit: {"text": "© OpenStreetMap contributors", "url": "https://osm.org", "short": "OSM"},
    Manifest: MANIFEST,
    DarkGrid: DARK,
    Layers: LAYERS,
    River: {
        "line": ((0.0, 0.0), (1.0, 1.0)),
        "cls": "major",
        "name": "East Lyn",
        "width_px": 4.0,
        "name_width_px": 2.0,
    },
    Road: {
        "line": ((0.0, 0.0), (1.0, 1.0)),
        "cls": "major",
        "band": "major",
        "highway": "primary",
        "name": "",
        "ref": "A39",
    },
    ElevationPatch: {
        "n": 1,
        "x0": 0.0,
        "y0": 0.0,
        "x1": 1.0,
        "y1": 1.0,
        "values": (0.0,),
        "low": 0,
        "high": 0,
    },
    ElevationGrid: {
        "n": 1,
        "box": BoundingBox(51.2, -3.9, 51.3, -3.8),
        "lats": (51.2,),
        "lons": (-3.9,),
        "elev": (0.0,),
    },
    VectorArea: {"path": "M0 0", "inner": ""},
    VectorLine: {"path": "M0 0"},
    HillshadeBand: {"path": "M0 0", "sign": 1, "level": 0.5},
    HillshadeImage: {"href": "", "x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0, "px": 1, "py": 1},
    Projection: {"lat0": 51.23, "lat_ref": 51.23, "lng_ref": -3.83},
}

#: The two mutable records, each with the fewest keywords that build it.
MUTABLE: dict[type, dict[str, Any]] = {
    Label: {"name": "Lynmouth"},
    Span: {"name": "Countisbury Hill"},
}

RECORDS: dict[type, dict[str, Any]] = {**FROZEN, **MUTABLE}


@pytest.mark.parametrize(
    ("record", "keywords"), RECORDS.items(), ids=[record.__name__ for record in RECORDS]
)
def test_a_returned_record_takes_only_keywords(record: type, keywords: dict[str, Any]) -> None:
    """A record builds from keywords, and the same values passed by position raise `TypeError`."""
    record(**keywords)
    with pytest.raises(TypeError):
        record(*keywords.values())


@pytest.mark.parametrize(
    ("record", "keywords"), FROZEN.items(), ids=[record.__name__ for record in FROZEN]
)
def test_a_returned_record_is_frozen(record: type, keywords: dict[str, Any]) -> None:
    """Assigning a field of a frozen record raises `FrozenInstanceError`."""
    built = record(**keywords)
    first = dataclasses.fields(built)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(built, first, getattr(built, first))
