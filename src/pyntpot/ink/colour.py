"""One colour value and the one place a hex becomes channels.

Key types: `Colour`, a lower-case `#rrggbb` that is also a plain `str`, with `.rgb` (float32,
0 to 1) and `.rgb8` (three bytes) and `Colour.parse` to accept any case. `channels` is the
shared arithmetic: `rgb` in `sheet.py` calls it, so hex is parsed in this module only.
`normalise_colours` is the one coercion every colour-holding group calls from its
`__post_init__`, so a plain `str` that reaches a colour field becomes a `Colour`.

It reads no style and no file, and takes no short `#abc` form or CSS name.

Invariants: a `Colour` always holds exactly `#` and six lower-case hexadecimal digits; it
hashes, compares, copies, pickles and serialises as the string it is. Its pydantic schema is a
plain function validator over `Colour.parse`, declared as data, so this module imports no
`pydantic`.
"""

import re
from collections.abc import Callable
from typing import Any

import numpy as np

from pyntpot.ink.noise import F32

_HEX = re.compile(r"#[0-9a-f]{6}")


def channels(hex_s: str) -> np.ndarray:
    """One hex colour as three float32 values in 0 to 1: a float64 division, then float32.

    Reads the first three digit pairs after any leading `#`; characters after the sixth digit
    are not read.

    Args:
        hex_s: A `#rrggbb` string; the `#` is optional.

    Returns:
        A float32 array of red, green and blue.

    Raises:
        ValueError: When one of the first three pairs is empty or not hexadecimal.
    """
    h = hex_s.lstrip("#")
    return np.array([int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)], F32)


class Colour(str):
    """A `#rrggbb` colour, lower-case, that is also a plain string.

    It is a `str` so that equality, `json.dumps` and `dataclasses.asdict` treat it as the
    string it is, and a hex colour hashes as itself.
    """

    __slots__ = ()

    def __new__(cls, text: str) -> "Colour":
        """Hold `text`, which must be a lower-case `#` and six hexadecimal digits.

        Raises:
            ValueError: When `text` is anything else; `Colour.parse` accepts upper case.
        """
        if not _HEX.fullmatch(text):
            raise ValueError(f"{text!r} is not a # and six hexadecimal digits")
        return super().__new__(cls, text)

    @classmethod
    def parse(cls, text: str) -> "Colour":
        """A `Colour` from `text` in either case; a `Colour` comes back as itself.

        Args:
            text: A `#rrggbb` string, in either case.

        Returns:
            The lower-case colour.

        Raises:
            ValueError: When `text` is not a string, or is not a `#` and six hexadecimal
                digits.
        """
        if not isinstance(text, str):
            raise ValueError(f"{text!r} is not a string")  # noqa: TRY004
        if isinstance(text, cls):
            return text
        return cls(text.lower())

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: object, handler: Callable[[Any], object]
    ) -> dict[str, object]:
        """The pydantic core schema: `Colour.parse` as a plain validator, as data.

        Args:
            source: The annotated type; unused.
            handler: Pydantic's schema generator; unused.

        Returns:
            A `function-plain` core schema, so no `arbitrary_types_allowed` is needed.
        """
        return {"type": "function-plain", "function": {"type": "no-info", "function": cls.parse}}

    @property
    def rgb(self) -> np.ndarray:
        """The colour as three float32 values in 0 to 1, as `rgb` returns them."""
        return channels(self)

    @property
    def rgb8(self) -> tuple[int, int, int]:
        """The colour as its three bytes, each 0 to 255."""
        h = self[1:]
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def normalise_colours(group: object, *names: str) -> None:
    """Set each named field of the frozen `group` through `Colour.parse`.

    A dict field is rebuilt with its values parsed. A `Colour` comes back as itself, so a
    group built from colours changes nothing.

    Args:
        group: A dataclass instance; each field is set with `object.__setattr__`.
        *names: The colour fields, each a `str` or a `dict` of `str` values.

    Raises:
        ValueError: When a value is not a string or not a `#` and six hexadecimal digits.
    """
    for name in names:
        value = getattr(group, name)
        if isinstance(value, dict):
            parsed: object = {key: Colour.parse(item) for key, item in value.items()}
        else:
            parsed = Colour.parse(value)
        object.__setattr__(group, name, parsed)
