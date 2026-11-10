"""Write a plain theme table as YAML text, for the loader's property tests."""

import io
from collections.abc import Mapping

from ruamel.yaml import YAML


def dump_theme(table: Mapping[str, object]) -> str:
    """`table`, plain dicts, tuples and scalars, as YAML text, each tuple written as a list."""
    yaml = YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    stream = io.StringIO()
    yaml.dump(_plain(table), stream)
    return stream.getvalue()


def _plain(value: object) -> object:
    """`value` with every mapping a dict, every tuple a list and every `str` subclass a plain `str`."""
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_plain(item) for item in value]
    if isinstance(value, str):
        return str(value)
    return value
