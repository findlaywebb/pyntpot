"""The relief phase: a quiet shaded relief laid among the trimmed layers.

Key names: `paint_relief`, which lays the elevation patch's shading as one pigment layer
the ribbon trims, when the style turns relief on and the basemap carries a patch.

It draws from no shared generator, so a card with no patch, or with relief off, consumes
nothing. The shading itself is `paper.relief_density`; this phase only decides whether
it is laid, and in which pigment.
"""

from pyntpot.ink.sheet import rgb
from pyntpot.maps.painter.job import PaintJob, PlateStack
from pyntpot.maps.painter.paper import relief_density


def paint_relief(job: PaintJob, stack: PlateStack) -> None:
    """Lay the relief among the trimmed layers when relief is on and there is a patch."""
    cover = job.style.cover
    elevation = job.layers.elevation
    if not cover.relief or elevation is None:
        return
    stack.trimmed.append(
        (
            relief_density(elevation, job.canvas, job.sheet),
            rgb(cover.pigments["relief"]),
            job.transp("relief"),
        )
    )
