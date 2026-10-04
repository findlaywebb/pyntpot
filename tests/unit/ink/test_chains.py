"""Tests for the chain joiners: which pieces join, and how each treats its tolerance."""

import numpy as np
import pytest

from pyntpot.ink.chains import chain_lines, join_chains, join_strokes, joined

#: Two segments that touch end to start.
LEFT = [(0.0, 0.0), (10.0, 0.0)]
RIGHT = [(10.0, 0.0), (20.0, 0.0)]
#: A segment whose start sits 0.9 across and 0.9 up from `LEFT`'s end: about
#: 1.27 away, so beyond a tolerance of 1 by distance but within it on each axis.
DIAGONAL = [(10.9, 0.9), (20.0, 5.0)]
#: A segment far beyond any tolerance used here.
APART = [(30.0, 0.0), (40.0, 0.0)]
#: Two candidates for `LEFT`'s end at (10, 0), both within a tolerance of 1:
#: `AHEAD` starts 0.6 to its right, in the grid cell `LEFT` ends in, and `ASIDE`
#: starts 0.5 to its left, in the cell before it.
AHEAD = [(10.6, 0.0), (20.0, 0.0)]
ASIDE = [(9.5, 0.0), (9.5, 10.0)]


def _chain_arrays(lines: list[list[tuple[float, float]]], tol: float) -> list[list[list[float]]]:
    """Run `chain_lines` on point lists and return plain nested lists."""
    return [c.tolist() for c in chain_lines([np.asarray(line) for line in lines], tol)]


@pytest.mark.parametrize(
    "join",
    [join_strokes, join_chains],
    ids=["join_strokes", "join_chains"],
)
class TestPointListJoiners:
    """The two open-line joiners on point lists."""

    def test_two_touching_segments_join_into_one(self, join) -> None:
        """Segments that share an end become one line without repeating it."""
        assert join([LEFT, RIGHT], 1.0) == [[(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)]]

    def test_segments_beyond_the_tolerance_stay_apart(self, join) -> None:
        """Segments whose ends are farther apart than the tolerance stay two."""
        assert len(join([LEFT, APART], 1.0)) == 2


class TestJoinChains:
    """The greedy pool joiner that rings and traced contours both go through."""

    def test_two_halves_close_into_one_ring(self) -> None:
        """Two member ways that meet at both ends chain into one closed ring."""
        lower = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
        upper = [(10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
        assert join_chains([lower, upper], 1.0) == [
            [(10.0, 10.0), (0.0, 10.0), (0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
        ]

    def test_the_input_lines_are_left_unchanged(self) -> None:
        """Joining copies its pieces, so the caller's lines keep their points."""
        lower = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
        upper = [(10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
        join_chains([lower, upper], 1.0)
        assert (lower, upper) == (
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)],
            [(10.0, 10.0), (0.0, 10.0), (0.0, 0.0)],
        )

    def test_a_short_chain_is_kept(self) -> None:
        """A chain of three points or fewer comes back; dropping it is the caller's choice."""
        assert join_chains([LEFT], 1.0) == [LEFT]


def test_join_chains_and_join_strokes_take_different_pieces_at_a_junction() -> None:
    """At a junction `join_chains` takes the first piece in pool order, `join_strokes` the first by grid cell."""
    assert join_chains([AHEAD, ASIDE, LEFT], 1.0) == [
        [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)],
        ASIDE,
    ]
    assert join_strokes([AHEAD, ASIDE, LEFT], 1.0) == [
        [(0.0, 0.0), (10.0, 0.0), (9.5, 10.0)],
        AHEAD,
    ]


class TestToleranceHandling:
    """Where `join_strokes` and `chain_lines` differ on the same pinned input."""

    def test_join_strokes_measures_the_gap_as_a_distance(self) -> None:
        """An end 1.27 away stays apart under a tolerance of 1 measured by distance."""
        assert join_strokes([LEFT, DIAGONAL], 1.0) == [DIAGONAL, LEFT]

    def test_chain_lines_measures_the_gap_on_each_axis(self) -> None:
        """An end 0.9 off on each axis joins under a tolerance of 1 per axis."""
        assert _chain_arrays([LEFT, DIAGONAL], 1.0) == [
            [[0.0, 0.0], [10.0, 0.0], [10.9, 0.9], [20.0, 5.0]]
        ]

    def test_chain_lines_keeps_the_shared_point_twice(self) -> None:
        """Joined arrays are concatenated whole, so a shared end appears twice."""
        assert _chain_arrays([LEFT, RIGHT], 1.0) == [
            [[0.0, 0.0], [10.0, 0.0], [10.0, 0.0], [20.0, 0.0]]
        ]

    def test_chain_lines_joins_nothing_at_zero_tolerance(self) -> None:
        """A tolerance of zero hands the lines back unjoined."""
        assert len(_chain_arrays([LEFT, RIGHT], 0.0)) == 2


@pytest.mark.parametrize(
    ("parts", "expected"),
    [
        ([LEFT, RIGHT], [[(0.0, 0.0), (10.0, 0.0), (10.0, 0.0), (20.0, 0.0)]]),
        ([LEFT, APART], [LEFT, APART]),
    ],
    ids=["touching", "apart"],
)
def test_joined_chains_point_lists_like_chain_lines(parts, expected) -> None:
    """`joined` gives `chain_lines`' chains back as point lists."""
    assert joined(parts, 8.0) == expected
