"""Tests for joining runs through a junction: a crossing's bridge is part of the crossing."""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import pytest

from pyntpot.letters.junction import join_through
from pyntpot.letters.spurs import prune

Cell = tuple[int, int]


def _run(*corners: Cell) -> tuple[list[Cell], list[tuple[float, float]]]:
    """A chain through raster corners `(row, col)`, a pixel a step, and its run of points `(x, y)`."""
    cells: list[Cell] = [corners[0]]
    for (r0, c0), (r1, c1) in pairwise(corners):
        n = max(abs(r1 - r0), abs(c1 - c0))
        cells.extend(
            (round(r0 + (r1 - r0) * t / n), round(c0 + (c1 - c0) * t / n)) for t in range(1, n + 1)
        )
    return cells, [(float(c), float(r)) for r, c in cells]


#: The two forks of a crossing thinned at a shallow angle, six pixels apart.
LEFT, RIGHT = (20, 20), (20, 26)

#: The four arms of an `X` and the bridge between its forks.
ARMS = [
    _run(LEFT, (8, 8)),
    _run(LEFT, (32, 8)),
    _run(RIGHT, (8, 38)),
    _run(RIGHT, (32, 38)),
]
BRIDGE = _run(LEFT, RIGHT)

#: The two bowls of an `8`, each from one fork round to the other.
BOWLS = [
    _run(LEFT, (8, 8), (0, 23), (8, 38), RIGHT),
    _run(LEFT, (32, 8), (44, 23), (32, 38), RIGHT),
]


def _length(run: list[tuple[float, float]]) -> float:
    """A run's length in raster pixels."""
    return sum(math.dist(a, b) for a, b in pairwise(run))


class TestBridge:
    """Two forks a short run apart are one crossing; the run is dropped."""

    def test_an_x_is_two_strokes_through_its_crossing(self) -> None:
        """Four arms and a six pixel bridge, under a ten pixel stroke, come back as two diagonals."""
        runs = join_through([*ARMS, BRIDGE], 10.0)
        assert len(runs) == 2
        assert sorted(round(_length(r)) for r in runs) == [40, 40]

    def test_a_bridge_as_long_as_a_stroke_is_a_stroke(self) -> None:
        """With the stroke no wider than the bridge, the bridge stays and the arms are not joined."""
        assert len(join_through([*ARMS, BRIDGE], 6.0)) == 5

    def test_a_short_run_to_a_free_end_is_no_bridge(self) -> None:
        """A short run from a fork to a free end is a stroke, not a bridge, however short."""
        stub = _run(LEFT, (20, 14))
        runs = join_through([ARMS[0], ARMS[2], stub, BRIDGE], 10.0)
        assert len(runs) == 3
        assert any((14.0, 20.0) in (run[0], run[-1]) for run in runs)
        assert any((23.0, 20.0) in run for run in runs), "the bridge was dropped"

    def test_an_eight_is_one_ring_through_its_waist(self) -> None:
        """Two bowls between the forks and the bridge come back as one closed stroke."""
        (ring,) = join_through([*BOWLS, BRIDGE], 10.0)
        assert ring[0] == ring[-1]
        assert len(ring) == len(BOWLS[0][1]) + len(BOWLS[1][1])

    def test_a_loop_that_turns_square_at_its_junction_stays_open(self) -> None:
        """A run joined back to its own junction is closed only when its two ends meet straight on."""
        square = _run(LEFT, (20, 8), (8, 8), (8, 20), (19, 20))
        runs = join_through([square, ARMS[1], _run(LEFT, (32, 32))], 10.0)
        assert all(run[0] != run[-1] for run in runs)

    def test_a_run_with_one_end_at_the_junction_is_not_closed(self) -> None:
        """An X with one diagonal ending free is not closed into a ring, only joined through."""
        runs = join_through([*ARMS, BRIDGE], 10.0)
        assert all(run[0] != run[-1] for run in runs)


class TestPrune:
    """A short spur is dropped unless it ends a stroke of the outline or carries one on."""

    @staticmethod
    def _chains(spur_end: Cell) -> list[list[Cell]]:
        """A stroke through a junction at (10, 30) and a spur off it, square to the stroke."""
        return [
            _run((10, 10), (10, 30))[0],
            _run((10, 30), (10, 50))[0],
            _run((10, 30), spur_end)[0],
        ]

    @pytest.mark.parametrize(
        ("radius", "kept"),
        [(7.0, 3), (11.0, 3), (12.0, 2), (13.0, 2), (14.0, 2)],
        ids=["well-out", "just-out", "on-the-edge", "just-in", "well-in"],
    )
    def test_a_spur_is_kept_once_it_leaves_its_junctions_disc(
        self, radius: float, kept: int
    ) -> None:
        """A six pixel spur stays past half the junction's inscribed radius and goes inside it."""
        reach = np.zeros((64, 64), np.float32)
        reach[10, 30] = radius
        assert len(prune(self._chains((16, 30)), 10.0, reach)) == kept

    def test_a_spur_is_read_from_its_free_end(self) -> None:
        """A spur written from its free end to the junction is measured against the same junction."""
        reach = np.zeros((64, 64), np.float32)
        reach[10, 30] = 14.0
        chains = self._chains((16, 30))
        chains[2] = chains[2][::-1]
        assert len(prune(chains, 10.0, reach)) == 2
        reach[10, 30] = 11.0
        assert len(prune(chains, 10.0, reach)) == 3

    def test_a_spur_as_long_as_the_limit_is_no_spur(self) -> None:
        """A seven pixel spur inside its junction's disc stays when the limit is seven."""
        reach = np.zeros((64, 64), np.float32)
        reach[10, 30] = 14.0
        assert len(prune(self._chains((16, 30)), 7.0, reach)) == 3
        assert len(prune(self._chains((16, 30)), 8.0, reach)) == 2

    def test_pruning_a_spur_keeps_what_follows_it(self) -> None:
        """A spur listed first is dropped and the chains after it are all kept."""
        reach = np.zeros((64, 64), np.float32)
        reach[10, 30] = 14.0
        spur, *rest = self._chains((16, 30))[::-1]
        assert prune([spur, *rest], 10.0, reach) == rest

    @pytest.mark.parametrize("flip", [False, True], ids=["from-the-junction", "from-the-free-end"])
    def test_a_spur_carrying_a_stroke_on_stays_inside_the_disc(self, flip: bool) -> None:
        """A short spur running straight on from a branch at its junction stays; one turned half way off both goes."""
        reach = np.zeros((64, 64), np.float32)
        reach[10, 30] = 14.0
        stem = _run((10, 10), (10, 30))[0]
        branch = _run((30, 30), (10, 30))[0]
        spur = _run((10, 30), (10, 36))[0]
        chains = [stem[::-1] if flip else stem, branch, spur[::-1] if flip else spur]
        assert len(prune(chains, 10.0, reach)) == 3
        turned = _run((10, 30), (6, 26))[0]
        chains[-1] = turned[::-1] if flip else turned
        assert len(prune(chains, 10.0, reach)) == 2

    def test_a_glyph_of_two_chains_is_still_pruned(self) -> None:
        """With only a stroke and a spur off its end, the spur inside the disc is dropped."""
        reach = np.zeros((64, 64), np.float32)
        reach[10, 30] = 14.0
        stroke = _run((10, 10), (10, 30))[0]
        spur = _run((10, 30), (16, 30))[0]
        assert prune([stroke, spur], 10.0, reach) == [stroke]
