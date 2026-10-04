"""The track projection: degrees to card metres about one track, and back."""

import pytest

from pyntpot.maps.projection import track_projection
from pyntpot.maps.track import Track

from support.paths import FIXTURE_DIR

#: The fixture track's first point, in card metres, as the projection put it.
FIRST_POINT_M = (1642.8932644810945, 1828.3315999999018)

#: Synthetic coordinates inside the Lynmouth box, as latitude and longitude.
INSIDE_BOX = ((51.2270, -3.8200), (51.1950, -3.8750), (51.2580, -3.8050))


def test_the_first_fixture_point_lands_on_the_pinned_metres() -> None:
    """The fixture track's first point projects to the metres pinned when it moved."""
    track = Track.from_gpx(FIXTURE_DIR / "track.gpx")
    lat, lng = list(track.lat), list(track.lng)
    proj, pts = track_projection(lat, lng)
    assert proj(lat[0], lng[0]) == pytest.approx(FIRST_POINT_M, abs=1e-6)
    assert pts[0] == pytest.approx(FIRST_POINT_M, abs=1e-6)


@pytest.mark.parametrize("point", INSIDE_BOX, ids=["centre", "south-west", "north-east"])
def test_inverse_round_trips(point: tuple[float, float]) -> None:
    """A coordinate projected and inverted comes back to within 1e-9 degrees."""
    track = Track.from_gpx(FIXTURE_DIR / "track.gpx")
    lat, lng = list(track.lat), list(track.lng)
    proj, _ = track_projection(lat, lng)
    assert proj.inverse(*proj(*point)) == pytest.approx(point, abs=1e-9)
