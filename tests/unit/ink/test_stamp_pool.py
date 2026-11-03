"""Tests for the pen's set-down blot as `stamp` lays it: where it lies, and how much it lays.

The blot's shape and its cover are tested in `test_deposit.py`.
"""

from dataclasses import replace

import numpy as np
import pytest

from pyntpot.ink.brush import brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.noise import chamfer_distance
from pyntpot.ink.pad import ink_density
from pyntpot.ink.sheet import Sheet
from pyntpot.ink.stamping import stamp

#: The ink the set-down blot of a `MAJ6-e` pen 1 to 2 render px wide laid before it was kept
#: on its stroke: its whole Gaussian, of radius 1.2 px (the floor) cut at 4 px, times pool
#: 0.9 and gain 1.9. Measured on `main` at `b78a1bb`.
THIN_BLOT_INK_BEFORE = 15.468


def blot_ink(width_display_px: float, path: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """What a `MAJ6-e` pen's set-down blot adds to the accumulator: with its pool less without."""
    pen, _ = brush_from_id("MAJ6-e", width_display_px, 2.0, BrushStyle())
    marks = []
    for brush in (pen, replace(pen, pool=0.0)):
        acc = np.zeros(shape, np.float32)
        stamp(acc, path, brush, np.random.default_rng(9))
        marks.append(acc)
    return marks[0] - marks[1]


def test_the_pen_sets_down_where_it_touches_and_nowhere_else():
    """A nib meeting the paper: extra ink over about a width, then nothing."""
    tuned, _ = brush_from_id("LAN5-a", 2.0, 2.0, BrushStyle(), "lane")
    assert tuned.load > 0 and tuned.pool > 0
    assert tuned.load_px == pytest.approx(tuned.width * 0.85)
    bare = replace(tuned, load=0.0, pool=0.0)
    line = np.stack([np.linspace(10, 190, 90), np.full(90, 20.0)], axis=1)
    marks = []
    for brush in (tuned, bare):
        acc = np.zeros((40, 200), np.float32)
        stamp(acc, line, brush, np.random.default_rng(5))
        marks.append(acc)
    assert marks[0][:, 8:18].sum() > marks[1][:, 8:18].sum() * 1.3
    assert marks[0][:, 60:160].sum() == pytest.approx(marks[1][:, 60:160].sum(), rel=1e-4)


#: The most the blot may add, on average, to a band of paper beside a wide pen's ink, as density.
#: 1 to 2 px out it is the bleed of the darker start, which wicks a pixel or two past the
#: ink (0.0021 at 5 render px, 0.0070 at 12, where the Gaussian laid round the start added
#: 0.038 and 0.133); 3 to 8 px out it is nothing.
BAND_BOUNDS = {(1.0, 2.0): 0.01, (3.0, 8.0): 1e-4}


@pytest.mark.parametrize(
    ("width", "band"),
    [(2.6, (1.0, 2.0)), (2.6, (3.0, 8.0)), (6.0, (1.0, 2.0)), (6.0, (3.0, 8.0))],
    ids=["5px-1to2", "5px-3to8", "12px-1to2", "12px-3to8"],
)
def test_a_wide_pen_leaves_no_grey_ring_round_its_ink(
    width: float, band: tuple[float, float]
) -> None:
    """A pen 5 or 12 render px wide adds under 0.01 of density 1 to 2 px out from its ink, and nothing 3 to 8 px out."""
    sheet = Sheet(80, 140, gran_px=6.0, seed=4)
    pen, _ = brush_from_id("MAJ6-e", width, 2.0, BrushStyle())
    line = np.stack([np.linspace(30, 100, 60), np.full(60, 30.0)], axis=1)
    dens = []
    for brush in (pen, replace(pen, pool=0.0)):
        acc = np.zeros((80, 140), np.float32)
        stamp(acc, line, brush, np.random.default_rng(9))
        dens.append(ink_density(acc, brush, sheet))
    away = chamfer_distance(dens[1] > 0.05)
    ring = (away >= band[0]) & (away <= band[1])
    assert ring.sum() > 300
    assert float((dens[0] - dens[1])[ring].mean()) < BAND_BOUNDS[band]


def test_a_start_at_zero_pressure_that_turns_back_lays_no_blot_off_its_ink():
    """A 10 render px pen that sets down, barely moves and turns back lays its blot on its own ink only."""
    path = np.array([(3.0, 7.0), (3.0, 7.1875), (2.0, 2.0)])
    pen, _ = brush_from_id("MAJ6-e", 5.0, 2.0, BrushStyle())
    marks = []
    for brush in (pen, replace(pen, pool=0.0)):
        acc = np.zeros((60, 220), np.float32)
        stamp(acc, path, brush, np.random.default_rng(0))
        marks.append(acc)
    blot = marks[0] - marks[1]
    assert blot.any()
    assert not blot[marks[1] == 0].any()


@pytest.mark.parametrize(
    ("width", "least"),
    [(1.75, 10.0), (2.0, 15.0), (6.0, 100.0)],
    ids=["3.5px", "4px", "12px"],
)
def test_a_pen_3_5_px_or_wider_lays_no_blot_on_paper_its_stroke_does_not(
    width: float, least: float
) -> None:
    """A pen 3.5, 4 or 12 render px wide adds blot ink only to pixels the same stroke without it inks."""
    line = np.stack([np.linspace(30, 100, 60), np.full(60, 30.3)], axis=1)
    pen, _ = brush_from_id("MAJ6-e", width, 2.0, BrushStyle())
    bare = np.zeros((80, 140), np.float32)
    stamp(bare, line, replace(pen, pool=0.0), np.random.default_rng(9))
    blot = blot_ink(width, line, (80, 140))
    assert blot.sum() > least
    assert not blot[bare == 0].any()


#: The least share of `THIN_BLOT_INK_BEFORE` a pen 1 to 2 render px wide keeps, at any
#: sub-pixel offset of its line: 0.760 at worst (1 px, the line 0.73 px below a pixel's
#: centre, measured in 0.01 px steps), with a margin.
THIN_BLOT_FLOOR = 0.74


@pytest.mark.parametrize(
    "dy", [0.0, 0.3, 0.5, 0.73, 0.9], ids=["y0", "y0.3", "y0.5", "y0.73", "y0.9"]
)
@pytest.mark.parametrize("width", [0.5, 0.75, 1.0], ids=["1px", "1.5px", "2px"])
def test_a_thin_pen_s_start_keeps_most_of_its_blot(width: float, dy: float) -> None:
    """A pen 1 to 2 render px wide lays 74% to 100% of the ink its blot laid before, at any sub-pixel offset."""
    line = np.stack([np.linspace(30, 100, 60), np.full(60, 30.0 + dy)], axis=1)
    laid = float(blot_ink(width, line, (60, 120)).sum())
    assert THIN_BLOT_FLOOR * THIN_BLOT_INK_BEFORE < laid <= THIN_BLOT_INK_BEFORE


def test_a_stroke_from_far_off_the_plate_in_one_axis_lays_no_blot():
    """A stroke that starts 80 px above the plate, its column on it, inks the plate but no blot."""
    line = np.stack([np.full(60, 60.0), np.linspace(-80, 40, 60)], axis=1)
    pen, _ = brush_from_id("MAJ6-e", 1.3, 2.0, BrushStyle())
    acc = np.zeros((60, 120), np.float32)
    stamp(acc, line, pen, np.random.default_rng(9))
    assert acc[:40].sum() > 0
    assert not blot_ink(1.3, line, (60, 120)).any()


def test_a_stroke_that_comes_back_over_its_start_does_not_widen_the_blot():
    """A loop that returns along the line behind its start leaves no blot there: it counts the set-down only."""
    loop = np.array(
        [(60.0, 30.0), (90.0, 30.0), (90.0, 45.0), (40.0, 45.0), (40.0, 30.0), (60.0, 30.0)]
    )
    blot = blot_ink(1.3, loop, (60, 120))
    assert blot[28:33, 61:65].sum() > 0
    assert not blot[28:33, 50:59].any()


def test_a_tight_loop_back_over_its_start_does_not_widen_the_blot():
    """A loop 8 px across that is back behind its start 44 px on leaves no blot there."""
    loop = np.array(
        [(60.0, 30.0), (68.0, 30.0), (68.0, 38.0), (52.0, 38.0), (52.0, 30.0), (60.0, 30.0)]
    )
    blot = blot_ink(1.3, loop, (60, 120))
    assert blot[28:33, 61:65].sum() > 0
    assert not blot[28:33, 50:59].any()
