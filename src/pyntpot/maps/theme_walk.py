"""The event walk over one theme file: every YAML feature a theme may not use, before a load.

Key names: `walk`, which parses a theme's text into YAML events and returns every problem
they show, each as its key path, its 1-based line and its message; `Found`, that triple;
`KEYS_ARE_STRINGS`, the message for a key that is not a string; `MAX_DEPTH`, how deep
mappings and sequences may nest.

The walk reports every alias, anchor, merge key, tag, directive, second document, key
that is not a string, duplicate key, mapping or sequence nested deeper than `MAX_DEPTH`,
plain scalar that resolves to something other than a string, number, bool or null (such
as a date), number that cannot be read (such as `0b_`), and the character or syntax error
that ends the walk.

Does not load the text, build plain data, or check keys and values against the model.
Never raises for any text: every problem, a reader's or a parser's included, is returned.

Invariants: when the walk finds nothing, every mapping key is a string whose text is its
value, so two keys are equal only when they are spelled alike, and the walk has seen each
of those; the load of a text the walk passes therefore meets no key it cannot construct,
no duplicate key and no nesting deep enough to exhaust the interpreter's stack.
"""

import io
from collections.abc import Callable
from dataclasses import dataclass, field

from ruamel.yaml import YAML
from ruamel.yaml.constructor import RoundTripConstructor
from ruamel.yaml.error import MarkedYAMLError, YAMLError
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
from ruamel.yaml.reader import ReaderError

#: A problem before it is placed in a file: its key path, its line, its message.
type Found = tuple[tuple[str, ...], int | None, str]

#: The message for a key that is not a string.
KEYS_ARE_STRINGS = "keys are strings"

#: How many mappings and sequences may be open at once. The packaged themes nest four
#: deep (`brush.overrides.stroke.jitter_px` is three mappings in the top one), so this is
#: far past any real theme and far short of what exhausts the interpreter's stack when
#: the loader builds the nested values.
MAX_DEPTH = 32

#: The prefix of a core-schema tag.
_CORE = "tag:yaml.org,2002:"

#: The resolved tags a plain scalar in a theme may have.
_SCALAR_TAGS = frozenset(f"{_CORE}{name}" for name in ("str", "int", "float", "bool", "null"))

#: The tag a date or time resolves to.
_TIMESTAMP = f"{_CORE}timestamp"

#: The tag a plain string resolves to.
_STR = f"{_CORE}str"


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
        self.found: list[Found] = []
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

    def resolves_to(self, event: ScalarEvent) -> str:
        """The tag the plain scalar `event` resolves to."""
        return str(self.resolver.resolve(ScalarNode, event.value, event.implicit))

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
        if top.key is not None and _string_key(event, self):
            top.seen.add(top.key)


def walk(text: str) -> list[Found]:
    """Every problem the YAML events of `text` show, ending at the error that stops the parse.

    Args:
        text: A theme file's content.

    Returns:
        Each problem as its key path, its 1-based line (`None` when it has no place) and
        its message, in the order found. Never raises for any text.
    """
    yaml = YAML(typ="rt")
    state = _Walk(yaml)
    try:
        for event in yaml.parse(io.StringIO(text)):
            state.visit(event)
    except YAMLError as exc:
        state.found.append(_located(exc, text, state.here(None)))
    return state.found


def _located(exc: YAMLError, text: str, keys: tuple[str, ...]) -> Found:
    """The problem `exc` names, at its line in `text`, against the key path `keys`.

    A reader's error, for a character no YAML file may hold, is located by its position
    and named for the file as a whole; a parser's or scanner's by its mark.
    """
    if isinstance(exc, ReaderError):
        before = text[: exc.position]
        line = len(f"{before}.".splitlines())
        message = f"unacceptable character #x{exc.character:04x}: {exc.reason}"
        return ((), line, message)
    if isinstance(exc, MarkedYAMLError):
        mark = exc.problem_mark
        return (keys, None if mark is None else int(mark.line) + 1, str(exc.problem or exc))
    return (keys, None, str(exc))


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


def _depth(event: Event, walk: _Walk) -> str | None:
    """A mapping or sequence that opens with `MAX_DEPTH` already open; deeper ones are not told."""
    if isinstance(event, CollectionStartEvent) and len(walk.stack) == MAX_DEPTH:
        return f"nested more than {MAX_DEPTH} deep"
    return None


def _key_kind(event: Event, walk: _Walk) -> str | None:
    """A key that is not a string: a mapping, a sequence, or a plain `5`, `true` or `~`."""
    if walk.is_key(event) and not _string_key(event, walk):
        return KEYS_ARE_STRINGS
    return None


def _duplicate(event: Event, walk: _Walk) -> str | None:
    """A string key whose text is already a key of the same mapping."""
    if walk.is_key(event) and isinstance(event, ScalarEvent) and _string_key(event, walk):
        return "duplicate key" if event.value in walk.stack[-1].seen else None
    return None


def _string_key(event: Event, walk: _Walk) -> bool:
    """Whether the key `event` counts as a string: quoted, or plain and resolving to one.

    An alias, a tagged scalar and a `<<` count as strings here because each is already
    its own rule's problem, which this one does not repeat.
    """
    if not isinstance(event, ScalarEvent):
        return isinstance(event, AliasEvent)
    if event.tag is not None or not event.implicit[0] or event.value == "<<":
        return True
    return walk.resolves_to(event) == _STR


def _scalar(event: Event, walk: _Walk) -> str | None:
    """A plain value that resolves outside the theme's types, or a number that cannot be read."""
    if not isinstance(event, ScalarEvent) or event.tag is not None or not event.implicit[0]:
        return None
    if walk.is_key(event):
        return None
    tag = walk.resolves_to(event)
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
    _depth,
    _key_kind,
    _duplicate,
    _scalar,
)
