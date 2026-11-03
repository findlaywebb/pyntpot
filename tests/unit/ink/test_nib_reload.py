"""Tests for a nib's reload: the spent share is continuous at every dip, so the line swells back."""

from dataclasses import replace

import numpy as np
import pytest

from pyntpot.ink.brush import Brush, brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.pad import ink_density
from pyntpot.ink.sheet import Sheet
from pyntpot.ink.stamping import _nib_spent, stamp

#: Just either side of a dip, in pressure-weighted render pixels.
EPSILON = 1e-6


def repro_pen(pen_reservoir: float = 22.0, pen_starve: bool = True) -> Brush:
    """The issue's nib: a 5 px `MAJ6-e`, thinning to nothing when empty, dipped every 1.4 reservoirs."""
    style = replace(
        BrushStyle(),
        pen_starve=pen_starve,
        pen_reservoir=pen_reservoir,
        pen_thin=1.0,
        ink_dip_mult=1.4,
    )
    pen, _ = brush_from_id("MAJ6-e", 5.0, 1.0, style)
    return pen


def either_side_of_dips(pen: Brush, count: int) -> tuple[np.ndarray, np.ndarray]:
    """The spent share just before and just after each of the first `count` dips."""
    dips = pen.dip_px * np.arange(1, count + 1)
    return _nib_spent(dips - EPSILON, pen), _nib_spent(dips + EPSILON, pen)


class TestTheSpentShare:
    """`_nib_spent` itself: no step at any dip, whatever the reservoir."""

    def test_the_spent_share_is_continuous_at_the_dip(self) -> None:
        """On the repro nib the share spent just before the first dip is the share just after it."""
        before, after = either_side_of_dips(repro_pen(), 1)
        assert before[0] == pytest.approx(0.7534, abs=1e-4)
        assert after[0] == pytest.approx(0.7534, abs=1e-4)

    def test_a_small_reservoir_is_continuous_at_every_dip(self) -> None:
        """With a reservoir shorter than the refill, each dip carries more, and none steps."""
        before, after = either_side_of_dips(repro_pen(pen_reservoir=1.0), 4)
        np.testing.assert_allclose(before, after, atol=1e-5)
        np.testing.assert_allclose(after, [0.7534, 0.8457, 0.8570, 0.8583], atol=1e-4)

    def test_a_small_reservoir_never_spends_the_whole_load(self) -> None:
        """The carried share approaches a limit below 1, so the line never reaches no width."""
        pen = repro_pen(pen_reservoir=0.5)
        spent = _nib_spent(np.linspace(0.0, 40 * pen.dip_px, 4001), pen)
        assert float(spent.min()) == 0.0
        assert float(spent.max()) == pytest.approx(0.9119, abs=1e-4)

    def test_before_the_first_dip_nothing_is_carried(self) -> None:
        """A stroke shorter than one dip spends as a single load, `1 - exp(-run / run_px)`."""
        pen = repro_pen()
        run = np.array([0.0, 50.0, 110.0])
        np.testing.assert_allclose(_nib_spent(run, pen), [0.0, 0.3653, 0.6321], atol=1e-4)

    def test_the_refill_eases_over_two_nib_widths(self) -> None:
        """Two nib widths past a dip, the carried share has fallen by `e` on top of the fresh run."""
        pen = repro_pen()
        spent = _nib_spent(np.array([pen.dip_px + 2.0 * pen.width]), pen)
        assert float(spent[0]) == pytest.approx(0.3400, abs=1e-4)


def dry_run(pen_starve: bool = True) -> tuple[np.ndarray, Brush]:
    """The ink across a 660 px line drawn with a nib that runs dry fast, column by column.

    The issue's repro: a 5 px `MAJ6-e` nib with a 22-width reservoir, thinning to nothing
    when empty and dipped every 1.4 reservoirs, so the line passes three reloads. With
    `pen_starve` off the same nib never runs down. Smoothed over three columns, and cut to
    the stroke's middle, clear of its set-down and lift.
    """
    pen = repro_pen(pen_starve=pen_starve)
    h, length = 40, 700
    pts = np.stack([np.linspace(20.0, length - 20.0, 500), np.full(500, h / 2)], axis=1)
    acc = np.zeros((h, length), np.float32)
    stamp(acc, pts, pen, np.random.default_rng(3))
    ink = ink_density(acc, pen, Sheet(h, length, gran_px=6.0, seed=1)).sum(axis=0)
    return np.convolve(ink, np.ones(3) / 3, mode="same")[40:640], pen


class TestTheReload:
    """A nib that runs dry swells back at each dip, neither stepping up nor dropping out."""

    def test_a_reloaded_nib_swells_back_rather_than_stepping(self) -> None:
        """At a reload the line regains under 60% of what its run lost within one nib width."""
        along, pen = dry_run()
        width = round(pen.width)
        rise = float((along[width:] - along[:-width]).max())
        lost = float(along.max() - along.min())
        assert lost > 2.0  # the run does thin the line
        assert rise < 0.6 * lost

    def test_a_reload_never_drops_the_line(self) -> None:
        """No nib width loses a quarter of what a run loses, and the line keeps 40% of its peak."""
        along, pen = dry_run()
        width = round(pen.width)
        fall = float((along[:-width] - along[width:]).max())
        lost = float(along.max() - along.min())
        assert fall < lost / 4
        assert float(along.min()) > 0.4 * float(along.max())

    def test_a_nib_that_runs_dry_is_never_wider_than_a_full_one(self) -> None:
        """Running down only ever takes ink away: the dry nib's line is nowhere darker than the full nib's."""
        dry, _ = dry_run()
        full, _ = dry_run(pen_starve=False)
        assert np.all(dry <= full + 0.05)
        assert float(dry.sum()) < 0.8 * float(full.sum())
