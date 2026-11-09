"""Suggest the nearest known name for a name that missed.

Key function: `nearest`. Every "did you mean X?" in `ink` and `maps` is written from it, so
the cutoff and the count are chosen once.

It raises nothing and reads no table: the caller supplies the known names.

Invariants: at most one name is returned; none is returned when nothing is close.
"""

import difflib
from collections.abc import Iterable


def nearest(name: str, known: Iterable[str]) -> tuple[str, ...]:
    """The single known name closest to `name`, or nothing when none is close.

    Args:
        name: The name that missed.
        known: Every name that would have matched.

    Returns:
        A tuple of at most one name, by `difflib` with a cutoff of 0.6.
    """
    return tuple(difflib.get_close_matches(name, list(known), n=1, cutoff=0.6))
