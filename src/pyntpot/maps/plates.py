"""The painted plates of one map and the manifest written beside them.

Key types: `Plates`, the directory a map's plates were written to together
with their `Manifest`; `Manifest`, the plates' sidecar record (`plates.json`):
the base hash, the files written, the card they were painted on and the
measurements later stages read; `DarkGrid`, the painter's coarse grid of how
dark the painted sheet is.

It does not paint, hash or letter anything, and it does not decide whether a
manifest is current: the painter writes one, the lettering and the compose
step read one. It carries no lettering input: the places, the candidates and
the named lines a label is set along are read from the basemap, not from
here. `Manifest.to_json` writes the record in a fixed key order with
the card as its five frame keys (`card`, `display`, `render`, `mpp`,
`mpp_display`); the card's offset is never written.

Invariants: every value here is immutable and compares by value;
`Manifest.from_json(m.to_json()) == m`, and `to_json` of a manifest read with
`from_json` gives back the same bytes; every path in `Plates.paths` is under
`Plates.directory`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyntpot.maps.card import Card

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


@dataclass(frozen=True)
class DarkGrid:
    """How dark the painted sheet is, cell by cell, on a coarse grid.

    Attributes:
        w: Cells across.
        h: Cells down.
        values: The darkness of each cell from 0 (bare paper) to 1, row by row
            from the top left, `h` rows of `w` cells.
    """

    w: int
    h: int
    values: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class Manifest:
    """The sidecar record of one map's painted plates.

    Attributes:
        hash: The base hash of the card and layers the plates were painted from.
        files: The file name of each plate, by plate name.
        sizes: The bytes written for each plate, by plate name.
        bytes: The bytes written for every plate together.
        card: The frame the plates were painted on.
        ribbon_m: The ribbon radius, in card metres.
        span_m: The longer side of the track's own box, in whole metres.
        wet_px: The painted width floor of each watercourse class, in display
            pixels.
        gran_px: The paper granulation's cell size, in render pixels.
        dark: How dark the painted sheet is.
        wood_px: Render pixels painted as wood.
        water_px: Render pixels painted as water.
    """

    hash: str
    files: Mapping[str, str]
    sizes: Mapping[str, int]
    bytes: int
    card: Card
    ribbon_m: int
    span_m: int
    wet_px: Mapping[str, float]
    gran_px: float
    dark: DarkGrid
    wood_px: int
    water_px: int

    def to_json(self) -> str:
        """The manifest as the compact JSON written to `plates.json`.

        Returns:
            One line of JSON, keys in the fixed order the painter writes.
        """
        card = self.card
        record = {
            "hash": self.hash,
            "files": dict(self.files),
            "sizes": dict(self.sizes),
            "bytes": self.bytes,
            "card": list(card.box),
            "display": list(card.display),
            "render": list(card.render),
            "mpp": card.mpp,
            "mpp_display": card.mpp_display,
            "ribbon_m": self.ribbon_m,
            "span_m": self.span_m,
            "wet_px": dict(self.wet_px),
            "gran_px": self.gran_px,
            "dark": {"w": self.dark.w, "h": self.dark.h, "v": [list(r) for r in self.dark.values]},
            "wood_px": self.wood_px,
            "water_px": self.water_px,
        }
        return json.dumps(record, separators=(",", ":"))

    def to_dict(self) -> dict[str, Any]:
        """The manifest as the plain mapping `plates.json` holds.

        Returns:
            The parsed form of `to_json`.
        """
        return json.loads(self.to_json())

    @classmethod
    def from_json(cls, text: str) -> Manifest:
        """Read a manifest from the JSON `to_json` writes.

        Args:
            text: The contents of a `plates.json`.

        Returns:
            The manifest.

        Raises:
            ValueError: When the text is not JSON.
            KeyError: When a key is missing.
        """
        record = json.loads(text)
        dark = record["dark"]
        return cls(
            hash=record["hash"],
            files=dict(record["files"]),
            sizes=dict(record["sizes"]),
            bytes=record["bytes"],
            card=Card.from_manifest(record),
            ribbon_m=record["ribbon_m"],
            span_m=record["span_m"],
            wet_px=dict(record["wet_px"]),
            gran_px=record["gran_px"],
            dark=DarkGrid(w=dark["w"], h=dark["h"], values=tuple(tuple(row) for row in dark["v"])),
            wood_px=record["wood_px"],
            water_px=record["water_px"],
        )


@dataclass(frozen=True)
class Plates:
    """One map's painted plates: where they were written and their manifest.

    Attributes:
        directory: The directory holding the plates and `plates.json`.
        manifest: The plates' manifest.
    """

    directory: Path
    manifest: Manifest

    @property
    def paths(self) -> Mapping[str, Path]:
        """The path of each plate, by plate name."""
        return {name: self.directory / file for name, file in self.manifest.files.items()}

    @property
    def hash(self) -> str:
        """The base hash the plates were painted from."""
        return self.manifest.hash

    @property
    def card(self) -> Card:
        """The frame the plates were painted on."""
        return self.manifest.card
