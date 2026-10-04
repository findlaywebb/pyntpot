"""The cache: provider payloads and painted plates on disk, keyed by what made them.

Key types: `Cache`, a directory the caller names, holding the feature, land cover and
elevation payloads for a track's bounding box under one key, and the plates painted from
them. Three more keys say when a painted thing is still current: `Cache.base_key`, the
hash the base plates' manifest carries (the basemap's canonical text and the style's base
digest); `Cache.lettering_key`, the key of the label plate (the marks the nib strokes,
the base hash and the style's lettering digest); and `Cache.load_plates`, which reads a
plates directory back.

The key is the first 16 hex characters of the `sha256` of the canonical JSON of the
bounding box (rounded to six decimal places), the margin and both provider ids. It
never comes from a caller's own id, so two tracks over the same ground with the same
providers share their payloads, and changing a provider or the margin fetches afresh.
The directory is always an explicit argument; nothing is resolved against the working
directory. Payload file names are `overpass-<key>.json`, `landcover-<key>.json` and
`elevation-<key>.json`, the names the painter reads.

The label plate's key is derived from the marks themselves, every coordinate rounded to
three decimals, with no list of fields: a field added to a mark, or a pin, leader or span
line moved, changes the key without this module being told. It is not a golden; only
`base_key` is frozen, because the manifest carries it.

`Cache` does not parse, validate or expire payloads, does not lock the directory against
a second process, and fetches only through the providers it is handed. `load_plates` reads
a manifest and checks its plates are on disk; it does not compare hashes.

Invariants: `ensure` fetches features, then land cover, then elevation, and writes each
payload to its path as soon as its call returns, before the next call, so a failure
part-way leaves every earlier payload on disk; it calls a provider only for a payload
whose file is missing, unless forced.
"""

import hashlib
import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, fields
from pathlib import Path

from pyntpot.letters.setting import Mark
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.plates import Manifest, Plates
from pyntpot.maps.providers.base import Elevation, Features
from pyntpot.maps.style import Style
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

#: Decimal places a mark's coordinates are rounded to before the lettering key hashes them.
MARK_PLACES = 3

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

    @staticmethod
    def load_plates(directory: Path) -> Plates | None:
        """Return the plates painted into a directory, or `None` when there are none.

        A manifest that cannot be read, or that names a plate no longer on disk,
        reads as no plates.

        Args:
            directory: A plates directory, as `plates_dir` names one.

        Returns:
            The plates, whatever hash they carry, or `None`.
        """
        path = directory / "plates.json"
        if not path.exists():
            return None
        try:
            manifest = Manifest.from_json(path.read_text())
        except (OSError, ValueError, KeyError, TypeError):
            return None
        plates = Plates(directory, manifest)
        if not all(plate.exists() for plate in plates.paths.values()):
            return None
        return plates

    @staticmethod
    def base_key(basemap: Basemap, style: Style) -> str:
        """Return the hash the base plates' manifest carries.

        Args:
            basemap: The basemap whose canonical text, the card frame and the
                layers, is hashed.
            style: The style whose base digest is appended.

        Returns:
            Sixteen hex characters of the canonical text's `sha256`, a hyphen and
            the style's base digest.
        """
        text = basemap.canonical().encode()
        return hashlib.sha256(text).hexdigest()[:KEY_LENGTH] + "-" + style.base_digest()

    @staticmethod
    def lettering_key(marks: Sequence[Mark], base_hash: str, style: Style) -> str:
        """Return the key a label plate is cached under.

        Args:
            marks: The marks the nib strokes, furniture included.
            base_hash: The hash of the base plates the label plate is drawn against.
            style: The style whose lettering digest is hashed in.

        Returns:
            The first 16 hex characters of the `sha256` of the canonical JSON of the
            base hash, the lettering digest and every mark's fields.
        """
        canonical = json.dumps(
            {
                "base": base_hash,
                "lettering": style.lettering_digest(),
                "marks": [
                    {field.name: _rounded(getattr(mark, field.name)) for field in fields(mark)}
                    for mark in marks
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode()).hexdigest()[:KEY_LENGTH]

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


def _rounded(value: object) -> object:
    """Return a value with every float in it rounded to `MARK_PLACES` places."""
    if isinstance(value, float):
        return round(value, MARK_PLACES)
    if isinstance(value, (list, tuple)):
        return [_rounded(item) for item in value]
    return value
