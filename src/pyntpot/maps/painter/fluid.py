"""The fluid phase: one bounded shallow-water pass over everything the ribbon carries.

Key names: `paint_fluid`, which runs the pass once for the whole sheet, on a grid
`WashStyle.fluid_grid` times coarser than the plate, rather than once a class. The
water does not know where one wash stops and the next begins, so the drying runs
across a class boundary the way it does on paper. What comes back multiplies the
densities that are already there and replaces the stack's trimmed layers.

It draws from no shared generator. It does nothing when the style switches the pass off
or when nothing has been laid, and it does not touch the sea, which is never trimmed.
"""

import numpy as np

from pyntpot.ink.noise import F32
from pyntpot.ink.wash import fluid_modulate
from pyntpot.maps.painter.job import PaintJob, PlateStack


def paint_fluid(job: PaintJob, stack: PlateStack) -> None:
    """Run the fluid pass over the trimmed layers, over the ground that is wet."""
    style = job.style
    if not style.wash.fluid_pass or not stack.trimmed:
        return
    if style.cover.land_cover:
        wet_all = np.clip((stack.label != 0).astype(F32) + stack.lake_cov, 0.0, 1.0)
    else:
        wet_all = np.clip(1.0 - stack.sea_cov, 0.0, 1.0)
    stack.trimmed = fluid_modulate(stack.trimmed, wet_all, job.sheet, style.wash)
