"""Terrain shading: a hillshade raster and posterised shade bands.

Key names: `Sun`, where the light comes from and how the relief is exaggerated;
`Terrain`, an elevation grid with its geography; `hillshade_png`, a terrain grid
shaded and returned as a `data:` URI of a greyscale-plus-alpha PNG; `shade_bands`,
the same shade cut into a few levels and traced as filled vector bands.

A lit slope paints white and a shaded one black over a transparent flat ground, so
one image reads as relief on a pale sheet and on a dark one. It does not fetch
elevations, trace contours or place anything on a card. Invariants: flat ground
carries no shade, and the raster and the bands compute the same signal.
"""

import base64
import math
import struct
import zlib
from dataclasses import dataclass
from typing import Any, cast

import numpy as np

from pyntpot.ink.polyline import simplify, smooth
from pyntpot.maps.contours import _grid_line_to_metres, _pad, marching_squares
from pyntpot.maps.projection import Projection
from pyntpot.maps.svg_path import path_d

#: The fewest points a simplified band outline needs to be kept.
BAND_MIN_POINTS = 4

#: How strongly illumination is stretched before it is clipped to [-1, 1].
SHADE_GAIN = 2.6


@dataclass(frozen=True)
class Sun:
    """Where the light comes from and how the relief is exaggerated.

    Attributes:
        azimuth: Sun bearing in degrees clockwise from north.
        altitude: Sun height in degrees above the horizon.
        z_factor: Vertical exaggeration. Relief at this scale is gentle.
        upsample: Bilinear factor applied before shading.
    """

    azimuth: float = 315.0
    altitude: float = 42.0
    z_factor: float = 1.4
    upsample: int = 2


DEFAULT_SUN = Sun()


@dataclass(frozen=True)
class Terrain:
    """An elevation grid with its geography.

    Attributes:
        grid: Elevation rows, row 0 southernmost.
        lats: Grid latitudes, ascending.
        lons: Grid longitudes, ascending.
        proj: The activity's projection.
        dx: Metres between columns.
        dy: Metres between rows.
    """

    grid: list[list[float]]
    lats: list[float]
    lons: list[float]
    proj: Projection
    dx: float
    dy: float


