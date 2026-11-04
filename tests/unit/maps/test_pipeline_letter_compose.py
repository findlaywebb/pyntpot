"""`letter` places the fixture's names on the strands; `compose` lays the card the goldens hold."""

import dataclasses
import importlib.util
import logging
import shutil
from pathlib import Path
from typing import NamedTuple

import pytest

from pyntpot.ink.polyline import length
from pyntpot.maps import pipeline
from pyntpot.maps.annotations import Annotations, SpanRequest
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.cache import Cache
from pyntpot.maps.lettering.picks_lines import named_lines
from pyntpot.maps.lettering.picks_roads import named_roads, road_min_px
from pyntpot.maps.lettering.pipeline import Lettering, letter
from pyntpot.maps.plates import Plates
from pyntpot.maps.style import Style
from pyntpot.maps.track import Track

from support.golden import MAX_CHANNEL_DELTA, MAX_DIFFERING_FRACTION, differing_fraction
from support.paths import FIXTURE_DIR, KEY
from support.providers import FixtureElevation, FixtureFeatures

#: The placed label names, in placement order, as the regeneration window pinned them.
PINNED_LABELS = (
    "Lynton",
    "Barbrook",
    "East Lyn",
    "A39",
    "B3234",
    "Saint Mary the Virgin",
    "Lynton and Exmoor Museum",
    "Wind Hill",
    "start",
)

#: Ten seconds a point over the fixture track's 400 points.
SYNTHETIC_TIME = tuple(10.0 * i for i in range(400))

#: The interim `pyntpot._port` package, emptied by the split and deleted.
DELETED: tuple[str, ...] = ("pyntpot._port",)


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


def copied_plates(painted: Painted, tmp_path: Path) -> Plates:
    """The painted plates over a copy of their directory, so a test's nib plate leaves the module's alone."""
    copy = tmp_path / "plates"
    shutil.copytree(painted.plates.directory, copy)
    return dataclasses.replace(painted.plates, directory=copy)


def road_names(lettering: Lettering) -> list[str]:
    """The placed road labels' names, in placement order."""
    return [label.name for label in lettering.labels if label.kind == "road"]


@pytest.fixture(scope="module")
def lettered(painted: Painted) -> Lettering:
    """The painted fixture lettered once, with no annotations."""
    return letter(painted.plates, painted.basemap, None, painted.style)


class TestDeleted:
    """The interim port package is gone."""

    @pytest.mark.parametrize("module", DELETED, ids=DELETED)
    def test_the_module_is_gone(self, module: str) -> None:
        """The deleted port package has no source left to import."""
        spec = importlib.util.find_spec(module)
        if spec is None:
            return
        # A stray __pycache__ leaves an empty namespace package: no origin, no sources.
        assert spec.origin is None
        sources = [
            path
            for location in spec.submodule_search_locations or []
            for path in Path(location).rglob("*.py")
        ]
        assert sources == []


@pytest.mark.golden
@pytest.mark.xdist_group("test_pipeline_letter_compose")
class TestLetter:
    """`letter` places the pinned names along the strands and resolves spans on them."""

    def test_the_labels_are_the_pinned_list(self, lettered: Lettering) -> None:
        """Lettering the fixture without annotations places the window's pinned names."""
        assert tuple(label.name for label in lettered.labels) == PINNED_LABELS

    def test_the_label_plate_is_written_beside_the_plates(
        self, lettered: Lettering, painted: Painted
    ) -> None:
        """The nib plate is a file inside the plates directory."""
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

    def test_empty_annotations_letter_the_pinned_list(
        self, painted: Painted, tmp_path: Path
    ) -> None:
        """Annotations naming nothing place exactly the pinned names, as no annotations do."""
        got = letter(
            copied_plates(painted, tmp_path), painted.basemap, Annotations(), painted.style
        )
        assert tuple(label.name for label in got.labels) == PINNED_LABELS

    def test_named_roads_replace_the_picked_roads(self, painted: Painted, tmp_path: Path) -> None:
        """Naming the B3234 letters it as the only road, in place of both picked roads."""
        notes = Annotations(roads=("B3234",))
        got = letter(copied_plates(painted, tmp_path), painted.basemap, notes, painted.style)
        assert road_names(got) == ["B3234"]

    def test_a_road_named_by_its_street_is_lettered_by_its_number(
        self, painted: Painted, tmp_path: Path
    ) -> None:
        """Naming Lynbridge Road letters the number its pieces carry, B3234."""
        notes = Annotations(roads=("Lynbridge Road",))
        got = letter(copied_plates(painted, tmp_path), painted.basemap, notes, painted.style)
        assert road_names(got) == ["B3234"]

    def test_an_unknown_named_road_raises_and_writes_no_plate(
        self, painted: Painted, tmp_path: Path
    ) -> None:
        """A named road the map does not draw raises before any nib plate is written."""
        plates = copied_plates(painted, tmp_path)
        before = {p.name: p.stat().st_mtime_ns for p in plates.directory.iterdir()}
        with pytest.raises(ValueError, match="'A591'"):
            letter(plates, painted.basemap, Annotations(roads=("A591",)), painted.style)
        after = {p.name: p.stat().st_mtime_ns for p in plates.directory.iterdir()}
        assert after == before

    def test_named_roads_are_lettered_when_the_style_letters_no_ground(
        self, painted: Painted, tmp_path: Path
    ) -> None:
        """With the ground unlettered, a named road is still lettered, and no ground name is."""
        style = painted.style
        lettering = dataclasses.replace(style.lettering, label_ground=False)
        quiet = style.model_copy(update={"lettering": lettering})
        notes = Annotations(roads=("B3234",))
        got = letter(copied_plates(painted, tmp_path), painted.basemap, notes, quiet)
        names = [label.name for label in got.labels]
        assert "B3234" in names
        for ground in ("Lynton", "Barbrook", "East Lyn", "start"):
            assert ground not in names

    def test_a_named_minor_road_is_set_along_its_lane(self, painted: Painted) -> None:
        """Lydiate Lane, a minor road on the path band, is set along a run long enough for it."""
        basemap = painted.basemap
        lines = named_lines(basemap, painted.style.lettering.label_geom_tol_px)
        got = named_roads(basemap, lines, basemap.card, ("Lydiate Lane",))
        assert [label.name for label in got] == ["Lydiate Lane"]
        assert length(got[0].baseline) >= road_min_px(got[0].size)

    def test_a_named_road_too_short_on_the_card_falls_back_to_the_picked_roads(
        self, painted: Painted, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Lee Road is too short to letter: it is logged, nothing raises, the picked roads stay."""
        caplog.set_level(logging.INFO, logger="pyntpot.maps.lettering.picks_roads")
        notes = Annotations(roads=("Lee Road",))
        got = letter(copied_plates(painted, tmp_path), painted.basemap, notes, painted.style)
        assert "Lee Road" in caplog.text
        assert road_names(got) == ["A39", "B3234"]

    def test_a_numbered_road_lettered_only_through_its_unnamed_pieces(
        self, painted: Painted, tmp_path: Path
    ) -> None:
        """The B3223 reaches its minimum run only with its unnamed numbered piece, and is lettered."""
        notes = Annotations(roads=("B3223",))
        got = letter(copied_plates(painted, tmp_path), painted.basemap, notes, painted.style)
        assert road_names(got) == ["B3223"]


@pytest.mark.golden
@pytest.mark.xdist_group("test_pipeline_letter_compose")
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
