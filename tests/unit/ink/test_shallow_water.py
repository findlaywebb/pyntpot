"""Tests for the shallow-water pass: it counts rather than converges, and it dries at the edge."""

import numpy as np

from pyntpot.ink.noise import chamfer_distance
from pyntpot.ink.shallow_water import shallow_water
from pyntpot.ink.style import WashStyle

from support.washes import fluid_fields


def fluid(steps: int) -> WashStyle:
    """The wash group with the water run for this many steps."""
    return WashStyle(fluid_steps=steps, fluid_relax=4, fluid_seed=41, fluid_gran=0.6)


def test_the_fluid_pass_is_deterministic_because_it_counts_rather_than_converges():
    """A tolerance would make the iteration count depend on the arithmetic."""
    wet, pig, paper = fluid_fields()
    a = shallow_water(wet, pig, paper, fluid(20))
    b = shallow_water(wet, pig, paper, fluid(20))
    assert np.array_equal(a, b)
    assert np.isfinite(a).all(), "the relaxation has to stay bounded"
    assert not np.array_equal(a, shallow_water(wet, pig, paper, fluid(30)))


def test_the_water_carries_pigment_out_to_the_edge_it_dries_at():
    """FlowOutward is what puts the deposit at the contact line, not the middle."""
    wet, _, paper = fluid_fields()
    # A flat pigment field, so what shows is the water's own doing and not the
    # noise it was handed.
    dep = shallow_water(wet, np.ones_like(wet), paper, fluid(40))
    inside = wet > 0.5
    d = chamfer_distance(~inside)
    near = inside & (d <= 3)
    deep = inside & (d > 14)
    assert dep[near].mean() > dep[deep].mean() * 1.1
    # And it varies around the shape rather than being one ring: that is the
    # thing a rim of a fixed width cannot do.
    band = dep[12:84, 16:19].mean(axis=1)
    assert band.std() / max(band.mean(), 1e-6) > 0.15
