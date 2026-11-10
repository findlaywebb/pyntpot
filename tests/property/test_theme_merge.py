"""Properties of `merge`, and of a theme against its expanded copy.

The merge properties draw one shape first, each key path a table or a leaf, and then
every input as a partial filling of it: the model fixes that shape, and the checker
refuses a leaf where a table belongs before anything is merged, so a merge never sees a
table and a leaf at one path. The digest property writes an override and its expanded
copy as theme files and loads both.
"""

import copy
import dataclasses
import tempfile
from collections.abc import Mapping
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from pyntpot.ink.colour import Colour
from pyntpot.maps.style import Style
from pyntpot.maps.theme_merge import merge
from pyntpot.maps.theme_vocab import LOADER_FIELDS

from support.properties import UNTIMED
from support.theme_dump import dump_theme

LEAF = None  # marks a leaf in a shape
_KEYS = st.sampled_from(("a", "b", "c", "d"))
_LEAVES = st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.text(max_size=3),
    st.tuples(st.integers(), st.integers()),
)
shapes = st.dictionaries(
    _KEYS,
    st.recursive(
        st.just(LEAF),
        lambda inner: st.dictionaries(_KEYS, inner, min_size=1, max_size=3),
        max_leaves=8,
    ),
    min_size=1,
    max_size=3,
)


@st.composite
def filling(draw: st.DrawFn, shape: Mapping[str, object]) -> dict[str, object]:
    """Draw a table that names some of `shape`'s keys, a leaf where it has a leaf and a table where it has a table."""
    table: dict[str, object] = {}
    for key, inner in shape.items():
        if not draw(st.booleans()):
            continue
        if inner is LEAF:
            table[key] = draw(_LEAVES)
        elif isinstance(inner, Mapping):
            table[key] = draw(filling(inner))
    return table


def _three(data: st.DataObject) -> tuple[dict[str, object], ...]:
    """Draw one shape, then three fillings of it."""
    shape = data.draw(shapes)
    return tuple(data.draw(filling(shape)) for _ in range(3))


class TestMerge:
    """Merge over inputs of one shape."""

    @given(st.data())
    @UNTIMED
    def test_merge_is_associative(self, data: st.DataObject) -> None:
        """Merging `a` with `b` then `c` equals merging `a` with `b` merged with `c`."""
        a, b, c = _three(data)
        assert merge(merge(a, b), c) == merge(a, merge(b, c))

    @given(st.data())
    @UNTIMED
    def test_an_empty_override_gives_the_base(self, data: st.DataObject) -> None:
        """An override naming nothing gives the base back."""
        a, _, _ = _three(data)
        assert merge(a, {}) == a

    @given(st.data())
    @UNTIMED
    def test_an_override_of_nothing_is_the_override(self, data: st.DataObject) -> None:
        """An override of an empty base is the override itself."""
        a, _, _ = _three(data)
        assert merge({}, a) == a

    @given(st.data())
    @UNTIMED
    def test_merge_never_mutates_its_inputs(self, data: st.DataObject) -> None:
        """The base and the override are unchanged by a merge."""
        a, b, _ = _three(data)
        before = (copy.deepcopy(a), copy.deepcopy(b))
        merge(a, b)
        assert (a, b) == before


type _Path = tuple[str, ...]

#: The default table, one entry per group, as the loader's base, less the loader-only fields,
#: which a theme sets only through `line_effects` and refuses inside their group.
_BASE: dict[str, object] = {
    name: {
        field: value
        for field, value in dataclasses.asdict(getattr(Style(), name)).items()
        if (name, field) not in LOADER_FIELDS
    }
    for name in Style.model_fields
}


def _leaves(table: Mapping[str, object], prefix: _Path = ()) -> list[tuple[_Path, object]]:
    """Every leaf of `table` with its key path, descending into every mapping."""
    found: list[tuple[_Path, object]] = []
    for key, value in table.items():
        here = (*prefix, key)
        if isinstance(value, Mapping):
            found.extend(_leaves(value, here))
        else:
            found.append((here, value))
    return found


def _is_colour(value: object) -> bool:
    """Whether the leaf `value` is a `Colour`, which `dataclasses.asdict` keeps as the subclass."""
    return isinstance(value, Colour)


def _is_number(value: object) -> bool:
    """Whether `value` is an int or a float and not a bool."""
    return isinstance(value, int | float) and not isinstance(value, bool)


def _drawable(value: object) -> bool:
    """Whether the leaf `value` is a kind the property gives a new value."""
    if isinstance(value, bool) or _is_number(value):
        return True
    if isinstance(value, tuple):
        return bool(value) and all(_is_number(item) for item in value)
    return _is_colour(value)


#: Every leaf of the default table the property may change, in table order.
_CANDIDATES: tuple[tuple[_Path, object], ...] = tuple(
    (path, value) for path, value in _leaves(_BASE) if _drawable(value)
)

_HEX = st.text(alphabet="0123456789abcdef", min_size=6, max_size=6).map(lambda h: f"#{h}")


def _scaled(value: object, factor: float) -> object:
    """`value` scaled by `factor`: an int stays an int, a float a float, a tuple element-wise."""
    if isinstance(value, int):
        return round(value * factor)
    if isinstance(value, float):
        return value * factor
    assert isinstance(value, tuple)
    return tuple(_scaled(item, factor) for item in value)


def _put(tables: dict[_Path, dict[str, object]], path: _Path, value: object) -> None:
    """Set `value` at `path` under `tables[()]`, making the tables on the way, each kept by its path."""
    for end in range(1, len(path)):
        if path[:end] not in tables:
            child: dict[str, object] = {}
            tables[path[: end - 1]][path[end - 1]] = child
            tables[path[:end]] = child
    tables[path[:-1]][path[-1]] = value


@st.composite
def overrides(draw: st.DrawFn) -> dict[str, object]:
    """Draw an override table giving a few of the default's leaves a new value by their type."""
    picks = draw(
        st.lists(st.sampled_from(range(len(_CANDIDATES))), min_size=1, max_size=8, unique=True)
    )
    factor = draw(st.floats(0.5, 2.0))
    table: dict[str, object] = {}
    tables: dict[_Path, dict[str, object]] = {(): table}
    for index in picks:
        path, value = _CANDIDATES[index]
        if isinstance(value, bool):
            new: object = not value
        elif isinstance(value, str):
            new = draw(_HEX)
        else:
            new = _scaled(value, factor)
        _put(tables, path, new)
    return table


@given(overrides())
@settings(UNTIMED, max_examples=50)
def test_an_override_and_its_expanded_copy_give_one_digest(override: dict[str, object]) -> None:
    """A theme naming only what it changes loads to the same style and digest as its full copy."""
    with tempfile.TemporaryDirectory() as directory:
        short = Path(directory) / "short.yaml"
        full = Path(directory) / "full.yaml"
        short.write_text(dump_theme(override), encoding="utf-8")
        full.write_text(dump_theme(merge(_BASE, override)), encoding="utf-8")
        trimmed, expanded = Style.from_yaml(short), Style.from_yaml(full)
    assert trimmed == expanded
    assert trimmed.digest() == expanded.digest()
