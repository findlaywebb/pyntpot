"""Journal notes are seated first as flat blocks with leaders, and no later name moves them."""

import shutil
from typing import NamedTuple

import pydantic
import pytest

from pyntpot.maps import pipeline
from pyntpot.maps.annotations import Annotations, JournalNote
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.cache import Cache
from pyntpot.maps.lettering.label import Box
from pyntpot.maps.lettering.pipeline import letter
from pyntpot.maps.plates import Plates
from pyntpot.maps.style import Style
from pyntpot.maps.track import Track

from support.paths import FIXTURE_DIR, KEY
from support.providers import FixtureElevation, FixtureFeatures

#: How far a leader may end from its point, in display pixels.
LEADER_TOLERANCE_PX = 3.0


class Painted(NamedTuple):
    """The fixture fetched and painted once, with two points of the track to note."""

    basemap: Basemap
    plates: Plates
    style: Style
    track: Track


@pytest.fixture(scope="module")
def painted(tmp_path_factory: pytest.TempPathFactory) -> Painted:
    """The Lynmouth fixture fetched and painted once over a copy of the fixture directory."""
    work = tmp_path_factory.mktemp("lynmouth-notes")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    style = Style.default()
    track = Track.from_gpx(work / "track.gpx")
    cache = Cache(work)
    basemap = pipeline.fetch(track, cache, FixtureFeatures(), FixtureElevation(), style)
    return Painted(basemap, pipeline.paint(basemap, style, cache.plates_dir(KEY)), style, track)


def _two_notes(track: Track) -> tuple[JournalNote, JournalNote]:
    """Two notes standing on the track, a third and two thirds of the way along."""
    a, b = len(track.lat) // 3, 2 * len(track.lat) // 3
    return (
        JournalNote(text="Rain came in here", lat=track.lat[a], lng=track.lng[a]),
        JournalNote(
            text="Lunch by the river, then the long pull up", lat=track.lat[b], lng=track.lng[b]
        ),
    )


def _overlap(a: Box, b: Box) -> bool:
    """True when two boxes share area."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


class TestValidation:
    """A map carries at most six notes of at most sixty characters."""

    def test_seven_notes_fail_validation(self) -> None:
        """Seven notes raise `ValidationError` naming the notes field."""
        notes = tuple(JournalNote(text="x", lat=51.2, lng=-3.8) for _ in range(7))
        with pytest.raises(pydantic.ValidationError, match="notes"):
            Annotations(notes=notes)

    def test_six_notes_pass(self) -> None:
        """Six notes are accepted."""
        notes = tuple(JournalNote(text="x", lat=51.2, lng=-3.8) for _ in range(6))
        assert len(Annotations(notes=notes).notes) == 6

    def test_a_long_note_fails_validation(self) -> None:
        """A note of sixty-one characters raises `ValidationError` naming its text."""
        with pytest.raises(pydantic.ValidationError, match="text"):
            JournalNote(text="x" * 61, lat=51.2, lng=-3.8)

    def test_a_note_of_sixty_passes(self) -> None:
        """A note of exactly sixty characters is accepted."""
        assert len(JournalNote(text="x" * 60, lat=51.2, lng=-3.8).text) == 60

    def test_no_notes_by_default(self) -> None:
        """`Annotations()` carries no notes."""
        assert Annotations().notes == ()


@pytest.mark.golden
class TestLettering:
    """`letter` seats notes before any other name and never moves them."""

    def test_two_notes_are_lettered_with_leaders_to_their_points(self, painted: Painted) -> None:
        """Each note is a label whose leader starts within 3 px of its point."""
        notes = _two_notes(painted.track)
        got = letter(painted.plates, painted.basemap, Annotations(notes=notes), painted.style)
        seated = [lb for lb in got.labels if lb.kind == "note"]
        assert [lb.name for lb in seated] == [n.text for n in notes]
        card = painted.basemap.card
        for note, lb in zip(notes, seated, strict=True):
            assert lb.leader is not None
            x, y = card.xy(*painted.basemap.projection(note.lat, note.lng))
            ax, ay = lb.leader[0]
            assert abs(ax - x) <= LEADER_TOLERANCE_PX
            assert abs(ay - y) <= LEADER_TOLERANCE_PX

    def test_no_note_box_overlaps_another_label(self, painted: Painted) -> None:
        """No note's box overlaps any other label's box."""
        notes = _two_notes(painted.track)
        got = letter(painted.plates, painted.basemap, Annotations(notes=notes), painted.style)
        seated = [lb for lb in got.labels if lb.kind == "note"]
        for lb in seated:
            assert lb.box is not None
            for other in got.labels:
                if other is not lb and other.box is not None:
                    assert not _overlap(lb.box, other.box), (lb.name, other.name)

    def test_a_note_off_the_card_raises(self, painted: Painted) -> None:
        """A note whose point is off the card raises `ValueError` naming it."""
        far = Annotations(notes=(JournalNote(text="Far away", lat=52.5, lng=-3.0),))
        with pytest.raises(ValueError, match="Far away"):
            letter(painted.plates, painted.basemap, far, painted.style)

    def test_without_notes_the_lettering_is_unchanged(self, painted: Painted) -> None:
        """Empty `Annotations` letters the same names as no annotations at all."""
        bare = letter(painted.plates, painted.basemap, None, painted.style)
        empty = letter(painted.plates, painted.basemap, Annotations(), painted.style)
        assert [lb.name for lb in empty.labels] == [lb.name for lb in bare.labels]
        assert [lb.box for lb in empty.labels] == [lb.box for lb in bare.labels]

    def test_notes_do_not_count_against_the_label_cap(self, painted: Painted) -> None:
        """The names lettered without notes are all still lettered beside the notes."""
        bare = letter(painted.plates, painted.basemap, None, painted.style)
        notes = _two_notes(painted.track)
        got = letter(painted.plates, painted.basemap, Annotations(notes=notes), painted.style)
        names = {lb.name for lb in got.labels if lb.kind != "note"}
        assert names == {lb.name for lb in bare.labels}
