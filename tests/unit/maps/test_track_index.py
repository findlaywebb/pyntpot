"""The track index: distance and interaction with the track."""

import pytest

from pyntpot.maps.projection import track_projection
from pyntpot.maps.track_index import TrackIndex

#: A short east-west track inside the Lynmouth box.
LATS = [51.2250 + 2e-5 * i for i in range(60)]
LNGS = [-3.8400 + 0.00040 * i for i in range(60)]


def test_the_track_index_measures_what_it_should():
    """A point on the track is at zero; one a field away is not."""
    _proj, pts = track_projection(LATS, LNGS)
    index = TrackIndex(pts)
    assert index.distance(*pts[10]) == pytest.approx(0.0, abs=0.5)
    assert index.distance(pts[10][0], pts[10][1] + 500.0, cap_m=900.0) > 400.0


def test_interaction_needs_a_run_not_a_moment():
    """Passing within 60 m for one step is not an interaction; running alongside is."""
    _proj, pts = track_projection(LATS, LNGS)
    index = TrackIndex(pts)
    alongside = [(x, y + 30.0) for x, y in pts[5:40]]
    glancing = [(pts[10][0], pts[10][1] + 40.0), (pts[10][0] + 10.0, pts[10][1] + 900.0)]
    assert index.interacts(alongside, 60.0, 100.0)
    assert not index.interacts(glancing, 60.0, 100.0)


def test_a_crossing_counts_even_though_it_is_brief():
    """A lane the track crossed is part of the session however short the contact."""
    _proj, pts = track_projection(LATS, LNGS)
    index = TrackIndex(pts)
    x, y = pts[20]
    crossing = [(x, y - 400.0), (x, y + 400.0)]
    assert index.interacts(crossing, 60.0, 100.0)


def test_distance_is_capped_so_a_far_feature_costs_nothing():
    """The index stops looking once a feature is clearly not near the track."""
    _proj, pts = track_projection(LATS, LNGS)
    index = TrackIndex(pts)
    assert index.distance(pts[0][0], pts[0][1] + 100000.0, cap_m=250.0) == 250.0
