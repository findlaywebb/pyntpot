"""A cover class's pigment: a colour that carries its own transparency.

Key types: `CoverPigment`, the colour a cover class paints and what it shows over black as a
share of what it shows over white; `built_in_transparency`, the transparency of a cover class's
built-in pigment; `default_pigments`, the default `CoverStyle.pigments`; `coerce_cover_pigment`,
which turns a Python-built entry into a `CoverPigment`.

`CoverPigment` is a `NamedTuple`, and so one leaf: the theme checker reads a tuple as a leaf, a
merge replaces it whole and `dataclasses.asdict` keeps it, so a child theme's entry for a class
replaces its parent's and never inherits half of it. A transparency of `None` means "take
`PaperStyle.km_transparency`"; only Python builds one, because every cover class has a built-in
transparency that a theme's entry falls back to. It carries a plain-function pydantic hook, as
`Colour` does, so `Style.model_validate` accepts a `CoverPigment`, a `{pigment, transparency}`
mapping or a `str`.

It resolves no pigment name, reads no theme and imports no style module. It does not check that a
transparency lies in 0 to 1: the theme checker does, at the key that wrote it.

Invariants: `colour` is always a `Colour` after `coerce_cover_pigment`; a `CoverPigment` written
out for a reader or the loader is a ref string or the mapping `as_table` returns, never a list.
"""

from collections.abc import Callable, Mapping
from typing import Any, NamedTuple

from pyntpot.ink.colour import Colour
from pyntpot.ink.pigment_table import ROLE_PIGMENTS

#: The keys of the written mapping form.
_KEYS = frozenset({"pigment", "transparency"})


class CoverPigment(NamedTuple):
    """The colour a cover class paints and its transparency.

    Attributes:
        colour: What a full-strength wash of the pigment transmits.
        transparency: What the pigment shows over black as a share of what it shows over
            white, or `None` to take `PaperStyle.km_transparency`.
    """

    colour: Colour
    transparency: float | None

    def as_table(self) -> dict[str, str | float]:
        """The one written form of a `CoverPigment` for a reader or the loader.

        Returns:
            `{pigment: "#rrggbb", transparency: t}`, with `transparency` left out when `None`.
        """
        table: dict[str, str | float] = {"pigment": str(self.colour)}
        if self.transparency is not None:
            table["transparency"] = self.transparency
        return table

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: object, handler: Callable[[Any], object]
    ) -> dict[str, object]:
        """The pydantic core schema: `_parse` as a plain validator, as data.

        Args:
            source: The annotated type; unused.
            handler: Pydantic's schema generator; unused.

        Returns:
            A `function-plain` core schema, so no `arbitrary_types_allowed` is needed.
        """
        return {"type": "function-plain", "function": {"type": "no-info", "function": _parse}}


def built_in_transparency(cover_class: str) -> float | None:
    """The transparency of `cover_class`'s built-in pigment, or `None` outside the 15 classes."""
    for pigment in ROLE_PIGMENTS:
        if pigment.name == cover_class:
            return pigment.transparency
    return None


def default_pigments() -> dict[str, CoverPigment]:
    """A fresh `CoverStyle.pigments` default: each role pigment, in registry order."""
    return {p.name: CoverPigment(p.colour, p.transparency) for p in ROLE_PIGMENTS}


def coerce_cover_pigment(cover_class: str, value: object) -> CoverPigment:
    """The `CoverPigment` a Python-built entry for `cover_class` stands for.

    Args:
        cover_class: The entry's key.
        value: A `CoverPigment` (its transparency kept), a `{pigment, transparency}` mapping,
            or a `str` or `Colour` (the class's built-in transparency).

    Returns:
        The entry with its colour through `Colour.parse`.

    Raises:
        ValueError: When `value` is anything else, a list included, or its colour is no hex.
    """
    if isinstance(value, CoverPigment):
        return CoverPigment(Colour.parse(value.colour), value.transparency)
    if isinstance(value, str):
        return CoverPigment(Colour.parse(value), built_in_transparency(cover_class))
    if isinstance(value, Mapping):
        return _from_table(value)
    raise ValueError(f"{value!r} is not a colour or a table of pigment and transparency")


def _parse(value: object) -> object:
    """The hook behind the pydantic schema: a table or a `CoverPigment` built, a `str` passed on."""
    if isinstance(value, CoverPigment | str):
        return value
    if isinstance(value, Mapping):
        return _from_table(value)
    raise ValueError(f"{value!r} is not a colour or a table of pigment and transparency")


def _from_table(table: Mapping[str, object]) -> CoverPigment:
    """A `CoverPigment` from `{pigment, transparency}`; the transparency may be left out."""
    unknown = set(table) - _KEYS
    if unknown or "pigment" not in table:
        raise ValueError(f"{dict(table)!r} is not a table of pigment and transparency")
    ref, transparency = table["pigment"], table.get("transparency")
    if not isinstance(ref, str):
        raise ValueError(f"{ref!r} is not a string")  # noqa: TRY004
    if transparency is not None and (
        isinstance(transparency, bool) or not isinstance(transparency, int | float)
    ):
        raise ValueError(f"{transparency!r} is not a number")
    return CoverPigment(Colour.parse(ref), None if transparency is None else float(transparency))
