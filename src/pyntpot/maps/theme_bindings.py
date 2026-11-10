"""What a theme's `cover.pigments` entry stands for: a `CoverPigment` built at load.

Key names: `resolve_cover_pigment`, the pydantic `BeforeValidator` behind a `CoverPigment` field;
`PIGMENT_REF`, the hint of a table's `pigment` key; `TRANSPARENCY_HINT`, the hint of its
`transparency` key.

An entry is a ref (a `#rrggbb`, a pigment name or an alias) or a table of `pigment` and
`transparency`. Every ref goes through `resolve_pigment`, which owns the lookup order and the text
of a miss; this module never reads a scope's aliases, palette or registry. One rule gives the
transparency of every form: the entry's own; else the resolved pigment's own (a derived pigment
that sets none already holds its base's); else the cover class's built-in pigment's, read from
the class key the checker puts in the validation context.

Does not check a table's keys or the range of its transparency (the checker does, key by key),
read a file or paint.

Invariants: the result is a `CoverPigment` whose colour is the resolved pigment's; a transparency
of `None` is built only for a class outside the 15 cover classes.
"""

from collections.abc import Mapping
from typing import Annotated, Any

import pydantic
from pydantic import BeforeValidator, Field

from pyntpot.ink.pigment_table import Pigment
from pyntpot.maps.cover_pigment import CoverPigment, built_in_transparency
from pyntpot.maps.theme_scope import ThemeScope, resolve_pigment

#: The message for a list, which an entry never is.
_LIST = "a list is not a pigment; write a colour reference or a table of pigment and transparency"


def _scope(info: pydantic.ValidationInfo) -> ThemeScope:
    """The scope the check carries, or the built-in one when there is no context."""
    if info.context is None:
        return ThemeScope.built_in()
    scope = info.context["scope"]
    assert isinstance(scope, ThemeScope)
    return scope


def _ref(value: object, info: pydantic.ValidationInfo) -> Pigment:
    """The pigment the ref `value` names in the scope; a `Pigment` comes back as itself.

    Raises:
        ValueError: When `value` is not a string, or `resolve_pigment` refuses it.
    """
    if isinstance(value, Pigment):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{value!r} is not a string")  # noqa: TRY004
    return resolve_pigment(value, _scope(info))


def resolve_cover_pigment(value: object, info: pydantic.ValidationInfo) -> CoverPigment:
    """The `CoverPigment` a theme's entry `value` stands for.

    Args:
        value: A ref string, or a table of `pigment` (a ref or a `Pigment`) and an optional
            `transparency`, which the checker has already checked.
        info: Pydantic's context; `info.context["scope"]` is the `ThemeScope` and
            `info.context["cover_class"]` the entry's class.

    Returns:
        The resolved colour with its transparency by the rule above.

    Raises:
        ValueError: When `value` is neither a ref nor such a table, or its ref names nothing.
    """
    if isinstance(value, tuple | list):
        raise ValueError(_LIST)  # noqa: TRY004
    if isinstance(value, str):
        pigment, own = _ref(value, info), None
    elif isinstance(value, Mapping) and "pigment" in value:
        pigment, own = _ref(value["pigment"], info), value.get("transparency")
    else:
        raise ValueError(
            f"{value!r} is not a colour reference or a table of pigment and transparency"
        )
    if own is None:
        own = pigment.transparency
    if own is None:
        own = built_in_transparency(
            "" if info.context is None else info.context.get("cover_class", "")
        )
    return CoverPigment(pigment.colour, own)


PIGMENT_REF = Annotated[Any, BeforeValidator(_ref)]
"""The hint of a table's `pigment` key: a ref resolved to its `Pigment`."""

TRANSPARENCY_HINT = Annotated[float, Field(strict=True, ge=0, le=1)]
"""The hint of a table's `transparency` key: a number from 0 to 1, never a `bool` or a `str`."""

#: The keys of a table form, with their hints.
TABLE_HINTS: Mapping[str, Any] = {"pigment": PIGMENT_REF, "transparency": TRANSPARENCY_HINT}
