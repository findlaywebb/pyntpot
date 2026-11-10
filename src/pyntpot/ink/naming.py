"""Suggest the nearest known name for a name that missed.

Key functions: `nearest`, and `did_you_mean`, the `; did you mean X?` suffix of a refusal.
Every "did you mean X?" in `ink` and `maps` is written from them, so the cutoff, the count and
the wording are chosen once.

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


def did_you_mean(name: str, known: Iterable[str]) -> str:
    """The suffix `; did you mean X?` naming the nearest of `known`, or `""` when none is close.

    Args:
        name: The name that missed.
        known: Every name that would have matched.

    Returns:
        The suffix to append to a refusal's message, empty when `nearest` finds nothing.
    """
    return "".join(f"; did you mean {near}?" for near in nearest(name, known))
