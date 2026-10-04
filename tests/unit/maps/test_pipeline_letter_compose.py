"""`letter` places the fixture's names on the strands; `compose` lays the card the goldens hold."""

import dataclasses
import shutil
from pathlib import Path
from typing import NamedTuple

import pytest
from golden.test_parity import MAX_CHANNEL_DELTA, MAX_DIFFERING_FRACTION

from pyntpot._port import labels, mapcard
from pyntpot.maps import pipeline
from pyntpot.maps.annotations import Annotations, SpanRequest
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.cache import Cache
from pyntpot.maps.lettering import Lettering, letter
from pyntpot.maps.plates import Plates
from pyntpot.maps.style import Style
from pyntpot.maps.track import Track

from support.golden import differing_fraction
from support.paths import FIXTURE_DIR, KEY
from support.providers import FixtureElevation, FixtureFeatures

#: The placed label names, in placement order, as the regeneration window pinned them.
PINNED_LABELS = (
    "Lynton",
    "Barbrook",
    "East Lyn",
    "East Lyn",
    "A39",
    "B3234",
    "Saint Mary the Virgin",
    "Hollerday Hill",
    "Lyn Valley Art and Craft Centre",
    "start",
)

#: Ten seconds a point over the fixture track's 400 points.
SYNTHETIC_TIME = tuple(10.0 * i for i in range(400))

#: Names deleted with the flat measure, the shims and the composed-card helpers.
DELETED: tuple[tuple[object, str], ...] = (
    (labels, "measure"),
    (labels, "_text_width"),
    (labels, "CHAR_W"),
    (labels, "DEFAULT_ADVANCE_PX"),
    (labels, "DEFAULT_SIDE_PX"),
    (labels, "_journal_picks"),
    (labels, "_journal_heuristic"),
    (labels, "_place_journal_labels"),
    (mapcard, "compose"),
    (mapcard, "letter_card"),
    (mapcard, "route_pixels"),
    (mapcard, "alphabet_sheet"),
    (mapcard, "ALPHABET_LINES"),
    (mapcard, "sport_from_gpx"),
)
DELETED_IDS: tuple[str, ...] = tuple(f"{module.__name__}.{name}" for module, name in DELETED)


class Painted(NamedTuple):
    """The fixture fetched and painted once, in the default style."""

    basemap: Basemap
    plates: Plates
    style: Style


@pytest.fixture(scope="module")
def painted(tmp_path_factory: pytest.TempPathFactory) -> Painted:
    """The fixture fetched and painted once over a copy of the fixture directory."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    style = Style.default()
    track = Track.from_gpx(work / "track.gpx")
    cache = Cache(work)
    basemap = pipeline.fetch(track, cache, FixtureFeatures(), FixtureElevation(), style)
    plates = pipeline.paint(basemap, style, cache.plates_dir(KEY))
    return Painted(basemap, plates, style)


@pytest.fixture(scope="module")
def lettered(painted: Painted) -> Lettering:
    """The painted fixture lettered once, with no annotations."""
    return letter(painted.plates, painted.basemap, None, painted.style)


class TestDeleted:
    """The flat measure, the shims and the composed-card helpers are gone."""

    @pytest.mark.parametrize(("module", "name"), DELETED, ids=DELETED_IDS)
    def test_the_name_is_gone(self, module: object, name: str) -> None:
        """The deleted name is no longer an attribute of its old module."""
        assert not hasattr(module, name)


@pytest.mark.golden
class TestLetter:
    """`letter` places the pinned names along the strands and resolves spans on them."""

    def test_the_labels_are_the_pinned_list(self, lettered: Lettering) -> None:
        """Lettering the fixture without annotations places the window's pinned names."""
        assert tuple(label.name for label in lettered.labels) == PINNED_LABELS

    def test_the_label_plate_is_written_beside_the_plates(
        self, lettered: Lettering, painted: Painted
    ) -> None:
        """The label plate is a file inside the plates directory."""
        assert lettered.plate_path is not None
        assert lettered.plate_path.parent == painted.plates.directory
        assert lettered.plate_path.is_file()

    def test_a_span_in_seconds_lands_on_the_pinned_indices(
        self, painted: Painted, tmp_path: Path
    ) -> None:
        """A span stated in seconds resolves on a basemap carrying the track's times."""
        copy = tmp_path / "plates"
        shutil.copytree(painted.plates.directory, copy)
        plates = dataclasses.replace(painted.plates, directory=copy)
        basemap = dataclasses.replace(painted.basemap, track_time=SYNTHETIC_TIME)
        notes = Annotations(spans=(SpanRequest(name="Dovedale", from_s=600.0, to_s=1500.0),))
        got = letter(plates, basemap, notes, painted.style)
        assert [(span.i0, span.i1) for span in got.spans] == [(60, 150)]


@pytest.mark.golden
class TestCompose:
    """`compose` lays the painted, lettered plates into the golden card."""

    def test_the_card_matches_the_golden_map(
        self,
        painted: Painted,
        lettered: Lettering,
        tmp_path: Path,
        golden_dir: Path,
        golden_tolerance: bool,
    ) -> None:
        """Composing without attribution reproduces `map.png`, exactly or within tolerance."""
        card = pipeline.compose(
            painted.plates, lettered, painted.basemap, painted.style, attribution=False
        )
        got, want = tmp_path / "map.png", golden_dir / "map.png"
        card.save(got)
        if not golden_tolerance:
            assert got.read_bytes() == want.read_bytes()
            return
        assert differing_fraction(got, want, MAX_CHANNEL_DELTA) <= MAX_DIFFERING_FRACTION
