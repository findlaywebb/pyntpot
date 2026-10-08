"""Terrain shading: the hillshade raster and the shade bands."""

import base64

from pyntpot.maps.projection import track_projection
from pyntpot.maps.relief import Sun, Terrain, _shade, hillshade_png, shade_bands

#: A short east-west track inside the Lynmouth box.
LATS = [51.2250 + 2e-5 * i for i in range(60)]
LNGS = [-3.8400 + 0.00040 * i for i in range(60)]


def test_the_png_encoder_writes_a_real_png():
    """The hillshade raster is a PNG, header and all, with no image library."""
    uri, width, height = hillshade_png(
        [[float(r * c) for c in range(8)] for r in range(8)], 30.0, 30.0, Sun(upsample=1)
    )
    assert uri.startswith("data:image/png;base64,")
    assert width == height == 8
    assert base64.b64decode(uri.split(",", 1)[1])[:8] == b"\x89PNG\r\n\x1a\n"


def test_shade_bands_come_back_darkest_and_lightest_apart():
    """Bands are signed, so the page can paint shadow in ink and light in paper."""
    grid = [
        [200.0 - ((row - 6) ** 2 + (col - 6) ** 2) * 2.0 for col in range(12)] for row in range(12)
    ]
    lats = [51.225 + 4e-4 * i for i in range(12)]
    lons = [-3.840 + 0.0006 * i for i in range(12)]
    proj, _ = track_projection(LATS, LNGS)
    bands = shade_bands(Terrain(grid, lats, lons, proj, 40.0, 40.0), levels=4)
    assert bands
    assert {band["s"] for band in bands} <= {-1, 1}
    assert all(band["d"].startswith("M") for band in bands)


def test_the_sun_never_lights_a_flat_plain():
    """Flat ground carries no shade, so a flat map stays empty paper."""
    flat = [[100.0] * 6 for _ in range(6)]
    signal = _shade(flat, 30.0, 30.0, 315.0, 42.0, 1.4)
    assert all(abs(value) < 1e-6 for row in signal for value in row)
