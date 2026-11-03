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
from pyntpot.ink.stamp import stamp

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


def test_a_wide_pen_leaves_no_grey_ring_round_its_ink():
    """A 2.6 px pen's set-down blot adds nothing to the paper 3 to 8 px out from its ink."""
    sheet = Sheet(60, 120, gran_px=6.0, seed=4)
    pen, _ = brush_from_id("MAJ6-e", 2.6, 2.0, BrushStyle())
    line = np.stack([np.linspace(30, 100, 60), np.full(60, 30.0)], axis=1)
    dens = []
    for brush in (pen, replace(pen, pool=0.0)):
        acc = np.zeros((60, 120), np.float32)
        stamp(acc, line, brush, np.random.default_rng(9))
        dens.append(ink_density(acc, brush, sheet))
    away = chamfer_distance(dens[1] > 0.05)
    ring = (away >= 3.0) & (away <= 8.0)
    assert ring.sum() > 500
    assert float((dens[0] - dens[1])[ring].mean()) < 1e-4


@pytest.mark.parametrize("width", [0.5, 0.75, 1.0], ids=["1px", "1.5px", "2px"])
def test_a_thin_pen_s_start_keeps_most_of_its_blot(width: float) -> None:
    """A pen 1 to 2 render px wide still lays 80% to 100% of the ink its blot laid before."""
    line = np.stack([np.linspace(30, 100, 60), np.full(60, 30.3)], axis=1)
    laid = float(blot_ink(width, line, (60, 120)).sum())
    assert 0.8 * THIN_BLOT_INK_BEFORE < laid <= THIN_BLOT_INK_BEFORE


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
