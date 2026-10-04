"""Relief strokes: hachures and waves."""

from pyntpot.maps.projection import track_projection
from pyntpot.maps.relief_strokes import Field, Hatching, hachures, wave_strokes
from pyntpot.maps.track_index import TrackIndex

#: A short east-west track inside the Lynmouth box.
LATS = [51.2250 + 2e-5 * i for i in range(60)]
LNGS = [-3.8400 + 0.00040 * i for i in range(60)]


def test_hachures_leave_the_track_alone():
    """No stroke starts inside the buffer the track keeps clear."""
    grid = [[float(col * 30) for col in range(20)] for _ in range(20)]
    lats = [51.225 + 4e-4 * i for i in range(20)]
    lons = [-3.840 + 0.0006 * i for i in range(20)]
    proj, pts = track_projection(LATS, LNGS)
    field = Field(grid, lats, lons, proj)
    index = TrackIndex(pts)
    clip = (
        min(x for x, _ in pts) - 200,
        min(y for _, y in pts) - 200,
        max(x for x, _ in pts) + 200,
        max(y for _, y in pts) + 200,
    )
    strokes = hachures(field, clip, index, Hatching(spacing_m=60.0, buffer_m=50.0))
    assert strokes
    for group in strokes:
        for chunk in group["d"].split("M")[1:]:
            x, y = (float(v) for v in chunk.split("l")[0].split(","))
            assert index.distance(x, y, cap_m=200.0) > 50.0


def test_wave_strokes_only_appear_over_water():
    """The hand-drawn sea is drawn where the grid says there is sea, and nowhere else."""
    proj, _ = track_projection(LATS, LNGS)
    dry = [[50.0] * 8 for _ in range(8)]
    lats = [51.225 + 1e-3 * i for i in range(8)]
    lons = [-3.840 + 1e-3 * i for i in range(8)]
    field = Field(dry, lats, lons, proj)
    box = (0.0, 0.0, 400.0, 400.0)
    assert wave_strokes(field, box) == ""
    wet = Field([[-3.0] * 8 for _ in range(8)], lats, lons, proj)
    assert wave_strokes(wet, box, spacing_m=100.0).count("M") >= 4
