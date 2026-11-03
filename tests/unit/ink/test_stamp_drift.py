"""Tests for an organic brush's drift: shared across the tip, never a shift of the stroke."""

from dataclasses import replace

import numpy as np
import pytest

from pyntpot.ink.brush import brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.stamp import _organic_fields, stamp
from pyntpot.ink.tip import fbm1


def test_a_short_ring_is_not_shifted_off_its_path_by_the_shared_drift():
    """On a stroke shorter than a drift cell, the drift's mean stays a drift, not a shift.

    Smoothing the drift across the tip and rescaling it to its old spread blew up the
    part every bristle shares, which on a short stroke is nearly a constant: the whole
    ring moved in or out along its normal by up to three times the drift's own reach, and
    a small letter's bowl closed. Across many seeds the ink's mean radius stays within it.
    """
    brush, _ = brush_from_id("MAJ2-a", 2.0, 2.0, BrushStyle(brush_organic=True), "road_major")
    assert brush.organic and brush.coherence > 0
    rx, ry = 5.3, 7.4
    turns = np.linspace(0.0, 2.0 * np.pi, 124)
    ring = np.stack([20.0 + rx * np.sin(turns), 20.0 + ry * np.cos(turns)], axis=1)
    yy, xx = np.mgrid[0:40, 0:40]
    # Each pixel's distance outside the ring, in pixels, near enough for an oval this round.
    outside = (np.hypot((xx - 20.0) / rx, (yy - 20.0) / ry) - 1.0) * (rx + ry) / 2.0
    shifts = []
    for seed in range(300):
        acc = np.zeros((40, 40), np.float32)
        stamp(acc, ring, brush, np.random.default_rng(seed))
        shifts.append(float((acc * outside).sum() / acc.sum()))
    worst = max(shifts, key=abs)
    assert abs(worst) < brush.jitter * 1.6, f"a ring moved {worst:.2f} px off its path"


def test_the_shared_drift_keeps_the_field_s_spread_and_mean_and_leans_its_way():
    """Sharing the drift across the tip keeps its spread and its mean, and each bristle's lean.

    Drawn from the same seed, the drift before sharing is the plain lattice field. After
    it, its spread is restored exactly, its mean over the stroke stays where the field put
    it (a short stroke's mean is not blown up into a shift), and it still correlates with
    the field it came from.
    """
    brush, _ = brush_from_id("MAJ2-a", 2.0, 2.0, BrushStyle(brush_organic=True), "road_major")
    m = brush.bristles
    t = np.linspace(0.0, 40.0, int(40.0 / brush.step) + 2).astype(np.float32)
    cell = 6.283 * 62.0 * brush.unit * brush.org_mult
    shifts, leans = [], []
    for seed in range(20):
        field = fbm1(t, cell, brush, np.random.default_rng(seed), m)
        drift, _along = _organic_fields(t, m, brush, np.random.default_rng(seed))
        assert float(drift.std()) == pytest.approx(float(field.std()), rel=1e-3)
        shifts.append(abs(float(drift.mean()) - float(field.mean())))
        leans.append(
            np.corrcoef((field - field.mean()).ravel(), (drift - drift.mean()).ravel())[0, 1]
        )
    assert max(shifts) < 0.25, "the shared part of a short stroke's drift was amplified"
    assert float(np.mean(leans)) > 0.1


def _neighbour_lean(drift: np.ndarray) -> float:
    """How closely neighbouring bristles drift together: their mean correlation along the stroke."""
    pairs = [np.corrcoef(drift[:, i], drift[:, i + 1])[0, 1] for i in range(drift.shape[1] - 1)]
    return float(np.mean(pairs))


def test_neighbouring_bristles_drift_together_once_the_drift_is_shared():
    """At the brush's coherence, neighbours drift more alike than the separate fields they came from."""
    brush, _ = brush_from_id("MAJ2-a", 2.0, 2.0, BrushStyle(brush_organic=True), "road_major")
    assert 0 < brush.coherence < 1
    m = brush.bristles
    t = np.linspace(0.0, 40.0, int(40.0 / brush.step) + 2).astype(np.float32)
    cell = 6.283 * 62.0 * brush.unit * brush.org_mult
    gains = []
    for seed in range(10):
        field = fbm1(t, cell, brush, np.random.default_rng(seed), m)
        drift, _along = _organic_fields(t, m, brush, np.random.default_rng(seed))
        gains.append(_neighbour_lean(drift) - _neighbour_lean(field))
    assert min(gains) > 0.2, f"sharing the drift left neighbours apart: {min(gains):.2f}"


def test_the_break_along_is_the_next_lattice_field_at_its_own_cell():
    """The break along the stroke is the field drawn after the drift, at 24 tau a brush unit.

    A brush whose unit and organic multiplier differ from one, so neither can stand in
    for the other in the cell.
    """
    brush, _ = brush_from_id("MAJ2-a", 2.0, 2.0, BrushStyle(brush_organic=True), "road_major")
    brush = replace(brush, unit=1.5, org_mult=0.7)
    m = brush.bristles
    t = np.linspace(0.0, 40.0, int(40.0 / brush.step) + 2).astype(np.float32)
    rng = np.random.default_rng(3)
    fbm1(t, 6.283 * 62.0 * 1.5 * 0.7, brush, rng, m)
    expected = fbm1(t, 6.283 * 24.0 * 1.5 * 0.7, brush, rng, m)
    _drift, along = _organic_fields(t, m, brush, np.random.default_rng(3))
    np.testing.assert_array_equal(along, expected)
