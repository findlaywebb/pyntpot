"""Tests for the ink pad: the repeat a class carries, joining ways and the finer ink grid."""

from dataclasses import replace

import numpy as np
import pytest

from pyntpot.ink.brush import brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.chains import chain_lines
from pyntpot.ink.pad import InkPad
from pyntpot.ink.sheet import Sheet

#: The classes whose repeat was worth measuring, with the brush and width the
#: plate paints each of them at.
REPEATERS = [
    ("MAJ6-e", 3.0, "route"),
    ("RIV1-a", 8.4, ""),
    ("LAN5-a", 1.8, "lane"),
    ("MAJ2-a", 3.6, "road_major"),
]


def padded(
    brush_id: str,
    width_px: float,
    over: str = "",
    seed: int = 91,
    sheet_seed: int = 11,
    **style_over: object,
) -> np.ndarray:
    """One straight stroke's density, through the pad the painter uses."""
    h, length = 44, 1500
    style = replace(BrushStyle(), **style_over)
    brush, _ = brush_from_id(brush_id, width_px, 2.0, style, over)
    sheet = Sheet(h, length, gran_px=9.0, seed=sheet_seed)
    pts = np.stack([np.linspace(20.0, length - 20.0, 900), np.full(900, h / 2)], axis=1)
    pad = InkPad((h, length), brush, style)
    pad.lay([(brush, pts)], np.random.default_rng(seed))
    return pad.read(brush, sheet)


