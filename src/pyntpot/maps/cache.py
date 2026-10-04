"""The fetch cache: provider payloads on disk, keyed by what was fetched.

Key types: `Cache`, a directory the caller names, holding the feature, land cover and
elevation payloads for a track's bounding box under one key.

The key is the first 16 hex characters of the `sha256` of the canonical JSON of the
bounding box (rounded to six decimal places), the margin and both provider ids. It
never comes from a caller's own id, so two tracks over the same ground with the same
providers share their payloads, and changing a provider or the margin fetches afresh.
The directory is always an explicit argument; nothing is resolved against the working
directory. Payload file names are `overpass-<key>.json`, `landcover-<key>.json` and
`elevation-<key>.json`, the names the painter reads.

`Cache` does not parse, validate or expire payloads, does not lock the directory against
a second process, and fetches only through the providers it is handed.

Invariants: `ensure` fetches features, then land cover, then elevation, and writes each
payload to its path as soon as its call returns, before the next call, so a failure
part-way leaves every earlier payload on disk; it calls a provider only for a payload
whose file is missing, unless forced.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from pyntpot.maps.providers.base import Elevation, Features
from pyntpot.maps.track import Track

log = logging.getLogger(__name__)

#: Ground kept around the track's extent for the features and the elevation grid.
MARGIN_M = 1500.0

#: Ground kept around the track's extent for the land cover. Wider than `MARGIN_M`,
#: because the painted card is grown by a ribbon radius before it is drawn.
LANDCOVER_MARGIN_M = 2600.0

#: Samples per side of the elevation grid.
ELEVATION_SAMPLES = 80

#: Hex characters of the digest kept as the key.
KEY_LENGTH = 16

#: Decimal places the bounding box is rounded to before hashing.
BOX_PLACES = 6

#: The subdirectory holding painted plates, one directory per key.
PLATES_SUBDIR = "plates"


@dataclass(frozen=True)
class Cache:
    """Provider payloads and painted plates under one explicit directory.

    Attributes:
        directory: Where the payloads live; created by `ensure` when missing.
    """

    directory: Path

    def key(
        self,
        track: Track,
        features: Features,
        elevation: Elevation,
        margin_m: float = MARGIN_M,
    ) -> str:
        """Return the key for a track's box, the margin and both providers.

        Args:
            track: The route whose extent is fetched.
            features: The feature and land cover provider.
            elevation: The elevation provider.
            margin_m: Ground kept around the track's extent, in metres.

        Returns:
            The first 16 hex characters of the `sha256` of the canonical JSON.
        """
        box = track.bounding_box(margin_m)
        canonical = json.dumps(
            {
                "box": [round(value, BOX_PLACES) for value in box],
                "margin_m": margin_m,
                "features": features.id,
                "elevation": elevation.id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode()).hexdigest()[:KEY_LENGTH]

    def features_path(self, key: str) -> Path:
        """Return where the feature payload for a key is cached."""
        return self.directory / f"overpass-{key}.json"

    def landcover_path(self, key: str) -> Path:
        """Return where the land cover payload for a key is cached."""
        return self.directory / f"landcover-{key}.json"

    def elevation_path(self, key: str) -> Path:
        """Return where the elevation grid for a key is cached."""
        return self.directory / f"elevation-{key}.json"

    def plates_dir(self, key: str) -> Path:
        """Return where the painted plates for a key are cached; nothing is created."""
        return self.directory / PLATES_SUBDIR / key

    def ensure(
        self,
        track: Track,
        features: Features,
        elevation: Elevation,
        *,
        force: bool = False,
    ) -> str:
        """Fetch whatever payload is missing for a track and return its key.

        Fetches in a fixed order: features over `MARGIN_M`, then land cover over
        `LANDCOVER_MARGIN_M`, then an `ELEVATION_SAMPLES` square elevation grid over
        `MARGIN_M`. Each payload is written to its path as soon as its call returns,
        before the next call is made.

        Args:
            track: The route whose extent is fetched.
            features: The feature and land cover provider.
            elevation: The elevation provider.
            force: Fetch every payload again even when its file exists.

        Returns:
            The key the payloads are cached under.
        """
        key = self.key(track, features, elevation)
        box = track.bounding_box(MARGIN_M)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.features_path(key)
        if force or not path.exists():
            _write(path, features.features(box))
        path = self.landcover_path(key)
        if force or not path.exists():
            _write(path, features.landcover(track.bounding_box(LANDCOVER_MARGIN_M)))
        path = self.elevation_path(key)
        if force or not path.exists():
            _write(path, elevation.grid(box, ELEVATION_SAMPLES).to_json())
        return key


def _write(path: Path, text: str) -> None:
    """Write one payload and log its size."""
    path.write_text(text, encoding="utf-8")
    log.info("cached %s, %d bytes", path.name, path.stat().st_size)
