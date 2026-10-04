"""Contours: marching squares and the traced shoreline."""

from pyntpot.maps.contours import marching_squares, sea_rings
from pyntpot.maps.projection import track_projection
from pyntpot.maps.svg_path import rings_path


def test_the_sea_is_traced_where_the_grid_is_below_the_waterline():
    """Cells at or below zero become water; ground above it does not."""
    grid = [[-5.0 if col < 4 else 40.0 for col in range(10)] for _ in range(10)]
    lats = [51.20 + 2e-3 * i for i in range(10)]
    lons = [-3.87 + 2e-3 * i for i in range(10)]
    proj, _ = track_projection([51.21, 51.22], [-3.86, -3.85])
    water, islands = sea_rings(grid, lats, lons, proj)
    assert water and not islands
    assert rings_path(water).startswith("M")


def test_dry_ground_has_no_sea():
    """A grid entirely above the waterline traces nothing."""
    grid = [[100.0] * 6 for _ in range(6)]
    lats = [51.225 + 2e-3 * i for i in range(6)]
    lons = [-3.840 + 2e-3 * i for i in range(6)]
    proj, _ = track_projection(
        [
            51.225,
            51.235,
        ],
        [-3.840, -3.830],
    )
    assert sea_rings(grid, lats, lons, proj) == ([], [])


def test_marching_squares_finds_the_level_it_was_asked_for():
    """A ramp crossed at one level gives one line, not a field of fragments."""
    grid = [[float(col * 10) for col in range(10)] for _ in range(10)]
    lines = marching_squares(grid, 45.0)
    assert len(lines) == 1
    assert all(abs(col - 4.5) < 1e-6 for col, _ in lines[0])
