"""Reading one theme file: YAML in, plain data and the line of every key out.

Key types: `ThemeFile`, one file read into plain dicts, tuples and scalars, with the
1-based line of every mapping key and every problem found; `read_theme`, which reads one.

A theme is plain YAML 1.2: one document, a mapping of style groups with string keys. The
reader walks the YAML events first and reports, at its line and key path, every alias,
anchor, merge key, tag, directive, second document, non-string key and duplicate key,
every plain scalar that resolves to something other than a string, number, bool or
null (such as a date), every number that cannot be read (such as `0b_`), and the syntax
error that ends the walk. A file with any such problem loads nothing.
Otherwise it is loaded, and each key that loaded as a non-string or holds no value is
reported and left out.

Does not check keys or values against the model, resolve `extends`, merge themes, read
files from disk, or raise: every problem is returned, and the caller reports them. This
is the one module that touches `ruamel.yaml`. A mapping, a sequence, a bool, an int, a
float and a string come out as the built-in type; a null inside a sequence stays `None`,
for the checker to refuse.

Invariants: `read_theme` never raises for a bad file, because the walk constructs every
number on its own first, so the load never meets a scalar it cannot construct; `table` is
empty whenever the event walk found a problem; `problems` are in line order.
"""

import io
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.constructor import RoundTripConstructor
from ruamel.yaml.error import MarkedYAMLError
from ruamel.yaml.events import (
    AliasEvent,
    CollectionEndEvent,
    CollectionStartEvent,
    DocumentStartEvent,
    Event,
    MappingStartEvent,
    NodeEvent,
    ScalarEvent,
)
from ruamel.yaml.nodes import ScalarNode

from pyntpot.maps.theme_errors import ThemeProblem

#: A problem before it is placed in a file: its key path, its line, its message.
type _Found = tuple[tuple[str, ...], int | None, str]

#: The message for a key that is not a string.
KEYS_ARE_STRINGS = "keys are strings"

#: The resolved tags a plain scalar in a theme may have.
_SCALAR_TAGS = frozenset(
    f"tag:yaml.org,2002:{name}" for name in ("str", "int", "float", "bool", "null")
)

#: The tag a date or time resolves to.
_TIMESTAMP = "tag:yaml.org,2002:timestamp"


@dataclass(frozen=True, kw_only=True)
class ThemeFile:
    """One theme file read into plain data, with where each key sits.

    Attributes:
        path: The file, as the caller named it.
        table: The file's content as plain dicts, tuples and scalars; empty when the
            event walk found a problem.
        lines: The 1-based line of every mapping key, by key path.
        problems: What the walk, the load and the conversion found, in line order.
    """

    path: Path
    table: dict[str, object]
    lines: dict[tuple[str, ...], int]
    problems: tuple[ThemeProblem, ...]


def read_theme(path: Path, text: str) -> ThemeFile:
    """Read the theme file `path`, whose content is `text`, into plain data and its problems.

    Args:
        path: The file, as the caller names it; it is not opened.
        text: The file's content.

    Returns:
        The file's table, the line of every key, and every problem found. Never raises
        for a bad file.
    """
    found = _walk(text)
    if found:
        return _file(path, {}, {}, found)
    loaded = YAML(typ="rt").load(text)
    if loaded is None:
        return _file(path, {}, {}, [])
    if not isinstance(loaded, CommentedMap):
        return _file(path, {}, {}, [((), 1, "a theme is a mapping of style groups")])
    lines: dict[tuple[str, ...], int] = {}
    table = _table(loaded, (), lines, found)
    return _file(path, table, lines, found)


def _file(
    path: Path, table: dict[str, object], lines: dict[tuple[str, ...], int], found: list[_Found]
) -> ThemeFile:
    """Assemble the `ThemeFile` for `path`, placing each found problem in it, in line order."""
    problems = tuple(
        ThemeProblem(path=path, key=".".join(keys), line=line, message=message)
        for keys, line, message in sorted(found, key=lambda one: one[1] or 0)
    )
    return ThemeFile(path=path, table=table, lines=lines, problems=problems)


