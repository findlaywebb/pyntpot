"""Benchmarks for the ink engine: the sheet, the distance transform, strokes, washes and the stack."""

import dataclasses
import math

import numpy as np
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pyntpot.ink.brush import brush_from_id, ink_aux
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.noise import edt
from pyntpot.ink.pigment import PIGMENTS, TRANSPARENCY, Layer, composite
from pyntpot.ink.sheet import Sheet, rgb
from pyntpot.ink.stamp import stamp
from pyntpot.ink.style import PaperStyle
from pyntpot.ink.wash import WashOptions, wash

pytestmark = pytest.mark.benchmark

#: The side of every square plate here, in render pixels.
SIDE = 512

#: The points along a winding stroke.
STROKE_POINTS = 2000

#: The compositing modes, by id: plain multiply and Kubelka-Munk glazing.
GLAZING = {"multiply": False, "kubelka-munk": True}


@pytest.fixture(scope="module")
def sheet() -> Sheet:
    """One square sheet, built once."""
    return Sheet(SIDE, SIDE, gran_px=6.0, seed=3)


def _disc() -> np.ndarray:
    """A float32 coverage disc of radius 180 centred on the plate."""
    yy, xx = np.mgrid[0:SIDE, 0:SIDE].astype(np.float32)
    return (np.hypot(xx - SIDE / 2, yy - SIDE / 2) < 180).astype(np.float32)


def _blob() -> np.ndarray:
    """A coverage mask: a lumpy disc filling the middle of the plate."""
    yy, xx = np.mgrid[0:SIDE, 0:SIDE].astype(np.float32)
    angle = np.arctan2(yy - SIDE / 2, xx - SIDE / 2)
    radius = SIDE * (0.30 + 0.05 * np.sin(5.0 * angle))
    inside = np.hypot(xx - SIDE / 2, yy - SIDE / 2) < radius
    return inside.astype(np.float32)


def _meander() -> np.ndarray:
    """A winding path across the plate, `STROKE_POINTS` long, in render pixels."""
    t = np.linspace(0.0, 1.0, STROKE_POINTS)
    x = 24.0 + (SIDE - 48.0) * t
    y = SIDE / 2 + 0.35 * SIDE * np.sin(t * 3.0 * math.tau) * np.cos(t * math.pi)
    return np.stack([x, y], axis=1)


def test_sheet_construction(benchmark: BenchmarkFixture) -> None:
    """Times building a sheet's noise fields from one seed."""
    benchmark(Sheet, 512, 512, gran_px=6.0, seed=3)


def test_edt(benchmark: BenchmarkFixture) -> None:
    """Times the chamfer distance from every cell of a sparse random mask."""
    mask = np.random.default_rng(5).random((512, 512)) < 0.01
    benchmark(edt, mask)


def test_stamp_a_2000_point_path(benchmark: BenchmarkFixture) -> None:
    """Times stamping a river brush along a 2000 point sine path."""
    x = np.linspace(20, 1180, 2000)
    path = np.stack([x, 200 + 120 * np.sin(x / 90)], axis=1)
    brush, _ = brush_from_id("RIV1-a", 3.0, 2.0, BrushStyle())
    benchmark(
        lambda: stamp(np.zeros((400, 1200), np.float32), path, brush, np.random.default_rng(7))
    )


def test_wash(benchmark: BenchmarkFixture, sheet: Sheet) -> None:
    """Times one pigment's wash over a plain disc."""
    cover = _disc()
    benchmark(wash, cover, sheet, 0.52, 0.20)


def test_building_a_sheet(benchmark: BenchmarkFixture) -> None:
    """Times building a sheet's five noise fields from a second seed."""
    benchmark(Sheet, SIDE, SIDE, 6.0, 11)


def test_the_distance_transform(benchmark: BenchmarkFixture) -> None:
    """Times the chamfer distance from every cell to a winding line."""
    mask = np.zeros((SIDE, SIDE), dtype=bool)
    pts = _meander().round().astype(int)
    mask[pts[:, 1], pts[:, 0]] = True
    benchmark(edt, mask)


@pytest.mark.parametrize("brush_id", ["TRK4-d", "RIV1-a"], ids=["dry-track", "wet-river"])
def test_stamping_a_long_stroke(benchmark: BenchmarkFixture, brush_id: str) -> None:
    """Times stamping one brush along a winding 2000 point path."""
    brush, _ = brush_from_id(brush_id, 3.0, 2.0, BrushStyle())
    pts = _meander()
    aux = ink_aux((SIDE, SIDE), brush)
    benchmark(
        lambda: stamp(
            np.zeros((SIDE, SIDE), np.float32), pts, brush, np.random.default_rng(7), aux=aux
        )
    )


def test_stamping_a_starved_directional_brush(benchmark: BenchmarkFixture) -> None:
    """Times a stroke with the reservoir and the directional break both on."""
    style = dataclasses.replace(BrushStyle(), ink_starve=True, dry_directional=True)
    brush, _ = brush_from_id("TRK4-d", 3.0, 2.0, style, "track")
    pts = _meander()
    aux = ink_aux((SIDE, SIDE), brush)
    benchmark(
        lambda: stamp(
            np.zeros((SIDE, SIDE), np.float32), pts, brush, np.random.default_rng(7), aux=aux
        )
    )


def test_laying_a_wash(benchmark: BenchmarkFixture, sheet: Sheet) -> None:
    """Times one pigment's wash over a lumpy disc, on the plain edge."""
    cover = _blob()
    benchmark(wash, cover, sheet, 0.52, 0.20)


def test_laying_a_wet_wash(benchmark: BenchmarkFixture, sheet: Sheet) -> None:
    """Times a wash inside a wet area, bleeding and granulating from the paper's pits."""
    cover = _blob()
    options = WashOptions(wet=np.clip(cover * 0.8, 0.0, 1.0), gran_gamma=1.6)
    benchmark(wash, cover, sheet, 0.52, 0.20, options)


@pytest.mark.parametrize("glazing", GLAZING.values(), ids=GLAZING.keys())
def test_compositing_a_stack(benchmark: BenchmarkFixture, sheet: Sheet, glazing: bool) -> None:
    """Times compositing four washes over the paper, by multiply or by glazing."""
    cover = _blob()
    keys = ("farmland", "wood", "water", "heath")
    layers: list[Layer] = [
        (wash(np.roll(cover, 40 * i, axis=1), sheet, 0.5, 0.2), rgb(PIGMENTS[k]), TRANSPARENCY[k])
        for i, k in enumerate(keys)
    ]
    base = np.ones((SIDE, SIDE, 3), np.float32)
    benchmark(composite, layers, base, PaperStyle(km_glazing=glazing))
