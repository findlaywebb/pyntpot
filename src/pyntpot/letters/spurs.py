"""The short spurs thinning grows on a glyph's skeleton, and the ones that stay.

`prune` drops a short branch hanging off a junction unless it carries straight on
from another branch there (the top of an `n`) or leaves the junction's own ink to
end a stroke of the outline (the tail of a `D`). It works on the chains
`letters.skeleton.skeleton_chains` walks, in raster pixels as `(row, col)`, and
reads the ink's inscribed radius from the caller. It does not thin, trace or draw.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pyntpot.letters.skeleton import PASSING, THROUGH_DOT

if TYPE_CHECKING:
    import numpy as np

#: A spur whose free end lies further from its junction than this share of the
#: junction's inscribed radius has left the junction's own ink: it is a stroke
#: of the outline ending, a tail or a tongue, and not a fork thinning grew
#: inside the blob where strokes meet.
TERMINAL_OF_DISC = 0.5


def _leaves(chain: list[tuple[int, int]], node: tuple[int, int]) -> tuple[float, float]:
    """The unit direction a chain sets off in from one of its own ends."""
    run = chain if chain[0] == node else chain[::-1]
    (r0, c0), (r1, c1) = run[0], run[min(3, len(run) - 1)]
    d = math.hypot(r1 - r0, c1 - c0) or 1.0
    return ((r1 - r0) / d, (c1 - c0) / d)


def prune(
    chains: list[list[tuple[int, int]]], limit: float, reach: np.ndarray
) -> list[list[tuple[int, int]]]:
    """Drop the short branches thinning grows at joins and at terminals.

    Two kinds of short branch are not those, and stay. One that carries
    straight on from another branch at its junction is the end of a stem that
    runs on past where something joins it, the top of an `n` or the foot of a
    `d`. One whose free end has left its junction's ink, further from it than
    `TERMINAL_OF_DISC` of the junction's inscribed radius, is a stroke of the
    outline ending: the tail of a `D` or a `Q`, the tongue of a `3`. A fork
    thinning grows stays inside the disc of the junction it grew from.

    Args:
        chains: The skeleton's chains, as `skeleton_chains` walks them.
        limit: A branch of fewer pixels than this may be a spur.
        reach: How far each inked pixel is from the nearest blank one: the
            inscribed radius of the ink there, on the same grid.

    Returns:
        The chains kept, or all of them when pruning would leave none.
    """
    ends: dict[tuple[int, int], int] = {}
    for chain in chains:
        for p in (chain[0], chain[-1]):
            ends[p] = ends.get(p, 0) + 1
    keep = []
    for chain in chains:
        spur = ends.get(chain[0], 0) == 1 or ends.get(chain[-1], 0) == 1
        if (
            spur
            and len(chain) < limit
            and len(chains) > 1
            and not _carries_on(chain, chains, ends)
            and not _terminal(chain, ends, reach)
        ):
            continue
        keep.append(chain)
    return keep or chains


def _carries_on(
    chain: list[tuple[int, int]],
    chains: list[list[tuple[int, int]]],
    ends: dict[tuple[int, int], int],
) -> bool:
    """Whether a spur runs straight on from another branch at its junction."""
    node = chain[-1] if ends.get(chain[0], 0) == 1 else chain[0]
    if ends.get(node, 0) < PASSING + 1:
        return False
    mine = _leaves(chain, node)
    for other in chains:
        if other is chain or node not in (other[0], other[-1]):
            continue
        theirs = _leaves(other, node)
        if mine[0] * theirs[0] + mine[1] * theirs[1] <= THROUGH_DOT:
            return True
    return False


def _terminal(
    chain: list[tuple[int, int]], ends: dict[tuple[int, int], int], reach: np.ndarray
) -> bool:
    """Whether a spur's free end has left its junction's disc, so it ends a stroke."""
    free, node = (chain[0], chain[-1]) if ends.get(chain[0], 0) == 1 else (chain[-1], chain[0])
    return math.dist(free, node) > TERMINAL_OF_DISC * float(reach[node])