def _located(exc: MarkedYAMLError, keys: tuple[str, ...]) -> _Found:
    """The problem `exc` names, at its mark's line, against the key path `keys`."""
    mark = exc.problem_mark
    return (keys, None if mark is None else int(mark.line) + 1, str(exc.problem or exc))


# ---------------------------------------------------------------------------
# The event walk
# ---------------------------------------------------------------------------


@dataclass
class _Frame:
    """One open mapping or sequence: its key path, and for a mapping, where its keys stand."""

    path: tuple[str, ...]
    mapping: bool
    expect_key: bool = True
    key: str | None = None
    seen: set[str] = field(default_factory=set)


class _Walk:
    """The state of the event walk: the open collections, the documents seen, the problems."""

    def __init__(self, yaml: YAML) -> None:
        """Start before the first event, resolving and constructing scalars as `yaml` does."""
        self.stack: list[_Frame] = []
        self.documents = 0
        self.found: list[_Found] = []
        self.resolver = yaml.resolver
        self.constructor: RoundTripConstructor = yaml.constructor

    def is_key(self, event: Event) -> bool:
        """Whether `event` is a mapping key."""
        if not isinstance(event, NodeEvent) or not self.stack:
            return False
        return self.stack[-1].mapping and self.stack[-1].expect_key

    def here(self, event: Event | None) -> tuple[str, ...]:
        """The key path being built at `event`: the key itself when `event` is a string key."""
        if not self.stack:
            return ()
        top = self.stack[-1]
        if not top.mapping or (top.expect_key and not isinstance(event, ScalarEvent)):
            return top.path
        if top.expect_key and isinstance(event, ScalarEvent):
            return (*top.path, str(event.value))
        return top.path if top.key is None else (*top.path, top.key)

    def visit(self, event: Event) -> None:
        """Report what `event` breaks, then move the walk past it."""
        here = self.here(event)
        line = event.start_mark.line + 1
        for rule in _RULES:
            message = rule(event, self)
            if message is not None:
                self.found.append((here, line, message))
        self._step(event, here)

    def _step(self, event: Event, here: tuple[str, ...]) -> None:
        """Count documents, and open, close and advance the collections at `event`."""
        if isinstance(event, DocumentStartEvent):
            self.documents += 1
        elif isinstance(event, CollectionEndEvent):
            self.stack.pop()
        elif isinstance(event, NodeEvent):
            self._advance(event)
            if isinstance(event, CollectionStartEvent):
                mapping = isinstance(event, MappingStartEvent)
                self.stack.append(_Frame(path=here, mapping=mapping))

    def _advance(self, event: NodeEvent) -> None:
        """Move the open mapping from key to value, or value to key, past `event`."""
        if not self.stack or not self.stack[-1].mapping:
            return
        top = self.stack[-1]
        if not top.expect_key:
            top.expect_key = True
            return
        top.expect_key = False
        top.key = event.value if isinstance(event, ScalarEvent) else None
        if top.key is not None:
            top.seen.add(top.key)


def _walk(text: str) -> list[_Found]:
    """Every problem the YAML events of `text` show, ending at a syntax error if there is one."""
    yaml = YAML(typ="rt")
    walk = _Walk(yaml)
    try:
        for event in yaml.parse(io.StringIO(text)):
            walk.visit(event)
    except MarkedYAMLError as exc:
        walk.found.append(_located(exc, walk.here(None)))
    return walk.found


def _alias(event: Event, _walk: _Walk) -> str | None:
    """An alias refers to an anchor; a theme reuses values through `extends` instead."""
    return "aliases are not allowed; use extends" if isinstance(event, AliasEvent) else None


def _anchor(event: Event, _walk: _Walk) -> str | None:
    """An anchor names a node for an alias; an alias's own anchor is the alias rule's."""
    anchored = isinstance(event, NodeEvent) and not isinstance(event, AliasEvent)
    if anchored and event.anchor is not None:
        return "anchors are not allowed; use extends"
    return None


def _merge_key(event: Event, walk: _Walk) -> str | None:
    """A `<<` key merges another mapping in; a theme extends another theme instead."""
    if walk.is_key(event) and isinstance(event, ScalarEvent) and event.value == "<<":
        return "merge keys are not allowed; use extends"
    return None


