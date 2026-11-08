"""The theme vocabularies: each dict field's keys, the brush-id fields and the colour fields."""

import dataclasses
import re
import typing

import pytest

from pyntpot.ink.brush import BRUSH_OVERRIDE_KEYS
from pyntpot.ink.brush_sheet import BRUSH_COLOURS
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.maps import Style
from pyntpot.maps.style_groups import CoverStyle
from pyntpot.maps.theme_vocab import BRUSH_ID_FIELDS, COLOUR_FIELDS, VOCABULARIES

from support.planted_groups import Cloud

HEX = re.compile(r"#[0-9a-f]{6}")


def _string_paths(style: Style) -> dict[tuple[str, ...], list[str]]:
    """Every string-valued path of `style`: a `str` field, or a dict field of strings as `*`."""
    paths: dict[tuple[str, ...], list[str]] = {}
    for group in type(style).model_fields:
        for item in dataclasses.fields(getattr(style, group)):
            value = getattr(getattr(style, group), item.name)
            if isinstance(value, str):
                paths[(group, item.name)] = [value]
            elif isinstance(value, dict) and all(isinstance(v, str) for v in value.values()):
                paths[(group, item.name, "*")] = list(value.values())
    return paths


def _has_vocabulary(path: tuple[str, ...]) -> bool:
    """Whether some `VOCABULARIES` key path is `path`, a `*` standing for any one key."""
    return any(
        len(path) == len(pattern)
        and all(want in ("*", have) for have, want in zip(path, pattern, strict=True))
        for pattern in VOCABULARIES
    )


def _unvocabularied(name: str, group: type) -> list[tuple[str, ...]]:
    """Key paths of dict fields under `group` with no vocabulary, recursing as `theme_check` does."""
    missing: list[tuple[str, ...]] = []

    def walk(hint: object, path: tuple[str, ...]) -> None:
        if isinstance(hint, type) and dataclasses.is_dataclass(hint):
            for key, item in typing.get_type_hints(hint).items():
                if key in {f.name for f in dataclasses.fields(hint)}:
                    walk(item, (*path, key))
        elif typing.get_origin(hint) is dict:
            if not _has_vocabulary(path):
                missing.append(path)
            walk(typing.get_args(hint)[1], (*path, "*"))

    walk(group, (name,))
    return missing


def test_the_colour_fields_are_what_the_model_implies():
    """`COLOUR_FIELDS` is exactly the paths whose default values are all `#rrggbb`, each once."""
    implied = {
        path
        for path, values in _string_paths(Style()).items()
        if values and all(HEX.fullmatch(value) for value in values)
    }
    assert set(COLOUR_FIELDS) == implied
    assert len(COLOUR_FIELDS) == len(set(COLOUR_FIELDS))


def test_the_brush_id_fields_are_the_four_the_brushes_are_read_from():
    """`BRUSH_ID_FIELDS` names the brush map's values and the three single brush ids."""
    assert BRUSH_ID_FIELDS == (
        ("brush", "brushes", "*"),
        ("route", "route_pen_brush"),
        ("nib", "label_brush"),
        ("nib", "label_leader_brush"),
    )


def test_every_dict_field_has_a_vocabulary():
    """Each dict-valued field has a vocabulary, and so do the brush override entries; nothing else."""
    style = Style()
    dict_fields = {
        (group, item.name)
        for group in type(style).model_fields
        for item in dataclasses.fields(getattr(style, group))
        if isinstance(getattr(getattr(style, group), item.name), dict)
    }
    assert set(VOCABULARIES) == dict_fields | {("brush", "brush_overrides", "*")}


def test_the_walk_finds_a_dict_field_with_no_vocabulary():
    """The guard's walk reports a dict field inside a sub-table that `VOCABULARIES` lacks."""
    assert _unvocabularied("cloud", Cloud) == [("cloud", "fog", "density")]


def test_every_real_dict_field_path_has_a_vocabulary():
    """Walking every real style group as the checker does, no dict field lacks a vocabulary."""
    missing = [
        path
        for group, info in Style.model_fields.items()
        for path in _unvocabularied(group, typing.cast("type", info.annotation))
    ]
    assert missing == []


PIGMENTS = frozenset(CoverStyle().pigments)
BRUSH = BrushStyle()


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (("paper", "pigment_transparency"), PIGMENTS),
        (("wash", "separation_pigments"), PIGMENTS),
        (("cover", "pigments"), PIGMENTS),
        (("cover", "cover_cfg"), frozenset(CoverStyle().cover_cfg)),
        (("brush", "river_curve"), frozenset(BRUSH.river_curve)),
        (("brush", "brushes"), frozenset(BRUSH.brushes)),
        (("brush", "brush_width_px"), frozenset(BRUSH.brush_width_px)),
        (
            ("brush", "brush_overrides"),
            frozenset(BRUSH.brushes) | {cls.lower() for cls in BRUSH_COLOURS} | {"route", "label"},
        ),
        (("brush", "brush_overrides", "*"), BRUSH_OVERRIDE_KEYS),
    ],
    ids=[
        "pigment-transparency",
        "separation-pigments",
        "pigments",
        "cover-cfg",
        "river-curve",
        "brushes",
        "brush-width",
        "override-names",
        "override-keys",
    ],
)
def test_each_vocabulary_is_its_default_s_keys(path: tuple[str, ...], expected: frozenset[str]):
    """Each dict field's vocabulary is the keys its readers use, from the defaults."""
    assert VOCABULARIES[path] == expected
