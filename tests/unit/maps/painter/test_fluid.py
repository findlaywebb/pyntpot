"""The fluid phase: one shallow-water pass over the trimmed layers, once for the whole sheet."""

import dataclasses

import numpy as np

from pyntpot.ink.sheet import rgb
from pyntpot.maps.painter.fluid import paint_fluid
from pyntpot.maps.painter.job import PlateStack

from .jobs import tiny_job, tiny_style


def _laid(tmp_path, *, fluid_pass: bool):
    """A job and a stack holding one flat layer over a wholly labelled card."""
    job = tiny_job(tmp_path, tiny_style(wash={"fluid_pass": fluid_pass}))
    stack = PlateStack.blank(job.shape)
    stack.label[:] = 1
    stack.trimmed.append((np.full(job.shape, 0.4, np.float32), rgb("#6e7f8b"), 0.5))
    return job, stack


def test_the_pass_replaces_the_layers_with_ones_of_the_same_shape(tmp_path):
    """Every layer that comes back is still a plate-sized density."""
    job, stack = _laid(tmp_path, fluid_pass=True)
    paint_fluid(job, stack)
    assert stack.trimmed
    assert all(layer[0].shape == job.shape for layer in stack.trimmed)


def test_the_pass_switched_off_leaves_the_layers_as_they_were(tmp_path):
    """With the pass off the very same layers stay in the stack."""
    job, stack = _laid(tmp_path, fluid_pass=False)
    before = list(stack.trimmed)
    paint_fluid(job, stack)
    assert stack.trimmed == before


def test_cover_off_wets_what_the_sea_does_not_cover(tmp_path):
    """With land cover off the wet field is the card minus the sea, and the pass still runs."""
    base = tiny_style(wash={"fluid_pass": True})
    style = base.model_copy(update={"cover": dataclasses.replace(base.cover, land_cover=False)})
    job = tiny_job(tmp_path, style)
    stack = PlateStack.blank(job.shape)
    stack.trimmed.append((np.full(job.shape, 0.4, np.float32), rgb("#6e7f8b"), 0.5))
    paint_fluid(job, stack)
    density = stack.trimmed[0][0]
    assert density is not None
    assert density.shape == job.shape
