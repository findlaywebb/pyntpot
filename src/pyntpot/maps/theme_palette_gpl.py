"""The GIMP palette (`.gpl`) format: rows read into aliases, aliases written back as rows.

Key names: `parse_gpl`, which reads a `.gpl` file's text into aliases, each the anonymous
`Pigment` of its row's colour, with every problem found; `write_gpl`, which writes names and
pigments as a `.gpl` text; `alias_of`, the normal form of a `.gpl` name.

A file is the `GIMP Palette` header, then `Name:`, an optional `Columns:` and `#` comments,
then `R G B name` rows, each channel 0 to 255. A name becomes an alias: lower case, each run of
other characters one `_`, stripped. A row with no name, a name whose normal form is no alias
(it starts with a digit, say), a second name with an alias already read and a name equal to a
built-in pigment are each a problem at the row's line, never a drop. A row whose channels are
not whole numbers from 0 to 255 is a problem too.

Does not carry transparency or Colour Index: a `.gpl` holds a name and an RGB colour, so an
import yields anonymous pigments and an export drops what the pigment knew beyond its colour.
Does not read files or check a theme.

Invariants: every problem names the file and the row's line; an alias read matches
`ALIAS_PATTERN`; `parse_gpl` never raises for any text.
"""

import re
from collections.abc import Mapping
from pathlib import Path

from pyntpot.ink.pigment_registry import PIGMENT_REGISTRY, pigment
from pyntpot.ink.pigment_table import Pigment
from pyntpot.maps.theme_errors import ThemeProblem
from pyntpot.maps.theme_vocab import ALIAS_PATTERN

#: The first line of a `.gpl` file.
HEADER = "GIMP Palette"

#: A run of characters that is no part of an alias.
_OTHER = re.compile(r"[^a-z0-9]+")

#: The highest channel value a row can hold.
_CHANNEL_MAX = 255

#: A row's channel count, before its name.
_CHANNELS = 3

#: A row's fields: three channels and a name that may hold spaces.
_FIELDS = _CHANNELS + 1

#: The metadata lines between the header and the rows.
_META = ("Name:", "Columns:")


def alias_of(name: str) -> str:
    """The alias a `.gpl` name reads as: lower case, each run of other characters one `_`."""
    return _OTHER.sub("_", name.lower()).strip("_")


def parse_gpl(path: Path, text: str) -> tuple[dict[str, Pigment], tuple[ThemeProblem, ...]]:
    """Read the `.gpl` file `path`, whose content is `text`, into aliases and its problems.

    Args:
        path: The file, as the caller names it; it is not opened.
        text: The file's content.

    Returns:
        Each alias read, in file order, mapped to the anonymous pigment of its row's colour,
        and every problem found, in line order.
    """
    found: list[ThemeProblem] = []

    def refuse(line: int, message: str) -> None:
        found.append(ThemeProblem(path=path, key="", line=line, message=message))

    lines = text.splitlines()
    if not lines or lines[0].strip() != HEADER:
        refuse(1, f"a .gpl file starts with the line '{HEADER}'")
        return {}, tuple(found)
    aliases: dict[str, Pigment] = {}
    first: dict[str, tuple[int, str]] = {}
    for number, raw in enumerate(lines[1:], start=2):
        row = raw.strip()
        if not row or row.startswith("#") or row.startswith(_META):
            continue
        parsed = _row(row)
        if isinstance(parsed, str):
            refuse(number, parsed)
            continue
        colour, name = parsed
        alias = alias_of(name)
        message = _refusal(name, alias, first)
        if message is not None:
            refuse(number, message)
            continue
        first[alias] = (number, name)
        aliases[alias] = pigment(colour)
    return aliases, tuple(found)


def write_gpl(name: str, pigments: Mapping[str, Pigment]) -> str:
    """The `.gpl` text of `pigments`, each written under its key.

    Args:
        name: The palette's name, for the `Name:` line.
        pigments: Each name and the pigment whose colour is written; transparency and
            Colour Index are dropped.

    Returns:
        The file's text, ending in a newline.
    """
    rows = [HEADER, f"Name: {name}", "Columns: 0", "#"]
    for key, one in pigments.items():
        r, g, b = one.colour.rgb8
        rows.append(f"{r:3d} {g:3d} {b:3d}\t{key}")
    return "\n".join(rows) + "\n"


def _row(row: str) -> tuple[str, str] | str:
    """The hex and name of the row `row`, or what is wrong with it."""
    parts = row.split(None, _CHANNELS)
    if len(parts) < _CHANNELS or not all(part.isascii() and part.isdecimal() for part in parts[:3]):
        return f"{row!r} is not a row of three channels and a name"
    r, g, b = (int(part) for part in parts[:3])
    if max(r, g, b) > _CHANNEL_MAX:
        return f"{row!r} has a channel above {_CHANNEL_MAX}"
    if len(parts) < _FIELDS:
        return f"{row!r} has no name"
    return f"#{r:02x}{g:02x}{b:02x}", parts[3].strip()


def _refusal(name: str, alias: str, first: Mapping[str, tuple[int, str]]) -> str | None:
    """What is wrong with the row named `name`, whose alias is `alias`, or `None`."""
    if re.fullmatch(ALIAS_PATTERN, alias) is None:
        return f"{name!r} reads as {alias!r}; an alias starts with a letter"
    if alias in first:
        line, earlier = first[alias]
        return f"{earlier!r} (line {line}) and {name!r} both read as {alias!r}"
    if alias in PIGMENT_REGISTRY:
        return f"{name!r} reads as {alias!r}, a built-in pigment; an alias needs a name of its own"
    return None
