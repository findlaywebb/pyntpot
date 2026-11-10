"""The brush sheet catalogue: the tables a brush id is read from.

Key types: `BRUSH_TREATMENTS`, the stroke treatment of each sheet row, keyed `"1"` to `"8"`;
`PEN_ROWS`, the rows that are a nib rather than a brush; and `BRUSH_COLOURS`, the colour
column of an id, keyed by the id's three-letter prefix and then the column letter.

A brush id `<PREFIX><row>-<column>`, such as `MAJ2-a`, is an opaque sheet cell name. It
builds no brush: `ink.brush` reads these tables and does that.
"""

from collections.abc import Mapping
from types import MappingProxyType

#: The stroke treatment of each sheet row. A brush id is a prefix, a row and a
#: colour column: `MAJ2-a` is treatment 2, colour a. Widths live in `BrushStyle`,
#: because one treatment is drawn at a river's width on one plate, a lane's on another.
BRUSH_TREATMENTS: Mapping[str, Mapping[str, float]] = MappingProxyType(
    {
        "1": MappingProxyType(
            {
                "name_wet": 1.0,
                "darkness": 1.8,
                "bristles": 26,
                "gap": 0.03,
                "dry": 0.15,
                "thr": 0.34,
                "texture": 0.32,
                "press": 0.14,
                "load": 0.6,
                "pool": 0.0,
                "bleed": 1.5,
                "lift": 34,
            }
        ),
        "2": MappingProxyType(
            {
                "darkness": 2.0,
                "bristles": 22,
                "gap": 0.09,
                "dry": 0.30,
                "thr": 0.38,
                "texture": 0.42,
                "press": 0.20,
                "load": 0.55,
                "pool": 0.0,
                "bleed": 1.1,
                "lift": 30,
            }
        ),
        "3": MappingProxyType(
            {
                "darkness": 2.4,
                "bristles": 16,
                "gap": 0.14,
                "dry": 0.42,
                "thr": 0.42,
                "texture": 0.55,
                "press": 0.26,
                "load": 0.5,
                "pool": 0.0,
                "bleed": 0.9,
                "lift": 26,
            }
        ),
        "4": MappingProxyType(
            {
                "darkness": 4.8,
                "bristles": 18,
                "gap": 0.28,
                "dry": 0.72,
                "thr": 0.48,
                "texture": 0.82,
                "press": 0.34,
                "load": 0.7,
                "pool": 0.0,
                "bleed": 0.5,
                "lift": 28,
            }
        ),
        "5": MappingProxyType(
            {
                "darkness": 7.2,
                "bristles": 5,
                "gap": 0.04,
                "dry": 0.22,
                "thr": 0.40,
                "texture": 0.40,
                "press": 0.18,
                "load": 1.6,
                "pool": 1.4,
                "bleed": 0.3,
                "lift": 12,
            }
        ),
        "6": MappingProxyType(
            {
                "darkness": 6.0,
                "bristles": 6,
                "gap": 0.0,
                "dry": 0.10,
                "thr": 0.32,
                "texture": 0.16,
                "press": 0.10,
                "load": 0.5,
                "pool": 0.9,
                "bleed": 0.45,
                "lift": 16,
                "solid": 0.75,
            }
        ),
        "7": MappingProxyType(
            {
                "darkness": 7.4,
                "bristles": 8,
                "gap": 0.44,
                "dry": 0.82,
                "thr": 0.53,
                "texture": 0.86,
                "press": 0.45,
                "load": 0.4,
                "pool": 0.0,
                "bleed": 0.35,
                "lift": 14,
            }
        ),
        "8": MappingProxyType(
            {
                "darkness": 6.4,
                "bristles": 4,
                "gap": 0.02,
                "dry": 0.20,
                "thr": 0.40,
                "texture": 0.36,
                "press": 0.14,
                "load": 1.2,
                "pool": 0.8,
                "bleed": 0.25,
                "lift": 14,
            }
        ),
    }
)

#: The treatment rows that are a nib rather than a brush: a flat core, a
#: touch-down blot, and a line that thins rather than breaking when it runs low.
PEN_ROWS = frozenset({"5", "6", "8"})

#: The colour column of a brush id, per three-letter prefix.
BRUSH_COLOURS: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        "RIV": MappingProxyType({"a": "#255d80"}),
        "STR": MappingProxyType({"a": "#255d80"}),
        "MAJ": MappingProxyType(
            {"a": "#b5623f", "b": "#8a5a2c", "c": "#6b4423", "d": "#7b7266", "e": "#2b2620"}
        ),
        "LAN": MappingProxyType({"a": "#6b4423"}),
        "TRK": MappingProxyType(
            {
                "a": "#6b4423",
                "b": "#b5623f",
                "c": "#7d7468",
                "d": "#6f6636",
                "e": "#95584a",
                "f": "#2b2620",
            }
        ),
    }
)
