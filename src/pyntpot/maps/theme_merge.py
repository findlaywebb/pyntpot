"""Merging one theme table over another: an override names only what it changes.

Key name: `merge`, which lays an override table over a base table. Where both hold a
mapping at a key, the two merge key by key, at every depth: a group, a dict field's
entries, a `brush_overrides` entry and a dataclass-typed sub-table. Anywhere else the
override's value replaces the base's whole, so a tuple is never merged by position.

Does not check keys or values, read files or resolve `extends`, and has no syntax for
removing a key. Merge is associative only where each key path is a table in every input
or a leaf in every input; the checker refuses a leaf where the model has a table, and a
table where it has a leaf, before anything is merged.

Invariants: `merge` returns a new dict and never mutates either input; every key of the
base the override does not name is kept.
"""

from collections.abc import Mapping


def merge(base: Mapping[str, object], over: Mapping[str, object]) -> dict[str, object]:
    """Lay `over` on `base`: mappings at one key merge key by key, any other value replaces.

    Args:
        base: The table overridden.
        over: The table naming only what it changes.

    Returns:
        A new table: every key of `base`, each key of `over` merged or replacing.
    """
    merged = dict(base)
    for key, value in over.items():
        below = base.get(key)
        if isinstance(value, Mapping) and isinstance(below, Mapping):
            merged[key] = merge(below, value)
        else:
            merged[key] = value
    return merged