def _tag(event: Event, _walk: _Walk) -> str | None:
    """An explicit tag, such as `!!str`, changes how a value reads."""
    tagged = isinstance(event, ScalarEvent | CollectionStartEvent) and event.tag is not None
    return "tags are not allowed" if tagged else None


def _directive(event: Event, _walk: _Walk) -> str | None:
    """A `%YAML` or `%TAG` directive; `%YAML 1.1` would read `no` as false."""
    if isinstance(event, DocumentStartEvent) and (
        event.version is not None or event.tags is not None
    ):
        return "directives are not allowed: a theme is YAML 1.2"
    return None


def _second_document(event: Event, walk: _Walk) -> str | None:
    """A document after the first in the same file."""
    if isinstance(event, DocumentStartEvent) and walk.documents > 0:
        return "one document per theme file"
    return None


def _key_kind(event: Event, walk: _Walk) -> str | None:
    """A key that is a mapping or a sequence, such as `? [a, b]`."""
    if walk.is_key(event) and isinstance(event, CollectionStartEvent):
        return KEYS_ARE_STRINGS
    return None


def _duplicate(event: Event, walk: _Walk) -> str | None:
    """A key already given in the same mapping."""
    if walk.is_key(event) and isinstance(event, ScalarEvent):
        return "duplicate key" if event.value in walk.stack[-1].seen else None
    return None


def _scalar(event: Event, walk: _Walk) -> str | None:
    """A plain scalar that resolves outside the theme's types, or a number that cannot be read."""
    if not isinstance(event, ScalarEvent) or event.tag is not None or not event.implicit[0]:
        return None
    if walk.is_key(event) and event.value == "<<":
        return None
    tag = str(walk.resolver.resolve(ScalarNode, event.value, event.implicit))
    if tag == _TIMESTAMP:
        return "a theme value is never a date; quote it if a string was meant"
    if tag not in _SCALAR_TAGS:
        return f"cannot read `{event.value}`; quote it if a string was meant"
    return _number(event.value, tag, walk.constructor)


def _number(value: str, tag: str, constructor: RoundTripConstructor) -> str | None:
    """Whether the plain scalar `value`, resolved to `tag`, constructs; only numbers can fail."""
    node = ScalarNode(tag, value)
    try:
        if tag.endswith(":int"):
            constructor.construct_yaml_int(node)
        elif tag.endswith(":float"):
            constructor.construct_yaml_float(node)
    except (ValueError, IndexError):
        return f"cannot read `{value}` as a number"
    return None


#: The rules the walk applies to every event, in the order their problems are reported.
_RULES: tuple[Callable[[Event, _Walk], str | None], ...] = (
    _alias,
    _anchor,
    _merge_key,
    _tag,
    _directive,
    _second_document,
    _key_kind,
    _duplicate,
    _scalar,
)


# ---------------------------------------------------------------------------
# The conversion
# ---------------------------------------------------------------------------


def _table(
    node: CommentedMap,
    prefix: tuple[str, ...],
    lines: dict[tuple[str, ...], int],
    found: list[_Found],
) -> dict[str, object]:
    """`node` as a plain dict, recording each key's line and each key that cannot stay."""
    table: dict[str, object] = {}
    for key, value in node.items():
        line = node.lc.key(key)[0] + 1
        here = (*prefix, str(key))
        if not isinstance(key, str):
            found.append((here, line, KEYS_ARE_STRINGS))
            continue
        lines[here] = line
        if value is None:
            found.append((here, line, "has no value"))
            continue
        table[key] = _plain(value, here, lines, found)
    return table


def _plain(
    value: object,
    path: tuple[str, ...],
    lines: dict[tuple[str, ...], int],
    found: list[_Found],
) -> object:
    """`value` as plain data: a mapping a dict, a sequence a tuple, a scalar its built-in type."""
    if isinstance(value, CommentedMap):
        return _table(value, path, lines, found)
    if isinstance(value, CommentedSeq):
        return tuple(_plain(item, path, lines, found) for item in value)
    for kind in (bool, int, float, str):
        if isinstance(value, kind):
            return kind(value)
    return value