def shared_repeat(
    brush_id: str, width_px: float, over: str, seeds: int = 6, **style_over: object
) -> tuple[float, int]:
    """The strongest repeat a class carries beyond the bristle scale.

    An autocorrelation along one stroke cannot tell a period from a lucky run
    of noise. Averaging it over strokes drawn on different sheets with
    different bristles can: what the brush itself repeats stays where it is and
    everything else cancels. Lags under 120 render pixels are left out, because
    the bristles, the tip and the paper's own coarse cell all live under that
    and are meant to.

    Args:
        brush_id: The brush sheet cell.
        width_px: The display width the class is painted at.
        over: The class's key in the style's brush overrides.
        seeds: How many strokes to average over.
        style_over: Paint style fields to move.

    Returns:
        The strongest correlation beyond that lag, and the lag it sits at.
    """
    acs = []
    for s in range(seeds):
        dens = padded(
            brush_id, width_px, over, seed=91 + 7 * s, sheet_seed=11 + 3 * s, **style_over
        )
        x = dens.sum(axis=0)[80:-80].astype(float)
        k = 201
        trend = np.convolve(np.pad(x, k // 2, mode="edge"), np.ones(k) / k, mode="valid")[: len(x)]
        x = x - trend
        f = np.fft.rfft(x, 2 * len(x))
        ac = np.fft.irfft(f * np.conj(f))[:900]
        acs.append(ac / max(ac[0], 1e-9))
    mean = np.mean(acs, axis=0)[120:]
    return float(mean.max()), int(np.argmax(mean)) + 120


def test_the_drift_along_a_stroke_repeats_and_the_flag_stops_it():
    """The complaint was repetition, and it was four sines saying the same thing.

    Every wander in a stroke was a sine, so a long mark came back to itself:
    the bristle drift every 390 render pixels and every bristle in step with
    the rest, the line's wobble every 210, the pressure every 2 pi cells, and
    each bristle's break between 116 and 215 with a beat near 500 where two of
    them differed a little. The route pen carries it plainest, because nothing
    else is happening on a nib.
    """
    off, lag = shared_repeat("MAJ6-e", 3.0, "route")
    assert off > 0.4
    assert 340 <= lag <= 430  # the bristle drift, 2 pi times its own 62 px
    for brush_id, width_px, over in REPEATERS:
        was, _ = shared_repeat(brush_id, width_px, over)
        now, _ = shared_repeat(brush_id, width_px, over, brush_organic=True)
        assert now < 0.15, brush_id
        # MAJ2-a no longer clears the second bar, and the reason is worth
        # keeping: its own repeat fell from 0.22 to 0.09 when the bristle drift
        # stopped being drawn independently per bristle. What carried the
        # sine's period into the density on a road was the tip folding into
        # filaments and the whole set of them swinging together; with the tip
        # laying a band there is almost nothing left for the sine to modulate,
        # so the flag has no period to remove and only the bar above applies.
        if was >= 0.15:
            assert now < was * 0.7, brush_id


def test_a_road_split_into_ways_is_one_mark_again():
    """OSM splits a road wherever a tag changes, and the joins show.

    Each way took a fresh tip pattern, a fresh set-down blob and a lift taper
    at both ends, so a road arrived as a chain of tapered lozenges. Joined
    first, the same six pieces paint the mark that was drawn in one.
    """
    h, w = 44, 1200
    whole = np.stack([np.linspace(20.0, w - 20.0, 901), np.full(901, h / 2)], axis=1)
    pieces = [whole[i * 150 : (i + 1) * 150 + 1] for i in range(6)]
    assert len(chain_lines(pieces, 2.5)) == 1
    sheet = Sheet(h, w, gran_px=9.0, seed=11)

    def lay(lines: list[np.ndarray], **style_over: object) -> np.ndarray:
        style = replace(BrushStyle(), **style_over)
        brush, _ = brush_from_id("MAJ2-a", 3.6, 2.0, style, "road_major")
        pad = InkPad((h, w), brush, style)
        pad.lay([(brush, line) for line in lines], np.random.default_rng(91))
        return pad.read(brush, sheet).sum(axis=0)[60:-60]

    ref = lay([whole])
    thin = float(np.median(ref)) * 0.6
    assert (lay(pieces) < thin).sum() > 40  # the tapers, in the mark's body
    assert (lay(pieces, ink_joins=True) < thin).sum() == 0
    assert lay(pieces, ink_joins=True) == pytest.approx(ref, abs=1e-4)


def test_a_way_that_arrives_backwards_is_still_joined():
    """A junction hands the painter whichever end it has; both are the mark."""
    a = np.stack([np.linspace(0.0, 100.0, 60), np.zeros(60)], axis=1)
    b = np.stack([np.linspace(220.0, 100.0, 60), np.zeros(60)], axis=1)
    chains = chain_lines([a, b], 2.5)
    assert len(chains) == 1
    assert chains[0][0][0] == pytest.approx(0.0)
    assert chains[0][-1][0] == pytest.approx(220.0)
    # And two that meet nowhere are left as the two marks they are.
    far = np.stack([np.linspace(400.0, 500.0, 60), np.zeros(60)], axis=1)
    assert len(chain_lines([a, far], 2.5)) == 2


def test_a_finer_grid_converges_on_the_mark_the_brush_describes():
    """What the eye reads as pixelation is the ink's own grid.

    The saturation and the paper gate are per pixel, so the plate's grid is
    where a thin mark's edge is decided. Painting the whole ink pipeline on a
    finer grid and reducing the density back converges: against a stroke
    painted six times finer, the plate's own grid is most of twice as far off
    as a grid twice as fine.
    """
    h, w = 40, 500
    t = np.linspace(20.0, w - 20.0, 900)
    pts = np.stack([t, 8.0 + t / 7.0], axis=1)  # a shallow diagonal: the worst case
    sheet = Sheet(h, w, gran_px=9.0, seed=11)

    def at(ss: int) -> np.ndarray:
        style = BrushStyle(ink_ss=ss)
        brush, _ = brush_from_id("MAJ6-e", 3.0, 2.0, style, "route")
        pad = InkPad((h, w), brush, style)
        assert pad.acc.shape == (h * ss, w * ss)
        pad.lay([(brush, pts)], np.random.default_rng(91))
        return pad.read(brush, sheet)

    ref = at(6)
    err = [float(np.abs(at(ss) - ref).mean()) for ss in (1, 2, 3)]
    assert err[0] > err[1] > err[2]
    assert err[1] < err[0] * 0.7


def test_a_finer_grid_lays_the_same_weight_of_ink():
    """The accumulator holds a thickness, not a count of deposits.

    Without the grid factor in the normalisation the same mark on a grid twice
    as fine comes out half as dark, which is a bug and not a look.
    """
    for brush_id, width_px, over in REPEATERS:
        one = float(padded(brush_id, width_px, over, ink_ss=1).sum())
        two = float(padded(brush_id, width_px, over, ink_ss=2).sum())
        assert two == pytest.approx(one, rel=0.2), brush_id
        assert two < one  # a sharper mark spreads less, and is honest about it