def _png(width: int, height: int, rows: list[bytes], colour_type: int = 4) -> bytes:
    """Encode raster rows as a PNG.

    Args:
        width: Pixels across.
        height: Pixels down.
        rows: One `bytes` per row, already in the sample layout `colour_type` wants.
        colour_type: 0 for greyscale, 4 for greyscale plus alpha.

    Returns:
        The PNG file.
    """
    raw = b"".join(b"\x00" + row for row in rows)

    def chunk(tag: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + tag
            + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, colour_type, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _resample(grid: list[list[float]], factor: int) -> list[list[float]]:
    """Bilinear upsample of a square grid, so the shading has somewhere to bend."""
    if factor <= 1:
        return grid
    n = len(grid)
    out_n = (n - 1) * factor + 1
    out = [[0.0] * out_n for _ in range(out_n)]
    for r in range(out_n):
        fr = r / factor
        r0 = min(int(fr), n - 2)
        tr = fr - r0
        for c in range(out_n):
            fc = c / factor
            c0 = min(int(fc), n - 2)
            tc = fc - c0
            top = grid[r0][c0] * (1 - tc) + grid[r0][c0 + 1] * tc
            bot = grid[r0 + 1][c0] * (1 - tc) + grid[r0 + 1][c0 + 1] * tc
            out[r][c] = top * (1 - tr) + bot * tr
    return out


def _shade(
    fine: list[list[float]], sx: float, sy: float, azimuth: float, altitude: float, z_factor: float
) -> list[list[float]]:
    """Signed illumination per cell: positive is lit, negative is in shadow.

    Source: `hillshade` in docs/explanation/references.md.
    """
    zen = math.radians(90.0 - altitude)
    az = math.radians(360.0 - azimuth + 90.0)
    flat = math.cos(zen)
    z = np.asarray(fine, dtype=float)
    dzdy, dzdx = np.gradient(z, sy, sx)
    slope = np.arctan(z_factor * np.hypot(dzdx, dzdy))
    aspect = np.arctan2(dzdy, -dzdx)
    illum = np.cos(zen) * np.cos(slope) + np.sin(zen) * np.sin(slope) * np.cos(az - aspect)
    return cast("list[list[float]]", np.clip((illum - flat) * SHADE_GAIN, -1.0, 1.0).tolist())


def hillshade_png(
    grid: list[list[float]], dx: float, dy: float, sun: Sun = DEFAULT_SUN
) -> tuple[str, int, int]:
    """Shade a terrain grid and return it as a data URI.

    The image is greyscale plus alpha rather than plain grey: a lit slope paints
    white and a shaded one paints black, both over a transparent flat ground, so
    the same PNG reads as relief on a pale sheet and on a dark one and the page
    needs no blend mode to make it work.

    Args:
        grid: Elevation rows, row 0 southernmost.
        dx: Metres between columns.
        dy: Metres between rows.
        sun: The light and the vertical exaggeration.

    Returns:
        The `data:` URI, and the image's width and height in pixels.
    """
    fine = _resample(grid, sun.upsample)
    n = len(fine)
    signal = _shade(
        fine, dx / sun.upsample, dy / sun.upsample, sun.azimuth, sun.altitude, sun.z_factor
    )
    # Rows are emitted north first, because SVG y grows downward and the grid's
    # row 0 is its southern edge.
    rows = [
        bytes(
            bytearray(
                b
                for value in row
                for b in (255 if value > 0 else 0, min(255, int(abs(value) * 255)))
            )
        )
        for row in reversed(signal)
    ]
    png = _png(n, n, rows, colour_type=4)
    return "data:image/png;base64," + base64.b64encode(png).decode(), n, n


def shade_bands(
    terrain: Terrain, levels: int = 5, sun: Sun = DEFAULT_SUN, eps: float = 14.0
) -> list[dict[str, Any]]:
    """Posterised hillshade as filled vector bands.

    The shade is computed exactly as the raster is, then cut into a few levels
    and traced. Nesting does the work a gradient would: every band is drawn at
    the same low opacity, so where four of them overlap the ground is four steps
    darker and the ramp costs no extra alpha bookkeeping.

    Args:
        terrain: The elevation grid and its geography.
        levels: Bands across the whole range, split between shadow and light.
        sun: The light and the vertical exaggeration.
        eps: Simplification tolerance in metres.

    Returns:
        Bands from the widest to the tightest, each `{"s": -1 or 1, "t": level,
        "d": path}`; `s` says whether the band is shadow or light.
    """
    lats, lons = terrain.lats, terrain.lons
    fine = _resample(terrain.grid, sun.upsample)
    signal = _pad(
        _shade(
            fine,
            terrain.dx / sun.upsample,
            terrain.dy / sun.upsample,
            sun.azimuth,
            sun.altitude,
            sun.z_factor,
        ),
        0.0,
    )
    fine_lats = [lats[0] + (lats[-1] - lats[0]) * i / (len(fine) - 1) for i in range(len(fine))]
    fine_lons = [lons[0] + (lons[-1] - lons[0]) * i / (len(fine) - 1) for i in range(len(fine))]
    steps = max(1, levels // 2)
    out: list[dict[str, Any]] = []
    for sign in (-1, 1):
        for i in range(1, steps + 1):
            level = sign * (i / (steps + 0.35))
            flipped = signal if sign > 0 else [[-v for v in row] for row in signal]
            rings = marching_squares(flipped, abs(level))
            parts = []
            for ring in rings:
                metres = _grid_line_to_metres(ring, fine_lats, fine_lons, terrain.proj, pad=1)
                metres = simplify(smooth(metres, passes=1, closed=False), eps)
                if len(metres) >= BAND_MIN_POINTS:
                    parts.append(path_d(metres, close=True))
            if parts:
                out.append({"s": sign, "t": round(abs(level), 3), "d": "".join(parts)})
    return out
