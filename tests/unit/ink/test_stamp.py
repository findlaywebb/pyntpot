"""Tests for the stamp: one stroke's marks, the reservoir, the break, the nib and the tip."""

from dataclasses import replace

import numpy as np
import pytest

from pyntpot.ink.brush import Brush, brush_from_id, ink_aux, scaled_brush
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.pad import ink_density
from pyntpot.ink.sheet import Sheet
from pyntpot.ink.stamp import stamp
from pyntpot.ink.tip import _tip_band


def test_a_dry_brush_breaks_where_a_wet_one_does_not():
    """Dryness is one number, and it is what makes a track scratchy."""
    sheet = Sheet(60, 220, gran_px=6.0, seed=3)
    line = np.stack([np.linspace(10, 210, 80), np.full(80, 30.0)], axis=1)
    marks = {}
    for key, brush_id in (("wet", "RIV1-a"), ("dry", "TRK4-d")):
        brush, _ = brush_from_id(brush_id, 3.0, 2.0, BrushStyle())
        acc = np.zeros((60, 220), np.float32)
        stamp(acc, line, brush, np.random.default_rng(7))
        marks[key] = ink_density(acc, brush, sheet)
    band = slice(24, 37)
    wet = marks["wet"][band] > 0.25
    dry = marks["dry"][band] > 0.25
    assert wet.mean() > dry.mean()
    assert dry.any()  # broken, not absent


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


def test_two_strokes_crossing_never_double():
    """Saturation is what stops a crossing reaching twice the black."""
    sheet = Sheet(60, 60, gran_px=6.0, seed=2)
    brush, _ = brush_from_id("MAJ2-a", 3.0, 2.0, BrushStyle())
    across = np.stack([np.linspace(5, 55, 40), np.full(40, 30.0)], axis=1)
    down = np.stack([np.full(40, 30.0), np.linspace(5, 55, 40)], axis=1)
    one = np.zeros((60, 60), np.float32)
    stamp(one, across, brush, np.random.default_rng(1))
    both = one.copy()
    stamp(both, down, brush, np.random.default_rng(1))
    d_one = ink_density(one, brush, sheet)
    d_both = ink_density(both, brush, sheet)
    assert d_both.max() <= 1.0
    assert d_both[28:33, 28:33].max() <= d_one.max() + 0.05


def long_stroke(
    brush_id: str, width_px: float, over: str = "", length: int = 1500, **style_over: object
) -> tuple[np.ndarray, Brush]:
    """One straight 1500 px stroke's density, as a swatch image paints it."""
    h = 44
    style = replace(BrushStyle(), **style_over)
    brush, _ = brush_from_id(brush_id, width_px, 2.0, style, over)
    sheet = Sheet(h, length, gran_px=9.0, seed=11)
    pts = np.stack([np.linspace(20.0, length - 20.0, 900), np.full(900, h / 2)], axis=1)
    acc = np.zeros((h, length), np.float32)
    aux = ink_aux((h, length), brush)
    stamp(acc, pts, brush, np.random.default_rng(91), aux=aux)
    return ink_density(acc, brush, sheet, aux), brush


