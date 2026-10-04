"""The candidate value: a frozen record compared by value."""

import dataclasses

import pytest

from pyntpot.maps.candidates.candidate import Candidate


def _lynmouth() -> Candidate:
    """A place candidate, built from literals."""
    return Candidate("place", "Lynmouth", 1, 79.9, (1599.8, 1738.4), (4, 4), {"km": 0.08})


def test_a_candidate_cannot_be_changed() -> None:
    """Assigning to a field of a candidate raises."""
    field = "rank"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(_lynmouth(), field, 2)


def test_candidates_compare_by_value() -> None:
    """Two candidates built from the same fields are equal, and a changed field breaks it."""
    assert _lynmouth() == _lynmouth()
    assert _lynmouth() != dataclasses.replace(_lynmouth(), rank=2)
