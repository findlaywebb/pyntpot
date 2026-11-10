"""Write a plain theme table as YAML text, for the loader's property tests."""

import io
from collections.abc import Mapping

from ruamel.yaml import YAML

from pyntpot.maps.cover_pigment import CoverPigment


def dump_theme(table: Mapping[str, object]) -> str:
    """`table`, plain dicts, tuples and scalars, as YAML text, each tuple written as a list.

    A `CoverPigment` is written as its mapping, not as a list: see `plain_table`.
    """
    yaml = YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    stream = io.StringIO()
    yaml.dump(plain_table(table), stream)
    return stream.getvalue()


def plain_table(value: object) -> object:
    """`value` with every mapping a dict, every tuple a list and every `str` subclass a plain `str`.

    A `CoverPigment` is the one tuple that is no list: it is `{pigment: "#rrggbb", transparency: t}`,
    with `transparency` left out when it is `None`, the one written form a theme loads back.
    """
    if isinstance(value, CoverPigment):
        return value.as_table()
    if isinstance(value, Mapping):
        return {str(key): plain_table(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [plain_table(item) for item in value]
    if isinstance(value, str):
        return str(value)
    return value