def thirds(dens: np.ndarray) -> list[float]:
    """Ink per column, averaged over each third of the stroke."""
    cols = dens.sum(axis=0)
    n = len(cols)
    return [float(cols[i * n // 3 : (i + 1) * n // 3].mean()) for i in range(3)]


def test_a_starved_brush_runs_out_along_the_stroke():
    """The mark starts loaded and breaks into skips, rather than fading evenly."""
    off, _ = long_stroke("TRK4-d", 2.4, "track")
    on, brush = long_stroke("TRK4-d", 2.4, "track", ink_starve=True)
    assert brush.starve and brush.run_px > 0
    # Against the same stroke unstarved, because a path's own ink wanders: what
    # the reservoir has to do is take more out of the end than out of the start.
    kept = [n / f for n, f in zip(thirds(on), thirds(off), strict=True)]
    assert kept[2] < kept[0] * 0.9
    assert thirds(off)[2] > thirds(on)[2] * 1.3
    assert on[:, -400:].max() > 0.2  # broken, not absent


def test_the_reservoir_is_read_off_the_final_density_not_the_deposits():
    """A per-sample gate is diluted by the splat: the mark must break, not thin.

    With the gate on the deposits alone a starved mark comes out evenly paler.
    Reading it off the accumulated density instead is what puts holes in it, so
    the last third loses more of its area than it loses of its ink.
    """

    def patchiness(dens: np.ndarray) -> float:
        cols = dens[:, -500:].sum(axis=0)
        return float(cols.std() / max(cols.mean(), 1e-6))

    for brush_id, width, over in (
        ("TRK4-d", 2.4, "track"),
        ("STR3-a", 2.2, "minor"),
        ("MAJ2-a", 3.6, "road_major"),
    ):
        off, _ = long_stroke(brush_id, width, over)
        on, _ = long_stroke(brush_id, width, over, ink_starve=True)
        assert patchiness(on) > patchiness(off) * 1.1, brush_id


def turned_stroke(vertical: bool, **style_over: object) -> tuple[np.ndarray, Sheet, Brush]:
    """The same dry brush drawn across the same paper, one way then the other."""
    size = 420
    style = replace(BrushStyle(), **style_over)
    brush, _ = brush_from_id("TRK4-d", 6.0, 2.0, style, "track")
    sheet = Sheet(size, size, gran_px=9.0, seed=11)
    t = np.linspace(20.0, size - 20.0, 600)
    mid = np.full(600, size / 2)
    pts = np.stack([mid, t] if vertical else [t, mid], axis=1)
    acc = np.zeros((size, size), np.float32)
    aux = ink_aux((size, size), brush)
    stamp(acc, pts, brush, np.random.default_rng(91), aux=aux)
    return ink_density(acc, brush, sheet, aux), sheet, brush


def test_a_directional_break_follows_the_stroke_not_the_sheet():
    """Where the mark breaks stops being a fact about the paper under it.

    The isotropic gate reads `sheet.paper` at the pixel, so a dry mark breaks
    wherever the paper happens to be low and the break is the same blotch
    whichever way the stroke was drawn. On the flag the break comes from a
    texture in the stroke's own frame, stretched along it, so the paper stops
    explaining where the mark is thin.
    """

    def explained(dens: np.ndarray, sheet: Sheet) -> float:
        inked = dens > 0.02
        return abs(
            float(np.corrcoef(sheet.paper[inked].astype(float), dens[inked].astype(float))[0, 1])
        )

    for vertical in (False, True):
        off, sheet, base = turned_stroke(vertical)
        on, _, brush = turned_stroke(vertical, dry_directional=True)
        assert brush.dir_dry and not base.dir_dry
        assert explained(off, sheet) > 0.2
        assert explained(on, sheet) < explained(off, sheet) * 0.4
        # It swaps where the break falls; it does not remove it or darken it.
        assert (on[on > 0.02] < 0.35).mean() > 0.1
        assert on.sum() == pytest.approx(off.sum(), rel=0.12)


def test_a_wet_brush_is_left_alone_by_the_directional_break():
    """A river is not a dry brush, so the flag barely moves it."""
    off, _ = long_stroke("RIV1-a", 8.4)
    on, _ = long_stroke("RIV1-a", 8.4, dry_directional=True)
    assert on.sum() == pytest.approx(off.sum(), rel=0.03)


def test_a_nib_thins_and_lightens_as_it_runs_down():
    """A pen does not break, it runs down: the line narrows and pales."""
    off, base = long_stroke("LAN5-a", 1.8, "lane")
    on, brush = long_stroke("LAN5-a", 1.8, "lane", pen_starve=True)
    assert brush.pen and brush.pen_starve and not brush.starve
    assert not base.pen_starve
    a, _b, c = thirds(on)
    assert c < a  # it runs down along the stroke
    wide = [(on[:, i * 500 : (i + 1) * 500] > 0.25).sum(axis=0).mean() for i in range(3)]
    assert wide[2] < wide[0]
    assert thirds(off)[2] > c  # and it is lighter than the same nib full


def test_a_nib_comes_back_at_the_reload():
    """The seam a dip leaves is what makes a long line look drawn."""
    run, _ = long_stroke("MAJ6-e", 3.0, "route", length=9000, pen_starve=True, pen_reservoir=60.0)
    cols = (run > 0.25).sum(axis=0).astype(float)
    # Somewhere past the first dip the line is back to its full width.
    assert cols[3000:8000].max() >= cols[200:800].max() * 0.95


def tip_across(
    brush_id: str,
    width_px: float,
    over: str = "",
    ss: int = 3,
    seeds: tuple[int, ...] = (91, 7, 33),
    **style_over: object,
) -> np.ndarray:
    """One stroke's accumulator sampled across the tip, on the ink's own grid.

    The fault the tip knobs are for lives in the accumulator, before the paper
    gate and before the reduce, so this reads it there. Each profile is
    normalised by its own mean, so what comes back is the shape of the tip and
    not how much ink it carried.

    Args:
        brush_id: The brush sheet cell.
        width_px: The display width the class is painted at.
        over: The class's key in the style's brush overrides.
        ss: The ink grid, as a multiple of the plate's.
        seeds: The tip patterns to pool over, because one draw is one tip.
        style_over: Paint style fields to move.

    Returns:
        `(windows, samples across)`, each row a normalised cross-tip profile.
    """
    style = replace(BrushStyle(), **style_over)
    b, _ = brush_from_id(brush_id, width_px, 2.0, style, over)
    sb = scaled_brush(b, ss)
    h, w = 150 * ss, 360 * ss
    # A shallow diagonal, so the tip crosses the pixel grid the way a road on
    # the card does rather than landing on whole rows.
    ang = np.radians(20.0)
    s = np.linspace(0.0, 320.0 * ss, 700)
    x0, y0 = 20.0 * ss, 40.0 * ss
    pts = np.stack([x0 + s * np.cos(ang), y0 + s * np.sin(ang)], 1).astype(np.float32)
    s = np.arange(60.0 * ss, 260.0 * ss)
    cx, cy = x0 + s * np.cos(ang), y0 + s * np.sin(ang)
    u = np.linspace(-0.28, 0.28, 61) * sb.width
    px = cx[:, None] - np.sin(ang) * u[None, :]
    py = cy[:, None] + np.cos(ang) * u[None, :]
    ix = np.clip(np.floor(px).astype(int), 0, w - 2)
    iy = np.clip(np.floor(py).astype(int), 0, h - 2)
    fx, fy = px - ix, py - iy
    rows = []
    for seed in seeds:
        acc = np.zeros((h, w), np.float32)
        stamp(acc, pts, sb, np.random.default_rng(seed))
        val = (
            acc[iy, ix] * (1 - fx) * (1 - fy)
            + acc[iy, ix + 1] * fx * (1 - fy)
            + acc[iy + 1, ix] * (1 - fx) * fy
            + acc[iy + 1, ix + 1] * fx * fy
        )
        n = len(val) // 40 * 40
        rows.append(val[:n].reshape(-1, 40, val.shape[1]).mean(1))
    prof = np.concatenate(rows)
    # Against the mark's own envelope rather than its mean, so what comes back
    # is the holes and steps inside the mark and not the tip's bell, nor the
    # sideways wander of the whole mark, which is a wander and not a fault.
    env = _tip_band(prof, prof.shape[1] / 5.0)
    return prof / np.maximum(env, 1e-9)


def test_the_tip_no_longer_folds_over_itself():
    """Streaking: a tip laying filaments, not a band.

    Every bristle's sideways drift was drawn independently of the one beside
    it, and on `road_major` that drift is 0.55 render pixels either way against
    a bristle spacing of 0.23. So neighbours crossed, the tip collapsed into
    four or five coincident filaments with bare paper between them, and because
    the phases do not change along the stroke those gaps ran its whole length.
    Sharing the drift across a quarter of the tip is what makes it a tip again.
    """
    was = tip_across(
        "MAJ2-a", 3.6, "road_major", bristle_drift_coherence=0.0, bristle_bandlimit_px=0.0
    )
    now = tip_across("MAJ2-a", 3.6, "road_major")
    # The deepest hole inside the mark, against the mark's own envelope. A
    # quarter is a bristle's worth of nearly bare paper in the middle of a
    # road; a tip laying a band sits close to 1.
    assert float(was.min(1).mean()) < 0.30
    assert float(now.min(1).mean()) > 0.85
    # And the step from one lane to the next, which is what reads as harsh.
    assert (
        float(np.abs(np.diff(now, axis=1)).max()) < float(np.abs(np.diff(was, axis=1)).max()) * 0.45
    )


def test_both_tip_knobs_are_wired_and_each_one_earns_its_place():
    """The fold and the bandlimit are two faults, and both have to be fixed.

    The tip carries a fixed number of logical bristles whatever it is painted
    at, so most of its detail is finer than the plate can draw and comes back
    as an alias. That is a second fault under the fold, and it only shows once
    the fold is gone: with the drift shared but the weights unbandlimited the
    tip is still twice as uneven as it needs to be.
    """
    style = BrushStyle()
    assert style.bristle_drift_coherence == 0.25
    assert style.bristle_bandlimit_px == 0.9
    assert style.bristle_contrast == 1.0
    b, _ = brush_from_id("MAJ2-a", 3.6, 2.0, style, "road_major")
    assert (b.coherence, b.band_px, b.contrast) == (0.25, 0.9, 1.0)
    assert scaled_brush(b, 3).coherence == 0.25

    both = float(tip_across("MAJ2-a", 3.6, "road_major").std(1).mean())
    drift_only = float(
        tip_across("MAJ2-a", 3.6, "road_major", bristle_bandlimit_px=0.0).std(1).mean()
    )
    neither = float(
        tip_across(
            "MAJ2-a", 3.6, "road_major", bristle_drift_coherence=0.0, bristle_bandlimit_px=0.0
        )
        .std(1)
        .mean()
    )
    assert drift_only < neither * 0.55
    assert both < drift_only * 0.35
    # And the contrast knob is the user's, so it has to move the tip both
    # ways: down to a smoother lane and up to a harder one.
    softer = float(tip_across("MAJ2-a", 3.6, "road_major", bristle_contrast=0.5).std(1).mean())
    harder = float(tip_across("MAJ2-a", 3.6, "road_major", bristle_contrast=2.0).std(1).mean())
    assert softer < both < harder


def test_a_corner_is_rounded_to_the_brush_rather_than_stamped_through():
    """A tip stamped through a 90 degree vertex folds over itself.

    The generalised track turns 82 degrees at the 95th percentile of its
    vertices. The normal swings through a turn like that in a couple of
    samples, the far side of the tip runs backwards, and what lands is a bead
    sitting in the quadrant outside the corner. No brush draws a corner
    tighter than it is wide.
    """
    h = w = 200
    leg_a = np.stack([np.linspace(20.0, 100.0, 300), np.full(300, 60.0)], axis=1)
    leg_b = np.stack([np.full(300, 100.0), np.linspace(60.0, 180.0, 300)], axis=1)
    pts = np.concatenate([leg_a, leg_b])
    sheet = Sheet(h, w, gran_px=9.0, seed=11)
    yy, xx = np.mgrid[0:h, 0:w]
    outside = (xx > 100) & (yy < 60)

    def mark(smooth: bool) -> tuple[np.ndarray, Brush]:
        style = BrushStyle(stroke_smooth=smooth)
        brush, _ = brush_from_id("MAJ2-a", 3.6, 2.0, style, "road_major")
        acc = np.zeros((h, w), np.float32)
        aux = ink_aux((h, w), brush)
        stamp(acc, pts, brush, np.random.default_rng(91), aux=aux)
        return ink_density(acc, brush, sheet, aux), brush

    off, base = mark(False)
    on, brush = mark(True)
    assert base.smooth == 0.0
    assert brush.smooth == pytest.approx(brush.width * 0.7)
    assert float(on[outside].sum()) < float(off[outside].sum()) * 0.75
    # It rounds the corner; it does not shorten the road or thin it.
    assert on.sum() == pytest.approx(off.sum(), rel=0.06)
    assert on[58:63, 25:75].sum() == pytest.approx(off[58:63, 25:75].sum(), rel=0.05)
