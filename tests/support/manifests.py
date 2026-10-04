"""Build small valid plates manifests for tests, one keyword per field to override.

A test states only the manifest fields it cares about; every other field takes a
small, valid value here, so no test hand-writes the whole record.
"""

from dataclasses import replace
from typing import Any

from pyntpot.maps.card import Card
from pyntpot.maps.plates import DarkGrid, Manifest

#: The frame of the default manifest: an 80 by 60 display card over 800 by 600 m.
CARD = Card(
    box=(0.0, 0.0, 800.0, 600.0), display=(80, 60), render=(160, 120), mpp=5.0, mpp_display=10.0
)

#: The manifest every override starts from.
_DEFAULT = Manifest(
    key="iTEST",
    hash="0123456789abcdef",
    route0=(0.0, 0.0),
    files={"paper": "paper.webp", "wash": "wash.webp", "pen": "pen.webp"},
    sizes={"paper": 1, "wash": 1, "pen": 1},
    bytes=3,
    card=CARD,
    ribbon_m=40,
    span_m=800,
    places=(),
    candidates=(),
    label_geom={"roads": [], "rivers": [], "coast": [], "crossings": []},
    wet_px={},
    gran_px=6.0,
    labels_hash="fedcba9876543210",
    sources=(),
    dark=DarkGrid(w=2, h=2, values=((0.0, 0.0), (0.0, 0.0))),
    wood_px=0,
    water_px=0,
    timing={},
)


def manifest_for_test(**over: Any) -> Manifest:
    """Return a small valid `Manifest` with every field set, overridden by keyword."""
    return replace(_DEFAULT, **over)
