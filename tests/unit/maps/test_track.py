"""`Track` and `BoundingBox`: the GPX read, the validators and the margin box."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pyntpot._port import geo
from pyntpot.maps.track import BoundingBox, Track

from support import REPO_ROOT

GPX = REPO_ROOT / "tests" / "fixtures" / "lynmouth" / "track.gpx"

TIMED_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="{version}" creator="test" xmlns="http://www.topografix.com/GPX/{path}">
  <trk><name>Watersmeet</name><trkseg>
    <trkpt lat="51.2300" lon="-3.8300"><ele>10.0</ele><time>2024-05-01T08:00:00+00:00</time></trkpt>
    <trkpt lat="51.2310" lon="-3.8310"><ele>12.5</ele><time>2024-05-01T08:00:05Z</time></trkpt>
    <trkpt lat="51.2320" lon="-3.8320"><ele>15.0</ele><time>2024-05-01T08:00:12+00:00</time></trkpt>
  </trkseg></trk>
</gpx>
"""


def _write(tmp_path: Path, version: str, path: str) -> Path:
    """Write the three-point timed GPX in one namespace version."""
    target = tmp_path / "watersmeet.gpx"
    target.write_text(TIMED_GPX.format(version=version, path=path))
    return target


class TestFixtureTrack:
    """The Lynmouth fixture read through `from_gpx`."""

    def test_reads_every_point_without_time(self) -> None:
        """The fixture has 400 points and no time or elevation."""
        track = Track.from_gpx(GPX)
        assert len(track.lat) == len(track.lng) == 400
        assert track.time is None
        assert track.ele is None

    def test_first_point_is_pinned(self) -> None:
        """The first point is the pinned coordinate pair."""
        track = Track.from_gpx(GPX)
        assert (track.lat[0], track.lng[0]) == (51.230678, -3.828447)

    def test_agrees_with_the_port_reader(self) -> None:
        """Latitudes and longitudes equal the interim reader's lists."""
        track = Track.from_gpx(GPX)
        lat, lng = geo.read_gpx(GPX)
        assert (list(track.lat), list(track.lng)) == (lat, lng)

    @pytest.mark.parametrize(
        ("margin", "expected"),
        [
            (0.0, (51.214138, -3.852012, 51.232043, -3.80824)),
            (500.0, (51.209615, -3.859184, 51.236566, -3.801068)),
        ],
        ids=["none", "500m"],
    )
    def test_bounding_box_is_pinned(
        self, margin: float, expected: tuple[float, float, float, float]
    ) -> None:
        """The box equals the pinned tuple to a millionth of a degree."""
        box = Track.from_gpx(GPX).bounding_box(margin)
        assert isinstance(box, BoundingBox)
        assert tuple(box) == pytest.approx(expected, abs=1e-6)

    @pytest.mark.parametrize("margin", [0.0, 750.0, 1500.0], ids=["none", "half", "full"])
    def test_bounding_box_matches_port(self, margin: float) -> None:
        """The box equals `geo.bounding_box` exactly at several margins."""
        track = Track.from_gpx(GPX)
        lat, lng = geo.read_gpx(GPX)
        assert tuple(track.bounding_box(margin)) == geo.bounding_box(lat, lng, margin)

    def test_box_fields_are_named(self) -> None:
        """The box unpacks as south, west, north, east."""
        box = Track.from_gpx(GPX).bounding_box(1500.0)
        assert (box.south, box.west, box.north, box.east) == tuple(box)
        assert box.south < box.north
        assert box.west < box.east


class TestTimedTrack:
    """A synthetic GPX with elevation and time."""

    @pytest.mark.parametrize(
        ("version", "path"), [("1.1", "1/1"), ("1.0", "1/0")], ids=["gpx-1.1", "gpx-1.0"]
    )
    def test_time_is_seconds_from_first_point(
        self, tmp_path: Path, version: str, path: str
    ) -> None:
        """Both namespaces give times in seconds from the first point."""
        track = Track.from_gpx(_write(tmp_path, version, path))
        assert track.time == (0.0, 5.0, 12.0)
        assert track.ele == (10.0, 12.5, 15.0)

    def test_partial_time_is_dropped(self, tmp_path: Path) -> None:
        """A point without time makes the whole time series absent."""
        target = _write(tmp_path, "1.1", "1/1")
        text = target.read_text().replace("<time>2024-05-01T08:00:05Z</time>", "")
        target.write_text(text)
        track = Track.from_gpx(target)
        assert track.time is None
        assert track.ele == (10.0, 12.5, 15.0)


class TestValidation:
    """The model's validators."""

    def test_mismatched_lengths_raise(self) -> None:
        """Latitudes and longitudes of different lengths are rejected."""
        with pytest.raises(ValidationError):
            Track(lat=(51.23, 51.24, 51.25), lng=(-3.83, -3.84))

    @pytest.mark.parametrize("field", ["ele", "time"])
    def test_mismatched_optional_series_raise(self, field: str) -> None:
        """An elevation or time series of the wrong length is rejected."""
        with pytest.raises(ValidationError):
            Track(lat=(51.23, 51.24), lng=(-3.83, -3.84), **{field: (1.0,)})

    def test_single_point_raises(self) -> None:
        """A track needs at least two points."""
        with pytest.raises(ValidationError):
            Track(lat=(51.23,), lng=(-3.83,))

    @pytest.mark.parametrize("bad", [90.5, -91.0], ids=["above", "below"])
    def test_latitude_out_of_range_raises(self, bad: float) -> None:
        """A latitude outside [-90, 90] is rejected."""
        with pytest.raises(ValidationError):
            Track(lat=(51.23, bad), lng=(-3.83, -3.84))

    def test_is_frozen(self) -> None:
        """A track is immutable, so it hashes."""
        track = Track(lat=(51.23, 51.24), lng=(-3.83, -3.84))
        assert hash(track) == hash(Track(lat=(51.23, 51.24), lng=(-3.83, -3.84)))
