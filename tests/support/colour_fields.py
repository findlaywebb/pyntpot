"""The `Colour`-typed fields of a `Style`, found by their declared type.

Key function: `colour_paths`, every path of a style whose declared type is `Colour`, or a
`dict` of them, whose values stand as `*`.

It reads no value; it does not say which fields a fed route colour moves.
"""

import typing
from collections.abc import Iterator

from pyntpot.ink import Colour
from pyntpot.maps import Style


def colour_paths(style: Style) -> Iterator[tuple[str, ...]]:
    """Every path of `style` whose declared type is `Colour`, a dict field's values as `*`."""
    for group, info in type(style).model_fields.items():
        cls = info.annotation
        assert isinstance(cls, type)
        for name, hint in typing.get_type_hints(cls).items():
            if hint is Colour:
                yield (group, name)
            elif typing.get_origin(hint) is dict and typing.get_args(hint)[1] is Colour:
                yield (group, name, "*")
